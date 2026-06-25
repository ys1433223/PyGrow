<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { coursesApi } from '../api/courses'
import { getNotesByCourse, createNote, deleteNote } from '../api/notes'
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
const noteSeconds = ref(0)
const addingNote = ref(false)
const completedLessons = ref(new Set())

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

onUnmounted(() => { if (aiPollTimer) clearInterval(aiPollTimer) })

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
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

async function handleAddNote() {
  if (!noteInput.value.trim()) return
  addingNote.value = true
  try {
    const res = await createNote(courseId.value, activeLesson.value.id, noteInput.value, noteSeconds.value)
    notes.value.unshift(res.data)
    noteInput.value = ''
  } finally {
    addingNote.value = false
  }
}

async function handleDeleteNote(noteId) {
  await deleteNote(noteId)
  notes.value = notes.value.filter(n => n.id !== noteId)
}

function goToLessonNote(lessonId, timestamp) {
  const lesson = course.value.lessons.find(l => l.id === lessonId)
  if (lesson) {
    activeLesson.value = lesson
    activeLessonIndex.value = course.value.lessons.indexOf(lesson)
    noteSeconds.value = timestamp
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
                <!-- Add note -->
                <div class="flex items-start space-x-3 mb-4">
                  <input
                    v-model.number="noteSeconds"
                    type="number" min="0" placeholder="秒"
                    class="w-20 text-center border border-gray-200 rounded-lg px-2 py-2 text-sm outline-none focus:border-blue-400"
                  />
                  <textarea
                    v-model="noteInput"
                    class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none"
                    rows="2"
                    placeholder="记录当前视频时间点的笔记..."
                  ></textarea>
                  <button
                    @click="handleAddNote"
                    :disabled="addingNote || !noteInput.trim()"
                    class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition-all flex-shrink-0"
                  >{{ addingNote ? '...' : '添加' }}</button>
                </div>

                <!-- Current lesson notes -->
                <div v-if="lessonNotes.length > 0" class="space-y-2">
                  <div v-for="n in lessonNotes" :key="n.id" class="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
                    <div class="flex items-start space-x-3">
                      <span @click="noteSeconds = n.timestamp_seconds" class="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded cursor-pointer hover:bg-blue-200 flex-shrink-0">{{ formatTime(n.timestamp_seconds) }}</span>
                      <p class="text-sm text-gray-700">{{ n.content }}</p>
                    </div>
                    <button @click="handleDeleteNote(n.id)" class="text-gray-400 hover:text-red-500 text-xs flex-shrink-0 ml-2"><i class="fas fa-trash"></i></button>
                  </div>
                </div>

                <!-- All course notes -->
                <div v-if="notes.length > 0 && lessonNotes.length !== notes.length" class="mt-6">
                  <h4 class="text-sm font-medium text-gray-500 mb-3">全部笔记（点击跳转对应课时）</h4>
                  <div class="space-y-2">
                    <div v-for="n in notes" :key="n.id" @click="goToLessonNote(n.lesson_id, n.timestamp_seconds)" class="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-blue-50 transition">
                      <span class="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">{{ formatTime(n.timestamp_seconds) }}</span>
                      <p class="text-sm text-gray-700 flex-1">{{ n.content }}</p>
                      <span class="text-xs text-gray-400">{{ n.created_at?.slice(0, 10) }}</span>
                    </div>
                  </div>
                </div>

                <p v-if="notes.length === 0" class="text-sm text-gray-400 text-center py-8">暂无笔记，在视频播放过程中添加笔记吧</p>
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
  </div>
</template>
