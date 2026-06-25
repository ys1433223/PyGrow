import client from './client'

export function chatWithMentor(message, history = []) {
  return client.post('/ai/chat', { message, history })
}
