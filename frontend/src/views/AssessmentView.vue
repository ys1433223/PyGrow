<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { assessmentApi } from '../api/assessment'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const router = useRouter()
const questions = ref([])
const currentIndex = ref(0)
const userAnswers = ref({})
const submitted = ref(false)
const loading = ref(true)
const showConfirm = ref(false)
const multiSelectTemp = ref({})

const totalQuestions = computed(() => questions.value.length)
const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
const isFirst = computed(() => currentIndex.value === 0)
const isLast = computed(() => currentIndex.value === totalQuestions.value - 1)
const answeredCount = computed(() => Object.keys(userAnswers.value).length)
const allAnswered = computed(() => answeredCount.value === totalQuestions.value && totalQuestions.value > 0)
const progressPct = computed(() => totalQuestions.value > 0 ? Math.round(answeredCount.value / totalQuestions.value * 100) : 0)

onMounted(async () => {
  try {
    const res = await assessmentApi.getQuestions()
    if (res.data.code === 200) {
      questions.value = res.data.data
      questions.value.forEach(q => {
        if (q.type === 'multi') multiSelectTemp.value[q.id] = []
      })
    }
  } catch (e) {
    console.error('Failed to load questions:', e)
  } finally {
    loading.value = false
  }
})

function selectAnswer(qid, option) {
  const q = questions.value.find(q => q.id === qid)
  if (!q) return
  if (q.type === 'multi') {
    const arr = multiSelectTemp.value[qid] || []
    const idx = arr.indexOf(option)
    if (idx >= 0) arr.splice(idx, 1)
    else arr.push(option)
    userAnswers.value[qid] = arr.join(',')
  } else {
    userAnswers.value[qid] = option
  }
}

function isSelected(qid, option) {
  const q = questions.value.find(q => q.id === qid)
  if (!q) return false
  if (q.type === 'multi') {
    return (multiSelectTemp.value[qid] || []).includes(option)
  }
  return userAnswers.value[qid] === option
}

function goNext() {
  if (currentIndex.value < totalQuestions.value - 1) currentIndex.value++
}

function goPrev() {
  if (currentIndex.value > 0) currentIndex.value--
}

function goToQuestion(idx) {
  currentIndex.value = idx
}

async function submitAssessment() {
  if (submitted.value) return
  submitted.value = true
  try {
    const res = await assessmentApi.submitAnswers(userAnswers.value)
    if (res.data.code === 200) {
      localStorage.setItem('lastAssessmentResult', JSON.stringify(res.data.data))
      router.push('/assessment/result')
    }
  } catch (e) {
    console.error('Submit failed:', e)
    submitted.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <div v-if="loading" class="text-center py-20">
        <div class="animate-spin-slow w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full mx-auto mb-4"></div>
        <p class="text-gray-500">正在加载测评题目...</p>
      </div>

      <template v-else-if="questions.length > 0">
        <!-- Header info -->
        <div class="max-w-3xl mx-auto mb-8">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h1 class="text-2xl font-bold text-gray-900 mb-2">能力测评</h1>
            <p class="text-gray-500 text-sm mb-4">共 {{ totalQuestions }} 题、满分 100 分，覆盖 Python 基础到中级知识点。测评结果将为你匹配萌新小白~稳扎玩家四个初始段位。</p>
            <!-- Progress -->
            <div class="flex items-center gap-3">
              <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all duration-500" :style="{ width: progressPct + '%' }"></div>
              </div>
              <span class="text-sm text-gray-400 whitespace-nowrap">{{ answeredCount }}/{{ totalQuestions }}</span>
            </div>
            <!-- Question dots -->
            <div class="flex flex-wrap gap-1.5 mt-4">
              <button
                v-for="(q, i) in questions" :key="q.id"
                @click="goToQuestion(i)"
                :class="[
                  'w-8 h-8 rounded-full text-xs font-bold transition-all',
                  currentIndex === i ? 'ring-2 ring-blue-500 scale-110' : '',
                  userAnswers[q.id] ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-400'
                ]"
              >{{ i + 1 }}</button>
            </div>
          </div>
        </div>

        <!-- Question card -->
        <div v-if="currentQuestion" class="max-w-3xl mx-auto">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs font-bold px-2 py-0.5 rounded-full"
                :class="{
                  'bg-green-100 text-green-600': currentQuestion.difficulty === 'easy',
                  'bg-yellow-100 text-yellow-600': currentQuestion.difficulty === 'medium',
                  'bg-red-100 text-red-600': currentQuestion.difficulty === 'hard',
                }"
              >{{ currentQuestion.difficulty === 'easy' ? '简单' : currentQuestion.difficulty === 'medium' ? '中等' : '困难' }}</span>
              <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{{ currentQuestion.knowledge_point }}</span>
              <span class="text-xs text-gray-400 ml-auto">第 {{ currentIndex + 1 }} / {{ totalQuestions }} 题</span>
            </div>

            <h2 class="text-lg font-bold text-gray-900 mt-3 mb-6">{{ currentQuestion.content }}</h2>

            <!-- Single/TF options -->
            <div v-if="currentQuestion.type === 'single' || currentQuestion.type === 'tf'" class="space-y-3">
              <button
                v-for="(opt, i) in currentQuestion.options" :key="i"
                @click="selectAnswer(currentQuestion.id, typeof opt === 'object' ? opt.label : opt)"
                :class="[
                  'w-full text-left px-5 py-3.5 rounded-xl border-2 transition-all font-medium',
                  isSelected(currentQuestion.id, typeof opt === 'object' ? opt.label : opt)
                    ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-md'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 text-gray-700'
                ]"
              >
                <span class="inline-flex items-center justify-center w-7 h-7 rounded-full border-2 text-sm font-bold mr-3"
                  :class="isSelected(currentQuestion.id, typeof opt === 'object' ? opt.label : opt) ? 'border-blue-500 bg-blue-500 text-white' : 'border-gray-300 text-gray-400'"
                >{{ String.fromCharCode(65 + i) }}</span>
                {{ typeof opt === 'object' ? opt.text : opt }}
              </button>
            </div>

            <!-- Multi options -->
            <div v-else-if="currentQuestion.type === 'multi'" class="space-y-3">
              <p class="text-xs text-orange-500 mb-2">多选题：请选择所有正确答案</p>
              <button
                v-for="(opt, i) in currentQuestion.options" :key="i"
                @click="selectAnswer(currentQuestion.id, typeof opt === 'object' ? opt.label : opt)"
                :class="[
                  'w-full text-left px-5 py-3.5 rounded-xl border-2 transition-all font-medium',
                  isSelected(currentQuestion.id, typeof opt === 'object' ? opt.label : opt)
                    ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-md'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 text-gray-700'
                ]"
              >
                <span class="inline-flex items-center justify-center w-7 h-7 rounded-md border-2 text-sm font-bold mr-3"
                  :class="isSelected(currentQuestion.id, typeof opt === 'object' ? opt.label : opt) ? 'border-blue-500 bg-blue-500 text-white rounded-md' : 'border-gray-300 text-gray-400 rounded-md'"
                >
                  <i v-if="isSelected(currentQuestion.id, typeof opt === 'object' ? opt.label : opt)" class="fas fa-check text-xs"></i>
                  <span v-else>{{ String.fromCharCode(65 + i) }}</span>
                </span>
                {{ typeof opt === 'object' ? opt.text : opt }}
              </button>
            </div>

            <!-- Fill input -->
            <div v-else-if="currentQuestion.type === 'fill'">
              <input
                :value="userAnswers[currentQuestion.id] || ''"
                @input="e => userAnswers[currentQuestion.id] = e.target.value"
                type="text" placeholder="请输入你的答案..."
                class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition text-lg"
              />
            </div>

            <!-- Navigation -->
            <div class="flex justify-between items-center mt-8 pt-6 border-t border-gray-100">
              <button @click="goPrev" :disabled="isFirst"
                class="px-5 py-2.5 rounded-xl font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed bg-gray-100 text-gray-600 hover:bg-gray-200">
                <i class="fas fa-arrow-left mr-2"></i>上一题
              </button>

              <button v-if="!isLast" @click="goNext"
                class="px-5 py-2.5 rounded-xl font-medium bg-blue-600 text-white hover:bg-blue-700 transition-all shadow-md">
                下一题<i class="fas fa-arrow-right ml-2"></i>
              </button>

              <button v-else @click="showConfirm = true" :disabled="!allAnswered"
                class="px-6 py-2.5 rounded-xl font-bold text-white transition-all shadow-md"
                :class="allAnswered ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-300 cursor-not-allowed'">
                <i class="fas fa-check mr-2"></i>提交测评
              </button>
            </div>
          </div>
        </div>
      </template>

      <div v-else class="text-center py-20 text-gray-400">
        <p class="text-5xl mb-4">📋</p>
        <p>暂无测评题目</p>
      </div>
    </main>

    <!-- Confirm modal -->
    <div v-if="showConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div class="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
        <h3 class="text-xl font-bold text-gray-900 mb-3">确认提交</h3>
        <p class="text-gray-500 mb-2">你已答完 {{ answeredCount }}/{{ totalQuestions }} 题，提交后将无法修改。</p>
        <p v-if="!allAnswered" class="text-orange-500 text-sm mb-4">还有 {{ totalQuestions - answeredCount }} 题未作答，将被记为错误。</p>
        <div class="flex gap-3">
          <button @click="showConfirm = false" class="flex-1 px-4 py-2.5 rounded-xl bg-gray-100 text-gray-600 hover:bg-gray-200 transition font-medium">继续检查</button>
          <button @click="submitAssessment" :disabled="submitted"
            class="flex-1 px-4 py-2.5 rounded-xl bg-green-600 text-white hover:bg-green-700 transition font-bold disabled:opacity-50">
            {{ submitted ? '提交中...' : '确认提交' }}
          </button>
        </div>
      </div>
    </div>

    <AppFooter />
  </div>
</template>
