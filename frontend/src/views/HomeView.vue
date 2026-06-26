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

const featureLinks = [
  { title: '6门课程', desc: '按阶段系统学习', to: '/courses', accent: '#2563eb', soft: '#eaf2ff', iconX: '0%', iconY: '0%', fallback: 'fas fa-graduation-cap' },
  { title: '每日一练', desc: '用短题巩固知识', to: '/daily-practice', accent: '#7c3aed', soft: '#f1eaff', iconX: '50%', iconY: '0%', fallback: 'fas fa-dumbbell' },
  { title: '在线编程', desc: '即写即运行', to: '/code-runner', accent: '#0ea5e9', soft: '#e7f6ff', iconX: '100%', iconY: '0%', fallback: 'fas fa-code' },
  { title: '宠物探险', desc: '收集明信片', to: '/adventure', accent: '#f59e0b', soft: '#fff5df', iconX: '0%', iconY: '100%', fallback: 'fas fa-compass' },
  { title: '项目挑战', desc: '把知识做成作品', to: '/projects', accent: '#ec4899', soft: '#fff0f7', iconX: '50%', iconY: '100%', fallback: 'fas fa-tasks' },
  { title: '学习社区', desc: '交流互助成长', to: '/community', accent: '#22c55e', soft: '#eafbf1', iconX: '100%', iconY: '100%', fallback: 'fas fa-comments' },
]

const tools = ref([
  { id: '1', name: 'PyCharm', icon: 'fas fa-leaf', desc: '专业 IDE', accent: '#3b82f6' },
  { id: '2', name: 'VS Code', icon: 'fas fa-laptop-code', desc: '轻量编辑器', accent: '#60a5fa' },
  { id: '3', name: 'Jupyter', icon: 'fas fa-chart-line', desc: '数据分析神器', accent: '#fb923c' },
  { id: '4', name: 'Anaconda', icon: 'fas fa-layer-group', desc: '环境管理', accent: '#34d399' },
  { id: '5', name: 'Pip', icon: 'fas fa-box-open', desc: '包管理工具', accent: '#fbbf24' },
  { id: '6', name: 'Docker', icon: 'fas fa-cube', desc: '容器部署', accent: '#38bdf8' }
])

function handleImageError(event) {
  event.currentTarget.classList.add('asset-hidden')
}

function authorInitial(name) {
  return (name || '学').trim().charAt(0).toUpperCase()
}

function postExcerpt(post) {
  const raw = post.summary || post.excerpt || post.content || post.body || '分享学习经验、代码思路和成长记录，一起把 Python 学扎实。'
  return String(raw).replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').slice(0, 72)
}

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
        <div class="feature-grid grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <router-link
            v-for="feature in featureLinks"
            :key="feature.to"
            :to="feature.to"
            class="feature-card group"
            :style="{ '--feature-accent': feature.accent, '--feature-soft': feature.soft, '--icon-x': feature.iconX, '--icon-y': feature.iconY }"
          >
            <div class="feature-icon-sprite" aria-hidden="true">
              <span class="feature-icon-fallback"><i :class="feature.fallback"></i></span>
            </div>
            <h4>{{ feature.title }}</h4>
            <p>{{ feature.desc }}</p>
            <span class="feature-card-arrow"><i data-lucide="arrow-right" width="14"></i></span>
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
                  :class="['flex items-center justify-between p-4 rounded-xl border transition-all', task.is_completed ? 'bg-green-50 border-green-200' : task.is_claimable ? 'bg-blue-50/50 border-blue-200 hover:shadow-md' : 'bg-gray-100 border-gray-200']">
                  <div class="flex items-center gap-3">
                    <div :class="['w-10 h-10 rounded-full flex items-center justify-center text-lg', task.is_completed ? 'bg-green-100' : task.is_claimable ? 'bg-blue-100' : 'bg-gray-200']">
                      <span v-if="task.is_completed">✅</span>
                      <span v-else>{{ task.task_type === 'watch_video' ? '📺' : task.task_type === 'do_practice' ? '📝' : task.task_type === 'run_code' ? '💻' : task.task_type === 'daily_checkin' ? '📅' : '🎯' }}</span>
                    </div>
                    <div>
                      <p class="text-sm font-bold text-gray-800">{{ task.title }}</p>
                      <p class="text-xs text-gray-400">+{{ task.reward_exp }} XP · +{{ task.reward_points }} 饼干</p>
                    </div>
                  </div>
                  <button v-if="!task.is_completed && task.is_claimable" @click="claimTaskReward(task.id)"
                    class="px-4 py-1.5 bg-blue-600 text-white text-xs font-bold rounded-full hover:bg-blue-700 transition whitespace-nowrap">
                    领取
                  </button>
                  <span v-else-if="!task.is_completed && !task.is_claimable"
                    class="px-4 py-1.5 bg-gray-300 text-gray-400 text-xs font-bold rounded-full whitespace-nowrap cursor-default">
                    未完成
                  </span>
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
      <section v-else class="container mx-auto px-4 mt-16 mb-20">
        <div class="locked-center-card group">
          <div class="locked-center-copy">
            <span class="section-kicker">成长档案</span>
            <h3>学习中心已锁定</h3>
            <p>登录后解锁课程进度、今日任务、实战练习和你的专属 Python 成长记录。</p>
            <div class="locked-benefits">
              <span><i class="fas fa-route"></i> 学习路径</span>
              <span><i class="fas fa-chart-simple"></i> 进度报告</span>
              <span><i class="fas fa-award"></i> 等级徽章</span>
            </div>
            <a href="/login" @click.prevent="$router.push('/login')" class="locked-login-button">
              立即登录 / 注册 <i data-lucide="arrow-right" width="16"></i>
            </a>
          </div>
          <div class="locked-center-visual" aria-hidden="true">
            <div class="visual-fallback"><i class="fas fa-lock"></i></div>
            <img
              src="/images/home/learning-center-locked.png"
              alt=""
              loading="lazy"
              @error="handleImageError"
            >
          </div>
        </div>
      </section>

      <!-- Discussion -->
      <section class="container mx-auto px-4 mt-20">
        <div class="community-head">
          <router-link to="/community" class="community-title-link group">
            <span class="section-kicker">学习社区</span>
            <h2>
              同学们正在讨论什么
              <i data-lucide="arrow-right" width="22" class="ml-2 opacity-0 group-hover:opacity-100 transition-opacity"></i>
            </h2>
            <p>把问题、笔记和项目心得放到桌面上，一起把 Python 学得更扎实。</p>
          </router-link>
          <div class="community-visual" aria-hidden="true">
            <div class="visual-fallback"><i class="fas fa-comments"></i></div>
            <img
              src="/images/home/community-collab.png"
              alt=""
              loading="lazy"
              @error="handleImageError"
            >
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div v-for="post in hotPosts" :key="post.id"
               @click="$router.push(`/community?post=${post.id}`)"
               class="community-post-card group">
            <div v-if="post.is_pinned" class="community-hot">HOT</div>
            <div class="community-post-top">
              <div class="community-avatar">
                <span>{{ authorInitial(post.author) }}</span>
                <img v-if="post.avatar" :src="post.avatar" :alt="post.author" @error="handleImageError">
              </div>
              <div class="min-w-0 flex-1">
                <div class="community-meta">
                  <span v-if="post.tags && post.tags.length" class="community-tag"># {{ post.tags[0] }}</span>
                  <span>@{{ post.author }}</span>
                </div>
                <h3>{{ post.title }}</h3>
                <p>{{ postExcerpt(post) }}</p>
                <div class="community-stats">
                  <span><i data-lucide="message-square" width="15"></i>{{ post.comment_count || 0 }}</span>
                  <span><i data-lucide="heart" width="15"></i>{{ post.like_count || 0 }}</span>
                  <span><i data-lucide="eye" width="15"></i>{{ post.view_count || post.views || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
          <!-- Empty state when no posts -->
          <div v-if="hotPosts.length === 0" class="empty-state-card md:col-span-2">
            <img src="/images/empty-states/learning-empty.png" alt="" loading="lazy" @error="handleImageError">
            <div class="visual-fallback"><i class="fas fa-comments"></i></div>
            <h3>暂无热门帖子</h3>
            <p>快去社区发帖，把今天的 Python 小发现分享出来。</p>
          </div>
        </div>
      </section>

      <!-- Tools -->
      <section class="container mx-auto px-4 mt-20 mb-20">
        <div class="tools-supply-panel">
          <div class="tools-texture" aria-hidden="true"></div>
          <div class="tools-head">
            <span class="section-kicker dark">工具补给</span>
            <h2><i data-lucide="zap" width="26"></i> 学习工具补给站</h2>
            <p>工欲善其事，必先利其器。把常用工具放在一个安静、好找的位置。</p>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <router-link
              v-for="tool in tools"
              :key="tool.id"
              to="/resources"
              class="tool-card group"
              :style="{ '--tool-accent': tool.accent }"
            >
              <div class="tool-icon"><i :class="tool.icon"></i></div>
              <h3>{{ tool.name }}</h3>
              <p>{{ tool.desc }}</p>
            </router-link>
          </div>
        </div>
      </section>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.section-kicker {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border-radius: 999px;
  background: #eaf2ff;
  color: #2563eb;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0;
  padding: 0.35rem 0.75rem;
}

.section-kicker.dark {
  background: rgba(96, 165, 250, 0.16);
  color: #bfdbfe;
}

.feature-card {
  position: relative;
  display: flex;
  min-height: 168px;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 1.5rem;
  background:
    radial-gradient(circle at 76% 18%, var(--feature-soft), transparent 34%),
    #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
  padding: 1rem;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.feature-card:hover {
  transform: translateY(-6px);
  border-color: color-mix(in srgb, var(--feature-accent) 30%, #dbeafe);
  box-shadow: 0 20px 48px rgba(37, 99, 235, 0.12);
}

.feature-card h4 {
  color: #1f2937;
  font-size: 0.95rem;
  font-weight: 800;
  margin-top: 0.8rem;
}

.feature-card p {
  color: #64748b;
  font-size: 0.78rem;
  margin-top: 0.25rem;
}

.feature-icon-sprite {
  position: relative;
  width: 76px;
  height: 58px;
  border-radius: 1rem;
  background: var(--feature-soft);
  overflow: hidden;
}

.feature-icon-sprite::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url('/images/icons/home-feature-icons.png');
  background-repeat: no-repeat;
  background-size: 300% 200%;
  background-position: var(--icon-x) var(--icon-y);
  z-index: 2;
}

.feature-icon-fallback {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--feature-accent);
  font-size: 1.35rem;
  z-index: 1;
}

.feature-card-arrow {
  position: absolute;
  right: 0.9rem;
  top: 0.9rem;
  display: grid;
  place-items: center;
  width: 1.8rem;
  height: 1.8rem;
  border-radius: 999px;
  color: var(--feature-accent);
  background: rgba(255, 255, 255, 0.78);
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.feature-card:hover .feature-card-arrow {
  opacity: 1;
  transform: translateX(0);
}

.locked-center-card {
  display: grid;
  grid-template-columns: minmax(0, 1.02fr) minmax(320px, 0.98fr);
  gap: 2rem;
  align-items: center;
  overflow: hidden;
  border: 1px solid rgba(191, 219, 254, 0.8);
  border-radius: 2rem;
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.98), rgba(245, 243, 255, 0.96)),
    #fff;
  box-shadow: 0 22px 55px rgba(37, 99, 235, 0.1);
  padding: clamp(1.5rem, 4vw, 3rem);
}

.locked-center-copy h3 {
  color: #111827;
  font-size: clamp(1.8rem, 3vw, 2.6rem);
  font-weight: 900;
  margin: 0.9rem 0 0.75rem;
}

.locked-center-copy p {
  color: #64748b;
  max-width: 34rem;
  line-height: 1.8;
}

.locked-benefits {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  margin: 1.5rem 0;
}

.locked-benefits span {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.74);
  color: #475569;
  font-size: 0.86rem;
  font-weight: 700;
  padding: 0.58rem 0.85rem;
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.6);
}

.locked-login-button {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-weight: 800;
  padding: 0.9rem 1.35rem;
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.28);
  transition: transform 0.25s ease, background 0.25s ease;
}

.locked-login-button:hover {
  transform: translateY(-2px);
  background: #1d4ed8;
}

.locked-center-visual,
.community-visual,
.empty-state-card {
  position: relative;
}

.locked-center-visual {
  min-height: 280px;
  border-radius: 1.5rem;
  background: linear-gradient(145deg, #dbeafe, #f5f3ff);
  overflow: hidden;
}

.locked-center-visual img,
.community-visual img,
.empty-state-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  position: relative;
  z-index: 2;
}

.asset-hidden {
  display: none !important;
}

.visual-fallback {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: grid;
  place-items: center;
  color: #2563eb;
  font-size: 3rem;
  background: linear-gradient(145deg, #eff6ff, #f5f3ff);
}

.community-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 440px);
  gap: 2rem;
  align-items: center;
  margin-bottom: 2rem;
}

.community-title-link h2 {
  display: flex;
  align-items: center;
  color: #111827;
  font-size: clamp(1.9rem, 3vw, 2.5rem);
  font-weight: 900;
  margin: 0.85rem 0 0.5rem;
  transition: color 0.25s ease;
}

.community-title-link:hover h2 {
  color: #2563eb;
}

.community-title-link p {
  color: #64748b;
}

.community-visual {
  height: 170px;
  border-radius: 1.5rem;
  overflow: hidden;
  border: 1px solid #e0e7ff;
  box-shadow: 0 16px 38px rgba(99, 102, 241, 0.11);
}

.community-post-card {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 1.5rem;
  background: #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
  padding: 1.35rem;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.community-post-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.07), transparent 42%);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.community-post-card:hover {
  transform: translateY(-5px);
  border-color: #bfdbfe;
  box-shadow: 0 20px 45px rgba(37, 99, 235, 0.12);
}

.community-post-card:hover::before {
  opacity: 1;
}

.community-hot {
  position: absolute;
  right: 0;
  top: 0;
  border-bottom-left-radius: 1rem;
  background: #fee2e2;
  color: #dc2626;
  font-size: 0.72rem;
  font-weight: 900;
  padding: 0.35rem 0.7rem;
  z-index: 3;
}

.community-post-top {
  position: relative;
  z-index: 2;
  display: flex;
  gap: 1rem;
}

.community-avatar {
  position: relative;
  flex: 0 0 auto;
  width: 3.25rem;
  height: 3.25rem;
  overflow: hidden;
  border-radius: 1.1rem;
  background: linear-gradient(135deg, #60a5fa, #a78bfa);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 900;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45);
}

.community-avatar img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.community-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #94a3b8;
  font-size: 0.76rem;
  margin-bottom: 0.35rem;
}

.community-tag {
  border-radius: 999px;
  background: #eff6ff;
  color: #2563eb;
  font-weight: 800;
  padding: 0.18rem 0.5rem;
}

.community-post-card h3 {
  color: #1f2937;
  font-size: 1.05rem;
  font-weight: 850;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.25s ease;
}

.community-post-card:hover h3 {
  color: #2563eb;
}

.community-post-card p {
  color: #64748b;
  font-size: 0.86rem;
  line-height: 1.65;
  margin: 0.55rem 0 1rem;
}

.community-stats {
  display: flex;
  gap: 1rem;
  color: #94a3b8;
  font-size: 0.82rem;
}

.community-stats span {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
}

.empty-state-card {
  min-height: 260px;
  overflow: hidden;
  border: 1px dashed #bfdbfe;
  border-radius: 1.5rem;
  background: #fff;
  text-align: center;
  padding: 2rem;
}

.empty-state-card img {
  width: min(260px, 72%);
  height: auto;
  margin: 0 auto 1rem;
}

.empty-state-card .visual-fallback {
  position: relative;
  height: 150px;
  border-radius: 1.5rem;
  margin-bottom: 1rem;
}

.empty-state-card img:not(.asset-hidden) + .visual-fallback {
  display: none;
}

.empty-state-card h3 {
  color: #1f2937;
  font-weight: 900;
  font-size: 1.15rem;
}

.empty-state-card p {
  color: #64748b;
  margin-top: 0.35rem;
}

.tools-supply-panel {
  position: relative;
  overflow: hidden;
  border-radius: 2.5rem;
  background: #0f172a;
  color: #fff;
  padding: clamp(2rem, 5vw, 3.2rem);
  box-shadow: 0 28px 65px rgba(15, 23, 42, 0.2);
}

.tools-texture {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.1), rgba(30, 41, 59, 0.34)),
    url('/images/home/tools-night-texture.png') center / cover no-repeat,
    radial-gradient(circle at 70% 20%, rgba(59, 130, 246, 0.26), transparent 36%),
    #0f172a;
  opacity: 0.9;
}

.tools-head {
  position: relative;
  z-index: 2;
  text-align: center;
  margin-bottom: 2.4rem;
}

.tools-head h2 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  font-size: clamp(1.9rem, 3vw, 2.35rem);
  font-weight: 900;
  margin: 0.85rem 0 0.55rem;
}

.tools-head h2 svg {
  color: #facc15;
  fill: currentColor;
}

.tools-head p {
  color: #cbd5e1;
}

.tool-card {
  position: relative;
  z-index: 2;
  min-height: 132px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.075);
  color: #e5e7eb;
  text-align: center;
  padding: 1.05rem 0.85rem;
  transition: transform 0.25s ease, background 0.25s ease, border-color 0.25s ease;
}

.tool-card:hover {
  transform: translateY(-5px);
  border-color: color-mix(in srgb, var(--tool-accent) 45%, rgba(255, 255, 255, 0.22));
  background: rgba(255, 255, 255, 0.12);
}

.tool-icon {
  display: grid;
  place-items: center;
  width: 3rem;
  height: 3rem;
  margin: 0 auto 0.75rem;
  border-radius: 1rem;
  background: color-mix(in srgb, var(--tool-accent) 20%, rgba(255, 255, 255, 0.08));
  color: var(--tool-accent);
  font-size: 1.18rem;
}

.tool-card h3 {
  color: #f8fafc;
  font-weight: 850;
  margin-bottom: 0.25rem;
}

.tool-card p {
  color: #94a3b8;
  font-size: 0.78rem;
}

@media (max-width: 900px) {
  .locked-center-card,
  .community-head {
    grid-template-columns: 1fr;
  }

  .locked-center-visual {
    min-height: 220px;
  }
}

@media (max-width: 640px) {
  .feature-card {
    min-height: 150px;
    padding: 0.85rem;
  }

  .feature-icon-sprite {
    width: 64px;
    height: 50px;
  }

  .community-post-top {
    gap: 0.8rem;
  }
}
</style>
