import client from './client'

export function getPosts(page = 1, category = null, keyword = null, tag = null) {
  const params = { page }
  if (category) params.category = category
  if (keyword) params.keyword = keyword
  if (tag) params.tag = tag
  return client.get('/community', { params })
}

export function getHotPosts(limit = 10) {
  return client.get('/community/hot/list', { params: { limit } })
}

export function getPostDetail(postId) {
  return client.get(`/community/${postId}`)
}

export function createPost(title, content, category = '问答专区', tags = '') {
  return client.post('/community', { title, content, category, tags })
}

export function addComment(postId, content) {
  return client.post(`/community/${postId}/comments`, { content })
}

export function toggleLike(postId) {
  return client.post(`/community/${postId}/like`)
}

export function toggleFavorite(postId) {
  return client.post(`/community/${postId}/favorite`)
}

export function toggleCommentLike(commentId) {
  return client.post(`/community/comments/${commentId}/like`)
}

export function getMyPosts() {
  return client.get('/community/my-posts')
}

export function deletePost(postId) {
  return client.delete(`/community/${postId}`)
}
