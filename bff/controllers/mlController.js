import { File, Tag } from '../models/index.js'

import path from 'path'
import fileService from '../services/fileService.js'
import fs from 'fs'

import { mlService } from '../services/mlSerivce.js'

class MLController {
  async getFeature (req, res) {
    try {
      const userId = req.user.id

      const file = await File.findOne({
        where: { _id: req.query.id, user: userId }
      })

      if (!file) {
        return res.status(404).json({
          success: false,
          message: 'Файл не найден'
        })
      }

      const jsonFileName = file.name.replace(/\.[^/.]+$/, '.json')
      console.log(jsonFileName)
      let path = fileService.getPathFeature(jsonFileName)

      if (!fs.existsSync(path)) {
        path = fileService.getPathFeature(jsonFileName, userId)
        console.log(path)
        if (!fs.existsSync(path)) {
          return res.status(404).json({
            success: false,
            message: `Файл аналитики '${jsonFileName}' не найден`
          })
        }
      }

      const fileContent = fs.readFileSync(path, 'utf8')
      const jsonData = JSON.parse(fileContent)

      // Извлекаем ID видео
      const videoId =
        jsonData.video_metadata?.video_id ||
        file.name.replace(/\.[^/.]+$/, '') ||
        'unknown'

      // Получение предсказания от ML модели
      let mlPrediction = await mlService.getMLPrediction(userId, videoId)

      const response = {
        success: true,
        fileInfo: {
          id: file._id,
          name: file.name,
          jsonFileName: jsonFileName,
          videoId: videoId,
          size: file.size,
          date: file.date
        },
        analytics: jsonData,
        mlPrediction: mlPrediction
      }

      return res.json(response)
    } catch (e) {
      console.error('getFeature error:', e)

      if (e instanceof SyntaxError) {
        return res.status(400).json({
          success: false,
          message: 'Неверный формат JSON файла'
        })
      }

      res.status(500).json({
        success: false,
        message: 'Ошибка загрузки аналитики',
        error: process.env.NODE_ENV === 'development' ? e.message : undefined
      })
    }
  }

  async startAnalysis (req, res) {
    try {
      const { fileId } = req.params

      const file = await File.findOne({
        where: { _id: fileId, user: req.user.id }
      })

      if (!file) {
        return res.status(404).json({ error: 'File not found' })
      }

      // Проверяем, не анализируется ли уже
      const status = await mlService.getStatus()
      if (status.is_analyzing) {
        return res.status(409).json({
          error: 'Другое видео уже анализируется',
          progress: status.progress,
          current_video: status.current_video
        })
      }

      const videoPath = fileService.getPath(file)

      // Запускаем анализ (это может занять много времени!)
      const result = await mlService.movment_analyze(req.user.id, videoPath)

      file.hasAnalysis = true
      await file.save()

      res.json({
        status: 'completed',
        result: result
      })
    } catch (error) {
      console.error('Start analysis error:', error)

      // Если 409 - другой анализ в процессе
      if (error.message.includes('Уже выполняется')) {
        return res.status(409).json({ error: error.message })
      }

      res.status(500).json({ error: error.message })
    }
  }

  async getStatus (req, res) {
    try {
      const status = await mlService.getStatus()
      res.json(status)
    } catch (error) {
      res.status(500).json({ error: error.message })
    }
  }
}
const mlController = new MLController()
export { mlController }
