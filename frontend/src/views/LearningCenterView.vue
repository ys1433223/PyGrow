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
import { asset } from '../utils/assets'

const router = useRouter()
const auth = useAuthStore()
const dashboard = ref(null)
const dailyTasks = ref([])
const showPromotionPopup = ref(false)
const promotionStatus = ref(null)
const promotionLoading = ref(false)

const primaryActions = [
  {
    title: '每日一练',
    desc: '5 道练习题，保持学习手感',
    to: '/daily-practice',
    icon: 'fas fa-dumbbell',
    accent: '#7c3aed',
    soft: '#f3e8ff',
    meta: '今日任务',
  },
  {
    title: '练习中心',
    desc: '专项练习、错题本，全方位提升编程能力',
    to: '/practice',
    icon: 'fas fa-pen-to-square',
    accent: '#2563eb',
    soft: '#eaf2ff',
    meta: '系统训练',
  },
]

const quickLinks = [
  { title: '实战练习场', desc: '在线运行 Python 代码', to: '/code-runner', icon: 'fas fa-code', accent: '#ec4899', soft: '#fff0f7' },
  { title: '晋级赛', desc: '经验满值即可挑战升段', action: 'promotion', icon: 'fas fa-trophy', accent: '#f59e0b', soft: '#fff7e6' },
  { title: '学习报告', desc: '查看成长记录', to: '/report', icon: 'fas fa-chart-line', accent: '#22c55e', soft: '#eafbf1' },
  { title: '我的收藏', desc: '收藏的课程与题目', to: '/favorites', icon: 'fas fa-heart', accent: '#ef4444', soft: '#fff1f2' },
  { title: '项目挑战', desc: '实战编程项目', to: '/projects', icon: 'fas fa-tasks', accent: '#6366f1', soft: '#eef2ff' },
]

function handleImageError(event) {
  event.currentTarget.classList.add('asset-hidden')
}

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

function handleQuickLink(item) {
  if (item.action === 'promotion') {
    goPromotion()
  } else if (item.to) {
    router.push(item.to)
  }
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
      <div class="learning-hero mb-8">
        <div class="learning-hero-copy">
          <span class="section-kicker">学习工作台</span>
          <h1>学习中心</h1>
          <p>把每日一练、实战编程、项目挑战和成长记录放进同一个工作台。</p>
          <div class="hero-chips">
            <span><i class="fas fa-calendar-check"></i> 今日任务</span>
            <span><i class="fas fa-code"></i> 在线练习</span>
            <span><i class="fas fa-trophy"></i> 晋级挑战</span>
          </div>
        </div>
        <div class="learning-hero-visual" aria-hidden="true">
          <div class="visual-fallback"><i class="fas fa-graduation-cap"></i></div>
          <img :src="asset('/images/learning-center/study-command-center.png')" alt="" loading="lazy" @error="handleImageError">
        </div>
      </div>

      <!-- Level + XP bar (logged in) -->
      <div v-if="auth.isLoggedIn && dashboard" class="profile-progress-card mb-8">
        <div class="profile-id">
          <div class="rank-avatar">
              {{ (dashboard.current_rank || '萌')[0] }}
          </div>
          <div>
            <p class="profile-label">当前学习档案</p>
            <h3>{{ auth.user.name }}</h3>
            <div class="rank-line">
              <span
                :class="{
                  'is-basic': dashboard.major_level === '初级',
                  'is-middle': dashboard.major_level === '中级',
                  'is-advanced': dashboard.major_level === '高级',
                }"
              >
                {{ dashboard.major_level || '初级' }} · {{ dashboard.current_rank || '萌新小白' }}
              </span>
            </div>
          </div>
        </div>
        <div class="profile-exp">
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
        <router-link
          v-for="action in primaryActions"
          :key="action.to"
          :to="action.to"
          class="primary-action-card group"
          :style="{ '--action-accent': action.accent, '--action-soft': action.soft }"
        >
          <span class="action-meta">{{ action.meta }}</span>
          <div class="action-icon"><i :class="action.icon"></i></div>
          <h3>{{ action.title }}</h3>
          <p>{{ action.desc }}</p>
          <span class="action-button">进入 <i data-lucide="arrow-right" width="15"></i></span>
        </router-link>
      </div>

      <!-- Small Cards Grid -->
      <div class="quick-link-grid mb-10">
        <button
          v-for="item in quickLinks"
          :key="item.title"
          type="button"
          class="quick-link-card group"
          :style="{ '--quick-accent': item.accent, '--quick-soft': item.soft }"
          @click="handleQuickLink(item)"
        >
          <div class="quick-icon">
            <i class="fas fa-spinner fa-spin" v-if="item.action === 'promotion' && promotionLoading"></i>
            <i :class="item.icon" v-else></i>
          </div>
          <div class="quick-copy">
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </div>
          <i data-lucide="arrow-right" width="15" class="quick-arrow"></i>
        </button>
      </div>

      <!-- Daily Tasks (logged in) -->
      <div v-if="auth.isLoggedIn && dailyTasks.length > 0" class="daily-task-panel">
        <div class="panel-heading">
          <div>
            <span class="section-kicker">今日任务</span>
            <h3><i class="fas fa-calendar-check"></i> 今日任务</h3>
            <p><span>经验</span>提升段位 · 每完成一项获 <span>1 饼干</span></p>
          </div>
          <div class="task-counter">{{ dailyTasks.filter(t => t.is_completed).length }}/{{ dailyTasks.length }}</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="task in dailyTasks" :key="task.id"
            @click="!task.is_completed && !task.is_claimable && goToTask(task)"
            :class="['task-card', task.is_completed ? 'is-done' : '', task.is_claimable && !task.is_completed ? 'is-claimable' : '', !task.is_completed && !task.is_claimable ? 'is-pending' : '']">
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <div :class="['task-icon', task.is_completed ? 'is-done' : '', task.is_claimable && !task.is_completed ? 'is-claimable' : '']">
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
              v-if="!task.is_completed && task.is_claimable"
              @click.stop="claimTaskReward(task.id)"
              class="claim-button"
            >
              领取
            </button>
            <span v-else-if="!task.is_completed && !task.is_claimable" class="claim-button disabled">未完成</span>
            <span v-else class="task-done-label">已完成</span>
          </div>
        </div>
      </div>

      <!-- Login prompt -->
      <div v-if="!auth.isLoggedIn" class="login-prompt-card">
        <div class="login-lock"><i class="fas fa-lock"></i></div>
        <h2>请先登录</h2>
        <p class="text-gray-500 mb-6">登录后查看个性化学习内容和进度</p>
        <router-link to="/login" class="login-button">
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

.section-kicker {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  background: #eaf2ff;
  color: #2563eb;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0;
  padding: 0.35rem 0.75rem;
}

.learning-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 520px);
  gap: 2rem;
  align-items: center;
  overflow: hidden;
  border: 1px solid rgba(191, 219, 254, 0.85);
  border-radius: 2.2rem;
  background:
    radial-gradient(circle at 88% 18%, rgba(167, 139, 250, 0.18), transparent 30%),
    linear-gradient(135deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
  box-shadow: 0 22px 55px rgba(37, 99, 235, 0.1);
  padding: clamp(1.5rem, 4vw, 3rem);
}

.learning-hero-copy h1 {
  color: #111827;
  font-size: clamp(2.35rem, 5vw, 4rem);
  font-weight: 950;
  margin: 0.9rem 0 0.65rem;
}

.learning-hero-copy p {
  max-width: 35rem;
  color: #64748b;
  line-height: 1.8;
}

.hero-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  margin-top: 1.45rem;
}

.hero-chips span {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: #475569;
  font-size: 0.86rem;
  font-weight: 750;
  padding: 0.58rem 0.85rem;
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.65);
}

.learning-hero-visual {
  position: relative;
  min-height: 260px;
  overflow: hidden;
  border-radius: 1.6rem;
  background: linear-gradient(145deg, #dbeafe, #f5f3ff);
}

.learning-hero-visual img {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
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

.profile-progress-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 2rem;
  background: #fff;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
  padding: 1.4rem;
}

.profile-id {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rank-avatar {
  display: grid;
  place-items: center;
  width: 4rem;
  height: 4rem;
  border-radius: 1.35rem;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 1.35rem;
  font-weight: 900;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.25);
}

.profile-label {
  color: #94a3b8;
  font-size: 0.78rem;
  font-weight: 750;
}

.profile-id h3 {
  color: #1f2937;
  font-size: 1.35rem;
  font-weight: 900;
}

.rank-line span {
  display: inline-flex;
  margin-top: 0.35rem;
  border-radius: 999px;
  background: #eaf2ff;
  color: #2563eb;
  font-size: 0.82rem;
  font-weight: 800;
  padding: 0.25rem 0.62rem;
}

.rank-line .is-basic {
  background: #dcfce7;
  color: #15803d;
}

.rank-line .is-middle {
  background: #dbeafe;
  color: #1d4ed8;
}

.rank-line .is-advanced {
  background: #ffedd5;
  color: #c2410c;
}

.profile-exp {
  min-width: min(420px, 48%);
}

.primary-action-card {
  position: relative;
  overflow: hidden;
  min-height: 245px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 2rem;
  background:
    radial-gradient(circle at 84% 18%, var(--action-soft), transparent 36%),
    linear-gradient(145deg, #fff, #f8fbff);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
  padding: 2rem;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.primary-action-card::after {
  content: "";
  position: absolute;
  right: -2rem;
  bottom: -2.4rem;
  width: 9rem;
  height: 9rem;
  border-radius: 3rem;
  background: var(--action-soft);
  transform: rotate(18deg);
  transition: transform 0.35s ease;
}

.primary-action-card:hover {
  transform: translateY(-6px);
  border-color: color-mix(in srgb, var(--action-accent) 30%, #dbeafe);
  box-shadow: 0 24px 52px rgba(37, 99, 235, 0.12);
}

.primary-action-card:hover::after {
  transform: rotate(18deg) scale(1.16);
}

.action-meta {
  position: relative;
  z-index: 2;
  display: inline-flex;
  border-radius: 999px;
  background: var(--action-soft);
  color: var(--action-accent);
  font-size: 0.76rem;
  font-weight: 850;
  padding: 0.35rem 0.7rem;
}

.action-icon {
  position: relative;
  z-index: 2;
  display: grid;
  place-items: center;
  width: 4.3rem;
  height: 4.3rem;
  border-radius: 1.35rem;
  background: var(--action-soft);
  color: var(--action-accent);
  font-size: 1.7rem;
  margin: 1.2rem 0 1.1rem;
}

.primary-action-card h3 {
  position: relative;
  z-index: 2;
  color: #1f2937;
  font-size: 1.55rem;
  font-weight: 950;
}

.primary-action-card p {
  position: relative;
  z-index: 2;
  color: #64748b;
  line-height: 1.7;
  margin-top: 0.45rem;
}

.action-button {
  position: relative;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 1.15rem;
  border-radius: 999px;
  background: var(--action-accent);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 850;
  padding: 0.58rem 0.92rem;
}

.quick-link-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 1rem;
}

.quick-link-card {
  position: relative;
  display: flex;
  min-height: 150px;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 1.45rem;
  background: #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.055);
  padding: 1rem;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.quick-link-card:hover {
  transform: translateY(-5px);
  border-color: color-mix(in srgb, var(--quick-accent) 28%, #dbeafe);
  box-shadow: 0 20px 45px rgba(37, 99, 235, 0.11);
}

.quick-icon {
  display: grid;
  place-items: center;
  width: 3rem;
  height: 3rem;
  border-radius: 1rem;
  background: var(--quick-soft);
  color: var(--quick-accent);
  font-size: 1.15rem;
  margin-bottom: 0.85rem;
}

.quick-copy h3 {
  color: #1f2937;
  font-size: 0.95rem;
  font-weight: 900;
}

.quick-copy p {
  color: #64748b;
  font-size: 0.76rem;
  line-height: 1.5;
  margin-top: 0.2rem;
}

.quick-arrow {
  position: absolute;
  right: 0.9rem;
  top: 0.95rem;
  color: var(--quick-accent);
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.quick-link-card:hover .quick-arrow {
  opacity: 1;
  transform: translateX(0);
}

.daily-task-panel {
  border: 1px solid #e5e7eb;
  border-radius: 2rem;
  background: #fff;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
  padding: clamp(1.25rem, 3vw, 2rem);
}

.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.35rem;
}

.panel-heading h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #1f2937;
  font-size: 1.35rem;
  font-weight: 950;
  margin-top: 0.7rem;
}

.panel-heading h3 i {
  color: #2563eb;
}

.panel-heading p {
  color: #94a3b8;
  font-size: 0.82rem;
  margin-top: 0.28rem;
}

.panel-heading p span {
  color: #f59e0b;
  font-weight: 850;
}

.task-counter {
  flex: 0 0 auto;
  border-radius: 1.1rem;
  background: #eff6ff;
  color: #2563eb;
  font-weight: 950;
  padding: 0.75rem 0.95rem;
}

.task-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 1rem;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.task-card:hover {
  transform: translateY(-3px);
  border-color: #bfdbfe;
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.1);
}

.task-card.is-done {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.task-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 2.65rem;
  height: 2.65rem;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.task-icon.is-done {
  background: #dcfce7;
  border-color: #bbf7d0;
}

.claim-button {
  flex: 0 0 auto;
  margin-left: 0.75rem;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 850;
  padding: 0.42rem 0.9rem;
  transition: background 0.2s ease;
}

.claim-button:hover {
  background: #1d4ed8;
}

.claim-button.disabled {
  background: #d1d5db;
  color: #9ca3af;
  cursor: default;
}

.task-card.is-claimable {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.task-card.is-pending {
  background: #f3f4f6;
  border-color: #e5e7eb;
  cursor: pointer;
}

.task-card.is-pending:hover {
  border-color: #93c5fd;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.task-icon.is-claimable {
  background: #dbeafe;
  border-color: #93c5fd;
}

.task-done-label {
  flex: 0 0 auto;
  margin-left: 0.75rem;
  color: #16a34a;
  font-size: 0.76rem;
  font-weight: 850;
}

.login-prompt-card {
  border: 1px solid #e5e7eb;
  border-radius: 2rem;
  background:
    radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.12), transparent 40%),
    #fff;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
  text-align: center;
  padding: 4rem 1.5rem;
}

.login-lock {
  display: grid;
  place-items: center;
  width: 4.5rem;
  height: 4.5rem;
  border-radius: 1.35rem;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 1.8rem;
  margin: 0 auto 1rem;
  box-shadow: 0 18px 35px rgba(37, 99, 235, 0.24);
}

.login-prompt-card h2 {
  color: #1f2937;
  font-size: 1.55rem;
  font-weight: 950;
  margin-bottom: 0.35rem;
}

.login-button {
  display: inline-flex;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-weight: 850;
  padding: 0.85rem 1.5rem;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.22);
  transition: background 0.2s ease, transform 0.2s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  background: #1d4ed8;
}

@media (max-width: 1100px) {
  .quick-link-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .learning-hero {
    grid-template-columns: 1fr;
  }

  .profile-progress-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .profile-exp {
    min-width: 100%;
  }
}

@media (max-width: 640px) {
  .quick-link-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .learning-hero-visual {
    min-height: 210px;
  }
}
</style>
