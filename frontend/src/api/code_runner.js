import client from './client'

export function runCode(code) {
  return client.post('/code/run', { code })
}
