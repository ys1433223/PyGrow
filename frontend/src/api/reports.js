import client from './client'

export const reportsApi = {
  getSummary() {
    return client.get('/report/summary')
  },
  getKnowledgePoints() {
    return client.get('/report/knowledge-points')
  },
  getRadarData() {
    return client.get('/report/radar-data')
  },
}
