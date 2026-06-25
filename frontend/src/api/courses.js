import client from './client'

export const coursesApi = {
  list() {
    return client.get('/courses')
  },
  detail(id) {
    return client.get(`/courses/${id}`)
  },
  getProgress(courseId) {
    return client.get(`/courses/${courseId}/progress`)
  },
  updateProgress(courseId, data) {
    return client.post(`/courses/${courseId}/progress`, data)
  },
}
