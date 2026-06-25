<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const emit = defineEmits(['close'])

const STORAGE_KEY = 'petMessages'

// Message categories and their nav targets
const CATEGORY_META = {
  system: { label: '系统通知', icon: 'fas fa-bullhorn', color: 'text-blue-500 bg-blue-100', target: null },
  community: { label: '社区回复', icon: 'fas fa-comment-dots', color: 'text-green-500 bg-green-100', target: '/community' },
  task: { label: '每日任务', icon: 'fas fa-clipboard-check', color: 'text-amber-500 bg-amber-100', target: '/' },
  promotion: { label: '晋级赛', icon: 'fas fa-trophy', color: 'text-orange-500 bg-orange-100', target: '/practice' },
  adventure: { label: '宠物探险', icon: 'fas fa-map-marked-alt', color: 'text-purple-500 bg-purple-100', target: '/learning-center' },
  farm: { label: '农场提醒', icon: 'fas fa-seedling', color: 'text-green-500 bg-green-100', target: '/learning-center' },
}

const messages = ref([])

function loadMessages() {
  try {
    messages.value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch { messages.value = [] }
}

function saveMessages() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value))
}

const unreadCount = computed(() => messages.value.filter(m => !m.read).length)

function markRead(msg) {
  msg.read = true
  saveMessages()
}

function markAllRead() {
  messages.value.forEach(m => m.read = true)
  saveMessages()
}

function deleteMsg(msg) {
  messages.value = messages.value.filter(m => m.id !== msg.id)
  saveMessages()
}

function clearAll() {
  if (confirm('确定清空所有消息？')) {
    messages.value = []
    saveMessages()
  }
}

function goTo(msg) {
  markRead(msg)
  const meta = CATEGORY_META[msg.category]
  if (meta?.target) {
    router.push(meta.target)
  }
  emit('close')
}

function timeAgo(ts) {
  const diff = Date.now() - ts
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  return `${Math.floor(hours / 24)}天前`
}

onMounted(loadMessages)
</script>

<template>
  <div
    class="bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden"
    style="width: 300px; height: 380px"
  >
    <!-- Header -->
    <div
      class="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 text-white select-none"
    >
      <div class="flex items-center gap-2">
        <i class="fas fa-bell"></i>
        <span class="text-sm font-bold">消息中心</span>
        <span v-if="unreadCount" class="bg-red-400 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">{{ unreadCount }}</span>
      </div>
      <div class="flex items-center gap-1">
        <button v-if="messages.length" @click.stop="markAllRead" class="text-white/70 hover:text-white text-[10px] px-1" title="全部已读">
          <i class="fas fa-check-double"></i>
        </button>
        <button @click.stop="$emit('close')" class="text-white/70 hover:text-white transition">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
        <i class="fas fa-inbox text-3xl mb-2"></i>
        <p class="text-xs">暂无消息</p>
      </div>
      <div v-else>
        <div v-for="msg in messages" :key="msg.id"
          @click="goTo(msg)"
          :class="['flex items-start gap-3 px-4 py-3 border-b border-gray-50 cursor-pointer hover:bg-gray-50 transition', !msg.read ? 'bg-blue-50/30' : '']">
          <span :class="['w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5', CATEGORY_META[msg.category]?.color || 'text-gray-400 bg-gray-100']">
            <i :class="[CATEGORY_META[msg.category]?.icon || 'fas fa-circle', 'text-[10px]']"></i>
          </span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-2">
              <span v-if="!msg.read" class="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0"></span>
              <span class="text-xs font-medium text-gray-700 truncate flex-1">{{ msg.title }}</span>
              <span class="text-[10px] text-gray-400 flex-shrink-0">{{ timeAgo(msg.ts) }}</span>
            </div>
            <p class="text-xs text-gray-500 mt-0.5 line-clamp-2">{{ msg.body }}</p>
            <span class="text-[10px] text-gray-400 mt-1 inline-block">{{ CATEGORY_META[msg.category]?.label }}</span>
          </div>
          <button @click.stop="deleteMsg(msg)" class="text-gray-300 hover:text-red-400 flex-shrink-0 opacity-0 hover:opacity-100 transition" title="删除">
            <i class="fas fa-times text-[10px]"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div v-if="messages.length > 0" class="p-2 border-t border-gray-100 text-center">
      <button @click="clearAll" class="text-[10px] text-gray-400 hover:text-red-500 transition">清空所有消息</button>
    </div>
  </div>
</template>
