import express from 'express'
import fileUpload from 'express-fileupload'
import cookieParser from 'cookie-parser'
import { router as authRouter } from './routes/auth.routes.js'
import { router as fileRouter } from './routes/file.routes.js'
import { router as videoRouter } from './routes/video.routes.js'
import { router as mlRouter } from './routes/ml.routes.js'
import sequelize from './DB/database.js'
import { errorHandler } from './middleware/errorMiddleware.js'
import { CONFIG } from './config/config.js'
import cors from 'cors'
import { userService } from './services/userService.js'

console.log(CONFIG.VERSION)

const app = express()
const PORT = CONFIG.PORT

const allowedOrigins = [
  'http://127.0.0.1:3000',
  'http://localhost:3000',
  'http://localhost',
  'http://c1r011v08.amm.vsu.ru',
  'http://www.amm.vsu.ru',
  'https://c1r011v08.amm.vsu.ru',
  'https://www.amm.vsu.ru'
]

const corsOptions = {
  origin: function (origin, callback) {
    if (!origin) return callback(null, true)

    if (!CONFIG.IS_PROD || allowedOrigins.includes(origin)) {
      callback(null, true)
    } else {
      callback(null, false) // Не блокируем, а просто запрещаем
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'Range',
    'Origin',
    'X-Requested-With',
    'Accept'
  ],
  exposedHeaders: [
    'Content-Range',
    'Accept-Ranges',
    'Content-Length',
    'Content-Type'
  ],
  credentials: true,
  optionsSuccessStatus: 200
}

// app.use(cors(corsOptions))

// Дополнительный middleware для видео запросов
app.use('/api/video', (req, res, next) => {
  // Разрешаем все заголовки для видео
  res.setHeader('Cross-Origin-Resource-Policy', 'cross-origin')
  res.setHeader('Cross-Origin-Embedder-Policy', 'credentialless')
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin')

  // Для preflight запросов
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
    res.setHeader(
      'Access-Control-Allow-Headers',
      'Range, Authorization, Content-Type'
    )
    res.setHeader('Access-Control-Max-Age', '86400')
    return res.status(200).end()
  }
  next()
})

app.use(cors(corsOptions))
// app.use(cors({
//     origin: true,
//     credentials: true
// }));
app.use(
  fileUpload({
    defCharset: 'utf8',
    defParamCharset: 'utf8'
  })
)
// app.use(corsMiddleware)
app.use(express.json())
app.use(cookieParser())
app.use(express.static('static'))
app.use(express.static('public'))
app.use('/api/auth', authRouter)
app.use('/api/files', fileRouter)
app.use('/api/video', videoRouter)
app.use(`/api/ml`, mlRouter)
app.use(errorHandler)

const start = async () => {
  try {
    await sequelize
      .sync()
      .then(() => console.log('DB is start'))
      .catch(error => console.log('ERROR! DB is not start', error))
    await sequelize.query('PRAGMA journal_mode = WAL;')
    await sequelize.query('PRAGMA synchronous = NORMAL;')
    await sequelize.query('PRAGMA busy_timeout = 5000;') // Ожидание 5 сек вместо ошибки
    try {
      if (CONFIG.SUPERUSER_LOGIN && CONFIG.SUPREUSER_PASS) {
        console.log('CONFIG.SUPERUSER_LOGIN', CONFIG.SUPERUSER_LOGIN)
        console.log('CONFIG.SUPREUSER_PASS', CONFIG.SUPREUSER_PASS)
        await userService.registration(
          CONFIG.SUPERUSER_LOGIN,
          CONFIG.SUPREUSER_PASS,
          new Date(),
          'male'
        )
      }
    } catch {
      console.log('')
    }

    app.listen(PORT, '0.0.0.0', () => {
      console.log('Server started on port ', PORT)
    })
  } catch (e) {
    console.log(e)
  }
}

start()
