<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { courseLevels } from '../data/courseData.js'
import { resourceManifest } from '../data/resourceData.js'
import { reviewsApi } from '../api/reviews'
import { favoritesApi } from '../api/favorites'
import { coursesApi } from '../api/courses'
import { aiNotesApi } from '../api/aiNotes'
import { triggerPetState } from '../hooks/usePetCompanion'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const levels = courseLevels
const activeLevel = ref('初级')
const expandedChapters = ref(new Set())
const expandedSections = ref(new Set())
const selectedLesson = ref(null)
const selectedChapter = ref(null)

// Reviews state
const reviews = ref([])
const reviewCount = ref(0)
const avgRating = ref(0)
const myRating = ref(0)
const myReviewContent = ref('')
const submittingReview = ref(false)

// Timestamp notes (localStorage)
const timestampNotes = ref([])
const noteTimestamp = ref('')
const noteContent = ref('')

function loadTimestampNotes() {
  const key = `ts-notes-${activeLevel.value}`
  try {
    timestampNotes.value = JSON.parse(localStorage.getItem(key) || '[]')
  } catch { timestampNotes.value = [] }
}

function saveTimestampNotes() {
  const key = `ts-notes-${activeLevel.value}`
  localStorage.setItem(key, JSON.stringify(timestampNotes.value))
}

function addTimestampNote() {
  const ts = noteTimestamp.value.trim()
  const text = noteContent.value.trim()
  if (!text) return
  const secs = parseTimestamp(ts)
  timestampNotes.value.unshift({
    id: Date.now(),
    timestamp: ts,
    seconds: secs,
    content: text,
    lessonTitle: selectedLesson.value?.title || '',
    chapterTitle: selectedChapter.value?.title || '',
    createdAt: new Date().toISOString(),
  })
  saveTimestampNotes()
  noteTimestamp.value = ''
  noteContent.value = ''
}

function parseTimestamp(val) {
  if (!val) return 0
  const parts = val.split(':')
  if (parts.length === 3) return +parts[0] * 3600 + +parts[1] * 60 + +parts[2]
  if (parts.length === 2) return +parts[0] * 60 + +parts[1]
  return parseInt(val) || 0
}

function deleteTimestampNote(id) {
  timestampNotes.value = timestampNotes.value.filter(n => n.id !== id)
  saveTimestampNotes()
}

// Computed
const currentCourse = computed(() => levels.find(l => l.level === activeLevel.value))
const chapters = computed(() => currentCourse.value?.chapters || [])

const videoUrl = computed(() => {
  if (!selectedLesson.value || !selectedChapter.value?.bvid) return ''
  return `https://player.bilibili.com/player.html?bvid=${selectedChapter.value.bvid}&page=${selectedLesson.value.page}&autoplay=1&high_quality=1`
})

const navInfo = computed(() => {
  if (!selectedLesson.value || !selectedChapter.value) return { prev: null, next: null, chapterIdx: 0, lessonIdxInChapter: 0, totalInChapter: 0 }
  const chs = chapters.value
  let prev = null, next = null, found = false
  let chIdx = 0, lessonIdx = 0, total = 0
  for (let ci = 0; ci < chs.length; ci++) {
    const ch = chs[ci]
    for (let si = 0; si < ch.sections.length; si++) {
      const sec = ch.sections[si]
      for (let li = 0; li < sec.lessons.length; li++) {
        const l = sec.lessons[li]
        if (l.page === selectedLesson.value.page && ch.num === selectedChapter.value.num) {
          found = true; chIdx = ci; lessonIdx = li
          for (let sj = 0; sj < ch.sections.length; sj++) total += ch.sections[sj].lessons.length
        } else if (!found) prev = { chapter: ch, lesson: l }
        else if (found && !next) next = { chapter: ch, lesson: l }
      }
    }
  }
  return { prev, next, chapterIdx: chIdx, lessonIdxInChapter: lessonIdx, totalInChapter: total }
})

// Actions
function selectChapter(chapter) {
  selectedChapter.value = chapter
  const fl = chapter.sections[0]?.lessons[0]
  if (fl) selectedLesson.value = fl
  loadReviews()
}

function selectLesson(chapter, section, lesson) {
  const chapterChanged = selectedChapter.value?.num !== chapter.num
  selectedChapter.value = chapter
  selectedLesson.value = lesson
  // Close AI notes panel and reset state when switching lessons
  showAiNotesPanel.value = false
  aiHasNote.value = false
  aiNote.value = null
  aiGenerating.value = false
  aiError.value = ''
  if (aiPollTimer) { clearInterval(aiPollTimer); aiPollTimer = null }
  triggerPetState('work', 4000)
  if (chapterChanged) loadReviews()
}

function toggleChapter(num) {
  const key = `ch-${activeLevel.value}-${num}`
  const s = new Set(expandedChapters.value)
  if (s.has(key)) s.delete(key); else s.add(key)
  expandedChapters.value = s
}

function toggleSection(chapterNum, secIdx) {
  const key = `sec-${activeLevel.value}-${chapterNum}-${secIdx}`
  const s = new Set(expandedSections.value)
  if (s.has(key)) s.delete(key); else s.add(key)
  expandedSections.value = s
}

function isChapterExpanded(num) { return expandedChapters.value.has(`ch-${activeLevel.value}-${num}`) }
function isSectionExpanded(chapterNum, secIdx) { return expandedSections.value.has(`sec-${activeLevel.value}-${chapterNum}-${secIdx}`) }

function switchLevel(level) {
  activeLevel.value = level
  selectedLesson.value = null
  selectedChapter.value = null
  const firstCh = levels.find(l => l.level === level)?.chapters?.[0]
  if (firstCh) expandedChapters.value = new Set([`ch-${level}-${firstCh.num}`])
  loadTimestampNotes()
  loadReviews()
}

function goToLesson(chapter, lesson) {
  selectedChapter.value = chapter
  selectedLesson.value = lesson
  const s = new Set(expandedChapters.value)
  s.add(`ch-${activeLevel.value}-${chapter.num}`)
  expandedChapters.value = s
}

function goPrev() { if (navInfo.value.prev) goToLesson(navInfo.value.prev.chapter, navInfo.value.prev.lesson) }
function goNext() { if (navInfo.value.next) goToLesson(navInfo.value.next.chapter, navInfo.value.next.lesson) }

function goPractice() {
  if (!selectedChapter.value || !selectedLesson.value) return
  const tag = selectedLesson.value.title || ''
  router.push({ path: '/practice', query: { stage: activeLevel.value, chapter: selectedChapter.value.num, tag } })
}

// Completed tracking
const completedLessons = ref(new Set())
function markCompleted() {
  if (!selectedLesson.value) return
  const key = `${activeLevel.value}-${selectedChapter.value.num}-${selectedLesson.value.page}`
  const s = new Set(completedLessons.value)
  if (s.has(key)) s.delete(key); else s.add(key)
  completedLessons.value = s
  localStorage.setItem('completedLessons', JSON.stringify([...completedLessons.value]))
}
function isCompleted(chNum, page) { return completedLessons.value.has(`${activeLevel.value}-${chNum}-${page}`) }

// Chapter resources
const chapterResources = computed(() => {
  if (!selectedChapter.value) return null
  const chNum = selectedChapter.value.num
  return resourceManifest.find(r => r.level === activeLevel.value && r.chapter === chNum) || null
})

const expandedResourceTypes = ref(new Set())
function toggleResourceType(type) {
  const s = new Set(expandedResourceTypes.value)
  if (s.has(type)) s.delete(type); else s.add(type)
  expandedResourceTypes.value = s
}
function isResourceExpanded(type) { return expandedResourceTypes.value.has(type) }

// Favorites
const favoriteIds = ref(new Set())
async function loadFavorites() {
  if (!auth.isLoggedIn) return
  try {
    const res = await favoritesApi.list('course')
    if (res.data.code === 200) {
      favoriteIds.value = new Set(res.data.data.map(f => f.item_id))
    }
  } catch { /* ignore */ }
}
const isCurrentFavorited = computed(() => {
  if (!selectedChapter.value) return false
  return favoriteIds.value.has(`${activeLevel.value}-${selectedChapter.value.num}`)
})
async function toggleFavorite() {
  if (!auth.isLoggedIn) { if (window.__openLoginPrompt) window.__openLoginPrompt(); return }
  if (!selectedChapter.value) return
  const itemId = `${activeLevel.value}-${selectedChapter.value.num}`
  const title = `第${selectedChapter.value.num}章 ${selectedChapter.value.title}`
  try {
    if (isCurrentFavorited.value) {
      await favoritesApi.removeByItem('course', itemId)
      const s = new Set(favoriteIds.value); s.delete(itemId); favoriteIds.value = s
    } else {
      await favoritesApi.add('course', itemId, title)
      const s = new Set(favoriteIds.value); s.add(itemId); favoriteIds.value = s
    }
  } catch (e) { console.error(e) }
}

// AI Notes — real integration
const showAiNotesPanel = ref(false)
const aiHasNote = ref(false)
const aiNote = ref(null)
const aiTaskId = ref(null)
const aiTaskStatus = ref('')
const aiTaskProgress = ref(0)
const aiTaskMessage = ref('')
const aiGenerating = ref(false)
const aiError = ref('')
const aiCourseId = ref(null)
const aiLessonId = ref(null)
let aiPollTimer = null

const statusLabelMap = {
  not_started: '未开始', queued: '排队中', downloading: '正在获取视频',
  extracting_audio: '正在提取音频', transcribing: '正在语音转文字',
  summarizing: '正在生成AI笔记', completed: '解析完成', failed: '解析失败',
}

onUnmounted(() => { if (aiPollTimer) clearInterval(aiPollTimer) })

async function resolveBackendIds() {
  if (!aiCourseId.value) {
    try {
      const res = await coursesApi.list()
      const courses = res.data?.data || res.data || []
      // Match by index: local courseLevels order matches backend sort_order
      const idx = levels.findIndex(l => l.level === activeLevel.value)
      if (idx >= 0 && idx < courses.length) {
        aiCourseId.value = courses[idx].id
      } else if (courses.length > 0) {
        // Fallback to first course
        aiCourseId.value = courses[0].id
      }
    } catch (e) {
      console.error('Failed to resolve course ID:', e)
      // Last resort: default to course 1
      aiCourseId.value = 1
    }
  }

  aiLessonId.value = null
  if (selectedLesson.value && selectedChapter.value) {
    try {
      const res = await coursesApi.detail(aiCourseId.value)
      const course = res.data?.data || res.data
      const lessons = course?.lessons || []
      // Match by chapter title + page + lesson title (pages reset per chapter; some chapters share pages)
      const match = lessons.find(l =>
        l.bilibili_page === selectedLesson.value.page &&
        l.chapter === selectedChapter.value.title &&
        l.title === selectedLesson.value.title
      )
      if (match) {
        aiLessonId.value = match.id
      } else {
        // Fallback: chapter + page (tolerate slight title mismatch)
        const chPageMatch = lessons.find(l =>
          l.bilibili_page === selectedLesson.value.page &&
          l.chapter === selectedChapter.value.title
        )
        if (chPageMatch) aiLessonId.value = chPageMatch.id
      }
    } catch (e) {
      console.error('Failed to resolve lesson ID:', e)
    }
  }
  return true
}

async function toggleAiNotes() {
  showAiNotesPanel.value = !showAiNotesPanel.value
  if (showAiNotesPanel.value) {
    await resolveBackendIds()
    if (aiCourseId.value) {
      loadAiNotesForLesson()
    }
  }
}

async function loadAiNotesForLesson() {
  aiHasNote.value = false
  aiNote.value = null
  aiError.value = ''
  if (!aiCourseId.value) return
  if (!aiLessonId.value) return  // Can't determine which lesson; don't fetch wrong notes
  try {
    const res = await aiNotesApi.getNotes(aiCourseId.value, aiLessonId.value)
    if (res.data.code === 200 && res.data.data?.has_note) {
      aiHasNote.value = true
      aiNote.value = res.data.data
    }
  } catch {}
}

async function handleGenerateAINotes() {
  if (!aiCourseId.value) {
    const ok = await resolveBackendIds()
    if (!ok || !aiCourseId.value) {
      aiError.value = '无法确定课程信息，请先选择课程'
      return
    }
  }
  if (!aiLessonId.value) {
    aiError.value = '无法确定课时信息，请先选择具体课时'
    return
  }
  aiError.value = ''
  aiGenerating.value = true
  triggerPetState('thinking')
  try {
    const bvid = selectedChapter.value?.bvid || ''
    const bp = selectedLesson.value?.page || 1
    const res = await aiNotesApi.generate(aiCourseId.value, aiLessonId.value, bvid, bp)
    if (res.data.code === 200) {
      const d = res.data.data
      if (d.status === 'completed') {
        aiHasNote.value = true
        aiNote.value = d.note
        aiGenerating.value = false
        return
      }
      aiTaskId.value = d.task_id
      aiTaskStatus.value = d.status
      aiTaskMessage.value = d.message || statusLabelMap[d.status]
      // Save to localStorage for floating panel
      saveTaskToFloat(d.task_id, aiCourseId.value, aiLessonId.value)
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
        updateTaskInFloat(aiTaskId.value, d.status, d.progress, d.message)
        if (d.status === 'completed') {
          clearInterval(aiPollTimer)
          aiPollTimer = null
          aiGenerating.value = false
          triggerPetState('happy', 4000)
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
          triggerPetState('wrong', 4000)
          aiError.value = d.error_message || 'AI 笔记生成失败，请稍后重试。'
        }
      }
    } catch {}
  }, 3000)
}

// Floating task panel helpers
function saveTaskToFloat(taskId, courseId, lessonId) {
  try {
    const tasks = JSON.parse(localStorage.getItem('ai_tasks') || '[]')
    tasks.push({
      task_id: taskId, course_id: courseId, lesson_id: lessonId,
      status: 'queued', progress: 0, message: '排队中',
      course_title: currentCourse.value?.name || '',
      lesson_title: selectedLesson.value?.title || '',
      level: activeLevel.value,
      chapter: selectedChapter.value?.num || 1,
      page: selectedLesson.value?.page || 1,
      created_at: Date.now(),
    })
    localStorage.setItem('ai_tasks', JSON.stringify(tasks))
  } catch {}
}

function updateTaskInFloat(taskId, status, progress, message) {
  try {
    const tasks = JSON.parse(localStorage.getItem('ai_tasks') || '[]')
    const idx = tasks.findIndex(t => t.task_id === taskId)
    if (idx >= 0) {
      tasks[idx].status = status
      tasks[idx].progress = progress
      tasks[idx].message = message
      localStorage.setItem('ai_tasks', JSON.stringify(tasks))
    }
  } catch {}
}

// Reviews — scoped to current chapter
const reviewCourseId = computed(() => {
  if (!selectedChapter.value) return null
  return activeLevel.value + '-ch' + selectedChapter.value.num
})

async function loadReviews() {
  if (!reviewCourseId.value) { reviews.value = []; reviewCount.value = 0; avgRating.value = 0; return }
  try {
    const res = await reviewsApi.list(reviewCourseId.value)
    if (res.data.code === 200) {
      const d = res.data.data
      reviews.value = d.reviews || []
      reviewCount.value = d.count || 0
      avgRating.value = d.avg_rating || 0
    }
  } catch { /* ignore */ }
}

async function submitReview() {
  if (myRating.value === 0 || !reviewCourseId.value) return
  if (!auth.isLoggedIn) { if (window.__openLoginPrompt) window.__openLoginPrompt(); return }
  submittingReview.value = true
  try {
    const res = await reviewsApi.create(reviewCourseId.value, myRating.value, myReviewContent.value.trim())
    if (res.data.code === 200) {
      myRating.value = 0
      myReviewContent.value = ''
      await loadReviews()
    } else {
      alert(res.data.message || '评价失败')
    }
  } catch (e) {
    alert('评价失败，请稍后再试')
  } finally {
    submittingReview.value = false
  }
}

// Init
onMounted(() => {
  try {
    const saved = JSON.parse(localStorage.getItem('completedLessons') || '[]')
    completedLessons.value = new Set(saved)
  } catch { /* ignore */ }
  loadTimestampNotes()
  loadReviews()
  loadFavorites()

  // Handle deep-link query params: ?level=初级&chapter=3&page=5
  const qLevel = route.query.level
  const qChapter = parseInt(route.query.chapter)
  const qPage = parseInt(route.query.page)
  if (qLevel && levels.find(l => l.level === qLevel)) {
    activeLevel.value = qLevel
    if (qChapter) {
      const targetCh = chapters.value.find(ch => ch.num === qChapter)
      if (targetCh) {
        selectChapter(targetCh)
        expandedChapters.value = new Set([`ch-${qLevel}-${qChapter}`])
        // Select specific lesson if page param provided
        if (qPage && targetCh) {
          for (const sec of targetCh.sections) {
            const match = sec.lessons.find(l => l.page === qPage)
            if (match) {
              selectedLesson.value = match
              break
            }
          }
        }
        return
      }
    }
  }

  const firstCh = chapters.value[0]
  if (firstCh) expandedChapters.value = new Set([`ch-初级-${firstCh.num}`])
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow flex overflow-hidden" style="min-height: calc(100vh - 4rem);">
      <!-- ===== LEFT: Course Tree ===== -->
      <aside class="w-80 lg:w-96 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
        <div class="p-4 border-b border-gray-100">
          <div class="flex bg-gray-100 rounded-lg p-0.5">
            <button v-for="l in levels" :key="l.level"
                    @click="switchLevel(l.level)"
                    :class="['flex-1 py-2 text-sm font-medium rounded-md transition', activeLevel === l.level ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']">
              {{ l.level }}
            </button>
          </div>
        </div>
        <div v-if="currentCourse" class="px-5 py-4 border-b border-gray-100">
          <h2 class="font-bold text-gray-900 text-base">{{ currentCourse.name }}</h2>
          <div class="flex items-center gap-3 mt-1.5 text-sm text-gray-500">
            <span><i class="fas fa-book-open text-blue-400 mr-1"></i>{{ currentCourse.chapterCount }}章</span>
            <span><i class="fas fa-play-circle text-blue-400 mr-1"></i>{{ currentCourse.lessonCount }}课时</span>
            <span><i class="fas fa-clock text-blue-400 mr-1"></i>{{ currentCourse.totalDuration }}</span>
          </div>
          <div class="mt-2">
            <div class="h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div class="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all" :style="{ width: currentCourse.lessonCount ? (completedLessons.size / 921 * 100).toFixed(1) + '%' : '0%' }"></div>
            </div>
          </div>
        </div>
        <div class="flex-grow overflow-y-auto">
          <div v-for="ch in chapters" :key="ch.num" class="border-b border-gray-50">
            <div @click="toggleChapter(ch.num)"
                 :class="['flex items-center px-5 py-3 cursor-pointer hover:bg-blue-50/50 transition group', selectedChapter?.num === ch.num ? 'bg-blue-50 border-l-2 border-blue-500' : 'border-l-2 border-transparent']">
              <i :class="['fas text-sm mr-2 transition text-gray-400', isChapterExpanded(ch.num) ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
              <span class="text-sm font-bold text-gray-700 group-hover:text-blue-600 truncate flex-grow">第{{ ch.num }}章 {{ ch.title }}</span>
              <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{{ ch.sections.reduce((s, sec) => s + sec.lessons.length, 0) }}课</span>
            </div>
            <div v-if="isChapterExpanded(ch.num)" class="bg-gray-50/50">
              <div v-for="(sec, si) in ch.sections" :key="si">
                <div v-if="sec.title" @click="toggleSection(ch.num, si)"
                     class="flex items-center pl-12 pr-4 py-2 cursor-pointer hover:bg-gray-100/50 text-sm text-gray-500">
                  <i :class="['fas text-[10px] mr-2', isSectionExpanded(ch.num, si) ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
                  <span class="truncate">{{ sec.title }}</span>
                  <span class="text-xs text-gray-400 ml-auto">{{ sec.lessons.length }}课</span>
                </div>
                <div v-if="!sec.title || isSectionExpanded(ch.num, si)">
                  <div v-for="lesson in sec.lessons" :key="lesson.page"
                       @click="selectLesson(ch, sec, lesson)"
                       :class="['flex items-center pl-20 pr-3 py-2 cursor-pointer hover:bg-blue-100/50 transition text-sm', selectedLesson?.page === lesson.page && selectedChapter?.num === ch.num ? 'bg-blue-100/70 text-blue-700 font-medium border-r-2 border-blue-500' : 'text-gray-600']">
                    <i v-if="isCompleted(ch.num, lesson.page)" class="fas fa-check-circle text-green-500 text-xs mr-1.5"></i>
                    <i v-else class="far fa-circle text-gray-300 text-xs mr-1.5"></i>
                    <span class="text-xs text-gray-400 w-8 flex-shrink-0">P{{ lesson.page }}</span>
                    <span class="truncate flex-grow">{{ lesson.title }}</span>
                    <span class="text-xs text-gray-400 ml-1">{{ lesson.duration }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- ===== CENTER: Video ===== -->
      <section class="flex-grow flex flex-col overflow-y-auto">
        <div v-if="!selectedLesson" class="flex-grow flex items-center justify-center text-gray-400 bg-gray-100/50">
          <div class="text-center">
            <div class="w-28 h-28 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <i class="fas fa-hand-point-left text-blue-400 text-4xl"></i>
            </div>
            <p class="text-xl font-bold text-gray-500 mb-1">选择课程开始学习</p>
            <p class="text-sm">从左侧目录选择章节和课时</p>
          </div>
        </div>
        <template v-else>
          <!-- Video -->
          <div class="bg-black flex-shrink-0" style="aspect-ratio: 16/9; max-height: 62vh;">
            <iframe v-if="videoUrl" :src="videoUrl" allowfullscreen allow="autoplay; fullscreen; encrypted-media" referrerpolicy="no-referrer" class="w-full h-full border-0"></iframe>
            <div v-else class="w-full h-full flex items-center justify-center text-gray-500 bg-gray-900">
              <div class="text-center"><i class="fas fa-video-slash text-4xl mb-2"></i><p>暂无视频链接</p></div>
            </div>
          </div>

          <!-- Info + Controls Bar -->
          <div class="bg-white border-b border-gray-200 px-5 py-4 flex-shrink-0">
            <div class="flex items-start justify-between gap-4 mb-3">
              <div class="flex-grow min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs font-bold bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">P{{ selectedLesson.page }}</span>
                  <span class="text-sm text-gray-400">{{ selectedLesson.duration }}</span>
                  <span v-if="isCompleted(selectedChapter?.num, selectedLesson.page)" class="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full"><i class="fas fa-check mr-1"></i>已完成</span>
                </div>
                <h3 class="text-base font-bold text-gray-900">{{ selectedLesson.title }}</h3>
                <p class="text-sm text-gray-400 mt-0.5">第{{ selectedChapter?.num }}章 {{ selectedChapter?.title }}</p>
              </div>
            </div>
            <!-- Buttons Row -->
            <div class="flex items-center gap-2 flex-wrap">
              <button @click="markCompleted"
                      :class="['px-3 py-1.5 rounded-lg text-sm font-medium transition border', isCompleted(selectedChapter?.num, selectedLesson.page) ? 'bg-green-50 text-green-600 border-green-200' : 'bg-gray-100 text-gray-500 hover:bg-green-50 hover:text-green-600 border-transparent']">
                <i :class="isCompleted(selectedChapter?.num, selectedLesson.page) ? 'fas fa-check-circle' : 'far fa-check-circle'"></i> 标记完成
              </button>
              <button @click="toggleAiNotes"
                      :class="['px-3 py-1.5 rounded-lg text-sm font-medium transition border', showAiNotesPanel ? 'bg-purple-50 text-purple-600 border-purple-200' : 'bg-gray-100 text-gray-500 hover:bg-purple-50 hover:text-purple-600 border-transparent']">
                <i class="fas fa-robot mr-1"></i>AI笔记
              </button>
              <button @click="toggleFavorite"
                      :class="['px-3 py-1.5 rounded-lg text-sm font-medium transition border', isCurrentFavorited ? 'bg-red-50 text-red-500 border-red-200' : 'bg-gray-100 text-gray-500 hover:bg-red-50 hover:text-red-400 border-transparent']">
                <i :class="isCurrentFavorited ? 'fas fa-heart' : 'far fa-heart'"></i> 收藏本章
              </button>
              <button @click="goPractice"
                      class="px-5 py-2.5 rounded-xl text-base font-bold transition border bg-gradient-to-r from-green-50 to-emerald-50 text-green-600 border-green-200 hover:from-green-100 hover:to-emerald-100 hover:shadow-md hover:-translate-y-0.5">
                <i class="fas fa-dumbbell mr-1.5"></i>练一练
              </button>
              <div class="flex-grow"></div>
              <button @click="goPrev" :disabled="!navInfo.prev"
                      :class="['flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition', navInfo.prev ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' : 'text-gray-300 cursor-not-allowed']">
                <i class="fas fa-chevron-left text-xs"></i> 上一课
              </button>
              <span class="text-sm text-gray-300">|</span>
              <button @click="goNext" :disabled="!navInfo.next"
                      :class="['flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition', navInfo.next ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' : 'text-gray-300 cursor-not-allowed']">
                下一课 <i class="fas fa-chevron-right text-xs"></i>
              </button>
            </div>
            <!-- AI Notes Panel -->
            <div v-if="showAiNotesPanel" class="mt-3 p-4 bg-purple-50/30 border border-purple-200 rounded-xl text-xs">
              <div class="flex items-center gap-2 mb-3">
                <i class="fas fa-robot text-purple-500"></i>
                <span class="font-bold text-purple-700">AI 智能笔记</span>
              </div>

              <!-- Has note -->
              <template v-if="aiHasNote && aiNote">
                <div class="space-y-3">
                  <div class="bg-white rounded-lg p-3">
                    <p class="text-xs font-bold text-gray-700 mb-1"><i class="fas fa-file-alt text-purple-500 mr-1"></i>课程简介</p>
                    <p class="text-xs text-gray-600 leading-relaxed">{{ aiNote.summary }}</p>
                  </div>
                  <div class="bg-white rounded-lg p-3">
                    <p class="text-xs font-bold text-gray-700 mb-2"><i class="fas fa-star text-amber-500 mr-1"></i>视频看点</p>
                    <div class="flex flex-wrap gap-1.5">
                      <span v-for="(h, i) in aiNote.highlights" :key="i" class="bg-amber-50 text-xs text-amber-700 px-2 py-1 rounded-lg flex items-center gap-1">
                        <span class="font-mono text-[10px] bg-amber-200 px-1 rounded">{{ h.time }}</span>{{ h.title }}
                      </span>
                    </div>
                  </div>
                  <div class="bg-white rounded-lg p-3">
                    <p class="text-xs font-bold text-gray-700 mb-1"><i class="fas fa-list-ul text-blue-500 mr-1"></i>知识点</p>
                    <ul class="space-y-0.5">
                      <li v-for="(n, i) in aiNote.notes" :key="i" class="text-xs text-gray-600 flex items-start gap-1.5">
                        <span class="w-4 h-4 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-[9px] font-bold flex-shrink-0 mt-0.5">{{ i + 1 }}</span>{{ n }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="aiNote.errors?.length" class="bg-white rounded-lg p-3">
                    <p class="text-xs font-bold text-gray-700 mb-1"><i class="fas fa-exclamation-circle text-red-500 mr-1"></i>易错点</p>
                    <ul class="space-y-0.5">
                      <li v-for="(e, i) in aiNote.errors" :key="i" class="text-xs text-red-700 flex items-start gap-1.5"><i class="fas fa-times-circle text-red-400 text-[10px] mt-0.5"></i>{{ e }}</li>
                    </ul>
                  </div>
                  <div v-if="aiNote.suggestions?.length" class="bg-white rounded-lg p-3">
                    <p class="text-xs font-bold text-gray-700 mb-1"><i class="fas fa-lightbulb text-green-500 mr-1"></i>学习建议</p>
                    <ul class="space-y-0.5">
                      <li v-for="(s, i) in aiNote.suggestions" :key="i" class="text-xs text-gray-600 flex items-start gap-1.5">
                        <span class="w-4 h-4 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-[9px] font-bold flex-shrink-0 mt-0.5">{{ i + 1 }}</span>{{ s }}
                      </li>
                    </ul>
                  </div>
                </div>
              </template>

              <!-- Generating -->
              <template v-else-if="aiGenerating">
                <div class="text-center py-4">
                  <div class="w-10 h-10 mx-auto mb-2 rounded-full bg-purple-100 flex items-center justify-center">
                    <i class="fas fa-robot text-purple-500 text-lg" :class="{ 'animate-bounce': aiTaskStatus !== 'failed' }"></i>
                  </div>
                  <p class="text-xs font-medium text-gray-700">AI 正在解析视频</p>
                  <p class="text-[10px] text-gray-400 mb-3">预计 1-3 分钟</p>
                  <div class="max-w-full">
                    <div class="flex justify-between text-[10px] text-gray-400 mb-1">
                      <span>{{ statusLabelMap[aiTaskStatus] || aiTaskStatus }}</span>
                      <span>{{ aiTaskProgress }}%</span>
                    </div>
                    <div class="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div class="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-700" :style="{ width: aiTaskProgress + '%' }"></div>
                    </div>
                  </div>
                </div>
              </template>

              <!-- No lesson resolved -->
              <template v-else-if="!aiLessonId">
                <p class="text-gray-500 leading-relaxed text-[10px]">
                  <i class="fas fa-info-circle mr-1"></i>当前课时暂不支持 AI 笔记功能，请切换到其他课时后再试。
                </p>
              </template>

              <!-- Generate button -->
              <template v-else>
                <p class="text-purple-600 leading-relaxed mb-3">AI 将自动解析当前课时视频，生成课程简介、知识点笔记、视频看点、易错提醒和学习建议。</p>
                <button @click="handleGenerateAINotes" :disabled="aiGenerating"
                        class="w-full py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-xs font-bold hover:shadow-md transition disabled:opacity-50">
                  <i class="fas fa-magic mr-1.5"></i>生成 AI 笔记
                </button>
                <p v-if="aiError" class="text-[10px] text-red-500 mt-1.5">{{ aiError }}</p>
              </template>
            </div>
          </div>
        </template>
      </section>

      <!-- ===== RIGHT: Notes + Reviews + Resources ===== -->
      <aside class="w-96 flex-shrink-0 bg-white border-l border-gray-200 flex flex-col overflow-hidden">
        <div class="flex-grow overflow-y-auto">
          <!-- Timestamp Notes -->
          <div class="p-5 border-b border-gray-100">
            <h4 class="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
              <i class="fas fa-clock text-blue-500"></i>时间戳笔记
            </h4>
            <div v-if="selectedLesson" class="space-y-2 mb-3">
              <div class="flex gap-1.5">
                <input v-model="noteTimestamp" placeholder="00:00" class="w-16 text-sm px-2 py-1.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-300 text-center">
                <input v-model="noteContent" placeholder="记录此刻的笔记..."
                       class="flex-grow text-sm px-2 py-1.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-300"
                       @keyup.enter="addTimestampNote">
                <button @click="addTimestampNote"
                        class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition flex-shrink-0">
                  <i class="fas fa-plus"></i>
                </button>
              </div>
            </div>
            <div v-else class="text-sm text-gray-400 text-center py-4">请先选择课时</div>
            <div v-if="timestampNotes.length === 0 && selectedLesson" class="text-sm text-gray-400 text-center py-2">暂无笔记，添加第一条吧</div>
            <div class="space-y-2">
              <div v-for="note in timestampNotes" :key="note.id" class="bg-gray-50 rounded-lg p-2.5 group">
                <div class="flex items-start justify-between gap-2">
                  <div class="flex-grow min-w-0">
                    <div class="flex items-center gap-1.5 mb-1">
                      <span class="text-xs font-bold text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded">{{ note.timestamp || '--:--' }}</span>
                      <span class="text-xs text-gray-400 truncate">{{ note.lessonTitle?.substring(0, 20) }}</span>
                    </div>
                    <p class="text-sm text-gray-700">{{ note.content }}</p>
                  </div>
                  <button @click="deleteTimestampNote(note.id)" class="text-gray-300 hover:text-red-400 transition opacity-0 group-hover:opacity-100 flex-shrink-0">
                    <i class="fas fa-times text-[10px]"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Course Resources -->
          <div class="p-5 border-b border-gray-100">
            <h4 class="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
              <i class="fas fa-folder-open text-yellow-500"></i>课程配套资源
            </h4>

            <div v-if="!selectedChapter" class="text-sm text-gray-400 text-center py-6">
              <i class="fas fa-hand-point-left text-3xl mb-2 block"></i>
              请先从左侧选择章节
            </div>
            <div v-else-if="!chapterResources" class="text-sm text-gray-400 text-center py-6">
              <i class="fas fa-inbox text-3xl mb-2 block"></i>
              本章暂无配套资源
            </div>

            <div v-else class="space-y-2.5">
              <!-- Mind Maps -->
              <div class="bg-gray-50 rounded-xl overflow-hidden">
                <div @click="toggleResourceType('mindmap')"
                     class="flex items-center justify-between p-3 cursor-pointer hover:bg-blue-50 transition">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <i class="fas fa-project-diagram text-blue-500 text-xs"></i>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-700">思维导图</p>
                      <p class="text-xs text-gray-400">{{ chapterResources.mindMaps.length }} 个文件</p>
                    </div>
                  </div>
                  <i :class="['fas text-sm text-gray-400 transition', isResourceExpanded('mindmap') ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
                </div>
                <div v-if="isResourceExpanded('mindmap')" class="px-3 pb-2 space-y-1">
                  <a v-for="(f, fi) in chapterResources.mindMaps" :key="fi"
                     :href="f.url" target="_blank"
                     class="flex items-center justify-between px-3 py-1.5 rounded-lg hover:bg-blue-100/50 transition text-sm">
                    <span class="truncate text-gray-600"><i class="far fa-image text-blue-400 mr-1.5"></i>{{ f.name }}</span>
                    <i class="fas fa-download text-gray-300 hover:text-blue-500 flex-shrink-0 ml-2"></i>
                  </a>
                  <p v-if="chapterResources.mindMaps.length === 0" class="text-xs text-gray-400 px-3 py-1">暂无思维导图</p>
                </div>
              </div>

              <!-- PPTs -->
              <div class="bg-gray-50 rounded-xl overflow-hidden">
                <div @click="toggleResourceType('ppt')"
                     class="flex items-center justify-between p-3 cursor-pointer hover:bg-orange-50 transition">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <i class="fas fa-file-powerpoint text-orange-500 text-xs"></i>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-700">PPT 课件</p>
                      <p class="text-xs text-gray-400">{{ chapterResources.ppts.length }} 个文件</p>
                    </div>
                  </div>
                  <i :class="['fas text-sm text-gray-400 transition', isResourceExpanded('ppt') ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
                </div>
                <div v-if="isResourceExpanded('ppt')" class="px-3 pb-2 space-y-1 max-h-48 overflow-y-auto">
                  <a v-for="(f, fi) in chapterResources.ppts" :key="fi"
                     :href="f.url" target="_blank"
                     class="flex items-center justify-between px-3 py-1.5 rounded-lg hover:bg-orange-100/50 transition text-sm">
                    <span class="truncate text-gray-600"><i class="far fa-file-powerpoint text-orange-400 mr-1.5"></i>{{ f.name }}</span>
                    <i class="fas fa-download text-gray-300 hover:text-orange-500 flex-shrink-0 ml-2"></i>
                  </a>
                  <p v-if="chapterResources.ppts.length === 0" class="text-xs text-gray-400 px-3 py-1">暂无PPT课件</p>
                </div>
              </div>

              <!-- Code Samples -->
              <div class="bg-gray-50 rounded-xl overflow-hidden">
                <div @click="toggleResourceType('code')"
                     class="flex items-center justify-between p-3 cursor-pointer hover:bg-green-50 transition">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <i class="fas fa-code text-green-500 text-xs"></i>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-700">案例代码</p>
                      <p class="text-xs text-gray-400">{{ chapterResources.codes.length }} 个文件</p>
                    </div>
                  </div>
                  <i :class="['fas text-sm text-gray-400 transition', isResourceExpanded('code') ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
                </div>
                <div v-if="isResourceExpanded('code')" class="px-3 pb-2 space-y-1 max-h-48 overflow-y-auto">
                  <a v-for="(f, fi) in chapterResources.codes" :key="fi"
                     :href="f.url" target="_blank"
                     class="flex items-center justify-between px-3 py-1.5 rounded-lg hover:bg-green-100/50 transition text-sm">
                    <span class="truncate text-gray-600"><i class="far fa-file-code text-green-400 mr-1.5"></i>{{ f.name }}</span>
                    <i class="fas fa-download text-gray-300 hover:text-green-500 flex-shrink-0 ml-2"></i>
                  </a>
                  <p v-if="chapterResources.codes.length === 0" class="text-xs text-gray-400 px-3 py-1">暂无案例代码</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Course Reviews -->
          <div class="p-5">
            <h4 class="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
              <i class="fas fa-star text-yellow-400"></i>课程评价
              <span v-if="selectedChapter" class="text-xs text-gray-400 font-normal">第{{ selectedChapter.num }}章</span>
            </h4>

            <!-- No chapter selected -->
            <div v-if="!selectedChapter" class="text-sm text-gray-400 text-center py-6">
              请选择章节后查看评价
            </div>

            <template v-else>
              <!-- Rating summary -->
              <div class="flex items-center gap-3 mb-3 p-3 bg-yellow-50 rounded-xl">
                <div class="text-3xl font-bold text-gray-800">{{ avgRating || '-' }}</div>
                <div>
                  <div class="flex text-yellow-400 text-base">
                    <i v-for="i in 5" :key="i" :class="i <= Math.round(avgRating) ? 'fas fa-star' : 'far fa-star'"></i>
                  </div>
                  <div class="text-xs text-gray-400">{{ reviewCount }} 条评价</div>
                </div>
              </div>

              <!-- My review -->
              <div v-if="auth.isLoggedIn" class="mb-3 p-3 bg-gray-50 rounded-xl">
                <p class="text-sm font-bold text-gray-600 mb-2">我的评价</p>
                <div class="flex gap-0.5 mb-2">
                  <button v-for="i in 5" :key="i" @click="myRating = i"
                          :class="['text-xl transition hover:scale-110', i <= myRating ? 'text-yellow-400' : 'text-gray-300']">
                    <i :class="i <= myRating ? 'fas fa-star' : 'far fa-star'"></i>
                  </button>
                </div>
                <textarea v-model="myReviewContent" placeholder="写下你的学习感受..."
                          class="w-full text-sm p-2 border border-gray-200 rounded-lg resize-none focus:outline-none focus:border-blue-300 h-16"></textarea>
                <button @click="submitReview" :disabled="myRating === 0 || submittingReview"
                        class="mt-2 text-sm bg-blue-600 text-white px-4 py-1.5 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                  {{ submittingReview ? '提交中...' : '提交评价' }}
                </button>
              </div>
              <div v-else class="mb-3 p-3 bg-gray-50 rounded-xl text-center text-sm text-gray-400">
                <a href="/login" class="text-blue-500 hover:underline">登录</a>后即可评价
              </div>

              <!-- Review list -->
              <div class="space-y-3">
                <div v-for="r in reviews" :key="r.id" class="border-t border-gray-50 pt-3">
                  <div class="flex items-center gap-2 mb-1">
                    <img :src="r.avatar" class="w-6 h-6 rounded-full">
                    <span class="text-sm font-bold text-gray-700">{{ r.username }}</span>
                    <span class="flex text-[10px] text-yellow-400">
                      <i v-for="i in 5" :key="i" :class="i <= r.rating ? 'fas fa-star' : 'far fa-star'"></i>
                    </span>
                  </div>
                  <p class="text-sm text-gray-500" v-if="r.content">{{ r.content }}</p>
                </div>
                <div v-if="reviews.length === 0" class="text-sm text-gray-400 text-center py-4">暂无评价，成为第一个评价的人吧</div>
              </div>
            </template>
          </div>
        </div>
      </aside>
    </main>

    <AppFooter />
  </div>
</template>
