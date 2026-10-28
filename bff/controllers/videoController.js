import fs from 'fs'
import path from 'path'
import { File } from '../models/index.js'

class VideoController {
  async streamVideo (req, res) {
    try {
      const { fileId } = req.params

      // Получаем информацию о файле из БД
      const file = await File.findByPk(fileId)
      if (!file) {
        return res.status(404).json({ error: 'File not found' })
      }

      // Проверяем права доступа
      if (file.userId.toString() !== req.user.id && !file?.isPublic) {
        return res.status(403).json({ error: 'Access denied' })
      }

      // const videoPath = file.path // путь к видео на диске
      const videoPath = `/app/dataset/${file.userId}/features/${file.name}`
      console.debug('videoPath: ', videoPath)
      const stat = fs.statSync(videoPath)
      const fileSize = stat.size
      const range = req.headers.range

      // Обработка Range заголовков для частичной загрузки
      if (range) {
        const parts = range.replace(/bytes=/, '').split('-')
        const start = parseInt(parts[0], 10)
        const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1
        const chunksize = end - start + 1

        const stream = fs.createReadStream(videoPath, { start, end })

        res.writeHead(206, {
          'Content-Range': `bytes ${start}-${end}/${fileSize}`,
          'Accept-Ranges': 'bytes',
          'Content-Length': chunksize,
          'Content-Type': 'video/mp4'
        })

        stream.pipe(res)
      } else {
        // Полный файл
        res.writeHead(200, {
          'Content-Length': fileSize,
          'Content-Type': 'video/mp4'
        })
        fs.createReadStream(videoPath).pipe(res)
      }
    } catch (error) {
      console.error('Streaming error:', error)
      res.status(500).json({ error: 'Streaming error' })
    }
  }

  async getVideoMetadata (req, res) {
    try {
      const { fileId } = req.params
      const file = await File.findByPk(fileId)

      if (!file) {
        return res.status(404).json({ error: 'File not found' })
      }

      // Получаем длительность видео с помощью ffprobe
      const { exec } = require('child_process')
      const videoPath = file.path

      exec(
        `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${videoPath}"`,
        (error, stdout) => {
          if (error) {
            return res.json({
              duration: 0,
              size: file.size,
              mimeType: file.mimeType
            })
          }

          res.json({
            duration: parseFloat(stdout),
            size: file.size,
            mimeType: file.mimeType,
            name: file.name
          })
        }
      )
    } catch (error) {
      res.status(500).json({ error: 'Metadata error' })
    }
  }
}

export const videoController = new VideoController()
