import Router from 'express'
import { authMiddleware } from '../middleware/auth.middleware.js'
import fileController from '../controllers/fileController.js'

const router = new Router()

router.post('', authMiddleware, fileController.createDir)
router.post('/upload', authMiddleware, fileController.uploadFile)

router.post('/upload/init', authMiddleware, fileController.initUpload)
router.post('/upload/chunk', authMiddleware, fileController.uploadChunk)
router.post('/upload/complete', authMiddleware, fileController.completeUpload)

router.post('/avatar', authMiddleware, fileController.uploadAvatar)
router.post('/change', authMiddleware, fileController.changeFileLink)
router.get('', authMiddleware, fileController.getFiles)
router.get('/links', authMiddleware, fileController.getLinks)
router.get('/download', authMiddleware, fileController.downloadFile)
router.get('/search', authMiddleware, fileController.searchFile)
router.delete('/', authMiddleware, fileController.deleteFile)
router.delete('/avatar', authMiddleware, fileController.deleteAvatar)

export { router }
