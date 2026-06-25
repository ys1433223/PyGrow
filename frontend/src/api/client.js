import axios from 'axios'
import router from '../router'

const client = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Only redirect if we're not already on the login page, and only if
      // the token was actually present (not a missing-token 401 from an
      // unauthenticated endpoint). This prevents redirect loops and spurious
      // logout when the backend is temporarily unreachable.
      const hadToken = localStorage.getItem('access_token')
      if (hadToken && router.currentRoute.value.path !== '/login') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('userInfo')
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default client
