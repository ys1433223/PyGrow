<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { setPetMode, triggerPetState } from '../hooks/usePetCompanion'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import AiHintCard from '../components/common/AiHintCard.vue'
import projects from '../data/projects'
import { submitProject } from '../api/projects'

const router = useRouter()
const auth = useAuthStore()

const activeLevel = ref('初级')
const expandedProject = ref(null)
const searchQuery = ref('')
const filterDifficulty = ref(null)

// ---- Submit / Review state ----
const activeProject = ref(null) // project being submitted
const codeInput = ref('')
const textInput = ref('')
const submitting = ref(false)
const reviewResult = ref(null) // AI review response
const submitError = ref('')
const hintsUsed = ref(0)

const levels = ['初级', '中级', '高级']
const levelColors = {
  '初级': { bg: 'bg-green-50', text: 'text-green-700', badge: 'bg-green-100 text-green-700', border: 'border-green-200', glow: 'from-green-500 to-emerald-600' },
  '中级': { bg: 'bg-blue-50', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-700', border: 'border-blue-200', glow: 'from-blue-500 to-purple-600' },
  '高级': { bg: 'bg-orange-50', text: 'text-orange-700', badge: 'bg-orange-100 text-orange-700', border: 'border-orange-200', glow: 'from-orange-500 to-red-600' },
}

const currentProjects = computed(() => {
  let list = projects[activeLevel.value] || []
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(p =>
      p.title.toLowerCase().includes(q) ||
      p.chapterName.toLowerCase().includes(q) ||
      p.knowledgePoints.some(k => k.toLowerCase().includes(q))
    )
  }
  if (filterDifficulty.value) list = list.filter(p => p.difficulty === filterDifficulty.value)
  return list
})

const groupedProjects = computed(() => {
  const groups = []; const seen = new Set()
  for (const p of currentProjects.value) {
    if (!seen.has(p.chapter)) {
      seen.add(p.chapter)
      groups.push({ chapter: p.chapter, chapterName: p.chapterName })
    }
  }
  return groups.map(g => ({ ...g, projects: currentProjects.value.filter(p => p.chapter === g.chapter) }))
})

const totalCount = computed(() => currentProjects.value.length)

function toggleProject(id) { expandedProject.value = expandedProject.value === id ? null : id }

function startChallenge(project) {
  activeProject.value = project
  codeInput.value = ''
  textInput.value = ''
  reviewResult.value = null
  submitError.value = ''
  hintsUsed.value = 0
  setPetMode('silent')
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function closeSubmit() {
  activeProject.value = null
  reviewResult.value = null
  setPetMode('active')
}

async function handleSubmit() {
  if (!codeInput.value.trim() && !textInput.value.trim()) {
    submitError.value = '请至少输入代码或项目说明'
    return
  }
  submitting.value = true
  submitError.value = ''
  setPetMode('active')
  triggerPetState('thinking')
  try {
    const res = await submitProject(activeProject.value.id, {
      code: codeInput.value,
      text: textInput.value,
      hints_used: hintsUsed.value,
    })
    if (res.data.code === 200) {
      reviewResult.value = res.data.data
      const s = res.data.data.total_score
      if (s >= 90) triggerPetState('excellent', 5000)
      else if (s >= 75) triggerPetState('happy', 4000)
      else if (s >= 60) triggerPetState('thinking', 4000)
      else triggerPetState('comfort', 4000)
    } else {
      submitError.value = res.data.message || '提交失败'
      triggerPetState('wrong', 4000)
    }
  } catch (e) {
    submitError.value = e.response?.data?.message || '网络错误，请重试'
    triggerPetState('wrong', 4000)
  } finally {
    submitting.value = false
  }
}

function onHintUsed(count) { hintsUsed.value = count }

function diffLabel(d) { return { easy: '简单', medium: '中等', hard: '困难' }[d] || d }
function diffColor(d) {
  return { easy: 'bg-green-50 text-green-600 border-green-200', medium: 'bg-amber-50 text-amber-600 border-amber-200', hard: 'bg-red-50 text-red-600 border-red-200' }[d] || ''
}
function scoreColor(s) {
  if (s >= 90) return { bg: 'bg-green-50', text: 'text-green-700', bar: 'bg-green-500', badge: 'bg-green-100 text-green-700' }
  if (s >= 75) return { bg: 'bg-blue-50', text: 'text-blue-700', bar: 'bg-blue-500', badge: 'bg-blue-100 text-blue-700' }
  if (s >= 60) return { bg: 'bg-amber-50', text: 'text-amber-700', bar: 'bg-amber-500', badge: 'bg-amber-100 text-amber-700' }
  return { bg: 'bg-red-50', text: 'text-red-700', bar: 'bg-red-500', badge: 'bg-red-100 text-red-700' }
}
function chapterIcon(n) { return n <= 12 ? String(n) : '★' }
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <PageLoader /><AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <div class="max-w-5xl mx-auto">
        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-3xl font-bold text-gray-900 mb-2">项目挑战</h1>
          <p class="text-gray-500">从基础语法到深度学习，40+ 实战项目 + AI 智能批改</p>
        </div>

        <!-- Login required -->
        <div v-if="!auth.isLoggedIn" class="text-center py-16 bg-white rounded-[2rem] shadow-sm border border-gray-100">
          <p class="text-5xl mb-4">🔒</p><h2 class="text-2xl font-bold text-gray-800 mb-2">请先登录</h2>
          <p class="text-gray-500 mb-6">登录后查看项目挑战内容</p>
          <router-link to="/login" class="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition shadow-lg">立即登录</router-link>
        </div>

        <!-- ====== PROJECT SUBMIT/REVIEW VIEW ====== -->
        <template v-if="auth.isLoggedIn && activeProject">
          <button @click="closeSubmit" class="flex items-center gap-2 text-gray-500 hover:text-blue-600 transition mb-6">
            <i class="fas fa-arrow-left"></i><span class="text-sm">返回项目列表</span>
          </button>

          <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <!-- Left: Project info + Submit form -->
            <div class="lg:col-span-3 space-y-5">
              <!-- Project info card -->
              <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div class="flex items-center gap-3 mb-4">
                  <div :class="['w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold shadow-sm', 'bg-gradient-to-br ' + levelColors[activeLevel].glow]">
                    {{ chapterIcon(activeProject.chapter) }}
                  </div>
                  <div>
                    <h2 class="text-xl font-bold text-gray-800">{{ activeProject.title }}</h2>
                    <div class="flex items-center gap-2 mt-0.5">
                      <span :class="['text-[10px] px-2 py-0.5 rounded-full font-medium border', diffColor(activeProject.difficulty)]">{{ diffLabel(activeProject.difficulty) }}</span>
                      <span class="text-xs text-gray-400">{{ activeLevel }} · 第{{ activeProject.chapter }}章</span>
                    </div>
                  </div>
                </div>
                <p class="text-sm text-gray-700 leading-relaxed mb-4">{{ activeProject.description }}</p>
                <div class="flex flex-wrap gap-1.5 mb-4">
                  <span v-for="kp in activeProject.knowledgePoints" :key="kp" class="text-[10px] px-2.5 py-1 rounded-full bg-blue-50 text-blue-600 font-medium">{{ kp }}</span>
                </div>
                <!-- Requirements / Tasks -->
                <div class="bg-gray-50 rounded-xl p-4">
                  <h4 class="text-sm font-bold text-gray-700 mb-2"><i class="fas fa-list-check text-blue-500 mr-1.5"></i>任务清单</h4>
                  <div class="space-y-1.5">
                    <div v-for="(t, i) in activeProject.tasks" :key="i" class="flex items-start gap-2 text-sm text-gray-600">
                      <span class="w-5 h-5 rounded-md bg-blue-100 text-blue-500 flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">{{ i + 1 }}</span>
                      <span>{{ t }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- AI Hint card -->
              <AiHintCard
                :question-id="activeProject.id"
                :question="activeProject.title + '\n' + activeProject.description"
                question-type="code"
                :difficulty="activeProject.difficulty"
                :knowledge-tag="activeProject.knowledgePoints.join(',')"
                :student-code="codeInput"
                @hint-used="onHintUsed"
              />

              <!-- Code submission -->
              <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <h3 class="font-bold text-gray-800 mb-3 flex items-center gap-2">
                  <i class="fas fa-code text-blue-500"></i>提交代码
                  <span v-if="hintsUsed > 0" class="text-[10px] text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">已使用 {{ hintsUsed }} 次AI提示</span>
                </h3>
                <textarea v-model="codeInput"
                  class="w-full h-48 font-mono text-sm bg-gray-900 text-green-400 rounded-xl p-4 outline-none resize-none"
                  placeholder="# 在这里编写你的 Python 代码...&#10;# 项目：{{ activeProject.title }}"></textarea>

                <h4 class="font-bold text-gray-700 text-sm mt-4 mb-2 flex items-center gap-2">
                  <i class="fas fa-align-left text-gray-400"></i>项目说明（可选）
                </h4>
                <textarea v-model="textInput"
                  class="w-full h-24 text-sm border border-gray-200 rounded-xl p-3 outline-none focus:border-blue-400 resize-none"
                  placeholder="描述你的设计思路、实现方法、遇到的问题..."></textarea>

                <p v-if="submitError" class="text-red-500 text-sm mt-3">{{ submitError }}</p>

                <button @click="handleSubmit" :disabled="submitting"
                  class="mt-4 w-full py-3 rounded-xl text-sm font-bold text-white transition-all shadow-md hover:shadow-lg"
                  :class="submitting ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:-translate-y-0.5'">
                  <i v-if="submitting" class="fas fa-spinner fa-spin mr-2"></i>
                  {{ submitting ? 'AI 批改中...' : '提交项目 · AI 智能批改' }}
                </button>
              </div>
            </div>

            <!-- Right: Review result -->
            <div class="lg:col-span-2 space-y-5">
              <!-- AI Review Result -->
              <div v-if="reviewResult" class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div :class="['px-6 py-5 text-white text-center', reviewResult.total_score >= 90 ? 'bg-gradient-to-r from-green-500 to-emerald-600' : reviewResult.total_score >= 75 ? 'bg-gradient-to-r from-blue-500 to-purple-600' : reviewResult.total_score >= 60 ? 'bg-gradient-to-r from-amber-500 to-orange-600' : 'bg-gradient-to-r from-red-500 to-pink-600']">
                  <p class="text-white/70 text-xs mb-1">AI 智能批改</p>
                  <div class="w-20 h-20 mx-auto mb-2 rounded-full bg-white/20 flex items-center justify-center">
                    <div>
                      <p class="text-3xl font-black">{{ reviewResult.total_score }}</p>
                      <p class="text-[10px] text-white/60">/ 100</p>
                    </div>
                  </div>
                  <p class="text-lg font-bold">{{ reviewResult.level }}</p>
                </div>

                <!-- Dimension scores -->
                <div class="p-5 space-y-3">
                  <h4 class="text-sm font-bold text-gray-700 mb-3">评分维度</h4>
                  <div v-for="(score, dim) in reviewResult.dimension_scores" :key="dim"
                    class="flex items-center gap-3">
                    <span class="text-xs text-gray-600 w-20 flex-shrink-0">{{ dim }}</span>
                    <div class="flex-grow h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div class="h-full rounded-full transition-all duration-700"
                        :class="score >= (dim === '功能完整性' ? 32 : dim === '代码正确性' ? 20 : dim === '代码规范性' ? 12 : dim === '知识点应用' ? 8 : 8) ? 'bg-green-500' : 'bg-amber-500'"
                        :style="{ width: (score / (dim === '功能完整性' ? 40 : dim === '代码正确性' ? 25 : dim === '代码规范性' ? 15 : 10) * 100) + '%' }"></div>
                    </div>
                    <span class="text-xs font-bold text-gray-700 w-8 text-right">{{ score }}</span>
                  </div>
                </div>

                <div class="border-t border-gray-100"></div>

                <!-- Strengths -->
                <div v-if="reviewResult.strengths?.length" class="p-5">
                  <h4 class="text-sm font-bold text-green-700 mb-2"><i class="fas fa-check-circle mr-1"></i>优点</h4>
                  <ul class="space-y-1.5">
                    <li v-for="(s, i) in reviewResult.strengths" :key="i" class="text-xs text-gray-600 flex items-start gap-2">
                      <span class="text-green-400 mt-0.5">•</span>{{ s }}
                    </li>
                  </ul>
                </div>

                <!-- Problems -->
                <div v-if="reviewResult.problems?.length" class="p-5 border-t border-gray-100">
                  <h4 class="text-sm font-bold text-red-700 mb-2"><i class="fas fa-exclamation-circle mr-1"></i>问题</h4>
                  <ul class="space-y-1.5">
                    <li v-for="(p, i) in reviewResult.problems" :key="i" class="text-xs text-gray-600 flex items-start gap-2">
                      <span class="text-red-400 mt-0.5">•</span>{{ p }}
                    </li>
                  </ul>
                </div>

                <!-- Suggestions -->
                <div v-if="reviewResult.suggestions?.length" class="p-5 border-t border-gray-100">
                  <h4 class="text-sm font-bold text-blue-700 mb-2"><i class="fas fa-lightbulb mr-1"></i>修改建议</h4>
                  <ul class="space-y-1.5">
                    <li v-for="(s, i) in reviewResult.suggestions" :key="i" class="text-xs text-gray-600 flex items-start gap-2">
                      <span class="text-blue-400 mt-0.5">•</span>{{ s }}
                    </li>
                  </ul>
                </div>

                <!-- Related knowledge -->
                <div v-if="reviewResult.related_knowledge?.length" class="p-5 border-t border-gray-100">
                  <h4 class="text-sm font-bold text-purple-700 mb-2"><i class="fas fa-book mr-1"></i>推荐复习知识点</h4>
                  <div class="flex flex-wrap gap-1.5">
                    <span v-for="k in reviewResult.related_knowledge" :key="k"
                      class="text-[10px] px-2.5 py-1 rounded-full bg-purple-50 text-purple-600 font-medium">{{ k }}</span>
                  </div>
                </div>

                <!-- XP gained -->
                <div class="p-5 border-t border-gray-100 bg-gray-50">
                  <div class="flex items-center justify-between">
                    <span class="text-xs text-gray-500">
                      <i class="fas fa-star text-amber-400 mr-1"></i>获得经验
                    </span>
                    <span class="text-lg font-black text-blue-600">+{{ reviewResult.experience_gained }} XP</span>
                  </div>
                  <div v-if="reviewResult.capped_reason" class="text-[10px] text-gray-400 mt-1">{{ reviewResult.capped_reason }}</div>
                  <div class="text-[10px] text-gray-400 mt-1">
                    基础 {{ reviewResult.base_xp }} × 评分 {{ Math.round(reviewResult.score_ratio * 100) }}% × 提示系数 {{ reviewResult.hint_coefficient.toFixed(2) }}
                  </div>
                  <p class="text-[10px] text-gray-400 mt-2" v-if="hintsUsed > 0">
                    <i class="fas fa-info-circle mr-1"></i>使用 {{ hintsUsed }} 次AI提示，经验系数 {{ reviewResult.hint_coefficient.toFixed(2) }}
                  </p>
                </div>
              </div>

              <!-- Empty state before submission -->
              <div v-else class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
                <div class="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <i class="fas fa-robot text-blue-400 text-2xl"></i>
                </div>
                <h4 class="font-bold text-gray-700 mb-2">AI 智能批改</h4>
                <p class="text-sm text-gray-400">提交代码后，AI 将根据评分量规自动批改</p>
                <div class="mt-4 text-left text-xs text-gray-500 bg-gray-50 rounded-xl p-4">
                  <p class="font-medium text-gray-600 mb-2">评分维度：</p>
                  <p>· 功能完整性 40分 | 代码正确性 25分</p>
                  <p>· 代码规范性 15分 | 知识点应用 10分</p>
                  <p>· 创新与表达 10分</p>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ====== PROJECT LIST VIEW ====== -->
        <template v-if="auth.isLoggedIn && !activeProject">
          <!-- Level tabs -->
          <div class="flex items-center justify-center mb-8">
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-1.5 flex gap-1">
              <button v-for="lvl in levels" :key="lvl"
                @click="activeLevel = lvl; expandedProject = null"
                :class="['px-6 py-2.5 rounded-xl text-sm font-bold transition-all',
                  activeLevel === lvl ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50']">
                <i :class="['fas mr-1.5', lvl === '初级' ? 'fa-seedling' : lvl === '中级' ? 'fa-fire' : 'fa-rocket']"></i>
                {{ lvl }} <span v-if="lvl === activeLevel" class="ml-1 text-white/70 text-xs">({{ totalCount }})</span>
              </button>
            </div>
          </div>

          <!-- Filters -->
          <div class="flex flex-wrap items-center gap-3 mb-6">
            <div class="relative flex-grow max-w-xs">
              <i class="fas fa-search absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-300 text-sm"></i>
              <input v-model="searchQuery" placeholder="搜索项目或知识点..."
                class="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-400 transition" />
            </div>
            <select v-model="filterDifficulty" class="px-4 py-2.5 border border-gray-200 rounded-xl text-sm bg-white">
              <option :value="null">全部难度</option><option value="easy">简单</option><option value="medium">中等</option><option value="hard">困难</option>
            </select>
            <span class="text-xs text-gray-400 ml-auto">共 {{ totalCount }} 个项目</span>
          </div>

          <!-- Empty -->
          <div v-if="currentProjects.length === 0" class="text-center py-20 bg-white rounded-[2rem] shadow-sm border border-gray-100">
            <i class="fas fa-search text-4xl text-gray-300 mb-4 block"></i>
            <p class="text-gray-500">没有找到匹配的项目</p>
            <button @click="searchQuery = ''; filterDifficulty = null" class="mt-2 text-blue-600 text-sm hover:underline">清除筛选</button>
          </div>

          <!-- Project groups -->
          <div v-else class="space-y-8">
            <div v-for="group in groupedProjects" :key="group.chapter">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white flex items-center justify-center text-xs font-bold shadow-sm">{{ chapterIcon(group.chapter) }}</div>
                <h3 class="text-lg font-bold text-gray-800">第{{ group.chapter }}章 · {{ group.chapterName }}</h3>
                <span class="text-xs text-gray-400">{{ group.projects.length }} 个项目</span>
              </div>

              <div class="grid grid-cols-1 gap-4">
                <div v-for="p in group.projects" :key="p.id"
                  :class="['bg-white rounded-2xl shadow-sm border transition-all duration-300 overflow-hidden',
                    expandedProject === p.id ? [levelColors[activeLevel].border, 'shadow-md'] : 'border-gray-100 hover:shadow-md hover:-translate-y-0.5']">
                  <button @click="toggleProject(p.id)" class="w-full text-left p-5 md:p-6 flex items-start gap-4">
                    <div :class="['w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 border', diffColor(p.difficulty)]">{{ diffLabel(p.difficulty).charAt(0) }}</div>
                    <div class="flex-grow min-w-0">
                      <div class="flex items-center gap-2 flex-wrap mb-1">
                        <h4 class="font-bold text-gray-800 text-sm md:text-base">{{ p.title }}</h4>
                        <span :class="['text-[10px] px-2 py-0.5 rounded-full font-medium border', diffColor(p.difficulty)]">{{ diffLabel(p.difficulty) }}</span>
                      </div>
                      <p class="text-sm text-gray-500 line-clamp-2 mb-2">{{ p.summary }}</p>
                      <div class="flex flex-wrap items-center gap-1.5">
                        <span v-for="kp in p.knowledgePoints.slice(0, 3)" :key="kp" class="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 font-medium">{{ kp }}</span>
                        <span v-if="p.knowledgePoints.length > 3" class="text-[10px] text-gray-400">+{{ p.knowledgePoints.length - 3 }}</span>
                        <span class="text-[10px] text-gray-400 ml-auto"><i class="far fa-clock mr-0.5"></i>{{ p.estimatedTime }}</span>
                      </div>
                    </div>
                    <i :class="['fas text-gray-300 transition flex-shrink-0 mt-1', expandedProject === p.id ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
                  </button>

                  <div v-if="expandedProject === p.id" class="px-5 md:px-6 pb-6 border-t border-gray-100 pt-5">
                    <div class="bg-gray-50 rounded-xl p-4 mb-5">
                      <p class="text-sm text-gray-700 leading-relaxed">{{ p.description }}</p>
                    </div>
                    <div class="mb-5">
                      <h5 class="text-sm font-bold text-gray-700 mb-3 flex items-center gap-1.5"><i class="fas fa-list-check text-blue-500"></i>任务清单</h5>
                      <div class="space-y-2">
                        <div v-for="(task, ti) in p.tasks" :key="ti" class="flex items-start gap-3 text-sm text-gray-600">
                          <span class="w-6 h-6 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{{ ti + 1 }}</span>
                          <span class="pt-0.5">{{ task }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="mb-5">
                      <h5 class="text-sm font-bold text-gray-700 mb-2 flex items-center gap-1.5"><i class="fas fa-tags text-blue-500"></i>涉及知识点</h5>
                      <div class="flex flex-wrap gap-1.5">
                        <span v-for="kp in p.knowledgePoints" :key="kp" class="text-xs px-2.5 py-1 rounded-full bg-blue-50 text-blue-600 font-medium">{{ kp }}</span>
                      </div>
                    </div>
                    <button @click="startChallenge(p)"
                      :class="['w-full py-3 rounded-xl text-sm font-bold text-white transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5', 'bg-gradient-to-r ' + levelColors[activeLevel].glow]">
                      <i class="fas fa-play mr-2"></i>开始挑战 · 预计{{ p.estimatedTime }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
