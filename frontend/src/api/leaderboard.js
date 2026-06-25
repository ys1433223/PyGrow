import client from './client'

export function getXPLeaderboard(limit = 20, majorLevel = null) {
  const params = { limit }
  if (majorLevel) params.major_level = majorLevel
  return client.get('/leaderboard/xp', { params })
}

export function getProjectsLeaderboard(limit = 20, majorLevel = null) {
  const params = { limit }
  if (majorLevel) params.major_level = majorLevel
  return client.get('/leaderboard/projects', { params })
}

export function getStreakLeaderboard(limit = 20, majorLevel = null) {
  const params = { limit }
  if (majorLevel) params.major_level = majorLevel
  return client.get('/leaderboard/streak', { params })
}
