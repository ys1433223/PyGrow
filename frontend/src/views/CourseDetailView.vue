<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { coursesApi } from '../api/courses'
import { getNotesByCourse, createNote, updateNote, deleteNote, formatSecondsToTime } from '../api/notes'
import { aiNotesApi } from '../api/aiNotes'

const route = useRoute()
const router = useRouter()
const courseId = computed(() => parseInt(route.params.id))

const course = ref(null)
const loading = ref(true)
const activeLesson = ref(null)
const activeLessonIndex = ref(0)
const notes = ref([])
const noteInput = ref('')
const noteTimeText = ref('00:00')
const noteType = ref('重点')
const addingNote = ref(false)
const completedLessons = ref(new Set())
const editingNoteId = ref(null)
const editForm = ref({ time_text: '', note_type: '重点', content: '' })
const copyToast = ref('')
const showTimeHint = ref(false)
let copyToastTimer = null

const NOTE_TYPES = ['重点', '疑问', '总结', '代码', '其他']
const NOTE_TYPE_COLORS = {
  '重点': 'bg-red-100 text-red-600',
  '疑问': 'bg-amber-100 text-amber-600',
  '总结': 'bg-blue-100 text-blue-600',
  '代码': 'bg-green-100 text-green-600',
  '其他': 'bg-gray-100 text-gray-500',
}
const QUICK_TEMPLATES = [
  { label: '自定义输入', value: '' },
  { label: '核心概念', value: '核心概念：' },
  { label: '代码片段', value: '代码关键点：' },
  { label: '易错点', value: '易错点：' },
  { label: '面试考点', value: '面试考点：' },
]

// --- AI Notes state ---
const activeNoteTab = ref('manual') // 'manual' | 'ai'
const aiHasNote = ref(false)
const aiNote = ref(null)
const aiTaskId = ref(null)
const aiTaskStatus = ref('')
const aiTaskProgress = ref(0)
const aiTaskMessage = ref('')
const aiGenerating = ref(false)
const aiError = ref('')
let aiPollTimer = null

onMounted(async () => {
  try {
    const [cRes, nRes] = await Promise.all([
      coursesApi.detail(courseId.value),
      getNotesByCourse(courseId.value),
    ])
    course.value = cRes.data
    notes.value = nRes.data || []
    if (course.value?.lessons?.length > 0) {
      activeLesson.value = course.value.lessons[0]
      activeLessonIndex.value = 0
      // Load AI notes for the first lesson
      loadAiNotesForLesson(activeLesson.value.id)
    }

    // Fetch progress
    try {
      const pRes = await coursesApi.getProgress(courseId.value)
      if (pRes.data?.completed_lessons) {
        completedLessons.value = new Set(pRes.data.completed_lessons)
      }
    } catch {}
  } finally {
    loading.value = false
  }
})

function selectLesson(lesson, index) {
  activeLesson.value = lesson
  activeLessonIndex.value = index
  loadAiNotesForLesson(lesson.id)
}

async function loadAiNotesForLesson(lessonId) {
  aiHasNote.value = false
  aiNote.value = null
  aiError.value = ''
  aiGenerating.value = false
  if (aiPollTimer) { clearInterval(aiPollTimer); aiPollTimer = null }
  try {
    const res = await aiNotesApi.getNotes(courseId.value, lessonId)
    if (res.data.code === 200 && res.data.data?.has_note) {
      aiHasNote.value = true
      aiNote.value = res.data.data
    }
  } catch {}
}

function formatTime(seconds) {
  return formatSecondsToTime(seconds)
}

// ---- Note CRUD ----

async function handleAddNote() {
  if (!noteInput.value.trim()) return
  addingNote.value = true
  try {
    const res = await createNote(
      courseId.value, activeLesson.value.id, noteInput.value,
      noteTimeText.value, noteType.value,
    )
    if (res.data.code === 200) {
      notes.value.push(res.data.data)
      sortNotes()
      noteInput.value = ''
      noteTimeText.value = '00:00'
      noteType.value = '重点'
    } else {
      alert(res.data.message || '添加失败')
    }
  } catch (e) {
    alert(e.message || '添加失败')
  } finally {
    addingNote.value = false
  }
}

async function handleDeleteNote(noteId) {
  if (!confirm('确定要删除这条笔记吗？')) return
  try {
    const res = await deleteNote(noteId)
    if (res.data.code === 200) {
      notes.value = notes.value.filter(n => n.id !== noteId)
    }
  } catch {}
}

function startEditNote(n) {
  editingNoteId.value = n.id
  editForm.value = {
    time_text: n.time_text || formatSecondsToTime(n.timestamp_seconds),
    note_type: n.note_type || '重点',
    content: n.content,
  }
}

function cancelEditNote() {
  editingNoteId.value = null
  editForm.value = { time_text: '', note_type: '重点', content: '' }
}

async function saveEditNote() {
  if (!editForm.value.content.trim()) return
  try {
    const res = await updateNote(
      editingNoteId.value,
      editForm.value.content,
      editForm.value.time_text,
      editForm.value.note_type,
    )
    if (res.data.code === 200) {
      const idx = notes.value.findIndex(n => n.id === editingNoteId.value)
      if (idx >= 0) notes.value[idx] = res.data.data
      sortNotes()
      cancelEditNote()
    } else {
      alert(res.data.message || '保存失败')
    }
  } catch (e) {
    alert(e.message || '保存失败')
  }
}

async function handleCopyTime(n) {
  const text = n.time_text || formatSecondsToTime(n.timestamp_seconds)
  try {
    await navigator.clipboard.writeText(text)
    showCopyToast('时间已复制')
  } catch {
    showCopyToast('复制失败，请手动复制')
  }
}

function handleTimeClick(n) {
  handleCopyTime(n)
}

function showCopyToast(msg) {
  copyToast.value = msg
  if (copyToastTimer) clearTimeout(copyToastTimer)
  copyToastTimer = setTimeout(() => { copyToast.value = '' }, 2000)
}

// ---- Current Time ----

function handleCurrentTime() {
  try {
    const iframe = document.querySelector('.aspect-video iframe')
    if (iframe && iframe.contentWindow) {
      // Try to postMessage to B站 player for current time
      iframe.contentWindow.postMessage({ type: 'getCurrentTime' }, '*')
      // B站 iframe doesn't respond to this — show hint after short delay
      setTimeout(() => {
        if (noteTimeText.value === '00:00') {
          showTimeHint.value = true
          setTimeout(() => { showTimeHint.value = false }, 4000)
        }
      }, 800)
    } else {
      showTimeHint.value = true
      setTimeout(() => { showTimeHint.value = false }, 4000)
    }
  } catch {
    showTimeHint.value = true
    setTimeout(() => { showTimeHint.value = false }, 4000)
  }
}

// Listen for B站 player time response (unlikely but harmless)
onMounted(() => {
  window._bilibiliTimeHandler = (e) => {
    if (e.data && typeof e.data.currentTime === 'number') {
      noteTimeText.value = formatSecondsToTime(Math.floor(e.data.currentTime))
      showTimeHint.value = false
    }
  }
  window.addEventListener('message', window._bilibiliTimeHandler)
})

onUnmounted(() => {
  if (aiPollTimer) clearInterval(aiPollTimer)
  if (copyToastTimer) clearTimeout(copyToastTimer)
  if (window._bilibiliTimeHandler) {
    window.removeEventListener('message', window._bilibiliTimeHandler)
    delete window._bilibiliTimeHandler
  }
})

// ---- Helpers ----

function sortNotes() {
  notes.value.sort((a, b) => (a.timestamp_seconds || 0) - (b.timestamp_seconds || 0))
}

function goToLessonNote(lessonId, timestamp) {
  const lesson = course.value.lessons.find(l => l.id === lessonId)
  if (lesson) {
    activeLesson.value = lesson
    activeLessonIndex.value = course.value.lessons.indexOf(lesson)
    noteTimeText.value = formatSecondsToTime(timestamp)
  }
}

// --- AI Notes functions ---
const statusLabelMap = {
  not_started: '未开始',
  queued: '排队中',
  downloading: '正在获取视频',
  extracting_audio: '正在提取音频',
  transcribing: '正在语音转文字',
  summarizing: '正在生成AI笔记',
  completed: '解析完成',
  failed: '解析失败',
}

async function handleGenerateAINotes() {
  aiError.value = ''
  aiGenerating.value = true
  try {
    const res = await aiNotesApi.generate(courseId.value, activeLesson.value?.id)
    if (res.data.code === 200) {
      const d = res.data.data
      if (d.status === 'completed') {
        // Already had cached notes
        aiHasNote.value = true
        aiNote.value = d.note
        aiGenerating.value = false
        return
      }
      aiTaskId.value = d.task_id
      aiTaskStatus.value = d.status
      aiTaskMessage.value = d.message || statusLabelMap[d.status]
      startPolling()
    }
  } catch (e) {
    aiError.value = '创建任务失败，请稍后重试'
    aiGenerating.value = false
  }
}

function startPolling() {
  if (aiPollTimer) clearInterval(aiPollTimer)
  aiPollTimer = setInterval(async () => {
    try {
      const res = await aiNotesApi.getTaskStatus(aiTaskId.value)
      if (res.data.code === 200) {
        const d = res.data.data
        aiTaskStatus.value = d.status
        aiTaskProgress.value = d.progress
        aiTaskMessage.value = d.message

        if (d.status === 'completed') {
          clearInterval(aiPollTimer)
          aiPollTimer = null
          aiGenerating.value = false
          // Fetch result
          try {
            const rRes = await aiNotesApi.getTaskResult(aiTaskId.value)
            if (rRes.data.code === 200 && rRes.data.data.ready) {
              aiHasNote.value = true
              aiNote.value = rRes.data.data
            }
          } catch {}
        } else if (d.status === 'failed') {
          clearInterval(aiPollTimer)
          aiPollTimer = null
          aiGenerating.value = false
          aiError.value = d.error_message || 'AI 笔记生成失败，请稍后重试。'
        }
      }
    } catch {}
  }, 3000)
}

const lessonNotes = computed(() =>
  activeLesson.value ? notes.value.filter(n => n.lesson_id === activeLesson.value.id) : []
)

const bvid = computed(() => course.value?.bvid || '')
const bilibiliPage = computed(() => activeLesson.value?.bilibili_page || 1)
const embedUrl = computed(() =>
  bvid.value ? `https://player.bilibili.com/player.html?bvid=${bvid.value}&page=${bilibiliPage.value}` : ''
)
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <AppHeader />
    <PageLoader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <div v-if="loading" class="flex justify-center py-20">
        <div class="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full"></div>
      </div>

      <template v-else-if="course">
        <!-- Back button -->
        <button @click="router.push('/courses')" class="text-sm text-gray-500 hover:text-blue-600 mb-4 flex items-center space-x-1">
          <i class="fas fa-arrow-left text-xs"></i>
          <span>返回课程中心</span>
        </button>

        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <!-- Sidebar: lesson list -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden max-h-[80vh] flex flex-col">
            <div class="px-4 py-3 border-b border-gray-100 bg-gray-50">
              <h2 class="font-bold text-gray-800 text-sm">{{ course.title }}</h2>
              <p class="text-xs text-gray-400">{{ course.lessons?.length || 0 }} 课时</p>
            </div>
            <div class="overflow-y-auto flex-1">
              <button
                v-for="(lesson, i) in course.lessons"
                :key="lesson.id"
                @click="selectLesson(lesson, i)"
                :class="[
                  activeLessonIndex === i ? 'bg-blue-50 border-l-2 border-blue-600 text-blue-700' : 'hover:bg-gray-50 text-gray-600',
                  'w-full text-left px-4 py-3 text-sm border-b border-gray-50 transition'
                ]"
              >
                <div class="flex items-center space-x-2">
                  <span :class="{ 'text-blue-600': activeLessonIndex === i }" class="text-xs font-mono w-8">{{ i + 1 }}</span>
                  <span class="flex-1 truncate">{{ lesson.title }}</span>
                  <span v-if="completedLessons.has(lesson.id)" class="text-green-500 text-xs"><i class="fas fa-check-circle"></i></span>
                </div>
              </button>
            </div>
          </div>

          <!-- Main: video + notes -->
          <div class="lg:col-span-3 space-y-6">
            <!-- Video player -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div v-if="activeLesson" class="px-4 py-3 border-b border-gray-100 bg-gray-50">
                <h3 class="font-bold text-gray-800">{{ activeLesson.title }}</h3>
                <p class="text-xs text-gray-400">{{ activeLesson.chapter }} · {{ activeLesson.duration }}</p>
              </div>
              <div v-if="embedUrl" class="aspect-video bg-black">
                <iframe :src="embedUrl" class="w-full h-full" frameborder="0" allowfullscreen></iframe>
              </div>
              <div v-else class="aspect-video bg-gray-900 flex items-center justify-center text-gray-500">
                暂无视频资源
              </div>
            </div>

            <!-- Notes panel with tabs -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <!-- Tab buttons -->
              <div class="flex border-b border-gray-100">
                <button @click="activeNoteTab = 'manual'" :class="['flex-1 py-3 text-sm font-medium transition', activeNoteTab === 'manual' ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' : 'text-gray-400 hover:text-gray-600']">
                  <i class="fas fa-pen mr-1.5"></i>时间点笔记
                </button>
                <button @click="activeNoteTab = 'ai'" :class="['flex-1 py-3 text-sm font-medium transition', activeNoteTab === 'ai' ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50/50' : 'text-gray-400 hover:text-gray-600']">
                  <i class="fas fa-robot mr-1.5"></i>AI 智能笔记
                </button>
              </div>

              <!-- Manual notes tab -->
              <div v-if="activeNoteTab === 'manual'" class="p-6">
                <!-- Add / Edit note form -->
                <div class="bg-gray-50 rounded-xl p-4 mb-4 space-y-3">
                  <!-- Row 1: time input + "当前时间" -->
                  <div class="flex items-center gap-3">
                    <div class="flex items-center gap-1.5">
                      <input
                        v-model="noteTimeText"
                        type="text"
                        placeholder="00:00"
                        maxlength="8"
                        class="w-20 text-center border border-gray-200 rounded-lg px-2 py-2 text-sm font-mono outline-none focus:border-blue-400 bg-white"
                      />
                      <button
                        @click="handleCurrentTime"
                        class="text-xs text-blue-500 hover:text-blue-600 transition whitespace-nowrap"
                        title="尝试读取播放器当前时间"
                      >
                        <i class="fas fa-clock mr-0.5"></i>当前时间
                      </button>
                    </div>
                    <!-- Note type -->
                    <select v-model="noteType"
                      class="border border-gray-200 rounded-lg px-2 py-2 text-xs outline-none focus:border-blue-400 bg-white text-gray-600">
                      <option v-for="t in NOTE_TYPES" :key="t" :value="t">{{ t }}</option>
                    </select>
                    <!-- Quick template -->
                    <select
                      @change="(e) => { if (e.target.value) noteInput = (noteInput ? noteInput + '\n' : '') + e.target.value; e.target.value = '' }"
                      class="border border-gray-200 rounded-lg px-2 py-2 text-xs outline-none focus:border-blue-400 bg-white text-gray-400">
                      <option value="">模板</option>
                      <option v-for="tpl in QUICK_TEMPLATES.filter(t => t.value)" :key="tpl.label" :value="tpl.value">{{ tpl.label }}</option>
                    </select>
                  </div>
                  <!-- Row 2: content + add button -->
                  <div class="flex items-start gap-3">
                    <textarea
                      v-model="noteInput"
                      class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none bg-white"
                      rows="2"
                      placeholder="记录当前视频时间点的笔记..."
                    ></textarea>
                    <button
                      @click="handleAddNote"
                      :disabled="addingNote || !noteInput.trim()"
                      class="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-all flex-shrink-0"
                    >{{ addingNote ? '...' : '添加' }}</button>
                  </div>
                  <!-- Time hint -->
                  <p v-if="showTimeHint" class="text-xs text-amber-500 flex items-center gap-1">
                    <i class="fas fa-info-circle"></i>当前播放器暂不支持自动读取时间，请手动填写时间。
                  </p>
                </div>

                <!-- Current lesson notes -->
                <div v-if="lessonNotes.length > 0" class="space-y-2.5">
                  <div v-for="n in lessonNotes" :key="n.id"
                    class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition">

                    <!-- View mode -->
                    <template v-if="editingNoteId !== n.id">
                      <div class="p-3.5">
                        <div class="flex items-start justify-between gap-2 mb-2">
                          <div class="flex items-center gap-2">
                            <span @click="handleTimeClick(n)"
                              class="text-xs font-mono bg-blue-100 text-blue-700 px-2 py-0.5 rounded cursor-pointer hover:bg-blue-200 transition flex-shrink-0"
                              title="点击复制时间">
                              <i class="fas fa-play text-[8px] mr-0.5"></i>{{ n.time_text || formatTime(n.timestamp_seconds) }}
                            </span>
                            <span :class="['text-[10px] font-medium px-1.5 py-0.5 rounded-full', NOTE_TYPE_COLORS[n.note_type] || NOTE_TYPE_COLORS['其他']]">
                              {{ n.note_type || '重点' }}
                            </span>
                          </div>
                          <div class="flex items-center gap-1">
                            <button @click="startEditNote(n)" class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition" title="编辑">
                              <i class="fas fa-pen text-xs"></i>
                            </button>
                            <button @click="handleCopyTime(n)" class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 hover:text-green-500 hover:bg-green-50 transition" title="复制时间">
                              <i class="far fa-copy text-xs"></i>
                            </button>
                            <button @click="handleDeleteNote(n.id)" class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition" title="删除">
                              <i class="fas fa-trash text-xs"></i>
                            </button>
                          </div>
                        </div>
                        <p class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{{ n.content }}</p>
                        <p class="text-[10px] text-gray-400 mt-2">{{ n.created_at?.slice(0, 16).replace('T', ' ') }}</p>
                      </div>
                    </template>

                    <!-- Edit mode -->
                    <template v-else>
                      <div class="p-3.5 bg-amber-50/30 space-y-2.5">
                        <div class="flex items-center gap-2">
                          <input v-model="editForm.time_text"
                            type="text" maxlength="8" placeholder="00:00"
                            class="w-20 text-center border border-gray-200 rounded-lg px-2 py-1.5 text-xs font-mono outline-none focus:border-blue-400 bg-white" />
                          <select v-model="editForm.note_type"
                            class="border border-gray-200 rounded-lg px-2 py-1.5 text-xs outline-none focus:border-blue-400 bg-white text-gray-600">
                            <option v-for="t in NOTE_TYPES" :key="t" :value="t">{{ t }}</option>
                          </select>
                        </div>
                        <textarea v-model="editForm.content"
                          class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none bg-white"
                          rows="2"></textarea>
                        <div class="flex items-center gap-2">
                          <button @click="saveEditNote"
                            class="px-4 py-1.5 rounded-lg text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 transition">保存</button>
                          <button @click="cancelEditNote"
                            class="px-4 py-1.5 rounded-lg text-xs font-medium bg-white text-gray-500 border border-gray-200 hover:bg-gray-50 transition">取消</button>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>

                <!-- All course notes -->
                <div v-if="notes.length > 0 && lessonNotes.length !== notes.length" class="mt-6">
                  <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">全部笔记 <span class="text-gray-300 font-normal">({{ notes.length }})</span></h4>
                  <div class="space-y-2">
                    <div v-for="n in notes" :key="n.id"
                      @click="goToLessonNote(n.lesson_id, n.timestamp_seconds)"
                      class="flex items-start gap-3 p-3 bg-gray-50 rounded-xl cursor-pointer hover:bg-blue-50 transition group">
                      <span class="text-xs font-mono bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded flex-shrink-0">{{ n.time_text || formatTime(n.timestamp_seconds) }}</span>
                      <span :class="['text-[10px] font-medium px-1.5 py-0.5 rounded-full flex-shrink-0', NOTE_TYPE_COLORS[n.note_type] || NOTE_TYPE_COLORS['其他']]">{{ n.note_type || '重点' }}</span>
                      <p class="text-sm text-gray-700 flex-1 line-clamp-1">{{ n.content }}</p>
                      <span class="text-[10px] text-gray-400 flex-shrink-0 hidden sm:inline">{{ n.created_at?.slice(5, 10) }}</span>
                      <i class="fas fa-chevron-right text-gray-300 text-xs flex-shrink-0 opacity-0 group-hover:opacity-100 transition"></i>
                    </div>
                  </div>
                </div>

                <p v-if="notes.length === 0" class="text-sm text-gray-400 text-center py-12">
                  <i class="far fa-sticky-note text-3xl text-gray-300 block mb-3"></i>
                  暂无笔记，添加第一条吧。
                </p>
              </div>

              <!-- AI Notes tab -->
              <div v-if="activeNoteTab === 'ai'" class="p-6">
                <!-- Has existing AI note -->
                <template v-if="aiHasNote && aiNote">
                  <div class="space-y-5">
                    <!-- Summary -->
                    <div>
                      <h4 class="text-sm font-bold text-gray-700 mb-2"><i class="fas fa-file-alt text-purple-500 mr-1.5"></i>课程简介</h4>
                      <p class="text-sm text-gray-600 leading-relaxed bg-purple-50 rounded-xl p-4">{{ aiNote.summary }}</p>
                    </div>
                    <!-- Highlights -->
                    <div>
                      <h4 class="text-sm font-bold text-gray-700 mb-2"><i class="fas fa-star text-amber-500 mr-1.5"></i>视频看点</h4>
                      <div class="grid grid-cols-2 gap-2">
                        <div v-for="(h, i) in aiNote.highlights" :key="i" class="flex items-center gap-2 bg-amber-50 rounded-xl px-3 py-2.5">
                          <span class="text-xs font-mono bg-amber-200 text-amber-700 px-1.5 py-0.5 rounded">{{ h.time }}</span>
                          <span class="text-sm text-gray-700">{{ h.title }}</span>
                        </div>
                      </div>
                    </div>
                    <!-- Notes -->
                    <div>
                      <h4 class="text-sm font-bold text-gray-700 mb-2"><i class="fas fa-list-ul text-blue-500 mr-1.5"></i>知识点笔记</h4>
                      <ul class="space-y-1.5">
                        <li v-for="(n, i) in aiNote.notes" :key="i" class="flex items-start gap-2 text-sm text-gray-600">
                          <span class="w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">{{ i + 1 }}</span>
                          {{ n }}
                        </li>
                      </ul>
                    </div>
                    <!-- Errors -->
                    <div>
                      <h4 class="text-sm font-bold text-gray-700 mb-2"><i class="fas fa-exclamation-circle text-red-500 mr-1.5"></i>易错点</h4>
                      <ul class="space-y-1.5">
                        <li v-for="(e, i) in aiNote.errors" :key="i" class="flex items-start gap-2 text-sm text-red-700 bg-red-50 rounded-xl px-3 py-2">
                          <i class="fas fa-times-circle text-red-400 text-xs mt-0.5"></i>{{ e }}
                        </li>
                      </ul>
                    </div>
                    <!-- Suggestions -->
                    <div>
                      <h4 class="text-sm font-bold text-gray-700 mb-2"><i class="fas fa-lightbulb text-green-500 mr-1.5"></i>学习建议</h4>
                      <ul class="space-y-1.5">
                        <li v-for="(s, i) in aiNote.suggestions" :key="i" class="flex items-start gap-2 text-sm text-gray-600">
                          <span class="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">{{ i + 1 }}</span>
                          {{ s }}
                        </li>
                      </ul>
                    </div>
                    <!-- Transcript -->
                    <div v-if="aiNote.transcript">
                      <h4 class="text-sm font-bold text-gray-700 mb-2"><i class="fas fa-align-left text-gray-500 mr-1.5"></i>文稿</h4>
                      <p class="text-sm text-gray-500 leading-relaxed bg-gray-50 rounded-xl p-4 max-h-48 overflow-y-auto">{{ aiNote.transcript }}</p>
                    </div>
                  </div>
                </template>

                <!-- Generating progress -->
                <template v-else-if="aiGenerating">
                  <div class="text-center py-8">
                    <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-100 flex items-center justify-center">
                      <i class="fas fa-robot text-purple-500 text-2xl" :class="{ 'animate-bounce': aiTaskStatus !== 'failed' }"></i>
                    </div>
                    <p class="text-sm font-medium text-gray-700 mb-2">AI 正在为你解析课程视频</p>
                    <p class="text-xs text-gray-400 mb-4">预计需要 1-3 分钟，请稍后。</p>
                    <!-- Progress bar -->
                    <div class="max-w-xs mx-auto">
                      <div class="flex justify-between text-xs text-gray-400 mb-1.5">
                        <span>{{ statusLabelMap[aiTaskStatus] || aiTaskStatus }}</span>
                        <span>{{ aiTaskProgress }}%</span>
                      </div>
                      <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div class="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-700" :style="{ width: aiTaskProgress + '%' }"></div>
                      </div>
                      <p v-if="aiTaskMessage" class="text-xs text-gray-400 mt-2">{{ aiTaskMessage }}</p>
                    </div>
                  </div>
                </template>

                <!-- Generate button or no-note state -->
                <template v-else>
                  <div class="text-center py-10">
                    <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-purple-50 flex items-center justify-center">
                      <i class="fas fa-robot text-purple-400 text-3xl"></i>
                    </div>
                    <h4 class="font-bold text-gray-700 mb-2">AI 智能笔记</h4>
                    <p class="text-sm text-gray-400 mb-6 max-w-sm mx-auto">AI 将自动解析课程视频，生成课程简介、知识点笔记、视频看点、易错提醒和学习建议。</p>
                    <button
                      @click="handleGenerateAINotes"
                      :disabled="aiGenerating"
                      class="px-6 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full text-sm font-bold hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-50"
                    >
                      <i class="fas fa-magic mr-1.5"></i>生成 AI 笔记
                    </button>
                    <p v-if="aiError" class="text-xs text-red-500 mt-3">{{ aiError }}</p>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>

    <AppFooter />

    <!-- Copy toast -->
    <Teleport to="body">
      <div v-if="copyToast" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-gray-800 text-white text-sm px-5 py-2.5 rounded-xl shadow-lg animate-fade-in">
        <i class="fas fa-check text-green-400 mr-2"></i>{{ copyToast }}
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.animate-fade-in {
  animation: fadeInUp 0.25s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateX(-50%) translateY(8px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}
</style>
