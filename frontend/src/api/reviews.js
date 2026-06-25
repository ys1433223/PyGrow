import client from './client'

export const reviewsApi = {
  list(courseId) {
    return client.get(`/reviews/${courseId}`)
  },
  create(courseId, rating, content) {
    return client.post('/reviews', { course_id: courseId, rating, content })
  },
}
