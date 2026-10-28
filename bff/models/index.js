import File from "./File.js"
import { Tag } from "./Tag.js";
import { FileTag } from "./FileTag.js";

File.belongsToMany(Tag, { through: FileTag, as: "tags" })
Tag.belongsToMany(File, { through: FileTag, as: "files" })

export { File, Tag, FileTag }