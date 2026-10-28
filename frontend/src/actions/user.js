import axios from 'axios'
import { setUser, logout } from '../reducers/userReducer'
import { API_URL } from '../config'
import { $api } from '../http'
import { hideLoader, showLoader } from '../reducers/appReducer'

export const registration = (email, password, date, gender) => {
  return async dispatch => {
    try {
      const reqData = { email, password, date, gender }
      dispatch(showLoader())
      const response = await $api.post(`api/auth/registration`, reqData)
      alert('Успешная регистрация. Подтвердите почту и войдите в аккаунт.')
    } catch (e) {
      console.log(e)
      alert(
        e?.response?.data?.message ? e.response.data.message : 'Server ERROR'
      )
    } finally {
      dispatch(hideLoader())
    }
  }
}

export const login = (email, password) => {
  return async dispatch => {
    try {
      dispatch(showLoader())
      const response = await $api.post(`api/auth/login`, {
        email,
        password
      })
      dispatch(setUser(response.data.user))
      console.log('login', response.data)
      localStorage.setItem('token', response.data.accessToken)
      console.log('get token', localStorage.getItem('token'))
    } catch (e) {
      alert(
        e?.response?.data?.message ? e.response.data.message : 'Server ERROR'
      )
    } finally {
      dispatch(hideLoader())
    }
  }
}

export const logoutService = () => {
  return async dispatch => {
    try {
      await $api.post(`api/auth/logout`)
      dispatch(logout())
    } catch (e) {
      alert(
        e?.response?.data?.message ? e.response.data.message : 'Server ERROR'
      )
    }
  }
}

export const auth = () => {
  return async dispatch => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/refresh`, {
        withCredentials: true
      })
      localStorage.setItem('token', response.data.accessToken)
      dispatch(setUser(response.data.user))
    } catch (e) {
      localStorage.removeItem('token')
    }
  }
}

export const uploadAvatar = file => {
  return async dispatch => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await axios.post(
        `${API_URL}/api/files/avatar`,
        formData,
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      )
      dispatch(setUser(response.data))
    } catch (e) {
      console.log(e)
    }
  }
}

export const deleteAvatar = () => {
  return async dispatch => {
    try {
      const response = await axios.delete(`${API_URL}/api/files/avatar`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      dispatch(setUser(response.data))
    } catch (e) {
      console.log(e)
    }
  }
}
