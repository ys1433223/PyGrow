<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { favoritesApi } from '../api/favorites'
import { practiceApi } from '../api/practice'
import { courseLevels } from '../data/courseData.js'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const router = useRouter()
const auth = useAuthStore()
const favorites = ref([])
const loading = ref(true)
const activeTab = ref('course')
const wrongQuestions = ref([])
const loadingWrong = ref(false)
const searchQuery = ref('')

const courseFavs = computed(() => favorites.value.filter(f => f.item_type === 'course'))
const questionFavs = computed(() => favorites.value.filter(f => f.item_type === 'question'))

const filteredCourseFavs = computed(() => {
  if (!searchQuery.value.trim()) return courseFavs.value
  const q = searchQuery.value.trim().toLowerCase()
  return courseFavs.value.filter(f => f.title.toLowerCase().includes(q))
})
const filteredQuestionFavs = computed(() => {
  if (!searchQuery.value.trim()) return questionFavs.value
  const q = searchQuery.value.trim().toLowerCase()
  return questionFavs.value.filter(f => f.title.toLowerCase().includes(q))
})
const filteredWrongQuestions = computed(() => {
  if (!searchQuery.value.trim()) return wrongQuestions.value
  const q = searchQuery.value.trim().toLowerCase()
  return wrongQuestions.value.filter(w =>
    (w.title || '').toLowerCase().includes(q) ||
    (w.content || '').toLowerCase().includes(q) ||
    (w.knowledge_tag || '').toLowerCase().includes(q)
  )
})

// Helpers for wrong questions display
function typeLabel(t) { const m = { single_choice: '单选题', multiple_choice: '多选题', judge: '判断题', fill_blank: '填空题', short_answer: '简答题', code: '代码题' }; return m[t] || t }
function diffLabel(d) { const m = { easy: '简单', medium: '中等', hard: '困难' }; return m[d] || d }
function diffColor(d) { const m = { easy: 'text-green-600 bg-green-50', medium: 'text-amber-600 bg-amber-50', hard: 'text-red-600 bg-red-50' }; return m[d] || '' }

async function fetchWrongQuestions() {
  loadingWrong.value = true
  try {
    const res = await practiceApi.getWrongQuestions(null)
    if (res.data.code === 200) {
      wrongQuestions.value = res.data.data.wrong_questions || []
    }
  } catch {} finally { loadingWrong.value = false }
}

onMounted(async () => {
  if (!auth.isLoggedIn) { loading.value = false; return }
  try {
    const res = await favoritesApi.list()
    if (res.data.code === 200) favorites.value = res.data.data
  } catch (e) { console.error(e) }
  fetchWrongQuestions()
  loading.value = false
})

async function removeFav(fav) {
  try {
    await favoritesApi.remove(fav.id)
    favorites.value = favorites.value.filter(f => f.id !== fav.id)
  } catch (e) { console.error(e) }
}

function getCourseInfo(itemId) {
  // item_id like "初级-1", "中级-3", "高级-2"
  const parts = itemId.split('-')
  const level = parts[0]
  const chNum = parseInt(parts[1])
  const course = courseLevels.find(c => c.level === level)
  const chapter = course?.chapters.find(ch => ch.num === chNum)
  return {
    level,
    chapterNum: chNum,
    chapterTitle: chapter?.title || '',
    courseName: course?.name || '',
  }
}

function goToCourse(itemId) {
  const parts = itemId.split('-')
  const level = parts[0]
  const chapterNum = parseInt(parts[1])
  router.push(`/courses?level=${encodeURIComponent(level)}&chapter=${chapterNum}`)
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <button @click="$router.push('/learning-center')" class="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mb-3 transition"><i class="fas fa-arrow-left"></i> 返回学习中心</button>
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">我的收藏</h1>
        <p class="text-gray-500">收藏的课程章节和练习题目</p>
      </div>

      <!-- Login check -->
      <div v-if="!auth.isLoggedIn" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
        <p class="text-5xl mb-4">🔒</p>
        <h2 class="text-2xl font-bold text-gray-800 mb-2">请先登录</h2>
        <p class="text-gray-500 mb-6">登录后查看收藏内容</p>
        <router-link to="/login" class="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition shadow-lg">
          立即登录
        </router-link>
      </div>

      <template v-else>
        <!-- Tabs -->
        <div class="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
          <div class="flex gap-2">
            <button @click="activeTab = 'course'; searchQuery = ''"
                    :class="['px-5 py-2 rounded-full text-sm font-medium transition', activeTab === 'course' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-gray-500 hover:bg-gray-100 border border-gray-200']">
              <i class="fas fa-book-open mr-1.5"></i>课程收藏
              <span class="ml-1 text-xs opacity-70">({{ filteredCourseFavs.length }})</span>
            </button>
            <button @click="activeTab = 'question'; searchQuery = ''"
                    :class="['px-5 py-2 rounded-full text-sm font-medium transition', activeTab === 'question' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-gray-500 hover:bg-gray-100 border border-gray-200']">
              <i class="fas fa-question-circle mr-1.5"></i>题目收藏
              <span class="ml-1 text-xs opacity-70">({{ filteredQuestionFavs.length }})</span>
            </button>
            <button @click="activeTab = 'wrong'; searchQuery = ''"
                    :class="['px-5 py-2 rounded-full text-sm font-medium transition', activeTab === 'wrong' ? 'bg-red-500 text-white shadow-md' : 'bg-white text-gray-500 hover:bg-gray-100 border border-gray-200']">
              <i class="fas fa-book mr-1.5"></i>错题本
              <span class="ml-1 text-xs opacity-70">({{ filteredWrongQuestions.length }})</span>
            </button>
          </div>

          <!-- Search bar -->
          <div class="relative sm:ml-auto w-full sm:w-64">
            <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs"></i>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索..."
              class="w-full pl-9 pr-8 py-2 text-sm border border-gray-200 rounded-xl bg-white focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition"
            />
            <button
              v-if="searchQuery"
              @click="searchQuery = ''"
              class="absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-gray-200 text-gray-500 hover:bg-gray-300 transition flex items-center justify-center text-[10px]"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-16 text-gray-400">
          <i class="fas fa-spinner fa-spin text-3xl mb-3"></i>
          <p>加载中...</p>
        </div>

        <!-- Course Favorites -->
        <div v-else-if="activeTab === 'course'">
          <div v-if="searchQuery && filteredCourseFavs.length !== courseFavs.length" class="mb-3 text-xs text-gray-400">
            搜索 "{{ searchQuery }}" — 找到 {{ filteredCourseFavs.length }}/{{ courseFavs.length }} 条
          </div>
          <div v-if="filteredCourseFavs.length === 0" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
            <i class="fas fa-bookmark text-5xl text-gray-300 mb-4 block"></i>
            <p class="text-gray-500 mb-2">{{ searchQuery ? '没有匹配的收藏课程' : '暂无收藏课程' }}</p>
            <p class="text-gray-400 text-sm" v-if="!searchQuery">前往 <router-link to="/courses" class="text-blue-500 hover:underline">课程中心</router-link> 浏览并收藏感兴趣的章节</p>
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="fav in filteredCourseFavs" :key="fav.id"
                 class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition group">
              <div class="flex items-start justify-between">
                <div class="flex-grow min-w-0">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-full"
                        :class="getCourseInfo(fav.item_id).level === '初级' ? 'bg-green-100 text-green-600' : getCourseInfo(fav.item_id).level === '中级' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'">
                    {{ getCourseInfo(fav.item_id).courseName }}
                  </span>
                  <h3 class="text-sm font-bold text-gray-800 mt-2">{{ fav.title }}</h3>
                  <p class="text-xs text-gray-400 mt-1">第{{ getCourseInfo(fav.item_id).chapterNum }}章 · {{ getCourseInfo(fav.item_id).chapterTitle }}</p>
                </div>
                <div class="flex flex-col items-center gap-2 ml-3">
                  <button @click="goToCourse(fav.item_id)"
                          class="w-8 h-8 bg-blue-50 text-blue-500 rounded-lg hover:bg-blue-100 transition flex items-center justify-center text-xs">
                    <i class="fas fa-arrow-right"></i>
                  </button>
                  <button @click="removeFav(fav)"
                          class="w-8 h-8 bg-red-50 text-red-400 rounded-lg hover:bg-red-100 hover:text-red-500 transition flex items-center justify-center text-xs">
                    <i class="fas fa-trash-alt"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Question Favorites -->
        <div v-else-if="activeTab === 'question'">
          <div v-if="searchQuery && filteredQuestionFavs.length !== questionFavs.length" class="mb-3 text-xs text-gray-400">
            搜索 "{{ searchQuery }}" — 找到 {{ filteredQuestionFavs.length }}/{{ questionFavs.length }} 条
          </div>
          <div v-if="filteredQuestionFavs.length === 0" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
            <i class="fas fa-star text-5xl text-gray-300 mb-4 block"></i>
            <p class="text-gray-500 mb-2">{{ searchQuery ? '没有匹配的收藏题目' : '暂无收藏题目' }}</p>
            <p class="text-gray-400 text-sm" v-if="!searchQuery">前往 <router-link to="/practice" class="text-blue-500 hover:underline">每日一练</router-link> 做题时收藏经典题目</p>
          </div>
          <div v-else class="space-y-3">
            <div v-for="fav in filteredQuestionFavs" :key="fav.id"
                 class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center text-amber-500 flex-shrink-0">
                  <i class="fas fa-question"></i>
                </div>
                <div>
                  <p class="text-sm font-bold text-gray-800">{{ fav.title }}</p>
                  <p class="text-xs text-gray-400">收藏于 {{ fav.created_at?.split('T')[0] }}</p>
                </div>
              </div>
              <button @click="removeFav(fav)"
                      class="w-8 h-8 bg-red-50 text-red-400 rounded-lg hover:bg-red-100 hover:text-red-500 transition flex items-center justify-center text-xs flex-shrink-0">
                <i class="fas fa-trash-alt"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- Wrong Questions -->
        <div v-else-if="activeTab === 'wrong'">
          <div v-if="loadingWrong" class="text-center py-12">
            <div class="animate-spin w-5 h-5 border-2 border-red-500 border-t-transparent rounded-full mx-auto"></div>
          </div>
          <div v-else-if="wrongQuestions.length === 0" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
            <div class="w-16 h-16 mx-auto mb-3 bg-red-50 rounded-full flex items-center justify-center">
              <i class="fas fa-check-circle text-red-300 text-2xl"></i>
            </div>
            <p class="text-gray-500 mb-2">暂无错题</p>
            <p class="text-gray-400 text-sm">继续保持！<router-link to="/practice" class="text-blue-500 hover:underline">去练习中心</router-link> 巩固知识</p>
          </div>
          <div v-else>
            <div v-if="searchQuery && filteredWrongQuestions.length !== wrongQuestions.length" class="mb-3 text-xs text-gray-400">
              搜索 "{{ searchQuery }}" — 找到 {{ filteredWrongQuestions.length }}/{{ wrongQuestions.length }} 条
            </div>
            <div v-if="filteredWrongQuestions.length === 0" class="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-100">
              <p class="text-gray-400 text-sm">没有匹配的错题</p>
            </div>
            <div v-else class="space-y-2">
              <div class="flex items-center justify-between mb-3">
                <p class="text-sm font-medium text-gray-500">共 <b class="text-red-500">{{ filteredWrongQuestions.length }}</b> 道错题</p>
                <button @click="router.push('/practice')"
                  class="text-xs text-red-500 hover:text-red-600 font-medium transition">
                  <i class="fas fa-pen-to-square mr-1"></i>去练习
                </button>
              </div>
              <div v-for="q in filteredWrongQuestions" :key="q.id"
                class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition cursor-pointer"
                @click="router.push('/practice?module=wrong')">
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1 min-w-0">
                    <p class="text-sm text-gray-700 leading-relaxed line-clamp-2">{{ q.title || q.content }}</p>
                    <div class="flex flex-wrap items-center gap-1.5 mt-2">
                      <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">{{ typeLabel(q.type) }}</span>
                      <span class="text-[10px] font-bold px-1.5 py-0.5 rounded" :class="diffColor(q.difficulty)">{{ diffLabel(q.difficulty) }}</span>
                      <span v-if="q.knowledge_tag" class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">{{ q.knowledge_tag }}</span>
                    </div>
                  </div>
                  <i class="fas fa-chevron-right text-gray-300 text-xs mt-1 flex-shrink-0"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>

    <AppFooter />
  </div>
</template>
