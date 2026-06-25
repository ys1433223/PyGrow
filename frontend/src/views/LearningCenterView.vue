<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { homeApi } from '../api/home'
import { gamificationApi } from '../api/gamification'
import { promotionApi } from '../api/promotion'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import ExpBar from '../components/common/ExpBar.vue'

const router = useRouter()
const auth = useAuthStore()
const dashboard = ref(null)
const dailyTasks = ref([])
const showPromotionPopup = ref(false)
const promotionStatus = ref(null)
const promotionLoading = ref(false)

async function goPromotion() {
  if (!auth.isLoggedIn) {
    router.push('/login')
    return
  }
  promotionLoading.value = true
  try {
    const res = await promotionApi.status()
    if (res.data.code === 200) {
      const d = res.data.data
      if (d.can_take) {
        router.push('/promotion')
      } else {
        promotionStatus.value = d
        showPromotionPopup.value = true
      }
    }
  } catch {
    alert('无法获取晋级赛状态，请稍后重试')
  }
  promotionLoading.value = false
}

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

function goToTask(task) {
  const map = {
    watch_video: '/courses',
    do_practice: '/daily-practice',
    run_code: '/code-runner',
    daily_checkin: '/daily-practice',
    write_note: '/courses',
    community_interact: '/community',
  }
  const path = map[task.task_type] || '/practice'
  router.push(path)
}

async function claimTaskReward(taskId) {
  try {
    const res = await gamificationApi.claimReward(taskId)
    if (res.data.code === 200) {
      const d = res.data.data
      if (dashboard.value) {
        dashboard.value.experience = d.total_exp
        dashboard.value.level = d.current_rank
      }
      const task = dailyTasks.value.find(t => t.id === taskId)
      if (task) task.is_completed = true
      if (d.cookies_gained > 0) {
        // brief toast-like feedback
      }
    } else {
      alert(res.data.message || '领取失败')
    }
  } catch (e) {
    console.error('Failed to claim:', e)
    alert('网络错误，请稍后重试')
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
              {{ (dashboard.current_rank || '萌')[0] }}
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
                  {{ dashboard.major_level || '初级' }} · {{ dashboard.current_rank || '萌新小白' }}
                </span>
              </div>
            </div>
          </div>
          <ExpBar
            v-if="dashboard.current_exp !== undefined"
            :experience="dashboard.current_exp"
            :next-level-xp="dashboard.rank_exp_limit"
            :current-level="dashboard.current_rank"
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

        <!-- 晋级赛 -->
        <div @click="goPromotion"
          class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all text-center cursor-pointer">
          <div class="w-12 h-12 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
            <i class="fas fa-spinner fa-spin" v-if="promotionLoading"></i>
            <i class="fas fa-trophy" v-else></i>
          </div>
          <h3 class="font-bold text-gray-800 text-sm mb-1">晋级赛</h3>
          <p class="text-gray-400 text-xs">经验满值即可挑战升段</p>
        </div>

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
        <h3 class="font-bold text-gray-800 text-lg mb-1 flex items-center">
          <i class="fas fa-calendar-check text-blue-500 mr-2"></i>今日任务
          <span class="text-xs font-normal text-gray-400 ml-2">点击任务可前往完成</span>
        </h3>
        <p class="text-xs text-gray-400 mb-5"><span class="text-amber-600 font-medium">经验</span>提升段位 · 每完成一项获 <span class="text-orange-500 font-medium">1 饼干</span> 🍪</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="task in dailyTasks" :key="task.id"
            @click="goToTask(task)"
            :class="['flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer', task.is_completed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-100 hover:shadow-md hover:-translate-y-0.5']">
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <div :class="['w-10 h-10 rounded-full flex items-center justify-center shrink-0', task.is_completed ? 'bg-green-100' : 'bg-white border border-gray-200']">
                <span v-if="task.is_completed">✅</span>
                <span v-else>{{ task.task_type === 'watch_video' ? '📺' : task.task_type === 'do_practice' ? '📝' : task.task_type === 'run_code' ? '💻' : task.task_type === 'daily_checkin' ? '📅' : task.task_type === 'write_note' ? '📒' : task.task_type === 'community_interact' ? '💬' : '🎯' }}</span>
              </div>
              <div class="min-w-0">
                <p class="text-sm font-bold text-gray-800 truncate">{{ task.title }}</p>
                <div class="flex items-center gap-2 text-xs mt-0.5">
                  <span class="text-amber-600 font-medium">+{{ task.reward_exp }} 经验</span>
                  <span class="text-gray-300">·</span>
                  <span class="text-orange-500 font-medium">+1 🍪 饼干</span>
                </div>
              </div>
            </div>
            <button
              v-if="!task.is_completed"
              @click.stop="claimTaskReward(task.id)"
              class="ml-3 px-4 py-1.5 bg-blue-600 text-white text-xs font-bold rounded-full hover:bg-blue-700 transition whitespace-nowrap shrink-0"
            >
              领取
            </button>
            <span v-else class="ml-3 text-xs text-green-600 font-bold shrink-0">已完成</span>
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

      <!-- Promotion eligibility popup -->
      <div v-if="showPromotionPopup" class="fixed inset-0 z-[10000] flex items-center justify-center" @click.self="showPromotionPopup = false">
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl p-6 md:p-8 max-w-md w-full mx-4 animate-bounce-in z-10">
          <div class="text-center">
            <div class="w-16 h-16 bg-amber-100 text-amber-500 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
              <i class="fas fa-lock"></i>
            </div>
            <h3 class="text-xl font-bold text-gray-800 mb-2">经验值未满</h3>
            <p class="text-gray-500 mb-2">当前段位：<span class="font-bold text-gray-700">{{ promotionStatus?.current_rank || '-' }}</span></p>
            <p class="text-gray-500 mb-2">
              经验值：<span class="font-bold text-amber-600">{{ promotionStatus?.current_exp || 0 }}</span>
              /
              <span class="font-bold text-gray-700">{{ promotionStatus?.rank_exp_limit || 0 }}</span>
            </p>
            <div class="w-full bg-gray-200 rounded-full h-2.5 mb-4 overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full transition-all duration-300"
                :style="{ width: promotionStatus ? Math.min(100, (promotionStatus.current_exp / promotionStatus.rank_exp_limit) * 100) + '%' : '0%' }"
              ></div>
            </div>
            <p class="text-gray-400 text-sm mb-3">积累经验值达到上限后，即可挑战晋级赛升段！</p>
            <div class="bg-amber-50 rounded-xl p-3 mb-6 text-left">
              <p class="text-xs font-bold text-amber-700 mb-2"><i class="fas fa-star mr-1"></i>获取经验的途径</p>
              <div class="space-y-2 text-xs text-gray-600">
                <button @click="showPromotionPopup = false; router.push('/daily-practice')" class="block w-full text-left p-2 rounded-lg bg-white hover:bg-amber-100 transition border border-amber-100">
                  <i class="fas fa-dumbbell text-purple-500 mr-1.5"></i><span class="font-medium">每日一练</span> — 每天5题，巩固知识点
                </button>
                <button @click="showPromotionPopup = false; router.push('/practice')" class="block w-full text-left p-2 rounded-lg bg-white hover:bg-amber-100 transition border border-amber-100">
                  <i class="fas fa-pen-to-square text-blue-500 mr-1.5"></i><span class="font-medium">练习中心</span> — 专项练习、错题复习
                </button>
                <button @click="showPromotionPopup = false; router.push('/code-runner')" class="block w-full text-left p-2 rounded-lg bg-white hover:bg-amber-100 transition border border-amber-100">
                  <i class="fas fa-code text-pink-500 mr-1.5"></i><span class="font-medium">实战练习场</span> — 在线编写运行代码
                </button>
              </div>
            </div>
            <div class="flex gap-3">
              <button @click="showPromotionPopup = false"
                class="flex-1 px-4 py-2.5 bg-gray-100 text-gray-600 rounded-xl font-medium hover:bg-gray-200 transition">
                知道了
              </button>
              <button @click="showPromotionPopup = false; router.push('/daily-practice')"
                class="flex-1 px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-bold hover:from-amber-600 hover:to-orange-600 transition shadow-md">
                去每日一练
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
@keyframes bounce-in {
  0% { opacity: 0; transform: scale(0.8); }
  60% { opacity: 1; transform: scale(1.03); }
  100% { opacity: 1; transform: scale(1); }
}
.animate-bounce-in {
  animation: bounce-in 0.25s ease-out;
}
</style>
