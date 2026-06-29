import client from './client'

export const aiNotesApi = {
  // Check if course (or specific lesson) has AI notes
  getNotes(courseId, lessonId, bvid, bilibiliPage) {
    const params = {}
    if (lessonId != null) params.lesson_id = lessonId
    if (bvid) params.bvid = bvid
    if (bilibiliPage != null) params.bilibili_page = bilibiliPage
    return client.get(`/courses/${courseId}/ai-notes`, { params })
  },

  // Start AI note generation for a specific lesson
  generate(courseId, lessonId, bvid, bilibiliPage) {
    const params = {}
    if (lessonId != null) params.lesson_id = lessonId
    if (bvid) params.bvid = bvid
    if (bilibiliPage != null) params.bilibili_page = bilibiliPage
    return client.post(`/courses/${courseId}/ai-notes/generate`, null, { params })
  },

  // Poll task status
  getTaskStatus(taskId) {
    return client.get(`/ai-note-tasks/${taskId}/status`)
  },

  // Get task result
  getTaskResult(taskId) {
    return client.get(`/ai-note-tasks/${taskId}/result`)
  },
}
