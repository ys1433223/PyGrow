import client from './client'

export const favoritesApi = {
  list(itemType) {
    return client.get('/favorites', { params: itemType ? { item_type: itemType } : {} })
  },
  add(itemType, itemId, title) {
    return client.post('/favorites', { item_type: itemType, item_id: itemId, title })
  },
  remove(id) {
    return client.delete(`/favorites/${id}`)
  },
  removeByItem(itemType, itemId) {
    return client.delete(`/favorites/item/${itemType}/${encodeURIComponent(itemId)}`)
  },
}
