import client from './client'

export const userApi = {
  getProfile() {
    return client.get('/user/profile')
  },
  updateProfile(data) {
    return client.put('/user/profile', data)
  },
  getCollections() {
    return client.get('/user/collections')
  },
  toggleCollection(courseId) {
    return client.post(`/user/collections/${courseId}`)
  },
}
