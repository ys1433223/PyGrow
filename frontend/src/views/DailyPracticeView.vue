<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { practiceApi } from '../api/practice'
import { calcMajorLevel } from '../utils/levels'
import { setPetMode, triggerPetState } from '../hooks/usePetCompanion'
import AppHeader from '../components/layout/AppHeader.vue'
import AiHintCard from '../components/common/AiHintCard.vue'

const auth = useAuthStore()
const router = useRouter()

// ---- State ----
const DURATION_MINUTES = 30
const TOTAL_SECONDS = DURATION_MINUTES * 60

const questions = ref([])
const currentIndex = ref(0)
const userAnswers = ref({})
const submitted = ref(false)
const submitting = ref(false)
const results = ref(null)
const loading = ref(true)
const error = ref('')
const timerSeconds = ref(TOTAL_SECONDS)
const timerExpired = ref(false)
const hintCounts = ref({}) // { questionId: number of hints used }
let timerInterval = null

const majorLevel = computed(() => {
  if (!auth.user?.level) return '初级'
  return calcMajorLevel(auth.user.level)
})

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
const totalQuestions = computed(() => questions.value.length)
const progressPct = computed(() => totalQuestions.value > 0 ? Math.round((currentIndex.value + 1) / totalQuestions.value * 100) : 0)
const answeredCount = computed(() => Object.keys(userAnswers.value).length)

const timerDisplay = computed(() => {
  const m = Math.floor(timerSeconds.value / 60)
  const s = timerSeconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const timerPct = computed(() => (timerSeconds.value / TOTAL_SECONDS) * 100)
const timerUrgent = computed(() => timerSeconds.value < 300)

// ---- Answer helpers ----
function selectAnswer(questionId, answer) {
  userAnswers.value = { ...userAnswers.value, [questionId]: answer }
}

function isSelected(questionId, answer) {
  return userAnswers.value[questionId] === answer
}

function isMultiSelected(questionId, label) {
  const ans = userAnswers.value[questionId] || ''
  return ans.split(',').map(s => s.trim().toUpperCase()).includes(label.toUpperCase())
}

function toggleMulti(questionId, label) {
  const current = userAnswers.value[questionId] || ''
  const parts = current ? current.split(',').map(s => s.trim().toUpperCase()).filter(Boolean) : []
  const idx = parts.indexOf(label.toUpperCase())
  if (idx >= 0) parts.splice(idx, 1)
  else parts.push(label.toUpperCase())
  userAnswers.value = { ...userAnswers.value, [questionId]: parts.join(',') }
}

// ---- Timer ----
function startTimer() {
  timerInterval = setInterval(() => {
    if (timerSeconds.value <= 1) {
      timerSeconds.value = 0
      timerExpired.value = true
      clearInterval(timerInterval)
      autoSubmit()
    } else {
      timerSeconds.value--
    }
  }, 1000)
}

function autoSubmit() {
  if (!submitted.value && !submitting.value) {
    submitAnswers()
  }
}

// ---- Navigation ----
function goToQuestion(idx) {
  if (idx >= 0 && idx < questions.value.length) currentIndex.value = idx
}

// ---- Data ----
async function loadDailyQuestions() {
  loading.value = true
  error.value = ''
  try {
    const res = await practiceApi.getDaily(5)
    if (res.data.code === 200) {
      questions.value = res.data.data.questions
      if (questions.value.length === 0) {
        error.value = '今日题库暂无可用题目，请稍后再来。'
      }
    } else {
      error.value = res.data.message || '加载题目失败'
    }
  } catch (e) {
    error.value = '加载题目失败，请检查网络连接。'
  } finally {
    loading.value = false
  }
}

async function submitAnswers() {
  if (submitted.value || submitting.value) return
  submitting.value = true
  try {
    const answers = questions.value.map(q => ({
      question_id: q.id,
      answer: userAnswers.value[q.id] || '',
      hints_used: hintCounts.value[q.id] || 0,
    }))
    const res = await practiceApi.batchSubmit(answers)
    if (res.data.code === 200) {
      results.value = res.data.data
      submitted.value = true
      clearInterval(timerInterval)
      setPetMode('active')
      // Pet feedback based on daily practice results
      const details = res.data.data.details || []
      const pct = res.data.data.score_percent || 0
      const streak = calcConsecutiveCorrect(details)
      const hasCode = questions.value.some(q => q.type === 'code')
      const usedHint = Object.values(hintCounts.value).some(c => c > 0)
      if (pct >= 90) triggerPetState('excellent', 5000)
      else if (pct >= 75) triggerPetState('happy', 4000)
      else if (pct >= 60) triggerPetState('thinking', 4000)
      else triggerPetState('comfort', 4000)
    } else {
      error.value = res.data.message || '提交失败，请重试。'
    }
  } catch (e) {
    error.value = '提交失败，请检查网络连接。'
  } finally {
    submitting.value = false
  }
}

function onHintUsed(questionId, count) {
  hintCounts.value = { ...hintCounts.value, [questionId]: count }
}

function getResultForQuestion(qId) {
  if (!results.value?.details) return null
  return results.value.details.find(d => d.question_id === qId)
}

function calcConsecutiveCorrect(details) {
  let streak = 0
  for (const d of details) {
    if (d.is_correct) streak++
    else break
  }
  return streak
}

// ---- Labels ----
function typeLabel(t) {
  const m = { single_choice: '单选', multiple_choice: '多选', judge: '判断', fill_blank: '填空', short_answer: '简答', code: '代码' }
  return m[t] || t
}

function diffLabel(d) {
  const m = { easy: '简单', medium: '中等', hard: '困难' }
  return m[d] || d
}

// ---- Cleanup ----
onMounted(async () => {
  if (!auth.isLoggedIn) {
    router.push('/login')
    return
  }
  setPetMode('simplified')
  await loadDailyQuestions()
  if (questions.value.length > 0) {
    startTimer()
  }
})

onUnmounted(() => {
  clearInterval(timerInterval)
  setPetMode('active')
})

// Update window globals for simplified pet menu
watch([currentQuestion, currentIndex, totalQuestions], () => {
  const q = currentQuestion.value
  window.__dailyCurrentQuestionId = q?.id
  window.__dailyCurrentIndex = currentIndex.value
  window.__dailyTotalQuestions = totalQuestions.value
  window.__dailyCurrentQuestion = q ? {
    title: q.title || q.content,
    type: q.type,
    difficulty: q.difficulty,
    knowledge_tag: q.knowledge_tag,
    knowledge_type: q.knowledge_type || '',
  } : null
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <AppHeader />

    <!-- Not logged in -->
    <main v-if="!auth.isLoggedIn" class="flex-grow container mx-auto px-4 py-16 text-center">
      <p class="text-5xl mb-4">🔒</p>
      <h2 class="text-2xl font-bold text-gray-800 mb-2">请先登录</h2>
      <p class="text-gray-500 mb-6">登录后开始每日一练</p>
      <router-link to="/login" class="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition">立即登录</router-link>
    </main>

    <!-- Loading -->
    <main v-else-if="loading" class="flex-grow flex items-center justify-center">
      <div class="text-center">
        <div class="w-12 h-12 mx-auto mb-4 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p class="text-gray-500">加载题目中...</p>
      </div>
    </main>

    <!-- Error / Empty -->
    <main v-else-if="error" class="flex-grow flex items-center justify-center">
      <div class="text-center bg-white rounded-2xl shadow-sm border border-gray-100 p-10 max-w-md mx-auto">
        <p class="text-4xl mb-3">📋</p>
        <p class="text-gray-600 mb-4">{{ error }}</p>
        <button @click="router.push('/practice')" class="text-blue-600 hover:text-blue-700 text-sm font-medium">
          <i class="fas fa-arrow-left mr-1"></i>返回练习中心
        </button>
      </div>
    </main>

    <!-- Empty questions fallback -->
    <main v-else-if="questions.length === 0 && !loading" class="flex-grow flex items-center justify-center">
      <div class="text-center bg-white rounded-2xl shadow-sm border border-gray-100 p-10 max-w-md mx-auto">
        <p class="text-4xl mb-3">📋</p>
        <p class="text-gray-600 mb-4">暂无可用题目</p>
        <button @click="router.push('/practice')" class="text-blue-600 hover:text-blue-700 text-sm font-medium">
          <i class="fas fa-arrow-left mr-1"></i>返回练习中心
        </button>
      </div>
    </main>

    <!-- ========== QUIZ MODE ========== -->
    <main v-else-if="!submitted" class="flex-grow container mx-auto px-4 py-6 max-w-5xl">
      <button @click="$router.push('/learning-center')" class="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mb-3 transition">
        <i class="fas fa-arrow-left"></i> 返回学习中心
      </button>
      <!-- Top bar: timer + progress -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-6">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <span class="text-sm font-bold text-gray-700">
              第 <span class="text-blue-600">{{ currentIndex + 1 }}</span> / {{ totalQuestions }} 题
            </span>
            <span class="text-xs text-gray-400">已答 {{ answeredCount }} 题</span>
          </div>
          <div class="flex items-center gap-3">
            <span :class="['flex items-center gap-1 text-sm font-mono font-bold', timerUrgent ? 'text-red-500 animate-pulse' : 'text-gray-700']">
              <i class="fas fa-clock text-xs"></i>{{ timerDisplay }}
            </span>
            <button @click="submitAnswers" :disabled="submitting"
              class="bg-blue-600 text-white px-4 py-1.5 rounded-full text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition">
              {{ submitting ? '提交中...' : '交卷' }}
            </button>
          </div>
        </div>
        <!-- Timer bar -->
        <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div :class="timerUrgent ? 'bg-red-500' : 'bg-blue-500'"
            class="h-full rounded-full transition-all duration-1000 ease-linear"
            :style="{ width: timerPct + '%' }"></div>
        </div>
      </div>

      <!-- Question card -->
      <div v-if="currentQuestion" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 md:p-8">
        <!-- Meta -->
        <div class="flex items-center gap-2 mb-4 flex-wrap">
          <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', currentQuestion.difficulty === 'easy' ? 'bg-green-100 text-green-600' : currentQuestion.difficulty === 'hard' ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-600']">
            {{ diffLabel(currentQuestion.difficulty) }}
          </span>
          <span class="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">{{ typeLabel(currentQuestion.type) }}</span>
          <span v-if="currentQuestion.knowledge_tag" class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{{ currentQuestion.knowledge_tag }}</span>
        </div>

        <!-- Title -->
        <h3 class="text-lg font-bold text-gray-800 mb-2 leading-relaxed">{{ currentQuestion.title }}</h3>

        <!-- Content / Code -->
        <div v-if="currentQuestion.content && currentQuestion.content !== currentQuestion.title"
          class="text-sm text-gray-700 mb-5 whitespace-pre-wrap bg-gray-50 rounded-xl p-4">{{ currentQuestion.content }}</div>

        <!-- Starter code -->
        <div v-if="currentQuestion.starter_code" class="bg-gray-900 text-green-400 text-xs font-mono rounded-xl p-4 mb-5 overflow-x-auto">
          <pre>{{ currentQuestion.starter_code }}</pre>
        </div>

        <!-- AI Hint -->
        <div class="mb-5">
          <AiHintCard
            :key="currentQuestion.id"
            :question-id="currentQuestion.id"
            :question="currentQuestion.title || currentQuestion.content"
            :question-type="currentQuestion.type"
            :difficulty="currentQuestion.difficulty"
            :knowledge-tag="currentQuestion.knowledge_tag"
            :knowledge-type="currentQuestion.knowledge_type || ''"
            :student-code="userAnswers[currentQuestion.id] || ''"
            @hint-used="(count) => onHintUsed(currentQuestion.id, count)"
          />
        </div>

        <!-- Answer area -->
        <div class="mt-4">
          <!-- Single choice -->
          <template v-if="currentQuestion.type === 'single_choice'">
            <div class="space-y-2">
              <button v-for="opt in (currentQuestion.options || [])" :key="opt.label"
                @click="selectAnswer(currentQuestion.id, opt.label)"
                :class="['w-full text-left px-4 py-3 rounded-xl text-sm border transition-all',
                  isSelected(currentQuestion.id, opt.label) ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium shadow-sm' : 'border-gray-200 hover:border-gray-300 bg-white text-gray-700']">
                <span class="font-bold mr-2">{{ opt.label }}.</span>{{ opt.text }}
              </button>
            </div>
          </template>

          <!-- Multiple choice -->
          <template v-else-if="currentQuestion.type === 'multiple_choice'">
            <p class="text-xs text-gray-400 mb-2">可多选</p>
            <div class="space-y-2">
              <button v-for="opt in (currentQuestion.options || [])" :key="opt.label"
                @click="toggleMulti(currentQuestion.id, opt.label)"
                :class="['w-full text-left px-4 py-3 rounded-xl text-sm border transition-all',
                  isMultiSelected(currentQuestion.id, opt.label) ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium shadow-sm' : 'border-gray-200 hover:border-gray-300 bg-white text-gray-700']">
                <span class="font-bold mr-2">{{ opt.label }}.</span>{{ opt.text }}
              </button>
            </div>
          </template>

          <!-- Judge -->
          <template v-else-if="currentQuestion.type === 'judge'">
            <div class="flex gap-4">
              <button @click="selectAnswer(currentQuestion.id, '正确')"
                :class="['flex-1 py-4 rounded-xl text-lg font-bold border-2 transition-all',
                  isSelected(currentQuestion.id, '正确') ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 hover:border-green-300 bg-white text-gray-500']">
                <i class="fas fa-check-circle mr-2"></i>正确
              </button>
              <button @click="selectAnswer(currentQuestion.id, '错误')"
                :class="['flex-1 py-4 rounded-xl text-lg font-bold border-2 transition-all',
                  isSelected(currentQuestion.id, '错误') ? 'border-red-500 bg-red-50 text-red-700' : 'border-gray-200 hover:border-red-300 bg-white text-gray-500']">
                <i class="fas fa-times-circle mr-2"></i>错误
              </button>
            </div>
          </template>

          <!-- Fill blank -->
          <template v-else-if="currentQuestion.type === 'fill_blank'">
            <input v-model="userAnswers[currentQuestion.id]"
              @input="userAnswers[currentQuestion.id] = $event.target.value; userAnswers = { ...userAnswers }"
              class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:border-blue-400 focus:outline-none"
              :placeholder="'请输入答案...'" />
          </template>

          <!-- Code / Short answer -->
          <template v-else>
            <textarea v-model="userAnswers[currentQuestion.id]"
              @input="userAnswers[currentQuestion.id] = $event.target.value; userAnswers = { ...userAnswers }"
              class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 text-sm focus:border-blue-400 focus:outline-none resize-none"
              rows="4" :placeholder="currentQuestion.type === 'code' ? '输入你的代码...' : '输入你的答案...'"></textarea>
          </template>
        </div>
      </div>

      <!-- Navigation buttons -->
      <div class="flex justify-between mt-4">
        <button @click="goToQuestion(currentIndex - 1)" :disabled="currentIndex === 0"
          class="px-5 py-2.5 bg-white border border-gray-200 rounded-full text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition">
          <i class="fas fa-chevron-left mr-1"></i>上一题
        </button>

        <!-- Question dots -->
        <div class="hidden sm:flex items-center gap-1.5">
          <button v-for="(q, i) in questions" :key="q.id" @click="goToQuestion(i)"
            :class="['w-8 h-8 rounded-full text-xs font-medium transition-all',
              i === currentIndex ? 'bg-blue-600 text-white shadow' :
              userAnswers[q.id] ? 'bg-blue-100 text-blue-600 border border-blue-300' :
              'bg-gray-100 text-gray-400 border border-gray-200 hover:border-gray-300']">
            {{ i + 1 }}
          </button>
        </div>

        <button v-if="currentIndex < totalQuestions - 1" @click="goToQuestion(currentIndex + 1)"
          class="px-5 py-2.5 bg-white border border-gray-200 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition">
          下一题<i class="fas fa-chevron-right ml-1"></i>
        </button>
        <button v-else @click="submitAnswers" :disabled="submitting"
          class="px-6 py-2.5 bg-blue-600 text-white rounded-full text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition">
          {{ submitting ? '提交中...' : '提交答卷' }}<i class="fas fa-check ml-1"></i>
        </button>
      </div>
    </main>

    <!-- ========== RESULTS ========== -->
    <main v-else-if="submitted && results" class="flex-grow container mx-auto px-4 py-6 max-w-5xl">
      <!-- Score header -->
      <div class="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-lg p-8 text-white text-center mb-6">
        <p class="text-sm text-white/70 mb-2">每日一练 · {{ majorLevel }}段</p>
        <div class="w-24 h-24 mx-auto mb-4 rounded-full bg-white/20 flex items-center justify-center">
          <div>
            <p class="text-3xl font-black">{{ results.score_percent }}%</p>
            <p class="text-[10px] text-white/60">{{ results.score }}/{{ results.total }}</p>
          </div>
        </div>
        <p class="text-lg font-bold">{{ results.score_percent >= 80 ? '🎉 太棒了！' : results.score_percent >= 60 ? '👍 继续加油！' : '💪 还有进步空间！' }}</p>
        <p class="text-sm text-white/70 mt-1">答对 {{ results.score }} 题，答错 {{ results.total - results.score }} 题</p>
        <p v-if="results.experience_gained" class="text-sm mt-2 bg-white/20 inline-block px-3 py-1 rounded-full">+{{ results.experience_gained }} 经验值</p>
      </div>

      <!-- Per-question review -->
      <div class="space-y-4 mb-8">
        <div v-for="(q, i) in questions" :key="q.id"
          class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div :class="['p-1', getResultForQuestion(q.id)?.is_correct ? 'bg-green-500' : 'bg-red-500']"></div>
          <div class="p-5 md:p-6">
            <!-- Header -->
            <div class="flex items-center justify-between flex-wrap gap-2 mb-3">
              <div class="flex items-center gap-2">
                <span :class="['w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white',
                  getResultForQuestion(q.id)?.is_correct ? 'bg-green-500' : 'bg-red-500']">
                  {{ getResultForQuestion(q.id)?.is_correct ? '✓' : '✗' }}
                </span>
                <span class="font-bold text-gray-700 text-sm">第 {{ i + 1 }} 题</span>
                <span class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{{ typeLabel(q.type) }}</span>
              </div>
              <span class="text-xs text-gray-400">{{ diffLabel(q.difficulty) }} · {{ q.knowledge_tag }}</span>
            </div>

            <!-- Question -->
            <p class="text-sm font-medium text-gray-800 mb-3">{{ q.title }}</p>
            <p v-if="q.content && q.content !== q.title" class="text-xs text-gray-600 mb-3">{{ q.content }}</p>

            <!-- Answer comparison -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div class="bg-gray-50 rounded-xl p-3">
                <p class="text-gray-400 mb-1">你的答案</p>
                <p :class="getResultForQuestion(q.id)?.is_correct ? 'text-green-700 font-medium' : 'text-red-700 font-medium'">
                  {{ userAnswers[q.id] || '(未作答)' }}
                </p>
              </div>
              <div v-if="!getResultForQuestion(q.id)?.is_correct" class="bg-green-50 rounded-xl p-3">
                <p class="text-green-500 mb-1">正确答案</p>
                <p class="text-green-700 font-medium">{{ getResultForQuestion(q.id)?.correct_answer }}</p>
              </div>
            </div>

            <!-- Analysis for wrong answers -->
            <div v-if="!getResultForQuestion(q.id)?.is_correct && getResultForQuestion(q.id)?.analysis"
              class="mt-3 bg-amber-50 border border-amber-100 rounded-xl p-3">
              <p class="text-xs font-bold text-amber-700 mb-1">📝 解析</p>
              <p class="text-xs text-amber-800 leading-relaxed">{{ getResultForQuestion(q.id)?.analysis }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-3 justify-center pb-8">
        <button @click="router.push('/practice')"
          class="px-6 py-3 bg-white border border-gray-200 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition">
          <i class="fas fa-th mr-1"></i>练习中心
        </button>
        <button @click="router.push('/report')"
          class="px-6 py-3 bg-blue-600 text-white rounded-full text-sm font-medium hover:bg-blue-700 transition">
          <i class="fas fa-chart-bar mr-1"></i>学习报告
        </button>
      </div>
    </main>
  </div>
</template>
