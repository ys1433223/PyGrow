import client from './client'

export const practiceApi = {
  // Daily practice
  getDaily(count = 5) {
    return client.get('/practice/daily', { params: { count } })
  },

  // Placement test (MC only)
  getPlacementTest() {
    return client.get('/practice/placement-test')
  },

  // Submit single answer
  submitAnswer(questionId, answer) {
    return client.post('/practice/submit', { question_id: questionId, answer })
  },

  // Batch submit answers
  batchSubmit(answers) {
    // answers: [{question_id, answer}, ...]
    return client.post('/practice/batch-submit', { answers })
  },

  // Chapter practice
  getByChapter(stage, chapterNum, type = null, difficulty = null, knowledgeTag = null) {
    return client.get('/practice/chapter', {
      params: { stage, chapter_num: chapterNum, type, difficulty, knowledge_tag: knowledgeTag }
    })
  },

  // Special practice by knowledge tag
  getSpecial(knowledgeTag, type = null, difficulty = null) {
    return client.get('/practice/special', {
      params: { knowledge_tag: knowledgeTag, type, difficulty }
    })
  },

  // Wrong question book
  getWrongQuestions(knowledgeTag = null) {
    return client.get('/practice/wrong-questions', {
      params: { knowledge_tag: knowledgeTag }
    })
  },

  // Smart recommendations
  getRecommend(count = 8) {
    return client.get('/practice/recommend', { params: { count } })
  },

  // Promotion test
  getPromotionTest() {
    return client.get('/practice/promotion-test')
  },

  // Submit promotion test
  submitPromotion(answers) {
    return client.post('/practice/promotion-submit', { answers })
  },

  // Knowledge points list
  getKnowledgePoints() {
    return client.get('/practice/knowledge-points')
  },

  // Chapters by stage
  getChapters(stage) {
    return client.get('/practice/chapters', { params: { stage } })
  },

  // Add question to wrong book (from favoriting)
  addToWrong(questionId) {
    return client.post('/practice/add-wrong', { question_id: questionId, answer: '' })
  },

  // AI Hint
  getHint(data) {
    // data: { question_id, question, question_type, difficulty, knowledge_tag, student_code, hint_level }
    return client.post('/practice/ai-hint', data)
  },
}
