import client from './client'

export const authApi = {
  login(username, password) {
    return client.post('/auth/login', { username, password })
  },
  register(username, password, confirm_password) {
    return client.post('/auth/register', { username, password, confirm_password })
  },
}
