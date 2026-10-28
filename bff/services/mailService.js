import nodemailer from "nodemailer"
import { CONFIG } from "../config/config.js"

class MailService {
    constructor() {
        this.transporter = nodemailer.createTransport({
            host: CONFIG.SMPT_HOST,
            port: CONFIG.SMTP_PORT,
            secure: false,
            auth: {
                user: CONFIG.SMTP_USER,
                pass: CONFIG.SMTP_PASSWORD
            }
        })
    }
    async sendActivationMail(to, link) {
        await this.transporter.sendMail({
            from: CONFIG.SMTP_USER,
            to,
            subject: `Активация аккаунта на http://127.0.0.1`,
            text: 'Подтвердите ваш аккаунт. Мы о вас заботимся!',
            html:
                `
                <div>
                    <h1>Для активации перейдите по ссылке</h1>
                    <a href="${link}">${link}</a>
                </div>
            `
        })
    }
}

const mailService = new MailService()
export { mailService }