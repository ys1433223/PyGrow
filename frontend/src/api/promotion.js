import client from './client'

export const promotionApi = {
  status() {
    return client.get('/promotion/status')
  },
  start() {
    return client.post('/promotion/start')
  },
  submit(examId, answers) {
    return client.post('/promotion/submit', answers, { params: { exam_id: examId } })
  },
  result(examId) {
    const params = examId ? { exam_id: examId } : {}
    return client.get('/promotion/result', { params })
  },
}
