import { Model, DataTypes } from 'sequelize'
import sequelize from '../DB/database.js'
import User from './User.js'

class File extends Model {}

File.init(
  {
    _id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true
    },
    name: {
      type: DataTypes.STRING,
      allowNull: false
    },
    type: {
      type: DataTypes.STRING,
      allowNull: false
    },
    accessLink: {
      type: DataTypes.STRING,
      allowNull: true
    },
    size: {
      type: DataTypes.INTEGER,
      defaultValue: 0
    },
    path: {
      type: DataTypes.STRING,
      defaultValue: ''
    },
    date: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW
    },
    user: {
      type: DataTypes.UUID,
      references: {
        model: User,
        key: '_id'
      }
    },
    parent: {
      type: DataTypes.UUID,
      references: {
        model: File,
        key: '_id'
      }
    },
    child: {
      type: DataTypes.UUID,
      references: {
        model: File,
        key: '_id'
      }
    },
    hasAnalysis: {
      type: DataTypes.BOOLEAN,
      defaultValue: false
    }
  },
  {
    sequelize,
    modelName: 'File',
    timestamps: false
  }
)

export default File
