<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'
import { calcMajorLevel } from '../../utils/levels'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  // Re-bind theme toggle on every mount since AppHeader is recreated per route
  const savedTheme = localStorage.getItem('siteTheme')
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-mode')
    const btn = document.querySelector('theme-button')
    if (btn) setTimeout(() => btn.setAttribute('value', 'dark'), 100)
  }

  const toggleBtn = document.querySelector('theme-button')
  if (toggleBtn) {
    toggleBtn.addEventListener('change', (e) => {
      if (e.detail === 'dark') {
        document.body.classList.add('dark-mode')
        localStorage.setItem('siteTheme', 'dark')
      } else {
        document.body.classList.remove('dark-mode')
        localStorage.setItem('siteTheme', 'light')
      }
    })
  }
})

const displayRank = computed(() => auth.user?.current_rank || auth.user?.level || '')

const majorLevel = computed(() => {
  if (!displayRank.value) return null
  return calcMajorLevel(displayRank.value)
})

const levelBadgeClass = computed(() => {
  if (!majorLevel.value) return ''
  return {
    '初级': 'bg-green-100 text-green-700 border-green-300',
    '中级': 'bg-blue-100 text-blue-700 border-blue-300',
    '高级': 'bg-orange-100 text-orange-700 border-orange-300',
  }[majorLevel.value] || 'bg-gray-100 text-gray-700 border-gray-300'
})

function handleLogout() {
  if (confirm('确定退出登录？')) {
    auth.logout()
    window.location.reload()
  }
}

function goTo(path) {
  router.push(path)
}
</script>

<template>
  <header class="bg-white/90 backdrop-blur-md shadow-sm sticky top-0 z-50 transition-all duration-300">
    <div class="container mx-auto px-4 h-16 flex items-center justify-between">
      <!-- Logo -->
      <a href="/" class="flex items-center space-x-2 group" @click.prevent="goTo('/')">
        <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white group-hover:rotate-12 transition-transform duration-300">
          <i class="fas fa-compass text-sm"></i>
        </div>
        <span class="text-xl font-bold text-gray-800 tracking-wide group-hover:text-blue-600 transition-colors">Python学习营地</span>
      </a>

      <nav class="hidden md:flex space-x-8 text-gray-600 font-medium text-sm">
        <a href="/" class="hover:text-blue-600 hover:-translate-y-0.5 transition-all" :class="{ 'text-blue-600 font-bold border-b-2 border-blue-600 pb-1': $route.path === '/' }" @click.prevent="goTo('/')">首页</a>
        <a href="/courses" class="hover:text-blue-600 hover:-translate-y-0.5 transition-all" :class="{ 'text-blue-600 font-bold border-b-2 border-blue-600 pb-1': $route.path === '/courses' }" @click.prevent="goTo('/courses')">课程中心</a>
        <a href="/code-runner" class="hover:text-blue-600 hover:-translate-y-0.5 transition-all" :class="{ 'text-blue-600 font-bold border-b-2 border-blue-600 pb-1': $route.path === '/code-runner' }" @click.prevent="goTo('/code-runner')">在线编程</a>
        <a href="/community" class="hover:text-blue-600 hover:-translate-y-0.5 transition-all" :class="{ 'text-blue-600 font-bold border-b-2 border-blue-600 pb-1': $route.path === '/community' }" @click.prevent="goTo('/community')">社区</a>
        <a href="/learning-center" class="hover:text-blue-600 hover:-translate-y-0.5 transition-all" :class="{ 'text-blue-600 font-bold border-b-2 border-blue-600 pb-1': $route.path === '/learning-center' }" @click.prevent="goTo('/learning-center')">学习中心</a>
        <a href="/resources" class="hover:text-blue-600 hover:-translate-y-0.5 transition-all" :class="{ 'text-blue-600 font-bold border-b-2 border-blue-600 pb-1': $route.path === '/resources' }" @click.prevent="goTo('/resources')">资源中心</a>
      </nav>

      <div class="flex items-center space-x-6">
        <div class="relative w-16 h-8 flex items-center justify-center">
          <theme-button id="theme-toggle" size="0.6" style="cursor: pointer;"></theme-button>
        </div>

        <!-- Logged in -->
        <div v-if="auth.isLoggedIn && auth.user" class="relative group flex items-center space-x-3 cursor-pointer">
          <!-- Rank badge -->
          <span v-if="displayRank" :class="['hidden sm:inline-block text-xs font-bold px-2 py-0.5 rounded-full border', levelBadgeClass]">
            {{ displayRank }}
          </span>
          <div class="text-right hidden sm:block">
            <p class="text-xs text-gray-500">欢迎回来,</p>
            <p class="text-sm font-bold text-gray-800 leading-none">{{ auth.user.name }}</p>
          </div>
          <div class="relative">
            <img :src="auth.user.avatar" class="w-9 h-9 rounded-full border-2 border-blue-100 shadow-sm">
            <span v-if="displayRank" :class="['absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border border-white text-[8px] font-bold flex items-center justify-center', levelBadgeClass.replace('border-', '')]">
              {{ displayRank.charAt(0) }}
            </span>
          </div>

          <div class="absolute right-0 top-full pt-2 w-48 hidden group-hover:block z-50">
            <div class="bg-white rounded-xl shadow-xl border border-gray-100 p-2 overflow-hidden">
              <a href="/assessment" class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 rounded-lg mb-1" @click.prevent="goTo('/assessment')">
                <i class="fas fa-clipboard-check mr-2 text-xs text-orange-500"></i> 能力测评
              </a>
              <a href="/profile" class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 rounded-lg mb-1" @click.prevent="goTo('/profile')">
                <i class="fas fa-user mr-2 text-xs"></i> 个人中心
              </a>
              <a href="/report" class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 rounded-lg mb-1" @click.prevent="goTo('/report')">
                <i class="fas fa-chart-bar mr-2 text-xs"></i> 学习报告
              </a>
              <button @click="handleLogout" class="w-full flex items-center px-4 py-2 text-sm text-red-500 hover:bg-red-50 rounded-lg">
                <i class="fas fa-sign-out-alt mr-2 text-xs"></i> 退出登录
              </button>
            </div>
          </div>
        </div>

        <!-- Not logged in -->
        <a v-else href="/login" class="bg-blue-600 text-white px-6 py-2 rounded-full text-sm font-medium hover:bg-blue-700 hover:shadow-lg transition-all flex items-center" @click.prevent="goTo('/login')">
          登录 / 注册
        </a>
      </div>
    </div>
  </header>
</template>
