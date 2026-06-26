import client from './client'

export function startFlask(files) {
  return client.post('/code/flask/start', { files })
}

export function stopFlask(runId) {
  return client.post('/code/flask/stop', { run_id: runId })
}

export function getFlaskStatus(runId) {
  return client.get(`/code/flask/status/${runId}`)
}
