import 'dotenv/config'

const CONFIG = {
  IS_PROD: false,
  VERSION: '241028 v1.0.0',

  PORT: process.env.SERVER_PORT || 80,
  FILE_PATH: process.env.FILE_PATH,
  STATIC_PATH: process.env.STATIC_PATH,
  DB_PATH: process.env.DB_PATH,
  JWT_ACCESS_SECRET: process.env.JWT_ACCESS_SECRET,
  JWT_REFRESH_SECRET: process.env.JWT_REFRESH_SECRET,
  SMPT_HOST: process.env.SMTP_HOST,
  SMTP_PORT: process.env.SMTP_PORT,
  SMTP_USER: process.env.SMTP_USER,
  SMTP_PASSWORD: process.env.SMTP_PASSWORD,
  DATASET_DIR: process.env.DATASET_DIR,
  SUPERUSER_LOGIN: process.env.SUPERUSER_LOGIN,
  SUPREUSER_PASS: process.env.SUPREUSER_PASS
}

export { CONFIG }
