import client from './client'

export function getAdminStats() { return client.get('/admin/stats') }
export function getAdminUsers(page = 1) { return client.get('/admin/users', { params: { page } }) }
export function toggleAdmin(userId) { return client.post(`/admin/users/${userId}/toggle-admin`) }
export function getAdminCourses() { return client.get('/admin/courses') }
export function deleteAdminCourse(id) { return client.delete(`/admin/courses/${id}`) }
export function getAdminQuestions(page = 1) { return client.get('/admin/questions', { params: { page } }) }
export function deleteAdminQuestion(id) { return client.delete(`/admin/questions/${id}`) }
export function getAdminProjects() { return client.get('/admin/projects') }
export function deleteAdminProject(id) { return client.delete(`/admin/projects/${id}`) }
export function getAdminPosts(page = 1) { return client.get('/admin/posts', { params: { page } }) }
export function deleteAdminPost(id) { return client.delete(`/admin/posts/${id}`) }
