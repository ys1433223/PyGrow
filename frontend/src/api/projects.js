import client from './client'

export function getProjects(stage = null, difficulty = null) {
  const params = {}
  if (stage) params.stage = stage
  if (difficulty) params.difficulty = difficulty
  return client.get('/projects', { params })
}

export function getProjectDetail(id) {
  return client.get(`/projects/${id}`)
}

export function submitProject(projectId, data) {
  // data: { code, text, file_url, screenshot_url, hints_used }
  return client.post(`/projects/${projectId}/submit`, data)
}
