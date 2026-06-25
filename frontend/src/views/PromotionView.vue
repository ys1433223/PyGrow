<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { promotionApi } from '../api/promotion'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const auth = useAuthStore()
const router = useRouter()

// ---- State ----
const status = ref(null)
const loading = ref(true)
const examStarted = ref(false)
const examSubmitted = ref(false)
const questions = ref([])
const answers = ref({})          // { question_id: user_answer }
const currentIndex = ref(0)
const result = ref(null)
const examId = ref(null)
const submitting = ref(false)

// ---- Computed ----
const currentQuestion = () => questions.value[currentIndex.value] || null
const sourceLabel = (s) => ({
  question_bank: '题库', wrong_question: '错题', ai_generated_promotion: 'AI生成'
}[s] || '题库')

// ---- Load status ----
async function loadStatus() {
  loading.value = true
  try {
    const res = await promotionApi.status()
    if (res.data.code === 200) {
      status.value = res.data.data
      // Resume in-progress exam
      if (status.value.has_in_progress) {
        examId.value = status.value.in_progress_id
        // Load existing exam questions
        const examRes = await promotionApi.result(status.value.in_progress_id)
        if (examRes.data.code === 200 && examRes.data.data.questions) {
          questions.value = examRes.data.data.questions.map(q => ({
            ...q,
            answer: q.correct_answer, // store for grading
          }))
          examStarted.value = true
        }
      }
    }
  } catch { /* ignore */ }
  loading.value = false
}

onMounted(() => {
  loadStatus()
})

// ---- Actions ----
async function startExam() {
  loading.value = true
  try {
    const res = await promotionApi.start()
    if (res.data.code === 200) {
      const d = res.data.data
      examId.value = d.exam_id
      questions.value = d.questions.map(q => ({
        ...q,
        answer: '', // Hide from student, stored server-side
      }))
      answers.value = {}
      currentIndex.value = 0
      examStarted.value = true
      examSubmitted.value = false
    } else {
      alert(res.data.message || '无法开始晋级赛')
    }
  } catch { alert('网络错误') }
  loading.value = false
}

function selectAnswer(qId, answer) {
  answers.value[String(qId)] = answer
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
  }
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

async function submitExam() {
  const q = questions.value[currentIndex.value]
  const qId = String(q?.question_id || '')
  // Warn if current question unanswered
  if (!answers.value[qId]) {
    if (!confirm('当前题目还未作答，确定提交吗？')) return
  }

  const unanswered = questions.value.filter(q => !answers.value[String(q.question_id)])
  if (unanswered.length > 0) {
    if (!confirm(`还有 ${unanswered.length} 题未作答，确定提交吗？`)) return
  }

  submitting.value = true
  try {
    const res = await promotionApi.submit(examId.value, answers.value)
    if (res.data.code === 200) {
      result.value = res.data.data
      examSubmitted.value = true
    } else {
      alert(res.data.message || '提交失败')
    }
  } catch { alert('提交失败，请稍后重试') }
  submitting.value = false
}

function viewResult() {
  // Show result view
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <PageLoader />
    <AppHeader />
    <main class="flex-grow container mx-auto px-4 py-8 max-w-3xl">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">晋级赛</h1>
        <p class="text-gray-500 mt-2">经验值满格后解锁，通过晋级赛即可升至下一段位</p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-20 text-gray-400">
        <i class="fas fa-spinner fa-spin text-3xl mb-4"></i>
        <p>加载中...</p>
      </div>

      <!-- API failed / status unavailable -->
      <div v-else-if="!status" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-10 text-center">
        <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-5">
          <i class="fas fa-exclamation-triangle text-red-400 text-3xl"></i>
        </div>
        <h2 class="text-lg font-bold text-gray-800 mb-2">加载失败</h2>
        <p class="text-gray-500 mb-6">无法获取晋级赛状态，请检查网络后重试</p>
        <div class="flex gap-3 justify-center">
          <button @click="loadStatus()" class="px-5 py-2 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition">
            重新加载
          </button>
          <button @click="router.push('/')" class="px-5 py-2 border border-gray-200 text-gray-600 rounded-xl font-medium hover:bg-gray-50 transition">
            返回首页
          </button>
        </div>
      </div>

      <!-- Not eligible -->
      <div v-else-if="!examStarted && status && !status.can_take" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-10 text-center">
        <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-5">
          <i class="fas fa-lock text-gray-400 text-3xl"></i>
        </div>
        <h2 class="text-xl font-bold text-gray-800 mb-2">暂未解锁</h2>
        <p class="text-gray-500 mb-6">
          当前段位 <span class="font-bold text-blue-600">{{ status.current_rank }}</span>
          · 经验 {{ status.current_exp }} / {{ status.rank_exp_limit }}
        </p>
        <div class="bg-gray-50 rounded-xl p-4 max-w-md mx-auto">
          <div class="flex justify-between text-sm text-gray-500 mb-2">
            <span>经验进度</span>
            <span>{{ Math.round(status.current_exp / status.rank_exp_limit * 100) }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2.5 mb-4">
            <div class="bg-blue-600 h-2.5 rounded-full transition-all" :style="{ width: Math.round(status.current_exp / status.rank_exp_limit * 100) + '%' }"></div>
          </div>
          <p class="text-xs text-gray-400">
            经验满格后可解锁晋级赛。完成每日任务、答题练习来积累经验吧！
          </p>
        </div>
        <button @click="router.push('/daily-practice')" class="mt-6 px-6 py-2.5 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition">
          去练习赚经验
        </button>
      </div>

      <!-- Eligible, not started -->
      <div v-else-if="!examStarted && status && status.can_take" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-10 text-center">
        <div class="w-20 h-20 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-5 shadow-lg">
          <i class="fas fa-trophy text-white text-3xl"></i>
        </div>
        <h2 class="text-xl font-bold text-gray-800 mb-2">可以参加晋级赛！</h2>
        <p class="text-gray-500 mb-1">
          当前段位 <span class="font-bold text-blue-600">{{ status.current_rank }}</span>
          → <span class="font-bold text-green-600">{{ status.next_rank }}</span>
        </p>
        <p class="text-sm text-gray-400 mb-6">
          已学习 {{ status.learned_tags_count }} 个知识点 · 薄弱点 {{ status.weak_tags_count }} 个
        </p>
        <div class="bg-amber-50 rounded-xl p-4 max-w-md mx-auto mb-6 text-left space-y-2 text-sm text-gray-600">
          <p><i class="fas fa-check-circle text-green-500 mr-2"></i>10 道题目，限时 30 分钟</p>
          <p><i class="fas fa-check-circle text-green-500 mr-2"></i>题目范围仅限已学内容</p>
          <p><i class="fas fa-check-circle text-green-500 mr-2"></i>80 分及格，核心正确率需 ≥ 70%</p>
        </div>
        <button @click="startExam" :disabled="loading"
          class="px-8 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-bold hover:from-amber-600 hover:to-orange-600 transition shadow-lg disabled:opacity-50">
          <i class="fas fa-play mr-2"></i>开始晋级赛
        </button>

        <!-- Last exam result -->
        <div v-if="status.last_exam" class="mt-6 text-sm text-gray-400">
          上次晋级赛：{{ status.last_exam.score }} 分
          <span :class="status.last_exam.passed ? 'text-green-500' : 'text-red-400'">
            · {{ status.last_exam.passed ? '已通过' : '未通过' }}
          </span>
        </div>
      </div>

      <!-- Exam in progress -->
      <div v-if="examStarted && !examSubmitted" class="space-y-6">
        <!-- Progress bar -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-bold text-gray-700">第 {{ currentIndex + 1 }} / {{ questions.length }} 题</span>
            <span class="text-xs text-gray-400">{{ Object.keys(answers).length }} 题已答</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-blue-600 h-2 rounded-full transition-all" :style="{ width: (currentIndex + 1) / questions.length * 100 + '%' }"></div>
          </div>
        </div>

        <!-- Question card -->
        <div v-if="questions[currentIndex]" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 md:p-8">
          <div class="flex items-center gap-2 mb-4 flex-wrap">
            <span :class="[
              'text-xs font-bold px-2 py-0.5 rounded-full',
              questions[currentIndex].difficulty === 'easy' ? 'bg-green-100 text-green-600' :
              questions[currentIndex].difficulty === 'hard' ? 'bg-red-100 text-red-600' :
              'bg-amber-100 text-amber-600'
            ]">{{ {easy:'简单', medium:'中等', hard:'困难'}[questions[currentIndex].difficulty] || '中等' }}</span>
            <span class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{{ questions[currentIndex].type === 'single_choice' ? '单选' : questions[currentIndex].type === 'multiple_choice' ? '多选' : questions[currentIndex].type === 'judge' ? '判断' : questions[currentIndex].type === 'fill_blank' ? '填空' : questions[currentIndex].type === 'code' ? '编程' : questions[currentIndex].type }}</span>
            <span class="text-xs bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full">{{ sourceLabel(questions[currentIndex].source) }}</span>
            <span v-if="questions[currentIndex].knowledge_tag" class="text-xs bg-purple-100 text-purple-600 px-2 py-0.5 rounded-full">{{ questions[currentIndex].knowledge_tag }}</span>
          </div>

          <h3 class="text-lg font-bold text-gray-800 mb-2">{{ questions[currentIndex].title }}</h3>
          <p class="text-gray-700 mb-6 whitespace-pre-wrap">{{ questions[currentIndex].content }}</p>

          <!-- Options -->
          <div v-if="['single_choice', 'multiple_choice'].includes(questions[currentIndex].type)" class="space-y-3 mb-6">
            <button
              v-for="(opt, oi) in (questions[currentIndex].options || [])" :key="oi"
              @click="selectAnswer(questions[currentIndex].question_id, opt)"
              :class="[
                'w-full text-left px-4 py-3 rounded-xl border transition font-medium text-sm',
                answers[String(questions[currentIndex].question_id)] === opt
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'
              ]"
            >
              {{ opt }}
            </button>
          </div>

          <!-- Judge -->
          <div v-else-if="questions[currentIndex].type === 'judge'" class="flex gap-4 mb-6">
            <button @click="selectAnswer(questions[currentIndex].question_id, '正确')"
              :class="['flex-1 py-3 rounded-xl border transition font-bold',
                answers[String(questions[currentIndex].question_id)] === '正确' ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 hover:border-gray-300']">
              <i class="fas fa-check mr-1"></i>正确
            </button>
            <button @click="selectAnswer(questions[currentIndex].question_id, '错误')"
              :class="['flex-1 py-3 rounded-xl border transition font-bold',
                answers[String(questions[currentIndex].question_id)] === '错误' ? 'border-red-500 bg-red-50 text-red-700' : 'border-gray-200 hover:border-gray-300']">
              <i class="fas fa-times mr-1"></i>错误
            </button>
          </div>

          <!-- Fill blank -->
          <div v-else-if="questions[currentIndex].type === 'fill_blank'" class="mb-6">
            <input
              :value="answers[String(questions[currentIndex].question_id)] || ''"
              @input="selectAnswer(questions[currentIndex].question_id, $event.target.value)"
              placeholder="请输入答案..."
              class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            />
          </div>

          <!-- Code -->
          <div v-else-if="questions[currentIndex].type === 'code'" class="mb-6">
            <p v-if="questions[currentIndex].starter_code" class="text-xs text-gray-400 mb-2">起始代码：</p>
            <pre v-if="questions[currentIndex].starter_code" class="bg-gray-100 rounded-lg p-3 text-xs mb-3 overflow-x-auto">{{ questions[currentIndex].starter_code }}</pre>
            <textarea
              :value="answers[String(questions[currentIndex].question_id)] || ''"
              @input="selectAnswer(questions[currentIndex].question_id, $event.target.value)"
              placeholder="请输入你的Python代码..."
              rows="5"
              class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none font-mono text-sm"
            ></textarea>
          </div>

          <!-- Short answer -->
          <div v-else class="mb-6">
            <textarea
              :value="answers[String(questions[currentIndex].question_id)] || ''"
              @input="selectAnswer(questions[currentIndex].question_id, $event.target.value)"
              placeholder="请输入你的答案..."
              rows="3"
              class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            ></textarea>
          </div>

          <!-- Reason -->
          <p v-if="questions[currentIndex].reason" class="text-xs text-gray-400 mb-4">
            <i class="fas fa-info-circle mr-1"></i>{{ questions[currentIndex].reason }}
          </p>

          <!-- Navigation -->
          <div class="flex justify-between items-center pt-4 border-t border-gray-100">
            <button @click="prevQuestion" :disabled="currentIndex === 0"
              class="px-5 py-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 transition disabled:opacity-30">
              <i class="fas fa-chevron-left mr-1"></i>上一题
            </button>

            <span class="text-xs text-gray-400 hidden sm:block">{{ currentIndex + 1 }} / {{ questions.length }}</span>

            <button v-if="currentIndex < questions.length - 1" @click="nextQuestion"
              class="px-5 py-2 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition">
              下一题 <i class="fas fa-chevron-right ml-1"></i>
            </button>

            <button v-else @click="submitExam" :disabled="submitting"
              class="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-bold hover:from-green-600 hover:to-emerald-600 transition shadow disabled:opacity-50">
              <i v-if="submitting" class="fas fa-spinner fa-spin mr-1"></i>
              提交答卷
            </button>
          </div>
        </div>

        <!-- Question index dots -->
        <div class="flex flex-wrap justify-center gap-2">
          <button v-for="(q, i) in questions" :key="q.question_id"
            @click="currentIndex = i"
            :class="[
              'w-8 h-8 rounded-full text-xs font-bold transition',
              i === currentIndex ? 'bg-blue-600 text-white shadow' :
              answers[String(q.question_id)] ? 'bg-green-100 text-green-700 border border-green-300' :
              'bg-white text-gray-400 border border-gray-200'
            ]"
          >{{ i + 1 }}</button>
        </div>
      </div>

      <!-- Result -->
      <div v-if="examSubmitted && result" class="space-y-6">
        <!-- Score card -->
        <div :class="[
          'rounded-2xl shadow-sm border p-10 text-center',
          result.passed ? 'bg-white border-green-200' : 'bg-white border-red-200'
        ]">
          <div :class="[
            'w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-5 shadow-lg',
            result.passed ? 'bg-gradient-to-br from-green-400 to-emerald-500' : 'bg-gradient-to-br from-red-400 to-pink-500'
          ]">
            <i :class="['fas text-white text-4xl', result.passed ? 'fa-check' : 'fa-times']"></i>
          </div>
          <h2 class="text-2xl font-bold text-gray-800 mb-1">
            {{ result.passed ? '恭喜通过！' : '未通过' }}
          </h2>
          <p class="text-gray-500 mb-4">
            {{ result.passed ? `成功晋升为 ${result.new_rank || ''}` : '继续加油，下次一定能通过！' }}
          </p>

          <div class="grid grid-cols-2 gap-4 max-w-sm mx-auto mb-6">
            <div class="bg-gray-50 rounded-xl p-4">
              <div class="text-3xl font-bold text-blue-600">{{ result.score }}</div>
              <div class="text-xs text-gray-400">总分 (满分100)</div>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <div class="text-3xl font-bold" :class="result.core_correct_rate >= 70 ? 'text-green-600' : 'text-red-500'">{{ result.core_correct_rate }}%</div>
              <div class="text-xs text-gray-400">核心正确率</div>
            </div>
          </div>

          <div class="flex gap-3 justify-center">
            <button @click="router.push('/practice')" class="px-5 py-2 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition">
              继续练习
            </button>
            <button @click="goBack" class="px-5 py-2 border border-gray-200 text-gray-600 rounded-xl font-medium hover:bg-gray-50 transition">
              返回首页
            </button>
          </div>
        </div>

        <!-- Failure feedback -->
        <div v-if="!result.passed && result.feedback && result.feedback.length > 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
            <i class="fas fa-lightbulb text-amber-500"></i>复习建议
          </h3>
          <div v-for="fb in result.feedback" :key="fb.tag" class="bg-amber-50 rounded-xl p-4 mb-3 last:mb-0">
            <div class="flex items-start gap-3">
              <span class="bg-amber-200 text-amber-700 text-xs font-bold px-2 py-0.5 rounded-full mt-0.5">{{ fb.tag }}</span>
              <div>
                <p class="text-sm text-gray-700">{{ fb.suggestion }}</p>
                <p v-if="fb.recommended_chapters && fb.recommended_chapters.length > 0" class="text-xs text-gray-400 mt-1">
                  推荐复习章节：{{ fb.recommended_chapters.join('、') }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Per-question results -->
        <div v-if="result.questions" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 class="font-bold text-gray-800 mb-4">答题详情</h3>
          <div v-for="(q, i) in result.questions" :key="q.question_id"
            :class="[
              'rounded-xl border p-4 mb-3 last:mb-0',
              q.your_answer === q.correct_answer ? 'border-green-100 bg-green-50/30' : 'border-red-100 bg-red-50/30'
            ]">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-bold text-gray-700">第{{ i + 1 }}题 · {{ q.knowledge_tag || '' }}</span>
              <span :class="q.your_answer === q.correct_answer ? 'text-green-600' : 'text-red-500'" class="text-xs font-bold">
                {{ q.your_answer === q.correct_answer ? '✓ 正确' : '✗ 错误' }}
              </span>
            </div>
            <p class="text-sm text-gray-600 mb-1">{{ q.title }}</p>
            <p v-if="q.your_answer !== q.correct_answer" class="text-xs text-gray-400">
              你的答案：<span class="text-red-500">{{ q.your_answer || '(空)' }}</span>
              · 正确答案：<span class="text-green-600">{{ q.correct_answer }}</span>
            </p>
            <p v-if="q.analysis" class="text-xs text-gray-500 mt-2 leading-relaxed">{{ q.analysis }}</p>
          </div>
        </div>
      </div>
    </main>
    <AppFooter />
  </div>
</template>
