import fs from 'fs'
import path from 'path'
import { CONFIG } from '../config/config.js'

class FileService {
  createDir (file) {
    const filePath = path.join(CONFIG.FILE_PATH, file.user, file.path)
    return new Promise((resolve, reject) => {
      try {
        if (!fs.existsSync(filePath)) {
          fs.mkdirSync(filePath)
          return resolve({ message: 'File was created' })
        } else {
          return reject({ message: 'File already exist' })
        }
      } catch (e) {
        console.log(e)
        return reject({ message: 'File error' })
      }
    })
  }

  deleteFile (file) {
    const path = this.getPath(file)
    if (file.type === 'dir') {
      fs.rmdirSync(path)
    } else {
      fs.unlinkSync(path)
    }
  }

  deleteFileLink (path, linkName) {
    fs.readFile(path, 'utf-8', (err, data) => {
      if (err) {
        console.log(`Can't read file`)
      }
      let jsonData = JSON.parse(data)
      delete jsonData[linkName]
      const updatedData = JSON.stringify(jsonData, null, 4)

      fs.writeFile(path, updatedData, 'utf-8', err => {
        if (err) {
          console.error(`Can't write file`, err)
          return
        }
        console.log('delete link done')
      })
    })
  }

  addFileLink (path, linkName, link) {
    const newData = {
      [linkName]: {
        type: 'linkNested',
        content: `${link}`
      }
    }
    fs.readFile(path, 'utf-8', (err, data) => {
      if (err) {
        console.log(`Can't read file`)
      }
      let jsonData = JSON.parse(data)
      Object.assign(jsonData, newData)
      const updatedData = JSON.stringify(jsonData, null, 4)
      fs.writeFile(path, updatedData, 'utf-8', err => {
        if (err) {
          console.error(`Can't write file`, err)
          return
        }
        console.log('add link done')
      })
    })
  }

  changeFileLink (path, linkNameOld, linkName, link, callback) {
    fs.readFile(path, 'utf8', (err, data) => {
      if (err) {
        console.error('Ошибка чтения файла:', err)
        return
      }

      let jsonData = JSON.parse(data)
      if (jsonData.hasOwnProperty(linkNameOld)) {
        if (linkNameOld !== linkName) {
          jsonData[linkName] = jsonData[linkNameOld]
          delete jsonData[linkNameOld]
        }
        jsonData[linkName].content = link
      } else {
        console.error('Объект с таким названием не найден в файле.')
        return
      }
      const updatedData = JSON.stringify(jsonData, null, 4)
      fs.writeFile(path, updatedData, 'utf8', err => {
        if (err) {
          console.error('Ошибка записи файла:', err)
          return
        }
        console.log('Название и ссылка успешно изменены в файле.')
      })
      const arr = []
      Object.entries(jsonData).forEach(([key, value]) => {
        if (value.type === 'linkNested') {
          arr.push({ name: key, content: value.content })
        }
      })
      callback(arr)
    })
  }

  getPath (file) {
    return path.join(CONFIG.FILE_PATH, file.user, file.path)
  }

  getPathFeature (filename, userId = null) {
    if (userId) {
      return path.join(CONFIG.DATASET_DIR, userId, 'features', filename)
    }
    return path.join(CONFIG.DATASET_DIR, 'features', filename)
  }
}

export default new FileService()
