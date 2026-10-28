import { API_URL } from '../config'

// Запуск анализа
export const startAnalysis = fileId => {
  return async dispatch => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })

      const response = await fetch(
        `${API_URL}/api/ml/start-analyze/${fileId}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.status === 409) {
        const data = await response.json()
        throw {
          message: data.error || 'Другое видео уже анализируется',
          status: 409
        }
      }

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Ошибка запуска анализа')
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Start analysis error:', error)
      throw error
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }
}

// Получение статуса анализа
export const getAnalysisStatus = () => {
  return async dispatch => {
    try {
      const response = await fetch(`${API_URL}/api/ml/status-analyze`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          Accept: 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Ошибка получения статуса')
      }

      return await response.json()
    } catch (error) {
      console.error('Get status error:', error)
      return null
    }
  }
}

// Получение готовой аналитики
export const getFileAnalytics = fileId => {
  return async dispatch => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })

      const response = await fetch(`${API_URL}/api/ml/feature?id=${fileId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          Accept: 'application/json'
        }
      })

      if (!response.ok) {
        let errorMessage = `Ошибка ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.message || errorMessage
        } catch (e) {}
        throw new Error(errorMessage)
      }

      const data = await response.json()

      if (data.success !== undefined) {
        return data.success ? data : Promise.reject(new Error(data.message))
      }

      return {
        success: true,
        data: data,
        analytics: data
      }
    } catch (error) {
      console.error('Error loading analytics:', error)
      throw error
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }
}
