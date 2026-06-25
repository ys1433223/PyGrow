import client from './client'

export const gamificationApi = {
  getStatus() {
    return client.get('/gamification/status')
  },
  getDailyTasks() {
    return client.get('/gamification/daily-tasks')
  },
  claimReward(taskId) {
    return client.post('/gamification/claim-reward', { task_id: taskId })
  },
}
