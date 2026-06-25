<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { pickGif, TMP_STATE_DEFAULTS } from '../data/petAnimationMap'
import { listenPetState, listenPetMode, listenPetMessage, listenPetAdventureStart, listenPetAdventureEnd } from '../hooks/usePetCompanion'
import PetMenu from './PetMenu.vue'
import PetAssistantChat from './PetAssistantChat.vue'
import PetMessagePanel from './PetMessagePanel.vue'
import PetSettingsPanel from './PetSettingsPanel.vue'
import PetAiNotesTaskPanel from './PetAiNotesTaskPanel.vue'

const route = useRoute()
const router = useRouter()

// ---- route → default mode ----
const ROUTE_MODE_DEFAULTS = {
  login: 'hidden',
  register: 'hidden',
  dailyPractice: 'simplified',
}

function getDefaultMode() {
  return ROUTE_MODE_DEFAULTS[route.name] || 'active'
}

// ---- position ----
const STORAGE_KEY = 'petPosition'
const SIZE = 130

function loadPos() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const p = JSON.parse(raw)
      if (typeof p.x === 'number' && typeof p.y === 'number') return p
    }
  } catch {}
  return { x: window.innerWidth - SIZE - 20, y: window.innerHeight - SIZE - 40 }
}

const pos = ref(loadPos())
const dragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

// ---- adventure fly-to-center animation ----
const adventureAnimating = ref(false)
const savedPosition = ref(null)
const adventureGif = ref(null)
const adventureScale = ref(1)
const adventureTransition = ref(false)

function savePos() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ x: pos.value.x, y: pos.value.y }))
}

function resetPosition() {
  pos.value = { x: window.innerWidth - SIZE - 20, y: window.innerHeight - SIZE - 40 }
  savePos()
}

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v))
}

function onDragStart(e) {
  if (petMode.value === 'silent') return
  const ev = e.touches ? e.touches[0] : e
  dragging.value = true
  dragOffset.value = { x: ev.clientX - pos.value.x, y: ev.clientY - pos.value.y }
  triggerState('drag', 2000)
}

function onDragMove(e) {
  if (!dragging.value) return
  e.preventDefault()
  const ev = e.touches ? e.touches[0] : e
  pos.value = {
    x: clamp(ev.clientX - dragOffset.value.x, 0, window.innerWidth - SIZE),
    y: clamp(ev.clientY - dragOffset.value.y, 0, window.innerHeight - SIZE),
  }
}

function onDragEnd() {
  if (!dragging.value) return
  dragging.value = false
  savePos()
}

// ---- click tracking for annoyed ----
let clickCount = 0
let clickTimer = null

function handleClick() {
  if (petMode.value === 'silent') return
  clickCount++
  if (clickCount >= 5) {
    triggerState('annoyed', 4000)
    clickCount = 0
    clearTimeout(clickTimer)
    clickTimer = null
    return
  }
  clearTimeout(clickTimer)
  clickTimer = setTimeout(() => { clickCount = 0 }, 1500)
}

// ---- panel management ----
const menuOpen = ref(false)
const activePanel = ref(null) // 'chat' | 'messages' | 'settings' | 'aiNotes' | null

function closeAllPanels() {
  menuOpen.value = false
  activePanel.value = null
}

function toggleMenu() {
  if (petMode.value === 'silent') return
  activePanel.value = null
  menuOpen.value = !menuOpen.value
  triggerState('click', 3000)
}

function openChat() {
  menuOpen.value = false
  activePanel.value = 'chat'
}

function openMessages() {
  menuOpen.value = false
  activePanel.value = 'messages'
}

function openSettings() {
  menuOpen.value = false
  activePanel.value = 'settings'
}

function openAiNotesTasks() {
  menuOpen.value = false
  activePanel.value = 'aiNotes'
}

// ---- settings ----
const interactionsEnabled = ref(
  localStorage.getItem('petInteractions') !== 'false'
)

function toggleInteractions() {
  interactionsEnabled.value = !interactionsEnabled.value
  localStorage.setItem('petInteractions', interactionsEnabled.value)
}

const messagesEnabled = ref(
  localStorage.getItem('petMessagesEnabled') !== 'false'
)

function toggleMessages() {
  messagesEnabled.value = !messagesEnabled.value
  localStorage.setItem('petMessagesEnabled', messagesEnabled.value)
}

// ---- daily practice helpers ----
const dailyHintText = ref('')
const dailyHintLoading = ref(false)

async function requestDailyHint() {
  dailyHintLoading.value = true
  dailyHintText.value = ''
  menuOpen.value = false
  try {
    const { practiceApi } = await import('../api/practice')
    const qId = window.__dailyCurrentQuestionId
    if (!qId) { dailyHintText.value = '当前没有题目信息。'; dailyHintLoading.value = false; return }
    const qInfo = window.__dailyCurrentQuestion || {}
    const res = await practiceApi.getHint({
      question_id: qId,
      question: qInfo.title || '',
      question_type: qInfo.type || '',
      difficulty: qInfo.difficulty || 'medium',
      knowledge_tag: qInfo.knowledge_tag || '',
      knowledge_type: qInfo.knowledge_type || '',
      student_code: '',
      hint_level: 1,
    })
    if (res.data.code === 200) {
      dailyHintText.value = res.data.data.content || '暂无提示。'
    } else {
      dailyHintText.value = '获取提示失败，请稍后再试。'
    }
  } catch {
    dailyHintText.value = '获取提示失败，请稍后再试。'
  }
  dailyHintLoading.value = false
}

const simplProgressMsg = ref('')

function showSimplProgress() {
  const total = window.__dailyTotalQuestions || 0
  const current = window.__dailyCurrentIndex || 0
  simplProgressMsg.value = `当前进度：第 ${current + 1}/${total} 题`
  menuOpen.value = false
  setTimeout(() => { simplProgressMsg.value = '' }, 3000)
}

function handleRest() {
  triggerState('rest')
  menuOpen.value = false
}

function handleHide() {
  hidden.value = true
  menuOpen.value = false
}

function goToAdventure() {
  menuOpen.value = false
  router.push('/adventure')
}

// ---- mode engine ----
const hidden = ref(false)
const petMode = ref(getDefaultMode())
let unlistenState = null
let unlistenMode = null
let unlistenMsg = null

watch(() => route.name, () => {
  petMode.value = getDefaultMode()
})

// ---- state engine ----
const currentState = ref('idle')
const currentGif = ref(pickGif('idle'))
let stateTimer = null

function setState(state) {
  currentState.value = state
  currentGif.value = pickGif(state)
}

function triggerState(state, duration) {
  if (!interactionsEnabled.value && state !== 'idle') return
  if (dragging.value && state !== 'drag') return
  if (petMode.value === 'silent' || petMode.value === 'hidden') return

  if (state === 'idle' || state === 'adventure' || state === 'rest') {
    clearTimeout(stateTimer)
    stateTimer = null
    setState(state)
    return
  }

  if (currentState.value === 'adventure' || currentState.value === 'rest') return

  setState(state)

  const d = duration || TMP_STATE_DEFAULTS[state] || 3000
  clearTimeout(stateTimer)
  stateTimer = setTimeout(() => setState('idle'), d)
}

// ---- message handling ----
const STORAGE_MSG_KEY = 'petMessages'

function handleIncomingMessage(msg) {
  // Save to localStorage
  try {
    const existing = JSON.parse(localStorage.getItem(STORAGE_MSG_KEY) || '[]')
    existing.unshift(msg)
    // Keep max 50 messages
    if (existing.length > 50) existing.length = 50
    localStorage.setItem(STORAGE_MSG_KEY, JSON.stringify(existing))
  } catch {}
  // Trigger pet state if messages enabled
  if (messagesEnabled.value) {
    triggerState('message', 4000)
  }
}

// ---- adventure animation helpers ----
const HAPPY_ADVENTURE_GIFS = ['点赞.gif', '喜欢.gif', '喜欢2.gif', '鼓掌.gif', '举牌100分.gif']

function startAdventureAnimation() {
  // Save current position
  savedPosition.value = { x: pos.value.x, y: pos.value.y }
  adventureAnimating.value = true
  // Pick random happy GIF
  const gif = HAPPY_ADVENTURE_GIFS[Math.floor(Math.random() * HAPPY_ADVENTURE_GIFS.length)]
  adventureGif.value = `/pets/default/${gif}`
  // Move to center
  const cx = (window.innerWidth - SIZE) / 2
  const cy = (window.innerHeight - SIZE) / 2
  adventureTransition.value = true
  pos.value = { x: cx, y: cy }
  adventureScale.value = 1.6
  closeAllPanels()
}

function endAdventureAnimation() {
  adventureTransition.value = true
  adventureScale.value = 1
  adventureGif.value = null
  if (savedPosition.value) {
    pos.value = { x: savedPosition.value.x, y: savedPosition.value.y }
  }
  adventureAnimating.value = false
  savedPosition.value = null
  // After transition, restore normal idle
  setTimeout(() => {
    adventureTransition.value = false
    setState('idle')
  }, 600)
}

let unlistenAdventureStart = null
let unlistenAdventureEnd = null

onMounted(() => {
  unlistenState = listenPetState((state, duration) => {
    triggerState(state, duration)
  })
  unlistenMode = listenPetMode((mode) => {
    petMode.value = mode
  })
  unlistenMsg = listenPetMessage((msg) => {
    handleIncomingMessage(msg)
  })
  unlistenAdventureStart = listenPetAdventureStart(() => {
    startAdventureAnimation()
  })
  unlistenAdventureEnd = listenPetAdventureEnd(() => {
    endAdventureAnimation()
  })
  setState('idle')
})

onUnmounted(() => {
  if (unlistenState) unlistenState()
  if (unlistenMode) unlistenMode()
  if (unlistenMsg) unlistenMsg()
  if (unlistenAdventureStart) unlistenAdventureStart()
  if (unlistenAdventureEnd) unlistenAdventureEnd()
  clearTimeout(stateTimer)
  clearTimeout(clickTimer)
})
</script>

<template>
  <template v-if="petMode !== 'hidden'">
    <!-- Pet body -->
    <div
      v-if="!hidden"
      class="fixed z-[9999] select-none"
      :class="{ 'pointer-events-none': petMode === 'silent' || adventureAnimating }"
      :style="{
        left: pos.x + 'px',
        top: pos.y + 'px',
        transition: adventureTransition ? 'left 0.6s ease-in-out, top 0.6s ease-in-out, transform 0.6s ease-in-out' : 'none',
        transform: 'scale(' + adventureScale + ')',
      }"
      @mousedown="onDragStart"
      @touchstart.prevent="onDragStart"
      @mousemove="onDragMove"
      @touchmove="onDragMove"
      @mouseup="onDragEnd"
      @touchend="onDragEnd"
      @mouseleave="onDragEnd"
      @click="handleClick"
    >
      <div
        class="relative"
        :class="petMode === 'silent' ? 'cursor-default opacity-50 grayscale' : 'cursor-grab active:cursor-grabbing'"
        @click.stop="toggleMenu"
      >
        <!-- Menu -->
        <div
          v-if="menuOpen"
          class="absolute -top-3 left-1/2 -translate-x-1/2 -translate-y-full z-50"
          @click.stop
        >
          <PetMenu
            :mode="petMode"
            :interactions-enabled="interactionsEnabled"
            :messages-enabled="messagesEnabled"
            @toggle-interactions="toggleInteractions"
            @toggle-messages="toggleMessages"
            @reset-position="resetPosition"
            @hide-pet="handleHide"
            @rest-pet="handleRest"
            @open-chat="openChat"
            @open-messages="openMessages"
            @open-settings="openSettings"
            @request-hint="requestDailyHint"
            @show-progress="showSimplProgress"
            @open-ai-notes="openAiNotesTasks"
          />
        </div>

        <!-- Speech bubble: progress info -->
        <div
          v-if="simplProgressMsg"
          class="absolute -top-3 left-1/2 -translate-x-1/2 -translate-y-full bg-blue-600 text-white rounded-lg px-3 py-1.5 text-xs whitespace-nowrap shadow-lg z-50"
          @click.stop
        >
          {{ simplProgressMsg }}
        </div>

        <!-- Speech bubble: daily hint -->
        <div
          v-if="dailyHintText"
          class="absolute left-1/2 -translate-x-1/2 -translate-y-full bg-white rounded-xl shadow-lg border border-purple-200 p-3 w-56 z-50"
          style="top: -8px;"
          @click.stop
        >
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-bold text-purple-600"><i class="fas fa-robot mr-1"></i>AI提示</span>
            <button @click.stop="dailyHintText = ''" class="text-gray-300 hover:text-gray-500"><i class="fas fa-times text-[10px]"></i></button>
          </div>
          <p class="text-xs text-gray-600 leading-relaxed">{{ dailyHintText }}</p>
        </div>

        <!-- Panel containers -->
        <!-- AI Chat -->
        <div
          v-if="activePanel === 'chat'"
          class="absolute z-[10001]"
          style="bottom: 140px; right: 0;"
          @click.stop
        >
          <PetAssistantChat @close="activePanel = null" />
        </div>

        <!-- Messages -->
        <div
          v-if="activePanel === 'messages'"
          class="absolute z-[10001]"
          style="bottom: 140px; right: 0;"
          @click.stop
        >
          <PetMessagePanel @close="activePanel = null" />
        </div>

        <!-- Settings -->
        <div
          v-if="activePanel === 'settings'"
          class="absolute z-[10001]"
          style="bottom: 140px; right: 0;"
          @click.stop
        >
          <PetSettingsPanel
            :interactions-enabled="interactionsEnabled"
            :messages-enabled="messagesEnabled"
            @toggle-interactions="toggleInteractions"
            @toggle-messages="toggleMessages"
            @reset-position="resetPosition"
            @close="activePanel = null"
          />
        </div>

        <!-- AI Notes Tasks -->
        <div
          v-if="activePanel === 'aiNotes'"
          class="absolute z-[10001]"
          style="bottom: 140px; right: 0;"
          @click.stop
        >
          <PetAiNotesTaskPanel @close="activePanel = null" />
        </div>

        <!-- GIF -->
        <img
          :src="adventureGif || currentGif"
          :alt="adventureAnimating ? 'adventure' : currentState"
          class="drop-shadow-lg transition-all duration-300 pointer-events-none"
          :style="{ width: SIZE + 'px', height: SIZE + 'px', objectFit: 'contain' }"
        />
        <div v-if="!adventureAnimating" class="flex justify-center mt-1">
          <span class="text-sm font-semibold select-none bg-white/90 backdrop-blur-sm text-blue-600 px-3.5 py-1.5 rounded-full shadow-sm border border-blue-100/80">有不懂的可以问我</span>
        </div>

        <!-- Circular Adventure button (right side, entertainment) -->
        <div
          v-if="menuOpen"
          class="absolute z-50 animate-bounce-in"
          style="top: 20px; left: calc(100% + 8px);"
          @click.stop
        >
          <button
            @click="goToAdventure"
            class="w-[42px] h-[42px] bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl hover:scale-110 active:scale-95 transition-all duration-200"
            title="宠物探险"
          >
            <i class="fas fa-compass text-white text-base"></i>
          </button>
          <p class="text-[10px] text-gray-400 text-center mt-0.5 whitespace-nowrap">宠物探险</p>
        </div>
      </div>
    </div>

    <!-- Minimized restore button -->
    <button
      v-if="hidden"
      @click="hidden = false; triggerState('idle')"
      class="fixed z-[10000] bottom-5 right-5 w-10 h-10 bg-white rounded-full shadow-lg border border-gray-200 flex items-center justify-center hover:shadow-xl transition text-gray-400 hover:text-blue-600"
      title="显示桌宠"
    >
      <i class="fas fa-paw text-lg"></i>
    </button>
  </template>
</template>

<style scoped>
@keyframes bounce-in {
  0% { opacity: 0; transform: scale(0); }
  60% { opacity: 1; transform: scale(1.15); }
  100% { opacity: 1; transform: scale(1); }
}
.animate-bounce-in {
  animation: bounce-in 0.3s ease-out;
}
</style>
