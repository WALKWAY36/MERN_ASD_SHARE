import { Model, DataTypes } from 'sequelize'
import sequelize from '../DB/database.js'
import User from './User.js';

class Token extends Model { }

Token.init(
    {
        userId: {
            type: DataTypes.UUID,
            allowNull: false,
            references: {
                model: User,
                key: '_id',
            },
            onDelete: 'CASCADE', // Что происходит при удалении пользователя (опционально)
        },
        refreshToken: {
            type: DataTypes.STRING,
            allowNull: false,
        },
    },
    {
        sequelize,
        modelName: 'Token',
        timestamps: false,
    },
);

User.hasMany(Token, { foreignKey: 'userId', as: 'tokens' }); // связь "один ко многим", указывающая, что один пользователь может иметь много токенов.
Token.belongsTo(User, { foreignKey: 'userId', as: 'user' }); // указывает, что токен принадлежит пользователю, используя поле userId как внешний ключ.

export { Token };
