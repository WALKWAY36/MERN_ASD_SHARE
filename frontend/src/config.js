const isDev = process.env.NODE_ENV !== 'production'
console.log('Is Dev mode? - ', isDev)
console.log('ver. 1.0.0')
// export const API_URL = isDev ? 'http://127.0.0.1:5000' : `/autmama/api` // for VSU server
export const API_URL = 'http://127.0.0.1:5000'
