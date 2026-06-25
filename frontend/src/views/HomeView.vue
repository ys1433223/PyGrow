<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { coursesApi } from '../api/courses'
import { homeApi } from '../api/home'
import { gamificationApi } from '../api/gamification'
import { getHotPosts } from '../api/community'
import { triggerPetState } from '../hooks/usePetCompanion'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import ExpBar from '../components/common/ExpBar.vue'

const router = useRouter()
const auth = useAuthStore()

const courses = ref([])
const dashboard = ref(null)
const dailyTasks = ref([])
const hotPosts = ref([])

// Course → CourseCenterView mapping (title, cover, level, chapter)
const COURSE_MAP = [
  {
    title: 'Python3.11零基础快速入门',
    cover: '/images/course-covers/Python3.11零基础快速入门.png',
    level: '初级', chapter: 1,
  },
  {
    title: 'Scrapy分布式爬虫',
    cover: '/images/course-covers/Scrapy分布式爬虫.png',
    level: '中级', chapter: 5,
  },
  {
    title: 'Python操作Excel与邮件自动化',
    cover: '/images/course-covers/ython操作Excel与邮件自动化.png',
    level: '高级', chapter: 2,
  },
  {
    title: 'Pandas &Matplotlib数据可视化',
    cover: '/images/course-covers/Pandas &Matplotlib数据可视化.png',
    level: '高级', chapter: 4,
  },
  {
    title: 'Django/Flask企业级开发实战',
    cover: '/images/course-covers/DjangoFlask开发.png',
    level: '中级', chapter: 3,
  },
  {
    title: 'PyTorch深度学习与神经网络',
    cover: '/images/course-covers/PyTorch深度学习与神经网络.png',
    level: '高级', chapter: 7,
  },
]

function getCourseInfo(courseTitle) {
  if (!courseTitle) return COURSE_MAP[0]
  return COURSE_MAP.find(m =>
    courseTitle === m.title || courseTitle.includes(m.title) || m.title.includes(courseTitle)
  ) || COURSE_MAP[0]
}

function getCourseCover(courseTitle) {
  return getCourseInfo(courseTitle).cover
}

function getCourseLevel(courseTitle) {
  return getCourseInfo(courseTitle).level
}

const tools = ref([
  { id: '1', name: 'PyCharm', icon: '🐍', desc: '专业IDE', color: 'bg-blue-50 border-blue-200' },
  { id: '2', name: 'VS Code', icon: '💻', desc: '轻量编辑器', color: 'bg-blue-50 border-blue-200' },
  { id: '3', name: 'Jupyter', icon: '📓', desc: '数据分析神器', color: 'bg-orange-50 border-orange-200' },
  { id: '4', name: 'Anaconda', icon: '🟢', desc: '环境管理', color: 'bg-green-50 border-green-200' },
  { id: '5', name: 'Pip', icon: '📦', desc: '包管理工具', color: 'bg-yellow-50 border-yellow-200' },
  { id: '6', name: 'Docker', icon: '🐳', desc: '容器部署', color: 'bg-blue-50 border-blue-200' }
])

onMounted(async () => {
  try {
    const res = await coursesApi.list()
    if (res.data.code === 200) {
      courses.value = res.data.data
    }
  } catch (e) {
    console.error('Failed to load courses:', e)
  }

  if (auth.isLoggedIn) {
    try {
      const [dRes, tRes] = await Promise.all([
        homeApi.getDashboard(),
        gamificationApi.getDailyTasks(),
      ])
      if (dRes.data.code === 200) dashboard.value = dRes.data.data
      if (tRes.data.code === 200) dailyTasks.value = tRes.data.data
    } catch (e) {
      console.error('Failed to load dashboard:', e)
    }
  }

  // Fetch hot posts for community section (public)
  try {
    const hRes = await getHotPosts(6)
    if (hRes.data.code === 200) {
      hotPosts.value = hRes.data.data || []
    }
  } catch (e) {
    console.error('Failed to load hot posts:', e)
  }

  if (typeof lucide !== 'undefined') lucide.createIcons()
})

async function claimTaskReward(taskId) {
  try {
    const res = await gamificationApi.claimReward(taskId)
    if (res.data.code === 200) {
      const d = res.data.data
      if (dashboard.value) {
        dashboard.value.current_exp = d.new_experience || dashboard.value.current_exp
        dashboard.value.current_rank = d.new_level || dashboard.value.current_rank
      }
      const task = dailyTasks.value.find(t => t.id === taskId)
      if (task) task.is_completed = true
      triggerPetState('happy', 3000)
      // Check if all tasks done
      if (dailyTasks.value.every(t => t.is_completed)) {
        setTimeout(() => triggerPetState('rest', 5000), 3000)
      }
    }
  } catch (e) {
    console.error('Failed to claim reward:', e)
  }
}

function checkLogin(targetPath) {
  if (auth.isLoggedIn) {
    router.push(targetPath)
  } else {
    if (window.__openLoginPrompt) window.__openLoginPrompt()
  }
}

function goToCourse(course) {
  const info = getCourseInfo(course.title)
  router.push(`/courses?level=${encodeURIComponent(info.level)}&chapter=${info.chapter}`)
}

</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow">
      <!-- Hero Section -->
      <section class="container mx-auto px-4 mt-8 mb-12">
        <div class="bg-white rounded-[2rem] shadow-sm p-8 md:p-16 flex flex-col md:flex-row items-center justify-between relative overflow-hidden border border-gray-100">
          <div class="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-blue-50 rounded-full opacity-50 blur-3xl pointer-events-none"></div>
          <div class="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 bg-purple-50 rounded-full opacity-50 blur-3xl pointer-events-none"></div>

          <div class="md:w-1/2 z-10 relative">
            <div class="inline-block bg-blue-100 text-blue-700 text-xs font-bold px-3 py-1 rounded-full mb-6">🐍 Python 全栈体系升级</div>
            <h1 class="text-4xl md:text-6xl font-extrabold text-gray-900 leading-tight mb-6">
              人生苦短，<br />
              <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">我用 Python。</span>
            </h1>
            <p class="text-gray-500 text-lg mb-8 max-w-lg">从语法基础到人工智能，启航教育带你掌握这门"万能语言"，解锁数据时代的无限可能。</p>
            <div class="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
              <a href="/courses" @click.prevent="$router.push('/courses')" class="flex items-center justify-center bg-blue-600 text-white px-8 py-3.5 rounded-xl font-bold hover:bg-blue-700 transition shadow-lg hover:-translate-y-1">
                开始学习 <i data-lucide="arrow-right" width="18" class="ml-2"></i>
              </a>
              <a href="/daily-practice" @click.prevent="$router.push('/daily-practice')" class="flex items-center justify-center bg-purple-600 text-white px-8 py-3.5 rounded-xl font-bold hover:bg-purple-700 transition shadow-lg hover:-translate-y-1">
                每日一练 <i data-lucide="dumbbell" width="18" class="ml-2"></i>
              </a>
            </div>
          </div>

          <div class="md:w-1/2 mt-12 md:mt-0 relative flex justify-center md:justify-end">
            <div class="relative w-full max-w-lg">
              <img src="/de-image/home-hero.png" alt="Python学习" class="w-full h-auto object-contain z-10 relative drop-shadow-2xl">
              <div class="absolute -left-4 top-8 bg-white p-4 rounded-xl shadow-lg z-20 animate-float border border-gray-50">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center text-green-600">
                    <i data-lucide="code-2" width="20"></i>
                  </div>
                  <div>
                    <div class="text-xs text-gray-400">正在学习</div>
                    <div class="font-bold text-gray-800">Python 编程</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Feature Overview -->
      <section class="container mx-auto px-4 mb-12">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <router-link to="/courses" class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center hover:shadow-md hover:-translate-y-1 transition-all">
            <div class="w-11 h-11 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center text-lg mx-auto mb-3 group-hover:scale-110 transition-transform">
              <i class="fas fa-play"></i>
            </div>
            <h4 class="font-bold text-sm text-gray-800 mb-1">6门课程</h4>
            <p class="text-gray-400 text-xs">系统学习</p>
          </router-link>
          <router-link to="/daily-practice" class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center hover:shadow-md hover:-translate-y-1 transition-all">
            <div class="w-11 h-11 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center text-lg mx-auto mb-3 group-hover:scale-110 transition-transform">
              <i class="fas fa-dumbbell"></i>
            </div>
            <h4 class="font-bold text-sm text-gray-800 mb-1">每日一练</h4>
            <p class="text-gray-400 text-xs">巩固知识</p>
          </router-link>
          <router-link to="/code-runner" class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center hover:shadow-md hover:-translate-y-1 transition-all">
            <div class="w-11 h-11 bg-pink-100 text-pink-600 rounded-xl flex items-center justify-center text-lg mx-auto mb-3 group-hover:scale-110 transition-transform">
              <i class="fas fa-code"></i>
            </div>
            <h4 class="font-bold text-sm text-gray-800 mb-1">在线编程</h4>
            <p class="text-gray-400 text-xs">即写即运行</p>
          </router-link>
          <router-link to="/adventure" class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center hover:shadow-md hover:-translate-y-1 transition-all">
            <div class="w-11 h-11 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center text-lg mx-auto mb-3 group-hover:scale-110 transition-transform">
              <i class="fas fa-compass"></i>
            </div>
            <h4 class="font-bold text-sm text-gray-800 mb-1">宠物探险</h4>
            <p class="text-gray-400 text-xs">收集明信片</p>
          </router-link>
          <router-link to="/projects" class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center hover:shadow-md hover:-translate-y-1 transition-all">
            <div class="w-11 h-11 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center text-lg mx-auto mb-3 group-hover:scale-110 transition-transform">
              <i class="fas fa-tasks"></i>
            </div>
            <h4 class="font-bold text-sm text-gray-800 mb-1">项目挑战</h4>
            <p class="text-gray-400 text-xs">学以致用</p>
          </router-link>
          <router-link to="/community" class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 text-center hover:shadow-md hover:-translate-y-1 transition-all">
            <div class="w-11 h-11 bg-green-100 text-green-600 rounded-xl flex items-center justify-center text-lg mx-auto mb-3 group-hover:scale-110 transition-transform">
              <i class="fas fa-comments"></i>
            </div>
            <h4 class="font-bold text-sm text-gray-800 mb-1">学习社区</h4>
            <p class="text-gray-400 text-xs">交流互助</p>
          </router-link>
        </div>
      </section>

      <!-- Course Cover Cards -->
      <section v-if="courses.length > 0" class="container mx-auto px-4 mt-16">
        <div class="flex justify-between items-end mb-10">
          <div>
            <h2 class="text-3xl font-bold text-gray-900">课程体系</h2>
            <p class="text-gray-500 mt-2">从零基础到人工智能，系统掌握 Python 全栈技能</p>
          </div>
          <a href="/courses" @click.prevent="$router.push('/courses')" class="text-blue-600 font-semibold hover:underline hidden sm:block">查看全部 &rarr;</a>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div v-for="course in courses.slice(0, 7)" :key="course.id"
               @click="goToCourse(course)"
               class="group relative bg-white rounded-2xl shadow-sm hover:shadow-xl hover:-translate-y-2 transition-all duration-300 overflow-hidden border border-gray-100 cursor-pointer flex flex-col">
            <!-- Cover image area -->
            <div class="relative h-44 overflow-hidden bg-gray-100">
              <img :src="getCourseCover(course.title)" :alt="course.title"
                   class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                   loading="lazy">
              <!-- Gradient overlay -->
              <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-black/15 to-transparent"></div>
              <!-- Level badge -->
              <span :class="[
                'absolute top-3 left-3 text-xs font-bold px-2.5 py-1 rounded-full backdrop-blur-sm',
                getCourseLevel(course.title) === '初级' ? 'bg-green-500/80 text-white' :
                getCourseLevel(course.title) === '中级' ? 'bg-blue-500/80 text-white' :
                'bg-orange-500/80 text-white'
              ]">{{ getCourseLevel(course.title) }}</span>
              <!-- Title overlay -->
              <div class="absolute bottom-3 left-4 right-4">
                <h3 class="text-white font-bold text-lg leading-tight drop-shadow-sm">{{ course.title }}</h3>
              </div>
            </div>
            <!-- Card footer -->
            <div class="p-4 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <span class="text-xs text-gray-400"><i class="fas fa-layer-group mr-1"></i>{{ course.chapters_count || 0 }} 章节</span>
                <span v-if="course.students_count" class="text-xs text-gray-400"><i class="fas fa-users mr-1"></i>{{ course.students_count }} 人学习</span>
              </div>
              <span class="text-blue-600 text-xs font-bold flex items-center group-hover:translate-x-1.5 transition-transform duration-300">
                进入课程 <i data-lucide="arrow-right" width="12" class="ml-1"></i>
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Learning Center (Logged In) -->
      <section v-if="auth.isLoggedIn" class="container mx-auto px-4 mt-16 mb-20">
        <div class="flex items-center space-x-3 mb-8">
          <div class="w-2 h-8 bg-blue-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">我的学习中心</h2>
        </div>

        <!-- Dashboard loaded -->
        <template v-if="dashboard">
          <div class="bg-white rounded-[2rem] shadow-lg border border-gray-100 p-8 md:p-12">
            <!-- Welcome + Level -->
            <div class="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
              <div>
                <h3 class="text-2xl font-bold text-gray-800">欢迎回来，{{ auth.user?.name || '同学' }} 👋</h3>
                <p v-if="dashboard.streak_days > 0" class="text-sm text-orange-500 mt-1">
                  <i class="fas fa-fire mr-1"></i>已连续学习 {{ dashboard.streak_days }} 天 · 🍪 {{ dashboard.cookies || 0 }} 饼干
                </p>
              </div>
              <div class="flex items-center gap-3 bg-gray-50 rounded-2xl px-5 py-3">
                <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-lg font-bold shadow-md">
                  {{ (dashboard.current_rank || '萌新小白').charAt(0) }}
                </div>
                <div class="min-w-[160px]">
                  <ExpBar
                    :experience="dashboard.current_exp || 0"
                    :next-level-xp="dashboard.rank_exp_limit || 100"
                    :current-level="dashboard.current_rank || '萌新小白'"
                    :major-level="dashboard.major_level || '初级'"
                    :progress-percent="dashboard.progress_percent || 0"
                  />
                </div>
              </div>
            </div>

            <!-- Daily tasks -->
            <div class="mb-10">
              <h4 class="font-bold text-gray-800 mb-4 flex items-center">
                <i class="fas fa-tasks text-blue-500 mr-2"></i>今日任务
              </h4>
              <div v-if="dailyTasks.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div v-for="task in dailyTasks" :key="task.id"
                  :class="['flex items-center justify-between p-4 rounded-xl border transition-all', task.is_completed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-100 hover:shadow-md']">
                  <div class="flex items-center gap-3">
                    <div :class="['w-10 h-10 rounded-full flex items-center justify-center text-lg', task.is_completed ? 'bg-green-100' : 'bg-white border border-gray-200']">
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
              <div v-else class="text-center py-8 text-gray-400">
                <i class="fas fa-tasks text-3xl mb-2 opacity-30"></i>
                <p class="text-sm">今日暂无任务，先去看看课程吧</p>
              </div>
            </div>

            <!-- Quick links -->
            <div>
              <h4 class="font-bold text-gray-800 mb-4 flex items-center">
                <i class="fas fa-th-large text-purple-500 mr-2"></i>快捷入口
              </h4>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <router-link v-if="dashboard.continue_learning" :to="'/courses'"
                  class="group cursor-pointer bg-blue-50 rounded-2xl p-5 border border-blue-100 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
                  <div class="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
                    <i class="fas fa-play"></i>
                  </div>
                  <h4 class="font-bold text-gray-800 text-sm mb-1">继续学习</h4>
                  <p class="text-gray-400 text-xs truncate">{{ dashboard.continue_learning.title }}</p>
                </router-link>

                <router-link to="/assessment"
                  class="group cursor-pointer bg-orange-50 rounded-2xl p-5 border border-orange-100 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
                  <div class="w-12 h-12 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
                    <i class="fas fa-clipboard-check"></i>
                  </div>
                  <h4 class="font-bold text-gray-800 text-sm mb-1">能力测评</h4>
                  <p class="text-gray-400 text-xs">测试 Python 水平</p>
                </router-link>

                <router-link to="/daily-practice"
                  class="group cursor-pointer bg-purple-50 rounded-2xl p-5 border border-purple-100 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
                  <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
                    <i class="fas fa-dumbbell"></i>
                  </div>
                  <h4 class="font-bold text-gray-800 text-sm mb-1">每日一练</h4>
                  <p class="text-gray-400 text-xs">巩固知识点</p>
                </router-link>

                <router-link to="/report"
                  class="group cursor-pointer bg-green-50 rounded-2xl p-5 border border-green-100 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
                  <div class="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
                    <i class="fas fa-chart-line"></i>
                  </div>
                  <h4 class="font-bold text-gray-800 text-sm mb-1">学习报告</h4>
                  <p class="text-gray-400 text-xs">查看成长记录</p>
                </router-link>

                <router-link to="/courses"
                  class="group cursor-pointer bg-teal-50 rounded-2xl p-5 border border-teal-100 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
                  <div class="w-12 h-12 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
                    <i class="fas fa-book-open"></i>
                  </div>
                  <h4 class="font-bold text-gray-800 text-sm mb-1">课程书架</h4>
                  <p class="text-gray-400 text-xs">全部视频课程</p>
                </router-link>

                <router-link to="/code-runner"
                  class="group cursor-pointer bg-pink-50 rounded-2xl p-5 border border-pink-100 hover:shadow-lg hover:-translate-y-1 transition-all text-center">
                  <div class="w-12 h-12 bg-pink-100 text-pink-600 rounded-full flex items-center justify-center text-xl mb-3 mx-auto group-hover:scale-110 transition-transform">
                    <i class="fas fa-code"></i>
                  </div>
                  <h4 class="font-bold text-gray-800 text-sm mb-1">实战练习场</h4>
                  <p class="text-gray-400 text-xs">在线运行代码</p>
                </router-link>
              </div>
            </div>
          </div>
        </template>

        <!-- Dashboard loading -->
        <div v-else class="bg-white rounded-[2rem] shadow-sm border border-gray-100 p-12 text-center">
          <div class="animate-pulse">
            <div class="h-8 bg-gray-200 rounded w-1/3 mx-auto mb-4"></div>
            <div class="h-4 bg-gray-200 rounded w-1/2 mx-auto mb-2"></div>
            <div class="h-4 bg-gray-200 rounded w-1/4 mx-auto"></div>
          </div>
        </div>
      </section>

      <!-- Locked state (not logged in) -->
      <section v-else class="container mx-auto px-4 mt-16 mb-20 text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100 relative overflow-hidden group">
        <div class="absolute inset-0 bg-blue-600 opacity-0 group-hover:opacity-5 transition-opacity pointer-events-none"></div>
        <div class="text-6xl mb-4">🔒</div>
        <h3 class="text-2xl font-bold text-gray-800 mb-2">学习中心已锁定</h3>
        <p class="text-gray-500 mb-6">登录后解锁我的课程、实战练习与专属书架</p>
        <a href="/login" @click.prevent="$router.push('/login')" class="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-bold shadow-lg hover:scale-105 transition-transform">
          立即登录 / 注册
        </a>
      </section>

      <!-- Discussion -->
      <section class="container mx-auto px-4 mt-20">
        <div class="flex items-center justify-between mb-8">
          <router-link to="/community" class="cursor-pointer group">
            <h2 class="text-3xl font-bold text-gray-900 flex items-center group-hover:text-blue-600 transition-colors">
              <span class="mr-2">💬</span> 学习社区
              <i data-lucide="arrow-right" class="ml-2 opacity-0 group-hover:opacity-100 transition-opacity"></i>
            </h2>
            <p class="text-gray-500 mt-2">不仅是学习，更是交流与成长的社区</p>
          </router-link>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div v-for="post in hotPosts" :key="post.id"
               @click="$router.push(`/community?post=${post.id}`)"
               class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md hover:-translate-y-1 transition-all relative overflow-hidden group cursor-pointer">
            <div v-if="post.is_pinned" class="absolute top-0 right-0 bg-red-100 text-red-600 text-xs px-3 py-1 rounded-bl-xl font-bold flex items-center">HOT</div>
            <div class="flex items-start space-x-4">
              <img :src="post.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + post.author" class="w-12 h-12 rounded-full bg-gray-100 border border-white shadow-sm">
              <div class="flex-1">
                <div class="flex items-center space-x-2 mb-1">
                  <span v-if="post.tags && post.tags.length" class="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded flex items-center"># {{ post.tags[0] }}</span>
                  <span class="text-gray-400 text-xs">@{{ post.author }}</span>
                </div>
                <h3 class="font-bold text-gray-800 text-lg mb-3 line-clamp-1 group-hover:text-blue-600 transition-colors">{{ post.title }}</h3>
                <div class="flex items-center space-x-6 text-gray-400 text-sm">
                  <span class="flex items-center"><i data-lucide="message-square" width="16" class="mr-1"></i> {{ post.comment_count }}</span>
                  <span class="flex items-center"><i data-lucide="heart" width="16" class="mr-1"></i> {{ post.like_count }}</span>
                </div>
              </div>
            </div>
          </div>
          <!-- Empty state when no posts -->
          <div v-if="hotPosts.length === 0" class="md:col-span-2 text-center py-12 bg-white rounded-2xl border border-gray-100">
            <div class="text-4xl mb-3">💬</div>
            <p class="text-gray-400">暂无热门帖子，快去社区发帖吧！</p>
          </div>
        </div>
      </section>

      <!-- Tools -->
      <section class="container mx-auto px-4 mt-20 mb-20">
        <div class="bg-gray-900 rounded-[2.5rem] p-8 md:p-12 relative overflow-hidden text-white">
          <div class="absolute top-0 right-0 w-64 h-64 bg-blue-600 rounded-full blur-[100px] opacity-30 pointer-events-none"></div>
          <div class="absolute bottom-0 left-0 w-64 h-64 bg-purple-600 rounded-full blur-[100px] opacity-30 pointer-events-none"></div>

          <div class="relative z-10 text-center mb-10">
            <h2 class="text-3xl font-bold mb-4 flex items-center justify-center">
              <i data-lucide="zap" class="mr-2 text-yellow-400 fill-current"></i> 学习工具补给站
            </h2>
            <p class="text-gray-400">工欲善其事，必先利其器。</p>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <router-link v-for="tool in tools" :key="tool.id" to="/resources" :class="['block p-4 rounded-2xl border bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-all hover:-translate-y-1 hover:shadow-lg group text-center', tool.color]">
              <div class="text-4xl mb-3 transform group-hover:scale-110 transition-transform">{{ tool.icon }}</div>
              <h3 class="font-bold text-gray-200 mb-1">{{ tool.name }}</h3>
              <p class="text-xs text-gray-500 line-clamp-1">{{ tool.desc }}</p>
            </router-link>
          </div>
        </div>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
