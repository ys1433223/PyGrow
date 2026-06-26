import client from './client'

export function getNotesByCourse(courseId) {
  return client.get(`/notes/course/${courseId}`)
}

export function createNote(courseId, lessonId, content, timeText = '00:00', noteType = '重点') {
  const parsed = parseTimeToSeconds(timeText)
  return client.post('/notes', {
    course_id: courseId,
    lesson_id: lessonId,
    content,
    timestamp_seconds: parsed.seconds,
    time_text: parsed.text,
    note_type: noteType,
  })
}

export function updateNote(noteId, content, timeText, noteType) {
  const parsed = parseTimeToSeconds(timeText)
  return client.put(`/notes/${noteId}`, {
    content,
    timestamp_seconds: parsed.seconds,
    time_text: parsed.text,
    note_type: noteType,
  })
}

export function deleteNote(noteId) {
  return client.delete(`/notes/${noteId}`)
}

/**
 * Parse a time string like '1:23', '01:23', '12:05', '1:02:33'.
 * Returns { seconds: number, text: string } or throws with an error message.
 */
export function parseTimeToSeconds(raw) {
  const s = raw.trim()
  const m = s.match(/^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$/)
  if (!m) throw new Error('请输入正确的时间格式，例如 03:20')
  const h = parseInt(m[1], 10)
  const min = parseInt(m[2], 10)
  const sec = m[3] ? parseInt(m[3], 10) : 0
  if (min >= 60 || sec >= 60) throw new Error('请输入正确的时间格式，例如 03:20')
  const total = h * 3600 + min * 60 + sec
  const text = m[3]
    ? `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
    : `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
  return { seconds: total, text }
}

/**
 * Format seconds to display time string: MM:SS (or H:MM:SS if >= 1 hour).
 */
export function formatSecondsToTime(totalSeconds) {
  if (!totalSeconds && totalSeconds !== 0) return '00:00'
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}
