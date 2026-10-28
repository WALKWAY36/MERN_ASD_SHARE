import { Model, DataTypes } from 'sequelize'
import sequelize from '../DB/database.js'

class User extends Model { }

User.init({
    _id: {
        type: DataTypes.UUID,
        defaultValue: DataTypes.UUIDV4,
        primaryKey: true
    },
    email: {
        type: DataTypes.STRING,
        allowNull: false,
        unique: true
    },
    password: {
        type: DataTypes.STRING,
        allowNull: false
    },
    diskSpace: {
        type: DataTypes.INTEGER,
        defaultValue: 1024 ** 4 * 1
    },
    usedSpace: {
        type: DataTypes.INTEGER,
        defaultValue: 0
    },
    avatar: {
        type: DataTypes.STRING
    },
    date: {
        type: DataTypes.DATE,
    },
    gender: {
        type: DataTypes.STRING
    },
    isActivated: { // Для подтверждения почты
        type: DataTypes.BOOLEAN,
        defaultValue: false
    },
    activationLink: {
        type: DataTypes.UUID,
        defaultValue: null
    }
}, {
    sequelize,
    modelName: 'User',
    timestamps: false
})

export default User

