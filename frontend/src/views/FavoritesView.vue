<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { favoritesApi } from '../api/favorites'
import { courseLevels } from '../data/courseData.js'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const router = useRouter()
const auth = useAuthStore()
const favorites = ref([])
const loading = ref(true)
const activeTab = ref('course')

const courseFavs = computed(() => favorites.value.filter(f => f.item_type === 'course'))
const questionFavs = computed(() => favorites.value.filter(f => f.item_type === 'question'))

onMounted(async () => {
  if (!auth.isLoggedIn) { loading.value = false; return }
  try {
    const res = await favoritesApi.list()
    if (res.data.code === 200) favorites.value = res.data.data
  } catch (e) { console.error(e) }
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
        <div class="flex gap-2 mb-6">
          <button @click="activeTab = 'course'"
                  :class="['px-5 py-2 rounded-full text-sm font-medium transition', activeTab === 'course' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-gray-500 hover:bg-gray-100 border border-gray-200']">
            <i class="fas fa-book-open mr-1.5"></i>课程收藏
            <span class="ml-1 text-xs opacity-70">({{ courseFavs.length }})</span>
          </button>
          <button @click="activeTab = 'question'"
                  :class="['px-5 py-2 rounded-full text-sm font-medium transition', activeTab === 'question' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-gray-500 hover:bg-gray-100 border border-gray-200']">
            <i class="fas fa-question-circle mr-1.5"></i>题目收藏
            <span class="ml-1 text-xs opacity-70">({{ questionFavs.length }})</span>
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-16 text-gray-400">
          <i class="fas fa-spinner fa-spin text-3xl mb-3"></i>
          <p>加载中...</p>
        </div>

        <!-- Course Favorites -->
        <div v-else-if="activeTab === 'course'">
          <div v-if="courseFavs.length === 0" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
            <i class="fas fa-bookmark text-5xl text-gray-300 mb-4 block"></i>
            <p class="text-gray-500 mb-2">暂无收藏课程</p>
            <p class="text-gray-400 text-sm">前往 <router-link to="/courses" class="text-blue-500 hover:underline">课程中心</router-link> 浏览并收藏感兴趣的章节</p>
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="fav in courseFavs" :key="fav.id"
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
        <div v-else>
          <div v-if="questionFavs.length === 0" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
            <i class="fas fa-star text-5xl text-gray-300 mb-4 block"></i>
            <p class="text-gray-500 mb-2">暂无收藏题目</p>
            <p class="text-gray-400 text-sm">前往 <router-link to="/practice" class="text-blue-500 hover:underline">每日一练</router-link> 做题时收藏经典题目</p>
          </div>
          <div v-else class="space-y-3">
            <div v-for="fav in questionFavs" :key="fav.id"
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
      </template>
    </main>

    <AppFooter />
  </div>
</template>
