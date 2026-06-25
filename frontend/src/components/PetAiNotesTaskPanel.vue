<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const emit = defineEmits(['close'])
const router = useRouter()

const tasks = ref([])
let pollTimer = null

const statusLabelMap = {
  not_started: '未开始', queued: '排队中', downloading: '正在获取视频',
  extracting_audio: '正在提取音频', transcribing: '正在语音转文字',
  summarizing: '正在生成AI笔记', completed: '已完成', failed: '失败',
}

const statusColorMap = {
  completed: 'text-green-600 bg-green-50',
  failed: 'text-red-600 bg-red-50',
  default: 'text-blue-600 bg-blue-50',
}

function loadTasks() {
  try {
    tasks.value = JSON.parse(localStorage.getItem('ai_tasks') || '[]')
      .sort((a, b) => b.created_at - a.created_at)
  } catch { tasks.value = [] }
}

async function pollInProgress() {
  const active = tasks.value.filter(t => !['completed', 'failed'].includes(t.status))
  if (active.length === 0) return
  const { aiNotesApi } = await import('../api/aiNotes')
  let changed = false
  for (const t of active) {
    try {
      const res = await aiNotesApi.getTaskStatus(t.task_id)
      if (res.data.code === 200) {
        const d = res.data.data
        if (t.status !== d.status || t.progress !== d.progress) {
          t.status = d.status
          t.progress = d.progress
          t.message = d.message
          changed = true
        }
      }
    } catch {}
  }
  if (changed) {
    // Remove completed tasks that were already present (keep them)
    localStorage.setItem('ai_tasks', JSON.stringify(
      JSON.parse(localStorage.getItem('ai_tasks') || '[]').map(orig => {
        const upd = tasks.value.find(t => t.task_id === orig.task_id)
        return upd || orig
      })
    ))
  }
}

function jumpToLesson(task) {
  if (!task.level) return
  router.push({ path: '/courses', query: { level: task.level, chapter: task.chapter, page: task.page } })
  emit('close')
}

function deleteTask(taskId) {
  try {
    const all = JSON.parse(localStorage.getItem('ai_tasks') || '[]')
    localStorage.setItem('ai_tasks', JSON.stringify(all.filter(t => t.task_id !== taskId)))
    loadTasks()
  } catch {}
}

function statusClass(status) {
  if (statusColorMap[status]) return statusColorMap[status]
  return statusColorMap.default
}

onMounted(() => {
  loadTasks()
  pollTimer = setInterval(() => {
    loadTasks()
    pollInProgress()
  }, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="bg-white rounded-xl shadow-xl border border-gray-200 w-80 overflow-hidden"
       @click.stop>
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gradient-to-r from-purple-50 to-blue-50">
      <div class="flex items-center gap-2">
        <i class="fas fa-robot text-purple-500"></i>
        <span class="text-sm font-bold text-gray-800">智能笔记生成记录</span>
      </div>
      <button @click.stop="$emit('close')"
              class="w-6 h-6 rounded-full hover:bg-gray-200/50 flex items-center justify-center transition text-gray-400 hover:text-gray-600">
        <i class="fas fa-times text-xs"></i>
      </button>
    </div>

    <!-- Task list -->
    <div class="max-h-72 overflow-y-auto">
      <div v-if="tasks.length === 0" class="text-center py-8 text-xs text-gray-400">
        <i class="fas fa-inbox text-2xl mb-2 block"></i>
        暂无生成记录
      </div>
      <div v-for="task in tasks" :key="task.task_id"
           :class="['px-4 py-3 border-b border-gray-50 last:border-b-0 transition', task.status === 'completed' ? 'cursor-pointer hover:bg-purple-50/50' : '']"
           @click="task.status === 'completed' ? jumpToLesson(task) : null">
        <div class="flex items-start justify-between gap-2">
          <div class="flex-grow min-w-0">
            <p class="text-xs font-medium text-gray-700 truncate">{{ task.lesson_title || task.course_title || '未知课程' }}</p>
            <p class="text-[10px] text-gray-400 truncate mt-0.5">{{ task.course_title }}</p>
          </div>
          <span :class="['text-[10px] px-1.5 py-0.5 rounded-full font-medium flex-shrink-0', statusClass(task.status)]">
            {{ statusLabelMap[task.status] || task.status }}
          </span>
        </div>
        <!-- Progress bar for active tasks -->
        <div v-if="!['completed', 'failed'].includes(task.status)" class="mt-2">
          <div class="flex justify-between text-[10px] text-gray-400 mb-0.5">
            <span>{{ task.message || '处理中...' }}</span>
            <span>{{ task.progress || 0 }}%</span>
          </div>
          <div class="h-1 bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-700"
                 :style="{ width: (task.progress || 0) + '%' }"></div>
          </div>
        </div>
        <!-- Completed hint -->
        <p v-if="task.status === 'completed'" class="text-[10px] text-green-500 mt-0.5">
          <i class="fas fa-check-circle mr-0.5"></i>点击跳转到该节课
        </p>
        <!-- Failed hint -->
        <p v-if="task.status === 'failed'" class="text-[10px] text-red-400 mt-0.5 flex items-center justify-between">
          <span><i class="fas fa-exclamation-circle mr-0.5"></i>生成失败</span>
          <button @click.stop="deleteTask(task.task_id)" class="text-gray-300 hover:text-red-400">
            <i class="fas fa-trash-alt text-[10px]"></i>
          </button>
        </p>
      </div>
    </div>
  </div>
</template>
