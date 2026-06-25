<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { practiceApi } from '../api/practice'
import { favoritesApi } from '../api/favorites'
import { setPetMode, triggerPetState } from '../hooks/usePetCompanion'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import AiHintCard from '../components/common/AiHintCard.vue'

const auth = useAuthStore()
const route = useRoute()

// ---- Module selection ----
const activeModule = ref(null)
const moduleTitle = computed(() => {
  const titles = { chapter: '章节练习', wrong: '错题本', recommend: '智能推荐' }
  return titles[activeModule.value] || ''
})

// ---- Shared question state ----
const questions = ref([])
const currentIndex = ref(0)
const userAnswers = ref({})
const submitted = ref(false)
const submitting = ref(false)
const results = ref(null)
const loading = ref(false)
const questionError = ref('')

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
const totalQuestions = computed(() => questions.value.length)
const progressPct = computed(() => totalQuestions.value > 0 ? Math.round((currentIndex.value + 1) / totalQuestions.value * 100) : 0)
const hintCounts = ref({}) // { questionId: hints_used count }

// ---- Recommend metadata ----
const recommendMeta = ref(null)
const RECOMMEND_MODE_LABELS = {
  foundation_consolidate: '基础巩固',
  weakness_reinforce: '薄弱补强',
  wrong_review: '错题复习',
  ai_supplement: 'AI补充练习',
  mixed: '混合推荐',
}
const recommendModeLabel = computed(() => {
  if (!recommendMeta.value) return ''
  return RECOMMEND_MODE_LABELS[recommendMeta.value.recommend_mode] || recommendMeta.value.recommend_mode || ''
})

// ---- Favorites (question-level) ----
const favQuestionIds = ref(new Set())
const favRecordIds = ref({}) // questionId → favorite record id

async function loadMyFavorites() {
  if (!auth.isLoggedIn) return
  try {
    const res = await favoritesApi.list('question')
    if (res.data.code === 200) {
      const ids = new Set()
      const map = {}
      for (const f of res.data.data) {
        ids.add(String(f.item_id))
        map[String(f.item_id)] = f.id
      }
      favQuestionIds.value = ids
      favRecordIds.value = map
    }
  } catch {}
}

async function toggleFavorite(q) {
  const qid = String(q.id)
  const title = (q.title || q.content || '').slice(0, 100)
  try {
    if (favQuestionIds.value.has(qid)) {
      const recId = favRecordIds.value[qid]
      if (recId) {
        await favoritesApi.remove(recId)
        favQuestionIds.value.delete(qid)
        delete favRecordIds.value[qid]
        favQuestionIds.value = new Set(favQuestionIds.value)
      }
    } else {
      const res = await favoritesApi.add('question', qid, title)
      if (res.data.code === 200) {
        favQuestionIds.value.add(qid)
        favRecordIds.value[qid] = res.data.data?.id
        favQuestionIds.value = new Set(favQuestionIds.value)
      }
      // Also add to wrong question book
      await practiceApi.addToWrong(q.id).catch(() => {})
    }
  } catch {}
}

function isFav(q) { return favQuestionIds.value.has(String(q.id)) }

// ---- Filter state ----
const chapterStage = ref('初级')
const chapterNum = ref(null) // null = no chapter selected yet
const chapterFilterType = ref(null)
const chapterFilterDiff = ref(null)
const chapterFilterTag = ref(null)
const chapterAvailableTags = ref([])
const wrongFilterTag = ref(null)
const knowledgeTags = ref([])
const expandedChapters = ref(new Set())
const chapterTagsMap = ref({}) // { chapterNum: [tag1, tag2, ...] }
const chaptersByStage = ref({}) // { '初级': [{chapter_num, chapter}], ... }

// Chapter structure from course data
const chapterInfoMap = {
  初级: [
    { n: 1, name: '认识Python' }, { n: 2, name: '编码规范与注释' }, { n: 3, name: '数据类型与序列结构' },
    { n: 4, name: '运算符与表达式' }, { n: 5, name: '函数基础' }, { n: 6, name: '正则表达式' },
    { n: 7, name: '面向对象编程' }, { n: 8, name: '文件与目录操作' }, { n: 9, name: '网页基础HTML/CSS' },
    { n: 10, name: '爬虫基础' }, { n: 11, name: '爬虫进阶' }, { n: 12, name: '数据存储' },
  ],
  中级: [
    { n: 1, name: '数据库基础' }, { n: 2, name: '非关系型数据库' }, { n: 3, name: 'Django框架' },
    { n: 4, name: 'Selenium自动化' }, { n: 5, name: '爬虫原理与实战' }, { n: 6, name: '分布式爬虫' },
    { n: 7, name: '反爬虫技术' },
  ],
  高级: [
    { n: 1, name: 'NumPy科学计算库' }, { n: 2, name: 'Pandas数据操作' }, { n: 3, name: '数据处理与清洗' },
    { n: 4, name: '数据可视化' }, { n: 5, name: '数据分析' }, { n: 6, name: '机器学习' },
    { n: 7, name: '深度学习' }, { n: 8, name: '推荐算法' },
  ],
}

const currentChapterList = computed(() => chapterInfoMap[chapterStage.value] || [])

// ---- Answer helpers ----
function selectAnswer(questionId, answer) { userAnswers.value = { ...userAnswers.value, [questionId]: answer } }
function isSelected(questionId, answer) { return userAnswers.value[questionId] === answer }

function isMultiSelected(questionId, label) {
  const ans = userAnswers.value[questionId] || ''
  return ans.split(',').map(s => s.trim().toUpperCase()).includes(label.toUpperCase())
}
function toggleMulti(questionId, label) {
  const current = userAnswers.value[questionId] || ''
  const parts = current ? current.split(',').map(s => s.trim().toUpperCase()).filter(Boolean) : []
  const idx = parts.indexOf(label.toUpperCase())
  if (idx >= 0) parts.splice(idx, 1); else parts.push(label.toUpperCase())
  userAnswers.value = { ...userAnswers.value, [questionId]: parts.join(',') }
}

function getResultForQuestion(qId) {
  if (!results.value?.details) return null
  return results.value.details.find(d => d.question_id === qId)
}

// ---- Module openers ----
function openModule(key) {
  if (key === 'chapter') { activeModule.value = 'chapter'; chapterNum.value = null; chapterFilterTag.value = null; chapterAvailableTags.value = []; chapterTagsMap.value = {}; expandedChapters.value = new Set(); questions.value = []; resetState() }
  else if (key === 'wrong') { activeModule.value = 'wrong'; questions.value = []; resetState(); loadWrong() }
  else if (key === 'recommend') { activeModule.value = 'recommend'; questions.value = []; resetState(); loadRecommend() }
}

function toggleChapterExpand(chNum) {
  const s = new Set(expandedChapters.value)
  if (s.has(chNum)) {
    s.delete(chNum)
  } else {
    s.add(chNum)
    loadChapterTags(chNum)
  }
  expandedChapters.value = s
}

async function loadChapterTags(chNum) {
  if (chapterTagsMap.value[chNum]) return
  try {
    const res = await practiceApi.getByChapter(chapterStage.value, chNum)
    if (res.data.code === 200) {
      chapterTagsMap.value = { ...chapterTagsMap.value, [chNum]: res.data.data.available_tags || [] }
    }
  } catch {}
}

function selectChapterPractice(chNum, tag = null) {
  chapterNum.value = chNum
  chapterFilterTag.value = tag
}

async function loadChapterQuestions() {
  if (!chapterNum.value) return
  loading.value = true; questionError.value = ''
  try {
    const res = await practiceApi.getByChapter(chapterStage.value, chapterNum.value, chapterFilterType.value, chapterFilterDiff.value, chapterFilterTag.value)
    if (res.data.code === 200) {
      questions.value = res.data.data.questions
      chapterAvailableTags.value = res.data.data.available_tags || []
      resetState()
    }
  } catch (e) { questionError.value = '加载失败' }
  loading.value = false
}

async function loadWrong() {
  loading.value = true; questionError.value = ''
  try {
    const res = await practiceApi.getWrongQuestions(wrongFilterTag.value)
    if (res.data.code === 200) { questions.value = res.data.data.wrong_questions; resetState() }
  } catch (e) { questionError.value = '加载失败' }
  loading.value = false
}

async function loadRecommend() {
  loading.value = true; questionError.value = ''
  try {
    const res = await practiceApi.getRecommend(8)
    if (res.data.code === 200) {
      questions.value = res.data.data.questions
      recommendMeta.value = {
        recommend_mode: res.data.data.recommend_mode,
        reason: res.data.data.reason,
        question_reasons: res.data.data.question_reasons || [],
        learned_scope: res.data.data.learned_scope || {},
      }
      resetState()
    }
  } catch (e) { questionError.value = '加载失败' }
  loading.value = false
}

function onHintUsed(questionId, count) {
  hintCounts.value = { ...hintCounts.value, [questionId]: count }
}

function resetState() {
  userAnswers.value = {}; submitted.value = false; results.value = null; currentIndex.value = 0; hintCounts.value = {}; recommendMeta.value = null
}

async function submitAnswers() {
  const answers = questions.value.map(q => ({
    question_id: q.id,
    answer: userAnswers.value[q.id] || '',
    hints_used: hintCounts.value[q.id] || 0,
  }))
  submitting.value = true
  try {
    const res = await practiceApi.batchSubmit(answers)
    if (res.data.code === 200) {
      results.value = res.data.data
      submitted.value = true
      setPetMode('active')
      const pct = res.data.data.score_percent || 0
      if (pct >= 90) triggerPetState('excellent', 5000)
      else if (pct >= 75) triggerPetState('happy', 4000)
      else if (pct >= 60) triggerPetState('thinking', 4000)
      else triggerPetState('comfort', 4000)
    }
  } catch (e) { questionError.value = '提交失败' }
  submitting.value = false
}

function goBack() { activeModule.value = null; questions.value = []; submitted.value = false; results.value = null; userAnswers.value = {}; currentIndex.value = 0; setPetMode('active') }
function goToQuestion(idx) { if (idx >= 0 && idx < questions.value.length) currentIndex.value = idx }

// Helpers
function typeLabel(t) { const m = { single_choice: '单选题', multiple_choice: '多选题', judge: '判断题', fill_blank: '填空题', short_answer: '简答题', code: '代码题' }; return m[t] || t }
function diffLabel(d) { const m = { easy: '简单', medium: '中等', hard: '困难' }; return m[d] || d }
function diffColor(d) { const m = { easy: 'text-green-600 bg-green-50', medium: 'text-amber-600 bg-amber-50', hard: 'text-red-600 bg-red-50' }; return m[d] || '' }

onMounted(async () => {
  if (!auth.isLoggedIn) return

  // Handle query params from course "练一练" button
  const qStage = route.query.stage
  const qChapter = parseInt(route.query.chapter)
  const qTag = route.query.tag
  if (qStage && qChapter) {
    chapterStage.value = qStage
    activeModule.value = 'chapter'
    chapterNum.value = qChapter
    chapterFilterTag.value = qTag || null
    questions.value = []
    resetState()
    loadChapterQuestions()
  }

  try {
    const [r] = await Promise.all([practiceApi.getKnowledgePoints()])
    if (r.data.code === 200) knowledgeTags.value = r.data.data
  } catch {}
  loadMyFavorites()
})

// Reload favorites when module changes
watch(activeModule, () => { if (activeModule.value) loadMyFavorites() })

// Pet mode: silent during answering, active at settlement or idle
watch([activeModule, submitted], ([mod, sub]) => {
  if (!mod) setPetMode('active')
  else if (sub) setPetMode('active')
  else setPetMode('silent')
})

onUnmounted(() => { setPetMode('active') })
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <PageLoader /><AppHeader />
    <main class="flex-grow container mx-auto px-4 py-8">
      <div class="mb-8"><h1 class="text-3xl font-bold text-gray-900 mb-2">练习中心</h1><p class="text-gray-500">章节练习 · 专项突破 · 错题巩固 · 智能推荐</p></div>

      <div v-if="!auth.isLoggedIn" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
        <p class="text-5xl mb-4">🔒</p><h2 class="text-2xl font-bold text-gray-800 mb-2">请先登录</h2><p class="text-gray-500 mb-6">登录后进入练习中心</p>
        <router-link to="/login" class="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition shadow-lg">立即登录</router-link>
      </div>

      <!-- ====== MODULE HUB ====== -->
      <template v-if="auth.isLoggedIn && !activeModule">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-5xl mx-auto">

          <!-- 章节练习 - large -->
          <div @click="openModule('chapter')" class="md:col-span-2 group bg-gradient-to-br from-blue-50 to-white rounded-[2rem] shadow-sm border border-blue-100 p-8 md:p-10 hover:shadow-xl hover:-translate-y-1.5 transition-all cursor-pointer overflow-hidden relative">
            <div class="absolute top-0 right-0 w-40 h-40 bg-blue-100/40 rounded-bl-full -mr-10 -mt-10 group-hover:scale-150 transition-transform duration-500"></div>
            <div class="relative z-10 flex items-start gap-6">
              <div class="w-20 h-20 bg-blue-100 text-blue-600 rounded-[1.5rem] flex items-center justify-center text-4xl flex-shrink-0 group-hover:scale-110 transition-transform shadow-sm"><i class="fas fa-book"></i></div>
              <div>
                <div class="flex items-center gap-2 mb-2"><h3 class="font-bold text-gray-800 text-2xl">章节练习</h3><span class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-blue-100 text-blue-600">系统学习</span></div>
                <p class="text-gray-500 text-sm md:text-base mb-3">按课程章节系统练习，从入门到高级，逐个知识点击破</p>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="ch in currentChapterList.slice(0, 6)" :key="ch.n" class="text-[10px] px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-500">{{ ch.name }}</span>
                  <span class="text-[10px] text-gray-400">+{{ currentChapterList.length - 6 }} 更多...</span>
                </div>
              </div>
              <i class="fas fa-chevron-right text-gray-300 group-hover:text-blue-400 transition flex-shrink-0 mt-2 text-xl"></i>
            </div>
          </div>

          <!-- 错题本 -->
          <div @click="openModule('wrong')" class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-lg hover:-translate-y-1 transition-all cursor-pointer">
            <div class="flex items-start gap-4">
              <div class="w-14 h-14 bg-orange-100 text-orange-600 rounded-2xl flex items-center justify-center text-2xl shadow-sm flex-shrink-0 group-hover:scale-110 transition-transform"><i class="fas fa-exclamation-triangle"></i></div>
              <div class="flex-grow min-w-0">
                <div class="flex items-center gap-2 mb-1"><h3 class="font-bold text-gray-800 text-lg">错题本</h3><span class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-orange-100 text-orange-600">温故知新</span></div>
                <p class="text-sm text-gray-500">自动收录错题，重新练习直到掌握</p>
              </div>
              <i class="fas fa-chevron-right text-gray-300 group-hover:text-gray-500 transition flex-shrink-0 mt-2"></i>
            </div>
          </div>

          <!-- 智能推荐 - large -->
          <div @click="openModule('recommend')" class="md:col-span-2 group bg-gradient-to-br from-indigo-50 to-white rounded-[2rem] shadow-sm border border-indigo-100 p-8 md:p-10 hover:shadow-xl hover:-translate-y-1.5 transition-all cursor-pointer overflow-hidden relative">
            <div class="absolute top-0 right-0 w-40 h-40 bg-indigo-100/40 rounded-bl-full -mr-10 -mt-10 group-hover:scale-150 transition-transform duration-500"></div>
            <div class="relative z-10 flex items-start gap-6">
              <div class="w-20 h-20 bg-indigo-100 text-indigo-600 rounded-[1.5rem] flex items-center justify-center text-4xl flex-shrink-0 group-hover:scale-110 transition-transform shadow-sm"><i class="fas fa-lightbulb"></i></div>
              <div>
                <div class="flex items-center gap-2 mb-2"><h3 class="font-bold text-gray-800 text-2xl">智能推荐</h3><span class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-indigo-100 text-indigo-600">AI 驱动</span></div>
                <p class="text-gray-500 text-sm md:text-base mb-3">多维分析掌握程度，智能评分匹配最佳练习题，题库不足时 AI 自动生成</p>
                <p class="text-xs text-gray-400"><i class="fas fa-info-circle mr-1"></i>基于作答记录、正确率、AI提示使用、学习范围综合评分，优先补薄弱环节</p>
              </div>
              <i class="fas fa-chevron-right text-gray-300 group-hover:text-indigo-400 transition flex-shrink-0 mt-2 text-xl"></i>
            </div>
          </div>
        </div>
      </template>

      <!-- ====== QUESTION SESSION ====== -->
      <template v-if="auth.isLoggedIn && activeModule">
        <div class="flex items-center gap-4 mb-6">
          <button @click="goBack" class="w-10 h-10 bg-white rounded-full shadow-sm border border-gray-200 flex items-center justify-center hover:bg-gray-100 transition"><i class="fas fa-arrow-left text-gray-500"></i></button>
          <div class="flex items-center gap-3">
            <h2 class="text-xl font-bold text-gray-800">{{ moduleTitle }}</h2>
            <span v-if="activeModule === 'recommend' && recommendMeta && recommendModeLabel"
              class="text-xs px-2.5 py-1 rounded-full font-medium"
              :class="recommendMeta.recommend_mode === 'weakness_reinforce' ? 'bg-red-100 text-red-600' : recommendMeta.recommend_mode === 'ai_supplement' ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'">
              {{ recommendModeLabel }}
            </span>
          </div>
          <p class="text-sm text-gray-400" v-if="!submitted && questions.length">{{ currentIndex + 1 }} / {{ totalQuestions }} 题</p>
        </div>

        <div v-if="loading" class="text-center py-20 bg-white rounded-[2rem]"><i class="fas fa-spinner fa-spin text-4xl text-blue-400 mb-4 block"></i><p class="text-gray-400">加载题目中...</p></div>

        <!-- ====== CHAPTER: left sidebar tree with expandable tags ====== -->
        <div v-else-if="activeModule === 'chapter' && questions.length === 0" class="flex gap-5 min-h-0" style="min-height: 55vh;">
          <!-- Left sidebar -->
          <div class="w-72 flex-shrink-0 bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
            <!-- Stage tabs -->
            <div class="flex border-b border-gray-100 bg-gray-50 p-1 gap-0.5">
              <button v-for="s in ['初级','中级','高级']" :key="s" @click="chapterStage = s; chapterNum = null; chapterFilterTag = null; chapterAvailableTags = []; expandedChapters = new Set(); chapterTagsMap = {}"
                      :class="['flex-1 py-2 text-xs font-medium rounded-xl transition', chapterStage === s ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-400 hover:text-gray-600']">{{ s }}</button>
            </div>
            <!-- Expandable chapter list -->
            <div class="flex-grow overflow-y-auto py-1">
              <div v-for="ch in currentChapterList" :key="ch.n">
                <!-- Chapter row -->
                <button @click="toggleChapterExpand(ch.n)"
                  :class="['w-full text-left px-3 py-2.5 text-sm transition flex items-center gap-2', chapterNum === ch.n && !chapterFilterTag ? 'bg-blue-50 text-blue-700 font-bold border-r-2 border-blue-500' : 'text-gray-600 hover:bg-gray-50']">
                  <i :class="['fas text-[10px] text-gray-300 transition', expandedChapters.has(ch.n) ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
                  <span :class="['w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold flex-shrink-0', chapterNum === ch.n && !chapterFilterTag ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500']">{{ ch.n }}</span>
                  <span class="truncate flex-1">{{ ch.name }}</span>
                </button>
                <!-- Knowledge tags under this chapter -->
                <div v-if="expandedChapters.has(ch.n)" class="border-l-2 border-blue-100 ml-5 pl-2 space-y-0.5 pb-1">
                  <button @click="selectChapterPractice(ch.n, null)"
                    :class="['w-full text-left px-3 py-1.5 rounded-lg text-xs transition flex items-center gap-2', chapterNum === ch.n && !chapterFilterTag ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-500 hover:bg-gray-50']">
                    <i class="fas fa-book-open text-[10px] opacity-50"></i>整章练习
                  </button>
                  <button v-for="tag in (chapterTagsMap[ch.n] || [])" :key="tag" @click="selectChapterPractice(ch.n, tag)"
                    :class="['w-full text-left px-3 py-1.5 rounded-lg text-xs transition flex items-center gap-2', chapterNum === ch.n && chapterFilterTag === tag ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-500 hover:bg-gray-50']">
                    <i class="fas fa-tag text-[10px] opacity-50"></i>{{ tag }}
                  </button>
                  <div v-if="!(chapterTagsMap[ch.n] || []).length" class="text-[10px] text-gray-300 px-3 py-1">加载中...</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right area -->
          <div class="flex-grow bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex flex-col items-center justify-center text-center">
            <template v-if="!chapterNum">
              <div class="w-20 h-20 bg-blue-50 rounded-[1.5rem] flex items-center justify-center text-3xl mb-5"><i class="fas fa-arrow-left text-blue-300"></i></div>
              <h3 class="text-lg font-bold text-gray-700 mb-2">请先选择章节</h3>
              <p class="text-sm text-gray-400">在左侧展开章节，选择整章练习或具体知识点</p>
            </template>
            <template v-else>
              <div class="w-20 h-20 rounded-[1.5rem] flex items-center justify-center text-3xl mb-5"
                :class="chapterFilterTag ? 'bg-amber-50 text-amber-500' : 'bg-blue-50 text-blue-400'">
                <i :class="chapterFilterTag ? 'fas fa-tag' : 'fas fa-book-open'"></i>
              </div>
              <h3 class="text-lg font-bold text-gray-700 mb-1">{{ chapterStage }} · 第{{ chapterNum }}章</h3>
              <p class="text-sm text-gray-400 mb-1">{{ currentChapterList.find(c => c.n === chapterNum)?.name || '' }}</p>
              <p v-if="chapterFilterTag" class="text-xs font-medium text-amber-600 bg-amber-50 px-3 py-1 rounded-full inline-block mb-4">
                <i class="fas fa-tag mr-1"></i>{{ chapterFilterTag }}
              </p>
              <p v-else class="text-xs text-blue-500 bg-blue-50 px-3 py-1 rounded-full inline-block mb-4">整章练习</p>
              <div class="flex flex-wrap items-center gap-3 mb-4 justify-center">
                <select v-model="chapterFilterType" class="px-4 py-2.5 border border-gray-200 rounded-xl text-sm"><option :value="null">全部题型</option><option value="single_choice">单选题</option><option value="multiple_choice">多选题</option><option value="judge">判断题</option><option value="fill_blank">填空题</option><option value="code">代码题</option></select>
                <select v-model="chapterFilterDiff" class="px-4 py-2.5 border border-gray-200 rounded-xl text-sm"><option :value="null">全部难度</option><option value="easy">简单</option><option value="medium">中等</option><option value="hard">困难</option></select>
              </div>
              <button @click="loadChapterQuestions" class="px-8 py-3 bg-blue-600 text-white rounded-full text-sm font-bold hover:bg-blue-700 transition shadow-md">开始练习</button>
            </template>
          </div>
        </div>

        <!-- Empty states -->
        <div v-else-if="activeModule === 'wrong' && questions.length === 0 && !loading" class="text-center py-16 bg-white rounded-[2rem]"><i class="fas fa-check-circle text-5xl text-green-300 mb-4 block"></i><p class="text-gray-500 mb-2">暂无错题</p><p class="text-gray-400 text-sm">继续保持！</p><button @click="goBack" class="mt-4 text-blue-600 hover:underline text-sm">返回练习中心</button></div>
        <div v-else-if="questions.length === 0 && !loading" class="text-center py-16 bg-white rounded-[2rem]"><p class="text-gray-400">暂无题目</p></div>

        <!-- ====== QUESTIONS DISPLAY ====== -->
        <div v-else-if="questions.length > 0 && !submitted" class="max-w-3xl mx-auto">
          <div class="bg-white rounded-2xl shadow-sm border p-4 mb-4">
            <div class="flex items-center justify-between mb-2"><span class="text-sm text-gray-500">进度</span><span class="text-sm font-medium text-gray-700">{{ currentIndex + 1 }} / {{ totalQuestions }}</span></div>
            <div class="h-2 bg-gray-100 rounded-full overflow-hidden"><div class="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all duration-300" :style="{ width: progressPct + '%' }"></div></div>
          </div>
          <div class="flex flex-wrap gap-1.5 mb-4">
            <button v-for="(q, idx) in questions" :key="q.id" @click="goToQuestion(idx)" :class="['w-8 h-8 rounded-lg text-xs font-medium transition', idx === currentIndex ? 'bg-blue-600 text-white shadow' : userAnswers[q.id] ? 'bg-blue-100 text-blue-600 border border-blue-200' : 'bg-white text-gray-400 border border-gray-200 hover:border-gray-300']">{{ idx + 1 }}</button>
          </div>

          <div class="bg-white rounded-2xl shadow-sm border p-6 md:p-8">
            <div class="flex flex-wrap items-center gap-2 mb-4">
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">{{ typeLabel(currentQuestion.type) }}</span>
              <span :class="['text-[10px] font-bold px-2 py-0.5 rounded-full', diffColor(currentQuestion.difficulty)]">{{ diffLabel(currentQuestion.difficulty) }}</span>
              <span v-if="currentQuestion.knowledge_tag" class="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">{{ currentQuestion.knowledge_tag }}</span>
              <span v-if="currentQuestion.source === 'ai_generated'" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-600"><i class="fas fa-robot mr-0.5"></i>AI生成</span>
              <span v-if="activeModule === 'recommend' && recommendMeta && recommendMeta.question_reasons[currentIndex]" class="text-[10px] text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded-full truncate max-w-[240px]">{{ recommendMeta.question_reasons[currentIndex] }}</span>
              <span v-if="currentQuestion.score" class="text-[10px] text-gray-400">{{ currentQuestion.score }} 分</span>
              <!-- Favorite toggle -->
              <button @click="toggleFavorite(currentQuestion)" class="ml-auto w-7 h-7 rounded-full flex items-center justify-center transition" :class="isFav(currentQuestion) ? 'bg-red-50 text-red-500' : 'text-gray-300 hover:text-red-400 hover:bg-red-50'" :title="isFav(currentQuestion) ? '取消收藏' : '收藏题目'">
                <i :class="isFav(currentQuestion) ? 'fas fa-heart' : 'far fa-heart'" class="text-sm"></i>
              </button>
            </div>
            <h3 class="text-base font-bold text-gray-800 mb-6 leading-relaxed">{{ currentQuestion.title || currentQuestion.content }}</h3>

            <!-- AI Hint -->
            <div class="mb-4">
              <AiHintCard
                :key="currentQuestion.id"
                :question-id="currentQuestion.id"
                :question="currentQuestion.title || currentQuestion.content"
                :question-type="currentQuestion.type"
                :difficulty="currentQuestion.difficulty"
                :knowledge-tag="currentQuestion.knowledge_tag"
                :knowledge-type="currentQuestion.knowledge_type || ''"
                :student-code="userAnswers[currentQuestion.id] || ''"
                @hint-used="(count) => onHintUsed(currentQuestion.id, count)"
              />
            </div>

            <div class="space-y-3">
              <template v-if="currentQuestion.type === 'judge'">
                <div v-for="opt in [{l:'√',t:'正确'},{l:'×',t:'错误'}]" :key="opt.l" @click="selectAnswer(currentQuestion.id, opt.t)" :class="['flex items-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all', isSelected(currentQuestion.id, opt.t) ? 'border-blue-400 bg-blue-50 shadow-sm' : 'border-gray-100 hover:border-gray-300']">
                  <div :class="['w-5 h-5 rounded-full border-2 flex items-center justify-center', isSelected(currentQuestion.id, opt.t) ? 'border-blue-500' : 'border-gray-300']"><div v-if="isSelected(currentQuestion.id, opt.t)" class="w-3 h-3 rounded-full bg-blue-500"></div></div>
                  <span class="text-sm text-gray-700">{{ opt.t }}</span>
                </div>
              </template>
              <template v-else-if="currentQuestion.type === 'fill_blank' || currentQuestion.type === 'short_answer'">
                <input v-model="userAnswers[currentQuestion.id]" :placeholder="currentQuestion.type === 'fill_blank' ? '请输入答案...' : '请输入你的回答...'" class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-400 transition" />
              </template>
              <template v-else-if="currentQuestion.type === 'code'">
                <textarea v-model="userAnswers[currentQuestion.id]" class="w-full h-48 p-4 font-mono text-sm bg-gray-900 text-green-400 rounded-xl outline-none resize-none" placeholder="在这里编写代码..."></textarea>
                <div v-if="currentQuestion.starter_code" class="mt-2 text-xs text-gray-400">参考框架：<pre class="inline font-mono bg-gray-100 px-1 rounded">{{ currentQuestion.starter_code }}</pre></div>
              </template>
              <template v-else-if="currentQuestion.type === 'multiple_choice'">
                <div v-for="opt in (currentQuestion.options || [])" :key="opt.label" @click="toggleMulti(currentQuestion.id, opt.label)" :class="['flex items-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all', isMultiSelected(currentQuestion.id, opt.label) ? 'border-blue-400 bg-blue-50 shadow-sm' : 'border-gray-100 hover:border-gray-300']">
                  <div :class="['w-5 h-5 rounded border-2 flex items-center justify-center text-xs font-bold transition', isMultiSelected(currentQuestion.id, opt.label) ? 'border-blue-500 bg-blue-500 text-white' : 'border-gray-300 text-transparent']"><i v-if="isMultiSelected(currentQuestion.id, opt.label)" class="fas fa-check text-[10px]"></i></div>
                  <span class="text-sm font-medium text-gray-500 mr-1">{{ opt.label }}.</span><span class="text-sm text-gray-700">{{ opt.text }}</span>
                </div>
              </template>
              <template v-else>
                <div v-for="opt in (currentQuestion.options || [])" :key="opt.label" @click="selectAnswer(currentQuestion.id, opt.label)" :class="['flex items-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all', isSelected(currentQuestion.id, opt.label) ? 'border-blue-400 bg-blue-50 shadow-sm' : 'border-gray-100 hover:border-gray-300']">
                  <div :class="['w-5 h-5 rounded-full border-2 flex items-center justify-center', isSelected(currentQuestion.id, opt.label) ? 'border-blue-500' : 'border-gray-300']"><div v-if="isSelected(currentQuestion.id, opt.label)" class="w-3 h-3 rounded-full bg-blue-500"></div></div>
                  <span class="text-sm font-medium text-gray-500 mr-1">{{ opt.label }}.</span><span class="text-sm text-gray-700">{{ opt.text }}</span>
                </div>
              </template>
            </div>

            <div class="flex items-center justify-between mt-8 pt-6 border-t border-gray-100">
              <button @click="goToQuestion(currentIndex - 1)" :disabled="currentIndex === 0" class="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition disabled:opacity-30 disabled:cursor-not-allowed"><i class="fas fa-chevron-left mr-1"></i>上一题</button>
              <div class="flex gap-2">
                <button v-if="currentIndex < totalQuestions - 1" @click="goToQuestion(currentIndex + 1)" class="px-5 py-2 text-sm bg-blue-600 text-white rounded-full hover:bg-blue-700 transition font-medium">下一题<i class="fas fa-chevron-right ml-1"></i></button>
                <button v-else @click="submitAnswers" :disabled="submitting" class="px-6 py-2 bg-green-600 text-white rounded-full text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition"><i v-if="submitting" class="fas fa-spinner fa-spin mr-1"></i>{{ submitting ? '提交中...' : '提交答案' }}</button>
              </div>
            </div>
          </div>
        </div>

        <!-- ====== RESULTS ====== -->
        <div v-if="submitted && results" class="max-w-3xl mx-auto">
          <div class="bg-white rounded-2xl shadow-sm border p-8 text-center mb-6">
            <div class="w-24 h-24 mx-auto mb-4 rounded-full flex items-center justify-center text-3xl font-bold" :class="results.score_percent >= 80 ? 'bg-green-100 text-green-600' : results.score_percent >= 60 ? 'bg-amber-100 text-amber-600' : 'bg-red-100 text-red-600'">{{ results.score_percent }}%</div>
            <h3 class="text-2xl font-bold text-gray-800 mb-1">{{ results.score_percent >= 80 ? '优秀！' : results.score_percent >= 60 ? '良好' : '继续加油' }}</h3>
            <p class="text-gray-500">共 {{ results.total }} 题，答对 {{ results.score }} 题<span v-if="results.experience_gained" class="text-blue-600 font-medium">，+{{ results.experience_gained }} 经验</span></p>
            <div v-if="results.weak_tags && results.weak_tags.length" class="mt-4">
              <p class="text-sm text-gray-500 mb-2">薄弱知识点：</p>
              <div class="flex flex-wrap justify-center gap-1.5">
                <span v-for="(tag, i) in (Array.isArray(results.weak_tags[0]) ? results.weak_tags : results.weak_tags.map(t => [t, 0]))" :key="i" class="text-xs px-2.5 py-1 rounded-full bg-red-50 text-red-600 font-medium">{{ Array.isArray(tag) ? tag[0] : tag }}</span>
              </div>
            </div>
          </div>

          <div class="space-y-3 mb-6">
            <div v-for="(q, idx) in questions" :key="q.id" class="bg-white rounded-xl shadow-sm border p-5" :class="getResultForQuestion(q.id)?.is_correct ? 'border-green-200' : 'border-red-200'">
              <div class="flex items-start gap-3">
                <div :class="['w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5', getResultForQuestion(q.id)?.is_correct ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600']">{{ getResultForQuestion(q.id)?.is_correct ? '✓' : '✗' }}</div>
                <div class="flex-grow min-w-0">
                  <div class="flex items-start justify-between gap-2">
                    <p class="text-sm font-medium text-gray-800 mb-1">
                      {{ idx + 1 }}. {{ q.title || q.content }}
                      <span v-if="q.source === 'ai_generated'" class="text-[10px] bg-purple-50 text-purple-500 px-1.5 py-0.5 rounded-full ml-1 align-middle"><i class="fas fa-robot mr-0.5"></i>AI</span>
                    </p>
                    <button @click="toggleFavorite(q)" class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition" :class="isFav(q) ? 'bg-red-50 text-red-500' : 'text-gray-300 hover:text-red-400 hover:bg-red-50'">
                      <i :class="isFav(q) ? 'fas fa-heart' : 'far fa-heart'" class="text-xs"></i>
                    </button>
                  </div>
                  <div v-if="!getResultForQuestion(q.id)?.is_correct" class="text-xs space-y-1">
                    <p class="text-red-600">你的答案：{{ userAnswers[q.id] || '（未作答）' }}</p>
                    <p class="text-green-600">正确答案：{{ getResultForQuestion(q.id)?.correct_answer || q.answer }}</p>
                  </div>
                  <p v-if="getResultForQuestion(q.id)?.analysis" class="text-xs text-gray-500 mt-1.5 leading-relaxed"><span class="font-medium text-gray-600">解析：</span>{{ getResultForQuestion(q.id)?.analysis }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="flex justify-center gap-3 mb-10">
            <button @click="goBack" class="px-6 py-2.5 bg-white border border-gray-200 text-gray-600 rounded-full text-sm font-medium hover:bg-gray-50 transition">返回练习中心</button>
            <button @click="activeModule === 'wrong' ? loadWrong() : activeModule === 'recommend' ? loadRecommend() : goBack()" class="px-6 py-2.5 bg-blue-600 text-white rounded-full text-sm font-medium hover:bg-blue-700 transition">再来一组</button>
          </div>
        </div>
      </template>
    </main>
    <AppFooter />
  </div>
</template>
