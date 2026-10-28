import axios from 'axios'
import { addFile, deleteFileAction, setFiles } from '../reducers/fileReducer'
import {
  addUploadFile,
  changeUploadFile,
  showUploader
} from '../reducers/uploadReducer'
import { hideLoader, showLoader } from '../reducers/appReducer'
import { API_URL } from '../config'
import { deleteLink, setLinks, addLinkAction } from '../reducers/linksReducer'

export function getFiles (dirId, sort) {
  return async dispatch => {
    try {
      dispatch(showLoader())
      let url = `${API_URL}/api/files`
      if (dirId) {
        url = `${API_URL}/api/files?parent=${dirId}`
      }
      if (sort) {
        url = `${API_URL}/api/files?sort=${sort}`
      }
      if (dirId && sort) {
        url = `${API_URL}/api/files?parent=${dirId}&sort=${sort}`
      }
      console.log('url', url)
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })

      dispatch(setFiles(response.data))
    } catch (e) {
      alert(e.response.data.message)
      if (e.response.status === 401) {
        window.location.href = window.location.href + '/login'
      }
    } finally {
      dispatch(hideLoader())
    }
  }
}

export function getLinks (fileID) {
  return async dispatch => {
    try {
      const url = `${API_URL}/api/files/links?fileId=${fileID}`
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      dispatch(setLinks(response.data))
    } catch (e) {
      alert(e.response.data.message)
    }
  }
}

export function createDir (dirId, name) {
  return async dispatch => {
    try {
      const response = await axios.post(
        `${API_URL}/api/files`,
        {
          name,
          parent: dirId,
          type: 'dir'
        },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      )
      dispatch(addFile(response.data))
    } catch (e) {
      alert(e.response.data.message)
    }
  }
}

export function addLink (linkName, link, fileId) {
  return async dispatch => {
    try {
      const formData = new FormData()
      formData.append('linkName', linkName)
      formData.append('link', link)
      formData.append('type', 'add')
      formData.append('fileId', fileId)
      await axios.post(`${API_URL}/api/files/change`, formData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      })
      dispatch(addLinkAction({ name: linkName, content: link }))
      console.log(`add link done`)
    } catch (e) {
      console.log('Error add link')
      alert(e.response.data.message)
    }
  }
}

export function changeLink (linkNameOld, linkName, link, fileID) {
  return async dispatch => {
    try {
      const formData = new FormData()
      formData.append('linkName', linkName)
      formData.append('link', link)
      formData.append('linkNameOld', linkNameOld)
      formData.append('type', 'change')
      formData.append('fileId', fileID)
      const response = await axios.post(
        `${API_URL}/api/files/change`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      )
      dispatch(setLinks(response.data))
      console.log(`change link done`)
    } catch (e) {
      console.log('Error change link')
      alert(e.response.data.message)
    }
  }
}

const CHUNK_SIZE = 0.5 * 1024 * 1024

export function uploadFile (file, dirId, tags) {
  return async dispatch => {
    try {
      const uploadFile = {
        name: String(file.name),
        progress: 0,
        id: Date.now()
      }

      dispatch(showUploader())
      dispatch(addUploadFile(uploadFile))
      if (file.size >= 1 * 1024 * 1024) {
        // Если больше 1MB
        await uploadFileInChunks(file, dirId, tags, uploadFile, dispatch)
      } else {
        await uploadFileNormal(file, dirId, tags, uploadFile, dispatch)
      }
    } catch (e) {
      alert(e?.response?.data?.message || 'Ошибка загрузки файла')
    }
  }
}

async function uploadFileNormal (file, dirId, tags, uploadFile, dispatch) {
  const formData = new FormData()
  formData.append('file', file)
  if (dirId) {
    formData.append('parent', dirId)
  }
  if (tags) {
    tags.forEach(tag => formData.append('tags', tag))
  }

  const response = await axios.post(`${API_URL}/api/files/upload`, formData, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`
    },
    onUploadProgress: progressEvent => {
      const totalLength =
        progressEvent.total ||
        progressEvent.target?.getResponseHeader('content-length')
      if (totalLength) {
        uploadFile.progress = Math.round(
          (progressEvent.loaded * 100) / totalLength
        )
        dispatch(changeUploadFile(uploadFile))
      }
    }
  })

  dispatch(addFile(response.data))
}

// Загрузка чанками для больших файлов
async function uploadFileInChunks (file, dirId, tags, uploadFile, dispatch) {
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE)
  let uploadedChunks = 0

  // 1. Инициализация загрузки
  const initResponse = await axios.post(
    `${API_URL}/api/files/upload/init`,
    {
      fileName: file.name,
      fileSize: file.size,
      totalChunks,
      parent: dirId,
      tags
    },
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    }
  )

  const { uploadId } = initResponse.data

  // 2. Загрузка чанков
  for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
    const start = chunkIndex * CHUNK_SIZE
    const end = Math.min(start + CHUNK_SIZE, file.size)
    const chunk = file.slice(start, end)

    const formData = new FormData()
    formData.append('chunk', chunk)
    formData.append('chunkIndex', chunkIndex)
    formData.append('uploadId', uploadId)

    await axios.post(`${API_URL}/api/files/upload/chunk`, formData, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })

    uploadedChunks++
    uploadFile.progress = Math.round((uploadedChunks / totalChunks) * 100)
    dispatch(changeUploadFile(uploadFile))
  }

  // 3. Завершение загрузки
  const completeResponse = await axios.post(
    `${API_URL}/api/files/upload/complete`,
    { uploadId },
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    }
  )

  dispatch(addFile(completeResponse.data))
}

export async function downloadFile (file) {
  const response = await fetch(`${API_URL}/api/files/download?id=${file._id}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`
    }
  })
  if (response.status === 200) {
    const blob = await response.blob() // Бинарные данные
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = file.name
    document.body.appendChild(link)
    link.click()
    link.remove()
  }
}

export function deleteFile (file, userId) {
  return async dispatch => {
    try {
      const response = await axios.delete(
        `${API_URL}/api/files?id=${file._id}&userId=${userId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      )
      dispatch(deleteFileAction(file._id))
      alert(response.data.message)
    } catch (e) {
      alert(e?.response?.data?.message)
    }
  }
}

export function deleteFileLink (link, fileId) {
  return async dispatch => {
    try {
      const formData = new FormData()
      formData.append('link', JSON.stringify(link))
      formData.append('fileId', fileId)
      await axios.post(`${API_URL}/api/files/change`, formData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      })
      dispatch(deleteLink(link.name))
    } catch (e) {
      alert(e?.response?.data?.message)
    }
  }
}

export function searchFiles (search) {
  return async dispatch => {
    try {
      const response = await axios.get(
        `${API_URL}/api/files/search?search=${search}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      )
      dispatch(setFiles(response.data))
      // alert(response.data.message)
    } catch (e) {
      alert(e?.response?.data?.message)
    } finally {
      dispatch(hideLoader())
    }
  }
}
