<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const router = useRouter()
const result = ref(null)
const loading = ref(true)

const rankGradients = {
  '萌新小白': 'from-gray-400 to-gray-600',
  '勤学学徒': 'from-green-400 to-emerald-600',
  '达标选手': 'from-blue-400 to-blue-600',
  '稳扎玩家': 'from-purple-400 to-purple-600',
  '进阶干将': 'from-amber-400 to-orange-600',
  '学科达人': 'from-red-400 to-rose-600',
  '专业先锋': 'from-cyan-400 to-teal-600',
  '满级学神': 'from-yellow-400 to-amber-600',
}

const rankBadgeColors = {
  '萌新小白': 'bg-gray-100 text-gray-600',
  '勤学学徒': 'bg-green-100 text-green-600',
  '达标选手': 'bg-blue-100 text-blue-600',
  '稳扎玩家': 'bg-purple-100 text-purple-600',
  '进阶干将': 'bg-amber-100 text-amber-700',
  '学科达人': 'bg-red-100 text-red-600',
  '专业先锋': 'bg-teal-100 text-teal-700',
  '满级学神': 'bg-yellow-100 text-yellow-700',
}

const rankDescriptions = {
  '萌新小白': 'Python 编程世界的新成员，从这里开启你的成长之旅！',
  '勤学学徒': '基础扎实，继续保持学习和练习的节奏。',
  '达标选手': '已掌握核心知识，具备独立解决问题的能力。',
  '稳扎玩家': '知识体系完善，是时候向更高段位发起挑战了！',
}

const rankLabel = computed(() => {
  if (!result.value) return ''
  return result.value.assigned_rank || result.value.level || ''
})

const rankDesc = computed(() => rankDescriptions[rankLabel.value] || '')

const gradientClass = computed(() => rankGradients[rankLabel.value] || 'from-gray-400 to-gray-600')
const badgeClass = computed(() => rankBadgeColors[rankLabel.value] || 'bg-gray-100 text-gray-600')

const scoreRingStyle = computed(() => {
  if (!result.value) return {}
  const pct = result.value.score_percent
  const color = pct >= 80 ? '#10b981' : pct >= 60 ? '#3b82f6' : pct >= 40 ? '#f59e0b' : '#ef4444'
  return {
    background: `conic-gradient(${color} ${pct * 3.6}deg, #e5e7eb ${pct * 3.6}deg)`,
  }
})

onMounted(() => {
  const cached = localStorage.getItem('lastAssessmentResult')
  if (cached) {
    try {
      result.value = JSON.parse(cached)
    } catch {}
  }
  loading.value = false
})

function goToCourses() {
  router.push('/courses')
}

function goToPractice() {
  router.push('/practice')
}

function retakeAssessment() {
  localStorage.removeItem('lastAssessmentResult')
  router.push('/assessment')
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <div v-if="loading" class="text-center py-20">
        <div class="animate-spin-slow w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full mx-auto mb-4"></div>
        <p class="text-gray-500">加载中...</p>
      </div>

      <template v-else-if="result">
        <div class="max-w-2xl mx-auto">
          <!-- Score card -->
          <div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden mb-8">
            <div class="h-32 bg-gradient-to-r" :class="gradientClass" style="display:flex;align-items:center;justify-content:center;position:relative">
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="w-28 h-28 rounded-full flex items-center justify-center" :style="scoreRingStyle">
                  <div class="w-24 h-24 rounded-full bg-white flex flex-col items-center justify-center">
                    <span class="text-3xl font-extrabold text-gray-900">{{ result.score_percent }}</span>
                    <span class="text-xs text-gray-400">分</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="p-8 text-center">
              <span class="inline-block text-sm font-bold px-4 py-1.5 rounded-full mb-3" :class="badgeClass">
                {{ rankLabel }}
              </span>
              <h1 class="text-2xl font-bold text-gray-900 mb-2">测评完成！</h1>
              <p class="text-gray-500">答对 {{ result.score }}/{{ result.total }} 题，正确率 {{ result.score_percent }}%</p>
              <p v-if="rankDesc" class="text-gray-600 text-sm mt-2 max-w-md mx-auto leading-relaxed">{{ rankDesc }}</p>
              <p v-if="result.experience_gained" class="text-blue-600 text-sm mt-2 font-medium">+{{ result.experience_gained }} 经验值</p>
            </div>
          </div>

          <!-- Weak points -->
          <div v-if="result.weak_points && result.weak_points.length > 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
            <h3 class="font-bold text-gray-900 mb-3 flex items-center">
              <i class="fas fa-exclamation-triangle text-orange-500 mr-2"></i>薄弱知识点
            </h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="wp in result.weak_points" :key="wp"
                class="px-3 py-1.5 bg-orange-50 text-orange-600 rounded-full text-sm font-medium border border-orange-200">
                {{ wp }}
              </span>
            </div>
          </div>

          <!-- Wrong questions -->
          <div v-if="result.wrong_questions && result.wrong_questions.length > 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
            <h3 class="font-bold text-gray-900 mb-4 flex items-center">
              <i class="fas fa-times-circle text-red-400 mr-2"></i>错题回顾 ({{ result.wrong_questions.length }} 题)
            </h3>
            <div class="space-y-4">
              <div v-for="wq in result.wrong_questions" :key="wq.id" class="p-4 bg-red-50 rounded-xl border border-red-100">
                <p class="font-medium text-gray-800 mb-2">{{ wq.content }}</p>
                <p class="text-sm text-red-500">你的答案：<span class="font-bold">{{ wq.user_answer }}</span></p>
                <p class="text-sm text-green-600">正确答案：<span class="font-bold">{{ wq.correct_answer }}</span></p>
                <p v-if="wq.analysis" class="text-sm text-gray-500 mt-2 bg-white p-3 rounded-lg">{{ wq.analysis }}</p>
              </div>
            </div>
          </div>

          <!-- Recommended courses -->
          <div v-if="result.recommended_courses && result.recommended_courses.length > 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-8">
            <h3 class="font-bold text-gray-900 mb-4 flex items-center">
              <i class="fas fa-book-open text-blue-500 mr-2"></i>推荐课程
            </h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div v-for="c in result.recommended_courses" :key="c.id"
                @click="goToCourses()"
                class="p-4 rounded-xl border-2 border-gray-100 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition-all">
                <p class="font-bold text-gray-800">{{ c.title }}</p>
                <p class="text-xs text-gray-400 mt-1">{{ c.category }}</p>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex flex-col sm:flex-row gap-3 mb-16">
            <button @click="goToCourses" class="flex-1 bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 transition shadow-lg">
              <i class="fas fa-play mr-2"></i>开始学习推荐课程
            </button>
            <button @click="goToPractice" class="flex-1 bg-purple-600 text-white py-3 rounded-xl font-bold hover:bg-purple-700 transition shadow-lg">
              <i class="fas fa-dumbbell mr-2"></i>去练习巩固
            </button>
            <button @click="retakeAssessment" class="flex-1 bg-gray-100 text-gray-600 py-3 rounded-xl font-medium hover:bg-gray-200 transition">
              <i class="fas fa-redo mr-2"></i>重新测评
            </button>
          </div>
        </div>
      </template>

      <div v-else class="text-center py-20">
        <p class="text-5xl mb-4">📋</p>
        <p class="text-gray-500 mb-4">暂无测评结果</p>
        <button @click="retakeAssessment" class="bg-blue-600 text-white px-6 py-2.5 rounded-full font-bold hover:bg-blue-700 transition shadow-lg">
          开始能力测评
        </button>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
