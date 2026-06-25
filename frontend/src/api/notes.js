import client from './client'

export function getNotesByCourse(courseId) {
  return client.get(`/notes/course/${courseId}`)
}

export function createNote(courseId, lessonId, content, timestampSeconds = 0) {
  return client.post('/notes', { course_id: courseId, lesson_id: lessonId, content, timestamp_seconds: timestampSeconds })
}

export function deleteNote(noteId) {
  return client.delete(`/notes/${noteId}`)
}
