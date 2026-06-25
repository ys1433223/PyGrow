<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { homeApi } from '../api/home'
import { gamificationApi } from '../api/gamification'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import ExpBar from '../components/common/ExpBar.vue'

const router = useRouter()
const auth = useAuthStore()
const dashboard = ref(null)
const dailyTasks = ref([])

onMounted(async () => {
  if (auth.isLoggedIn) {
    try {
      const [dRes, tRes] = await Promise.all([
        homeApi.getDashboard(),
        gamificationApi.getDailyTasks(),
      ])
      if (dRes.data.code === 200) dashboard.value = dRes.data.data
      if (tRes.data.code === 200) dailyTasks.value = tRes.data.data
    } catch (e) {
      console.error('Failed to load:', e)
    }
  }
})

async function claimTaskReward(taskId) {
  try {
    const res = await gamificationApi.claimReward(taskId)
    if (res.data.code === 200) {
      const d = res.data.data
      if (dashboard.value) {
        dashboard.value.experience = d.new_experience
        dashboard.value.level = d.new_level
      }
      const task = dailyTasks.value.find(t => t.id === taskId)
      if (task) task.is_completed = true
    }
  } catch (e) {
    console.error('Failed to claim:', e)
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <!-- Header -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">学习中心</h1>
        <p class="text-gray-500">每日一练、实战编程、课程书架，一站式学习管理</p>
      </div>

      <!-- Level + XP bar (logged in) -->
      <div v-if="auth.isLoggedIn && dashboard" class="bg-white rounded-[2rem] shadow-sm border border-gray-100 p-6 md:p-8 mb-8">
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold shadow-md">
              {{ dashboard.level?.charAt(0) || '黑' }}
            </div>
            <div>
              <h3 class="text-xl font-bold text-gray-800">{{ auth.user.name }}</h3>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="text-sm px-2 py-0.5 rounded-full font-bold"
                  :class="{
                    'bg-green-100 text-green-700': dashboard.major_level === '初级',
                    'bg-blue-100 text-blue-700': dashboard.major_level === '中级',
                    'bg-orange-100 text-orange-700': dashboard.major_level === '高级',
                  }">
                  {{ dashboard.major_level || '初级' }} · {{ dashboard.level || '萌新小白' }}
                </span>
              </div>
            </div>
          </div>
          <ExpBar
            v-if="dashboard.experience !== undefined"
            :experience="dashboard.experience"
            :next-level-xp="dashboard.next_level_xp"
            :current-level="dashboard.level"
            :major-level="dashboard.major_level || '初级'"
            :progress-percent="dashboard.progress_percent"
          />
        </div>
      </div>

      <!-- Large Cards: 每日一练 + 练习中心 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <!-- 每日一练 (enlarged) -->
        <router-link to="/daily-practice"
          class="group bg-gradient-to-br from-purple-50 to-white rounded-[2rem] shadow-sm border border-purple-100 p-8 md:p-10 hover:shadow-xl hover:-translate-y-1.5 transition-all text-center overflow-hidden relative">
          <div class="absolute top-0 right-0 w-32 h-32 bg-purple-100/50 rounded-bl-full -mr-8 -mt-8 group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative z-10">
            <div class="w-20 h-20 bg-purple-100 text-purple-600 rounded-[1.5rem] flex items-center justify-center text-4xl mb-5 mx-auto group-hover:scale-110 transition-transform shadow-sm">
              <i class="fas fa-dumbbell"></i>
            </div>
            <h3 class="font-bold text-gray-800 text-xl md:text-2xl mb-2">每日一练</h3>
            <p class="text-gray-500 text-sm md:text-base">5道练习题，巩固今日所学知识点</p>
            <span class="inline-block mt-4 text-purple-600 text-sm font-medium bg-purple-100 px-4 py-1.5 rounded-full group-hover:bg-purple-200 transition">立即练习 →</span>
          </div>
        </router-link>

        <!-- 练习中心 (enlarged) -->
        <router-link to="/practice"
          class="group bg-gradient-to-br from-blue-50 to-white rounded-[2rem] shadow-sm border border-blue-100 p-8 md:p-10 hover:shadow-xl hover:-translate-y-1.5 transition-all text-center overflow-hidden relative">
          <div class="absolute top-0 right-0 w-32 h-32 bg-blue-100/50 rounded-bl-full -mr-8 -mt-8 group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative z-10">
            <div class="w-20 h-20 bg-blue-100 text-blue-600 rounded-[1.5rem] flex items-center justify-center text-4xl mb-5 mx-auto group-hover:scale-110 transition-transform shadow-sm">
              <i class="fas fa-pen-to-square"></i>
            </div>
            <h3 class="font-bold text-gray-800 text-xl md:text-2xl mb-2">练习中心</h3>
            <p class="text-gray-500 text-sm md:text-base">专项练习、错题本，全方位提升编程能力</p>
            <span class="inline-block mt-4 text-blue-600 text-sm font-medium bg-blue-100 px-4 py-1.5 rounded-full group-hover:bg-blue-200 transition">进入练习 →</span>
          </div>
        </router-link>
      </div>

      <!-- Small Cards Grid -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <!-- Code Runner -->
        <router-link to="/code-runner"
          class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
          <div class="w-12 h-12 bg-pink-100 text-pink-600 rounded-xl flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
            <i class="fas fa-code"></i>
          </div>
          <h3 class="font-bold text-gray-800 text-sm mb-1">实战练习场</h3>
          <p class="text-gray-400 text-xs">在线运行 Python 代码</p>
        </router-link>

        <!-- 晋级赛 (replaces 能力测评) -->
        <router-link to="/practice"
          class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
          <div class="w-12 h-12 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
            <i class="fas fa-trophy"></i>
          </div>
          <h3 class="font-bold text-gray-800 text-sm mb-1">晋级赛</h3>
          <p class="text-gray-400 text-xs">经验满值即可挑战升段</p>
        </router-link>

        <!-- Report -->
        <router-link to="/report"
          class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
          <div class="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
            <i class="fas fa-chart-line"></i>
          </div>
          <h3 class="font-bold text-gray-800 text-sm mb-1">学习报告</h3>
          <p class="text-gray-400 text-xs">查看成长记录</p>
        </router-link>

        <!-- Favorites -->
        <router-link to="/favorites"
          class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
          <div class="w-12 h-12 bg-red-100 text-red-500 rounded-xl flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
            <i class="fas fa-heart"></i>
          </div>
          <h3 class="font-bold text-gray-800 text-sm mb-1">我的收藏</h3>
          <p class="text-gray-400 text-xs">收藏的课程与题目</p>
        </router-link>

        <!-- AI Mentor -->
        <router-link to="/ai-mentor"
          class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
          <div class="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
            <i class="fas fa-robot"></i>
          </div>
          <h3 class="font-bold text-gray-800 text-sm mb-1">AI 导师</h3>
          <p class="text-gray-400 text-xs">智能答疑解惑</p>
        </router-link>

        <!-- Project -->
        <router-link to="/projects"
          class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
          <div class="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
            <i class="fas fa-tasks"></i>
          </div>
          <h3 class="font-bold text-gray-800 text-sm mb-1">项目挑战</h3>
          <p class="text-gray-400 text-xs">实战编程项目</p>
        </router-link>
      </div>

      <!-- Daily Tasks (logged in) -->
      <div v-if="auth.isLoggedIn && dailyTasks.length > 0" class="bg-white rounded-[2rem] shadow-sm border border-gray-100 p-6 md:p-8">
        <h3 class="font-bold text-gray-800 text-lg mb-5 flex items-center">
          <i class="fas fa-calendar-check text-blue-500 mr-2"></i>今日任务
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="task in dailyTasks" :key="task.id"
            :class="['flex items-center justify-between p-4 rounded-xl border transition-all', task.is_completed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-100 hover:shadow-md']">
            <div class="flex items-center gap-3">
              <div :class="['w-10 h-10 rounded-full flex items-center justify-center', task.is_completed ? 'bg-green-100' : 'bg-white border border-gray-200']">
                <span v-if="task.is_completed">✅</span>
                <span v-else>{{ task.task_type === 'watch_video' ? '📺' : task.task_type === 'do_practice' ? '📝' : task.task_type === 'run_code' ? '💻' : task.task_type === 'daily_checkin' ? '📅' : '🎯' }}</span>
              </div>
              <div>
                <p class="text-sm font-bold text-gray-800">{{ task.title }}</p>
                <p class="text-xs text-gray-400">+{{ task.reward_exp }} XP · +{{ task.reward_points }} 积分</p>
              </div>
            </div>
            <button v-if="!task.is_completed" @click="claimTaskReward(task.id)"
              class="px-4 py-1.5 bg-blue-600 text-white text-xs font-bold rounded-full hover:bg-blue-700 transition whitespace-nowrap">
              领取
            </button>
            <span v-else class="text-xs text-green-600 font-bold">已完成</span>
          </div>
        </div>
      </div>

      <!-- Login prompt -->
      <div v-if="!auth.isLoggedIn" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
        <p class="text-5xl mb-4">🔒</p>
        <h2 class="text-2xl font-bold text-gray-800 mb-2">请先登录</h2>
        <p class="text-gray-500 mb-6">登录后查看个性化学习内容和进度</p>
        <router-link to="/login" class="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition shadow-lg">
          立即登录
        </router-link>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
