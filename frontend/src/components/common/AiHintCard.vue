<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { practiceApi } from '../../api/practice'

const props = defineProps({
  questionId: { type: Number, required: true },
  question: { type: String, default: '' },
  questionType: { type: String, default: '' },
  difficulty: { type: String, default: 'medium' },
  knowledgeTag: { type: String, default: '' },
  knowledgeType: { type: String, default: '' },
  studentCode: { type: String, default: '' },
})

const emit = defineEmits(['hint-used'])

// ---- state ----
const visible = ref(false)
const loading = ref(false)
const hints = ref([]) // [{hint_level, hint_mode, title, content, examples, common_mistakes, keywords, still_no_answer}]
const showRemediation = ref(false)
const hintListRef = ref(null)
const maxLevel = 3

// ---- mode labels per knowledge type ----
const modeLabels = {
  concept: ['概念卡片', '举个例子', '记忆关键词'],
  comparison: ['对比表', '判断依据', '常见混淆点'],
  application: ['关键信息', '解题思路', '易错提醒'],
  code: ['相关知识点', '解题思路', '代码结构'],
  debug: ['报错含义', '定位方向', '修改思路'],
}

const modeIcons = {
  concept: ['fa-book', 'fa-lightbulb', 'fa-key'],
  comparison: ['fa-table', 'fa-scale-balanced', 'fa-circle-exclamation'],
  application: ['fa-magnifying-glass', 'fa-compass', 'fa-triangle-exclamation'],
  code: ['fa-bookmark', 'fa-compass', 'fa-code'],
  debug: ['fa-bug', 'fa-magnifying-glass-location', 'fa-wrench'],
}

const ktLabel = computed(() => props.knowledgeType || 'application')
const currentLabels = computed(() => modeLabels[ktLabel.value] || modeLabels.application)
const currentIcons = computed(() => modeIcons[ktLabel.value] || modeIcons.application)

const canRequestMore = computed(() => hints.value.length < maxLevel && !loading.value && !showRemediation)
const nextLevel = computed(() => hints.value.length + 1)
const nextLabel = computed(() => currentLabels.value[nextLevel.value - 1] || '')

// ---- reset on question change ----
watch(() => props.questionId, () => {
  visible.value = false
  hints.value = []
  showRemediation.value = false
  loading.value = false
})

// ---- API ----
async function requestHint(level) {
  if (loading.value) return
  loading.value = true
  try {
    const res = await practiceApi.getHint({
      question_id: props.questionId,
      question: props.question,
      question_type: props.questionType,
      difficulty: props.difficulty,
      knowledge_tag: props.knowledgeTag,
      knowledge_type: props.knowledgeType,
      student_code: props.studentCode,
      hint_level: level || nextLevel.value,
    })
    if (res.data.code === 200) {
      const data = res.data.data
      if (data.still_no_answer) {
        // Remediation card
        showRemediation.value = true
        hints.value.push(data)
      } else {
        hints.value.push(data)
        emit('hint-used', hints.value.length)
      }
      // Auto-scroll hint list to bottom
      await nextTick()
      if (hintListRef.value) {
        hintListRef.value.scrollTop = hintListRef.value.scrollHeight
      }
    }
  } catch {
    // Silently fail
  } finally {
    loading.value = false
  }
}

function toggleCard() {
  visible.value = !visible.value
  if (visible.value && hints.value.length === 0) {
    requestHint(1)
  }
}

function requestStillDontKnow() {
  requestHint(4)
}

function dismissRemediation() {
  showRemediation.value = false
  visible.value = false
  hints.value = []
  emit('hint-used', 0)
}

function addToReview() {
  // TODO: integrate with review system
  dismissRemediation()
}
</script>

<template>
  <div class="ai-hint-wrapper">
    <!-- Trigger button -->
    <button
      @click="toggleCard"
      :class="[
        'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all',
        visible
          ? 'bg-blue-600 text-white shadow'
          : 'bg-blue-50 text-blue-600 border border-blue-200 hover:bg-blue-100',
      ]"
    >
      <i class="fas fa-robot text-xs"></i>
      AI提示
      <span v-if="hints.length > 0 && !visible" class="bg-white/30 text-white w-5 h-5 rounded-full text-[10px] flex items-center justify-center">
        {{ hints.length }}
      </span>
    </button>

    <!-- Hint card -->
    <div v-if="visible" class="hint-card mt-3 bg-white rounded-2xl border border-blue-100 shadow-lg overflow-hidden animate-fade-in">
      <!-- Header -->
      <div class="bg-gradient-to-r from-blue-600 to-purple-600 px-5 py-3 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fas fa-robot text-white/80 text-sm"></i>
          <span class="text-white text-sm font-bold">AI 学习提示</span>
          <span class="text-white/60 text-[10px]">{{ hints.length }}/{{ maxLevel }} 层</span>
        </div>
        <button @click="visible = false" class="text-white/60 hover:text-white transition">
          <i class="fas fa-times text-xs"></i>
        </button>
      </div>

      <!-- Hint list (scrollable) -->
      <div class="px-4 pt-4 space-y-3 max-h-60 overflow-y-auto" ref="hintListRef">
        <div v-for="(hint, i) in hints" :key="i"
          class="rounded-xl border border-blue-100 bg-blue-50/50 overflow-hidden animate-slide-in">
          <div class="flex items-center gap-2 px-4 py-2.5 bg-blue-50 border-b border-blue-100">
            <i :class="['fas text-sm', currentIcons[i] || 'fa-lightbulb', 'text-blue-500']"></i>
            <span class="text-xs font-bold text-blue-700">
              第{{ hint.hint_level }}层 · {{ hint.title || currentLabels[i] }}
            </span>
          </div>
          <div class="px-4 py-3">
            <p class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{{ hint.content }}</p>
            <p v-if="hint.examples" class="text-xs text-gray-500 mt-2 italic whitespace-pre-wrap">{{ hint.examples }}</p>
            <p v-if="hint.keywords" class="text-xs text-blue-600 mt-2">{{ hint.keywords }}</p>
            <p v-if="hint.common_mistakes" class="text-xs text-amber-600 mt-2">{{ hint.common_mistakes }}</p>
          </div>
        </div>

        <!-- Loading state -->
        <div v-if="loading" class="flex items-center justify-center py-3 text-gray-400">
          <i class="fas fa-spinner fa-spin mr-2"></i>
          <span class="text-xs">AI 思考中...</span>
        </div>

        <!-- Remediation card -->
        <div v-if="showRemediation" class="rounded-xl border-2 border-amber-300 bg-amber-50 overflow-hidden animate-slide-in">
          <div class="flex items-center gap-2 px-4 py-2.5 bg-amber-100 border-b border-amber-200">
            <i class="fas fa-book-medical text-amber-600 text-sm"></i>
            <span class="text-xs font-bold text-amber-700">知识点补救卡片</span>
          </div>
          <div class="px-4 py-3 space-y-3">
            <div v-if="hints[hints.length - 1]?.content" class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
              {{ hints[hints.length - 1].content }}
            </div>
            <div class="flex flex-col gap-2">
              <button
                @click="dismissRemediation"
                class="w-full py-2 rounded-xl text-xs font-medium bg-green-500 text-white hover:bg-green-600 transition"
              >
                <i class="fas fa-check mr-1"></i>我懂了，继续答题
              </button>
              <button
                @click="addToReview"
                class="w-full py-2 rounded-xl text-xs font-medium bg-white text-amber-700 border border-amber-300 hover:bg-amber-50 transition"
              >
                <i class="fas fa-bookmark mr-1"></i>加入错题本，稍后复习
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Expand / actions area (always visible, outside scroll) -->
      <div class="px-4 py-3 border-t border-blue-50 space-y-2">
        <!-- State: no hints yet, waiting for first load -->
        <button
          v-if="hints.length === 0 && !loading && !showRemediation"
          @click="requestHint(1)"
          class="w-full py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600 shadow-md hover:shadow-lg transition flex items-center justify-center gap-2"
        >
          <i class="fas fa-robot"></i>
          获取第1层提示 · {{ currentLabels[0] }}
        </button>

        <!-- State: has hints but not all 3 → show expand button -->
        <button
          v-if="canRequestMore && !loading"
          @click="requestHint(nextLevel)"
          class="w-full py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600 shadow-md hover:shadow-lg transition flex items-center justify-center gap-2"
        >
          <i class="fas fa-unlock-alt"></i>
          展开第{{ nextLevel }}层 · {{ nextLabel }}
          <span class="text-white/60 text-xs font-normal">(共{{ maxLevel }}层)</span>
        </button>

        <!-- State: loading -->
        <div v-if="loading" class="text-center text-xs text-gray-400 py-2">
          <i class="fas fa-spinner fa-spin mr-1"></i>AI 正在生成提示...
        </div>

        <!-- State: all 3 layers loaded → show "still don't know" -->
        <template v-if="hints.length >= maxLevel && !showRemediation && !loading">
          <p class="text-center text-xs text-gray-400 py-1">
            <i class="fas fa-check-circle text-green-400 mr-1"></i>已展开全部 {{ maxLevel }} 层提示
          </p>
          <button
            @click="requestStillDontKnow"
            class="w-full py-2.5 rounded-xl text-sm font-medium bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 transition flex items-center justify-center gap-1.5"
          >
            <i class="fas fa-hand"></i>
            还是不会，查看知识点补救卡片
          </button>
        </template>
      </div>

      <!-- Footer note -->
      <div class="px-5 py-2.5 bg-amber-50 border-t border-amber-100">
        <p class="text-[10px] text-amber-600">
          <i class="fas fa-info-circle mr-1"></i>使用提示后答对，经验奖励会适当减少哦~ 独立思考收获更大！
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}
.animate-slide-in {
  animation: slideIn 0.25s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
