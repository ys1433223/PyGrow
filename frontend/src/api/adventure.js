import client from './client'

export const adventureApi = {
  getProfile() {
    return client.get('/pet/profile')
  },
  startAdventure() {
    return client.post('/pet/adventure/start')
  },
  getCurrentAdventure() {
    return client.get('/pet/adventure/current')
  },
  claimReward() {
    return client.post('/pet/adventure/claim')
  },
  getAdventureLogs(limit = 20) {
    return client.get('/pet/adventure/logs', { params: { limit } })
  },
  getRewards(type = null, limit = 50) {
    return client.get('/pet/rewards', { params: { reward_type: type, limit } })
  },
  markRewardSeen(rewardId) {
    return client.post('/pet/rewards/seen', null, { params: { reward_id: rewardId } })
  },
  getCookieRecords(limit = 50) {
    return client.get('/pet/cookie-records', { params: { limit } })
  },
}
