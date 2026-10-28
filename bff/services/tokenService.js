import jwt from "jsonwebtoken"
import { Token } from "../models/Token.js";
import { CONFIG } from "../config/config.js";
import { where } from "sequelize";

class TokenService {
    generateTokens(payload) {
        const accessToken = jwt.sign(payload, CONFIG.JWT_ACCESS_SECRET, { expiresIn: '1d' });
        const refreshToken = jwt.sign(payload, CONFIG.JWT_REFRESH_SECRET, { expiresIn: '360d' });
        return {
            accessToken,
            refreshToken,
        };
    };

    validateAccessToken(token) {
        try {
            const userData = jwt.verify(token, CONFIG.JWT_ACCESS_SECRET)
            return userData
        } catch (e) {
            return null
        }
    }

    validateRefreshToken(token) {
        try {
            const userData = jwt.verify(token, CONFIG.JWT_REFRESH_SECRET)
            return userData
        } catch (e) {
            return null
        }
    }

    async saveToken(userId, refreshToken) {
        const tokenData = await Token.findOne({ where: { userId } });
        if (tokenData) {
            tokenData.refreshToken = refreshToken;
            return tokenData.save();
        }
        const token = new Token({ userId, refreshToken });
        await token.save();
        return token;
    };

    async removeToken(refreshToken) {
        const tokenData = await Token.destroy({ where: { refreshToken } })
        return tokenData
    }

    async findToken(refreshToken) {
        const tokenData = await Token.findOne({ where: { refreshToken } })
        return tokenData
    }
}

const tokenService = new TokenService()
export { tokenService }