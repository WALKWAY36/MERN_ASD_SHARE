import { Sequelize } from 'sequelize'
import { CONFIG } from '../config/config.js'

const sequelize = new Sequelize({
    dialect: 'sqlite',
    storage: CONFIG.DB_PATH,
    logging: false
})

export default sequelize