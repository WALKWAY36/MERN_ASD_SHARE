import { DataTypes, Model } from "sequelize";
import sequelize from '../DB/database.js'
import { Tag } from "./Tag.js";
import File from "./File.js";

// Промежуточная таблица для связи "Многие ко многим"
class FileTag extends Model { }

FileTag.init({
    FileId: {
        type: DataTypes.UUID,
        references: {
            model: File,
            key: "_id"
        }
    },
    TagId: {
        type: DataTypes.UUID,
        references: {
            model: Tag,
            key: "id"
        }
    }
}, { sequelize, modelName: "FileTag", timestamps: false })

export { FileTag }