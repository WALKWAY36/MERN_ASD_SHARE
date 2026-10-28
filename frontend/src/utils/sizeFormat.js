const totalSpace = 1024 ** 3 + 1

export default (size) => {
    if (size > 1024 * 1024 * 1024) {
        return (size / (1024 * 1024 * 1024)).toFixed(1) + "Gb"
    }
    if (size > 1024 * 1024) {
        return (size / (1024 * 1024)).toFixed(1) + "Mb"
    }
    if (size > 1024) {
        return (size / 1024).toFixed(1) + "Kb"
    }

    return size + "B"
}

const getColorOfSpace = (usedSpace, totalSpace) => {
    const ocupiedSpacePrecent = usedSpace / totalSpace * 100
    if (ocupiedSpacePrecent < 25) {
        return "#00FF00"
    } else if (ocupiedSpacePrecent >= 25 && ocupiedSpacePrecent < 75) {
        return "#FFFF00"
    }
    return "#B22222"
}

export { totalSpace, getColorOfSpace }