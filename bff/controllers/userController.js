import { ApiError } from '../exceptions/apiError.js'
import { userService } from '../services/userService.js'
import { validationResult } from 'express-validator'
import { fileURLToPath } from 'url'
import path, { dirname } from 'path'
import { CONFIG } from '../config/config.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

class UserController {
  async registration (req, res, next) {
    try {
      const errors = validationResult(req)
      if (!errors.isEmpty()) {
        return next(ApiError.BadRequest('Ошибка при валидации', errors.array()))
      }

      const { email, password, date, gender } = req.body
      const userData = await userService.registration(
        email,
        password,
        date,
        gender
      )
      res.cookie('refreshToken', userData.refreshToken, {
        maxAge: 30 * 24 * 60 * 60 * 1000,
        httpOnly: true,
        sameSite: 'lax'
      })
      return res.json(userData)
    } catch (e) {
      next(e)
    }
  }

  async login (req, res, next) {
    try {
      const { email, password } = req.body
      const userData = await userService.login(email, password)
      if (CONFIG.IS_PROD) {
        res.cookie('refreshToken', userData.refreshToken, {
          maxAge: 30 * 24 * 60 * 60 * 1000,
          httpOnly: true,
          sameSite: 'lax'
        })
      } else {
        res.cookie('refreshToken', userData.refreshToken, {
          maxAge: 30 * 24 * 60 * 60 * 1000,
          httpOnly: true,
          sameSite: 'lax', // или 'Strict' для DEV
          secure: false
        })
      }

      return res.json(userData)
    } catch (e) {
      next(e)
    }
  }

  async logout (req, res, next) {
    try {
      const { refreshToken } = req.cookies
      const token = await userService.logout(refreshToken)
      res.clearCookie('refreshToken')
      return res.json(token)
    } catch (e) {
      next(e)
    }
  }

  async activate (req, res, next) {
    try {
      const activationLink = req.params.link
      await userService.activate(activationLink)
      const pathSuccessPage = path.join(
        __dirname,
        '../',
        'public',
        'success.html'
      )
      res.sendFile(pathSuccessPage)
    } catch (e) {
      next(e)
    }
  }

  async refresh (req, res, next) {
    try {
      const { refreshToken } = req.cookies
      console.log('refresh req.cookies: ', refreshToken)
      const userData = await userService.refresh(refreshToken)
      if (CONFIG.IS_PROD) {
        res.cookie('refreshToken', userData.refreshToken, {
          maxAge: 30 * 24 * 60 * 60 * 1000,
          httpOnly: true,
          sameSite: 'lax'
        })
      } else {
        res.cookie('refreshToken', userData.refreshToken, {
          maxAge: 30 * 24 * 60 * 60 * 1000,
          httpOnly: true,
          sameSite: 'Lax', // или 'Strict' для DEV
          secure: false
        })
      }

      return res.json(userData)
    } catch (e) {
      next(e)
    }
  }

  async getUsers (req, res, next) {
    try {
      res.json(['123', '456'])
    } catch (e) {
      next(e)
    }
  }
}

const userController = new UserController()
export { userController }
