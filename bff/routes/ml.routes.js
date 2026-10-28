import Router from 'express'
import { authMiddleware } from '../middleware/auth.middleware.js'
import fileController from '../controllers/fileController.js'
import { mlController } from '../controllers/mlController.js'

const router = new Router()

router.post(
  '/start-analyze/:fileId',
  authMiddleware,
  mlController.startAnalysis
)
router.get('/status-analyze', mlController.getStatus)
router.get('/feature', authMiddleware, mlController.getFeature)

export { router }
