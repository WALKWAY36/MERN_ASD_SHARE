import ffmpeg from 'fluent-ffmpeg'
import fs from 'fs'
import path from 'path'

class VideoEncodingService {
  async convertToHLS (inputPath, outputDir, fileName) {
    const hlsDir = path.join(outputDir, fileName.replace(/\.[^/.]+$/, ''))

    if (!fs.existsSync(hlsDir)) {
      fs.mkdirSync(hlsDir, { recursive: true })
    }

    return new Promise((resolve, reject) => {
      ffmpeg(inputPath)
        .outputOptions([
          '-codec: copy', // Копируем кодек
          '-start_number 0',
          '-hls_time 10', // Сегменты по 10 секунд
          '-hls_list_size 0', // Все сегменты в плейлисте
          '-f hls',
          '-hls_segment_filename',
          path.join(hlsDir, 'segment_%03d.ts')
        ])
        .output(path.join(hlsDir, 'playlist.m3u8'))
        .on('end', () => {
          resolve({
            playlistPath: path.join(hlsDir, 'playlist.m3u8'),
            segmentsDir: hlsDir
          })
        })
        .on('error', reject)
        .run()
    })
  }
}

module.exports = new VideoEncodingService()
