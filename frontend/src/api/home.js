import client from './client'

export const homeApi = {
  getDashboard() {
    return client.get('/home/dashboard')
  },
}
