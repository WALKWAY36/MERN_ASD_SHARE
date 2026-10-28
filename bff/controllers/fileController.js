import fileService from '../services/fileService.js'
import fs from 'fs'
import User from '../models/User.js'
import { File, Tag } from '../models/index.js'
import { v4 as uuidv4 } from 'uuid'
import path from 'path'
import { CONFIG } from '../config/config.js'
import sequelize from '../DB/database.js'

import { mlService } from '../services/mlSerivce.js'

const activeUploads = new Map()

const cleanupTempFiles = tempDir => {
  try {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true })
    }
  } catch (e) {
    console.error('Cleanup error:', e)
  }
}

class FileController {
  async createDir (req, res) {
    try {
      const { name, type, parent } = req.body
      const file = new File({ name, type, parent, user: req.user.id })
      const parentFile = await File.findOne({ where: { _id: parent } })
      if (!parentFile) {
        file.path = name
        await fileService.createDir(file)
      } else {
        parentFile.childs = file._id
        await parentFile.save()
        file.path = path.join(parentFile.path, file.name)
        await fileService.createDir(file)
      }
      await file.save()
      console.log('create dir done')
      return res.json(file)
    } catch (e) {
      console.log('create dir error', e)
      return res.status(400).json(e)
    }
  }

  async getFiles (req, res) {
    try {
      const { sort } = req.query
      let files
      switch (sort) {
        case 'name':
          files = await File.findAll({
            where: {
              user: req.user.id,
              parent: req.query.parent ? req.query.parent : null
            },
            order: [['name', 'ASC']],
            include: {
              model: Tag,
              as: 'tags',
              attributes: ['name'],
              through: { attributes: [] }
            }
          })
          break
        case 'type':
          files = await File.findAll({
            where: {
              user: req.user.id,
              parent: req.query.parent ? req.query.parent : null
            },
            order: [['type', 'ASC']],
            include: {
              model: Tag,
              as: 'tags',
              attributes: ['name'],
              through: { attributes: [] }
            }
          })
          break
        case 'date':
          files = await File.findAll({
            where: {
              user: req.user.id,
              parent: req.query.parent ? req.query.parent : null
            },
            order: [['date', 'ASC']],
            include: {
              model: Tag,
              as: 'tags',
              attributes: ['name'],
              through: { attributes: [] }
            }
          })
          break
        default:
          files = await File.findAll({
            where: {
              user: req.user.id,
              parent: req.query.parent ? req.query.parent : null
            },
            include: {
              model: Tag,
              as: 'tags',
              attributes: ['name'],
              through: { attributes: [] }
            }
          })
          break
      }
      console.log('get Files done')
      return res.json(files)
    } catch (e) {
      console.log('get Files error', e)
      return res.status(500).json({ message: 'Can not get files' })
    }
  }

  async getLinks (req, res) {
    try {
      console.log('Получено содержимое .txt')
      const file = await File.findOne({
        where: { _id: req.query.fileId }
      })
      const pathToFile = path.join(
        CONFIG.FILE_PATH,
        req.user.id,
        file.dataValues.path
      )
      fs.readFile(pathToFile, 'utf-8', (err, data) => {
        if (err) {
          console.log(`Can't read file`)
        }
        const obj = JSON.parse(data)
        const arr = []
        Object.entries(obj).forEach(([key, value]) => {
          if (value.type === 'linkNested') {
            arr.push({ name: key, content: value.content })
          }
        })
        console.log('get Links done')
        return res.json(arr)
      })
    } catch (e) {
      return res.status(500).json({ message: 'Can not get files' })
    }
  }

  // 1. Инициализация загрузки
  async initUpload (req, res) {
    try {
      const { fileName, fileSize, totalChunks, parent, tags } = req.body
      const user = await User.findOne({ where: { _id: req.user.id } })

      // Проверка места на диске
      if (user.usedSpace + fileSize > user.diskSpace) {
        return res.status(400).json({ message: 'Нет места на диске' })
      }

      // Проверка родительской папки
      const parentFolder = parent
        ? await File.findOne({ where: { user: req.user.id, _id: parent } })
        : null

      // Создаем уникальный ID для загрузки
      const uploadId = uuidv4()

      // Создаем временную директорию для чанков
      const tempDir = path.join(CONFIG.FILE_PATH, 'temp', uploadId)
      if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true })
      }

      // Сохраняем информацию о загрузке
      activeUploads.set(uploadId, {
        fileName,
        fileSize,
        totalChunks,
        uploadedChunks: [],
        parent: parentFolder?._id,
        user: user._id,
        tags: tags || [],
        tempDir,
        createdAt: Date.now()
      })

      res.json({ uploadId })
    } catch (e) {
      console.error('Init upload error:', e)
      res.status(500).json({ message: 'Ошибка инициализации загрузки' })
    }
  }

  // 2. Загрузка чанка
  async uploadChunk (req, res) {
    try {
      const { uploadId, chunkIndex } = req.body
      const chunk = req.files.chunk

      const uploadInfo = activeUploads.get(uploadId)
      if (!uploadInfo) {
        return res.status(404).json({ message: 'Загрузка не найдена' })
      }

      // Сохраняем чанк
      const chunkPath = path.join(uploadInfo.tempDir, `chunk_${chunkIndex}`)
      await chunk.mv(chunkPath)

      uploadInfo.uploadedChunks.push(parseInt(chunkIndex))

      res.json({
        message: 'Чанк загружен',
        uploaded: uploadInfo.uploadedChunks.length,
        total: uploadInfo.totalChunks
      })
    } catch (e) {
      console.error('Upload chunk error:', e)
      res.status(500).json({ message: 'Ошибка загрузки чанка' })
    }
  }

  // 3. Завершение загрузки
  async completeUpload (req, res) {
    try {
      const { uploadId } = req.body
      const uploadInfo = activeUploads.get(uploadId)

      if (!uploadInfo) {
        return res.status(404).json({ message: 'Загрузка не найдена' })
      }

      // Проверяем, что все чанки загружены
      if (uploadInfo.uploadedChunks.length !== uploadInfo.totalChunks) {
        return res.status(400).json({
          message: 'Не все чанки загружены',
          uploaded: uploadInfo.uploadedChunks.length,
          total: uploadInfo.totalChunks
        })
      }

      const user = await User.findOne({ where: { _id: uploadInfo.user } })
      const parent = uploadInfo.parent
        ? await File.findOne({ where: { _id: uploadInfo.parent } })
        : null

      // Определяем финальный путь файла
      let finalPath
      if (parent) {
        finalPath = path.join(
          CONFIG.FILE_PATH,
          user._id,
          parent.path,
          uploadInfo.fileName
        )
      } else {
        finalPath = path.join(CONFIG.FILE_PATH, user._id, uploadInfo.fileName)
      }

      // Проверяем существование файла
      if (fs.existsSync(finalPath)) {
        // Удаляем временные файлы
        cleanupTempFiles(uploadInfo.tempDir)
        activeUploads.delete(uploadId)
        return res.status(400).json({ message: 'Файл уже существует' })
      }

      // Объединяем чанки
      const writeStream = fs.createWriteStream(finalPath)

      for (let i = 0; i < uploadInfo.totalChunks; i++) {
        const chunkPath = path.join(uploadInfo.tempDir, `chunk_${i}`)
        const chunkBuffer = fs.readFileSync(chunkPath)
        writeStream.write(chunkBuffer)
      }

      writeStream.end()

      await new Promise((resolve, reject) => {
        writeStream.on('finish', resolve)
        writeStream.on('error', reject)
      })

      // Сохраняем в БД
      const transaction = await sequelize.transaction()

      const type = uploadInfo.fileName.split('.').pop()
      let filePath = uploadInfo.fileName
      if (parent) {
        filePath = path.join(parent.path, uploadInfo.fileName)
      }

      const dbFile = await File.create(
        {
          name: uploadInfo.fileName,
          type,
          size: uploadInfo.fileSize,
          path: filePath,
          parent: parent?._id,
          user: user._id
        },
        { transaction }
      )

      // Обновляем использованное место
      user.usedSpace = user.usedSpace + uploadInfo.fileSize
      await user.save({ transaction })

      // Добавляем теги
      const tags = []
      for (const tagName of uploadInfo.tags) {
        if (tagName) {
          const [tag] = await Tag.findOrCreate({
            where: { name: tagName },
            transaction
          })
          tags.push(tag)
        }
      }
      await dbFile.setTags(tags, { transaction })

      await transaction.commit()

      // Удаляем временные файлы
      cleanupTempFiles(uploadInfo.tempDir)
      activeUploads.delete(uploadId)

      console.log('Upload completed:', uploadInfo.fileName)
      res.json(dbFile)
    } catch (e) {
      console.error('Complete upload error:', e)
      res.status(500).json({ message: 'Ошибка при завершении загрузки' })
    }
  }

  // Вспомогательная функция для очистки временных файлов
  cleanupTempFiles (tempDir) {
    try {
      if (fs.existsSync(tempDir)) {
        fs.rmSync(tempDir, { recursive: true, force: true })
      }
    } catch (e) {
      console.error('Cleanup error:', e)
    }
  }

  // Оригинальный метод для обратной совместимости
  async uploadFile (req, res) {
    try {
      const file = req.files.file
      const parent = await File.findOne({
        where: {
          user: req.user.id,
          _id: req.body.parent ? req.body.parent : null
        }
      })
      const user = await User.findOne({ where: { _id: req.user.id } })

      if (user.usedSpace + file.size > user.diskSpace) {
        return res.status(400).json({ message: 'Нет места на диске' })
      }

      user.usedSpace = user.usedSpace + file.size

      let paths
      if (parent) {
        paths = path.join(CONFIG.FILE_PATH, user._id, parent.path, file.name)
      } else {
        paths = path.join(CONFIG.FILE_PATH, user._id, file.name)
      }

      if (fs.existsSync(paths)) {
        return res.status(400).json({ message: 'Файл уже существует' })
      }

      file.mv(paths)

      const type = file.name.split('.').pop()
      let filePath = file.name
      if (parent) {
        filePath = path.join(parent.path, file.name)
      }

      const transaction = await sequelize.transaction()

      const dbFile = await File.create(
        {
          name: file.name,
          type,
          size: file.size,
          path: filePath,
          parent: parent?._id,
          user: user._id
        },
        { transaction }
      )

      await user.save({ transaction })

      const tagNames = Array.isArray(req.body.tags)
        ? req.body.tags
        : req.body.tags
        ? [req.body.tags]
        : []

      const tags = []
      for (const tagName of tagNames) {
        if (tagName) {
          const [tag] = await Tag.findOrCreate({
            where: { name: tagName },
            transaction
          })
          tags.push(tag)
        }
      }

      await dbFile.setTags(tags, { transaction })
      await transaction.commit()

      console.log('Upload file done')

      const finalPath = path.join(CONFIG.FILE_PATH, user._id, file.name)

      res.json(dbFile)
    } catch (e) {
      console.log('Upload file error', e)
      return res.status(500).json({
        message: 'При загрузке файла произошла ошибка'
      })
    }
  }

  async downloadFile (req, res) {
    try {
      const file = await File.findOne({
        where: { _id: req.query.id, user: req.user.id }
      })
      const path = fileService.getPath(file)
      if (fs.existsSync(path)) {
        return res.download(path, file.name)
      }
      console.log('download File done')
      return res.status(400).json({ message: 'Ошибка скачивания' })
    } catch (e) {
      console.log('download File error', e)
      res.status(500).json({ message: 'Ошибка скачивания файла' })
    }
  }

  async deleteFile (req, res) {
    try {
      const file = await File.findOne({
        where: { _id: req.query.id }
      })
      if (!file) {
        return res.status(400).json({ message: 'Файл не найден' })
      }
      const user = await User.findOne({
        where: { _id: req.query.userId }
      })
      user.usedSpace = user.usedSpace - file.size
      await user.save()
      fileService.deleteFile(file)
      await file.destroy()
      console.log('delete File done')
      return res.json({ message: 'Файл был удалён' })
    } catch (e) {
      console.log('delete File error', e)
      return res.status(400).json({ message: 'Dir is not empty' })
    }
  }

  async changeFileLink (req, res) {
    try {
      const file = await File.findOne({
        where: { _id: req.body.fileId, user: req.user.id }
      })
      if (!file) {
        return res.status(400).json({ message: 'Файл не найден' })
      }
      const path = fileService.getPath(file)
      if (req.body.type === 'add') {
        fileService.addFileLink(path, req.body.linkName, req.body.link)
        return res.json({ message: 'link was added' })
      } else if (req.body.type === 'change') {
        fileService.changeFileLink(
          path,
          req.body.linkNameOld,
          req.body.linkName,
          req.body.link,
          arr => {
            res.json(arr)
          }
        )
      } else {
        fileService.deleteFileLink(path, JSON.parse(req.body.link).name)
        return res.json({ message: 'link was deleted' })
      }
    } catch (e) {
      console.log('delete link error', e)
      return res.status(400).json({ message: 'delete link error' })
    }
  }

  async searchFile (req, res) {
    try {
      const searchName = req.query.search
      let files = await File.findAll({
        where: { user: req.user.id }
      })
      files = files.filter(file => file.name.includes(searchName))
      console.log('search File done')
      return res.json(files)
    } catch (e) {
      console.log('search File error', e)
      return res.status(400).json({ message: 'Search error' })
    }
  }

  async uploadAvatar (req, res) {
    try {
      const file = req.files.file
      const user = await User.findByPk(req.user.id)
      const avatarName = uuidv4() + '.jpg'
      file.mv(path.join(CONFIG.STATIC_PATH, avatarName))
      user.avatar = avatarName
      await user.save()
      console.log('upload Avatar done')
      return res.json(user)
    } catch (e) {
      console.log('upload Avatar error', e)
      return res
        .status(400)
        .json({ message: 'При загрузке аватара произошла ошибка' })
    }
  }

  async deleteAvatar (req, res) {
    try {
      const user = await User.findByPk(req.user.id)
      fs.unlinkSync(path.join(CONFIG.STATIC_PATH, user.avatar))
      user.avatar = null
      await user.save()
      console.log('delete Avatar done')
      return res.json(user)
    } catch (e) {
      console.log('delete Avatar error', e)
      return res
        .status(400)
        .json({ message: 'При удалении аватара произошла ошибка' })
    }
  }
}

export default new FileController()
