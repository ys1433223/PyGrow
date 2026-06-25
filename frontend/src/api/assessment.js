import client from './client'

export const assessmentApi = {
  getQuestions() {
    return client.get('/assessment/questions')
  },
  submitAnswers(answers) {
    return client.post('/assessment/submit', { answers })
  },
  getResult() {
    return client.get('/assessment/result')
  },
}
