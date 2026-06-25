<script setup>
import { ref, onMounted } from 'vue'
import { reportsApi } from '../api/reports'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import ExpBar from '../components/common/ExpBar.vue'

const summary = ref(null)
const knowledge = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [sRes, kRes] = await Promise.all([
      reportsApi.getSummary(),
      reportsApi.getKnowledgePoints(),
    ])
    if (sRes.data.code === 200) summary.value = sRes.data.data
    if (kRes.data.code === 200) knowledge.value = kRes.data.data
  } catch (e) {
    console.error('Failed to load report:', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <div class="max-w-3xl mx-auto">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">学习报告</h1>
        <p class="text-gray-500 mb-8">你的学习成长记录</p>

        <div v-if="loading" class="text-center py-20">
          <div class="animate-spin-slow w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full mx-auto mb-4"></div>
          <p class="text-gray-400">加载中...</p>
        </div>

        <template v-else-if="summary">
          <!-- Level & XP -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
            <h3 class="font-bold text-gray-900 mb-4 flex items-center">
              <i class="fas fa-trophy text-yellow-500 mr-2"></i>当前等级
            </h3>
            <div class="flex items-center gap-4 mb-4">
              <div class="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xl font-bold shadow-lg">
                {{ summary.level.charAt(0) }}
              </div>
              <div class="flex-1">
                <ExpBar
                  :experience="summary.experience"
                  :next-level-xp="summary.nextLevelXp || (summary.experience + 100)"
                  :current-level="summary.level"
                  :progress-percent="summary.progressPercent || 0"
                />
              </div>
            </div>
            <div class="flex items-center text-sm text-gray-500 gap-6">
              <span><i class="fas fa-star text-yellow-400 mr-1"></i>{{ summary.points }} 积分</span>
            </div>
          </div>

          <!-- Stats grid -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center">
              <p class="text-3xl font-extrabold text-blue-600">{{ summary.completed_courses }}</p>
              <p class="text-xs text-gray-400 mt-1">完成课程</p>
            </div>
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center">
              <p class="text-3xl font-extrabold text-green-600">{{ summary.total_practice }}</p>
              <p class="text-xs text-gray-400 mt-1">练习总数</p>
            </div>
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center">
              <p class="text-3xl font-extrabold text-purple-600">{{ summary.accuracy }}%</p>
              <p class="text-xs text-gray-400 mt-1">正确率</p>
            </div>
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center">
              <p class="text-3xl font-extrabold text-red-500">{{ summary.wrong_count }}</p>
              <p class="text-xs text-gray-400 mt-1">错题数</p>
            </div>
          </div>

          <!-- Second row -->
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center">
              <p class="text-2xl font-extrabold text-indigo-600">{{ summary.in_progress_courses }}</p>
              <p class="text-xs text-gray-400 mt-1">学习中课程</p>
            </div>
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center">
              <p class="text-2xl font-extrabold text-orange-500">{{ summary.experience }}</p>
              <p class="text-xs text-gray-400 mt-1">总经验值</p>
            </div>
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center col-span-2 md:col-span-1">
              <p class="text-2xl font-extrabold text-teal-500">{{ summary.points }}</p>
              <p class="text-xs text-gray-400 mt-1">总积分</p>
            </div>
          </div>

          <!-- Knowledge mastery -->
          <div v-if="knowledge.length > 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
            <h3 class="font-bold text-gray-900 mb-4 flex items-center">
              <i class="fas fa-chart-bar text-blue-500 mr-2"></i>知识点掌握度
            </h3>
            <div class="space-y-4">
              <div v-for="kp in knowledge" :key="kp.knowledge_point">
                <div class="flex justify-between items-center mb-1">
                  <span class="text-sm font-medium text-gray-700">{{ kp.knowledge_point }}</span>
                  <span class="text-xs text-gray-400">{{ kp.correct }}/{{ kp.total }} ({{ kp.mastery_percent }}%)</span>
                </div>
                <div class="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-700"
                    :class="{
                      'bg-red-400': kp.mastery_percent < 40,
                      'bg-yellow-400': kp.mastery_percent >= 40 && kp.mastery_percent < 70,
                      'bg-green-500': kp.mastery_percent >= 70
                    }"
                    :style="{ width: kp.mastery_percent + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- AI suggestion placeholder -->
          <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl border border-blue-100 p-6 mb-8">
            <h3 class="font-bold text-gray-900 mb-2 flex items-center">
              <i class="fas fa-robot text-blue-500 mr-2"></i>AI 学习建议
            </h3>
            <p v-if="summary.accuracy >= 80" class="text-gray-600 text-sm">
              你的正确率非常优秀！建议挑战更高难度的练习题目，尝试完成项目挑战，进一步提升实战能力。
            </p>
            <p v-else-if="summary.accuracy >= 60" class="text-gray-600 text-sm">
              基础扎实，继续加油！重点关注错题本中的薄弱知识点，多做专项练习来巩固。
            </p>
            <p v-else-if="summary.completed_courses > 0" class="text-gray-600 text-sm">
              建议多花时间在基础练习上，特别是错题本中的知识点。每天坚持"每日一练"可以有效提升正确率。
            </p>
            <p v-else class="text-gray-600 text-sm">
              欢迎来到 PyGrow！建议先从能力测评开始，了解自己的水平，然后按照推荐课程系统地学习 Python。
            </p>
          </div>
        </template>

        <div v-else class="text-center py-20 bg-white rounded-2xl border border-gray-100">
          <p class="text-5xl mb-4">📊</p>
          <p class="text-gray-500">暂无学习数据，快去学习吧！</p>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
