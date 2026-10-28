import { v4 as uuidv4 } from 'uuid'
import bcrypt from 'bcryptjs'
import User from '../models/User.js'
import File from '../models/File.js'
import { Token } from '../models/Token.js'
import { mailService } from './mailService.js'
import { CONFIG } from '../config/config.js'
import { tokenService } from './tokenService.js'
import fileService from './fileService.js'
import { UserDto } from '../dtos/userDto.js'
import { ApiError } from '../exceptions/apiError.js'

class UserService {
  async registration (email, password, date, gender) {
    const candidate = await User.findOne({ where: { email } })

    if (candidate) {
      throw ApiError.BadRequest(
        `Пользователь с почтовым адресом ${email} уже существует`
      )
    }
    const hashPassword = await bcrypt.hash(password, 15)
    const activationLink = uuidv4()
    // await mailService.sendActivationMail(email, `http://c1r011v08.amm.vsu.ru/api/auth/activate/${activationLink}`)
    const user = new User({
      email,
      password: hashPassword,
      date,
      gender,
      activationLink
    })
    await user.save()

    const userDto = new UserDto(user) // id, email, isActivated
    const tokens = tokenService.generateTokens({ ...userDto })
    const tokenModel = new Token({
      userId: userDto.id,
      refreshToken: tokens.refreshToken
    })
    await tokenModel.save()

    const file = new File({ user: userDto.id, name: '' })
    await fileService.createDir(file)
    console.log('Registration done')
    const result = {
      ...tokens,
      user: {
        userDto,
        date: user.date,
        gender: user.gender,
        usedSpace: user.usedSpace
      }
    }
    return result
  }

  async activate (activationLink) {
    const user = await User.findOne({ where: { activationLink } })
    if (!user) {
      throw ApiError.BadRequest('Неккоректная ссылка активации')
    }
    user.isActivated = true
    await user.save()
  }

  async login (email, password) {
    const user = await User.findOne({ where: { email } })
    // if (!user.isActivated) {
    //   throw ApiError.BadRequest(`Подтвердите почту`)
    // }
    if (!user) {
      throw ApiError.BadRequest(`Пользователь не существует`)
    }
    const isPassValid = bcrypt.compare(password, user.password)
    if (!isPassValid) {
      throw ApiError.BadRequest(`Неверный пароль`)
    }
    const userDto = new UserDto(user)
    const tokens = tokenService.generateTokens({ ...userDto })
    const tokenModel = new Token({
      userId: userDto.id,
      refreshToken: tokens.refreshToken
    })
    await tokenModel.save()
    const result = {
      ...tokens,
      user: {
        ...userDto,
        date: user.date,
        gender: user.gender,
        avatar: user.avatar,
        usedSpace: user.usedSpace
      }
    }
    return result
  }

  async logout (refreshToken) {
    const token = await tokenService.removeToken(refreshToken)
    return token
  }

  async refresh (refreshToken) {
    if (!refreshToken) {
      throw ApiError.UnauthorizedError()
    }
    const userData = tokenService.validateRefreshToken(refreshToken)
    const tokenFromDB = await tokenService.findToken(refreshToken)
    if (!userData || !tokenFromDB) {
      throw ApiError.UnauthorizedError()
    }
    const user = await User.findOne({ where: { _id: userData.id } })
    const userDto = new UserDto(user)
    const tokens = tokenService.generateTokens({ ...userDto })
    const tokenModel = new Token({
      userId: userDto.id,
      refreshToken: tokens.refreshToken
    })
    await tokenModel.save()
    return {
      ...tokens,
      user: {
        ...userDto,
        date: user.date,
        gender: user.gender,
        avatar: user.avatar,
        usedSpace: user.usedSpace
      }
    }
  }
}

const userService = new UserService()
export { userService }
