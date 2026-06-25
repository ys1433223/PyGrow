<script setup>
const props = defineProps({
  interactionsEnabled: Boolean,
  messagesEnabled: Boolean,
})

const emit = defineEmits([
  'toggleInteractions',
  'toggleMessages',
  'resetPosition',
  'close',
])

function handleResetPosition() {
  if (confirm('确定恢复宠物到默认位置（右下角）？')) {
    localStorage.removeItem('petPosition')
    emit('resetPosition')
    emit('close')
  }
}
</script>

<template>
  <div
    class="bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden"
    style="width: 260px"
  >
    <!-- Header -->
    <div
      class="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-gray-600 to-gray-700 text-white select-none"
    >
      <div class="flex items-center gap-2">
        <i class="fas fa-cog text-sm"></i>
        <span class="text-sm font-bold">宠物设置</span>
      </div>
      <button @click.stop="$emit('close')" class="text-white/70 hover:text-white transition">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <div class="p-3 space-y-1">
      <!-- Toggle interactions -->
      <button @click="$emit('toggleInteractions')"
        class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-gray-50 transition">
        <div class="flex items-center gap-2.5">
          <span class="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
            <i class="fas fa-smile text-yellow-500 text-xs"></i>
          </span>
          <div class="text-left">
            <p class="text-xs font-medium text-gray-700">互动效果</p>
            <p class="text-[10px] text-gray-400">场景切换宠物动图</p>
          </div>
        </div>
        <span :class="['w-10 h-5 rounded-full relative transition-colors flex-shrink-0', interactionsEnabled ? 'bg-green-500' : 'bg-gray-300']">
          <span :class="['absolute w-4 h-4 rounded-full bg-white top-0.5 shadow transition-transform', interactionsEnabled ? 'translate-x-5' : 'translate-x-0.5']"></span>
        </span>
      </button>

      <!-- Toggle messages -->
      <button @click="$emit('toggleMessages')"
        class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-gray-50 transition">
        <div class="flex items-center gap-2.5">
          <span class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <i class="fas fa-bell text-blue-500 text-xs"></i>
          </span>
          <div class="text-left">
            <p class="text-xs font-medium text-gray-700">消息提醒</p>
            <p class="text-[10px] text-gray-400">接收系统通知和回复</p>
          </div>
        </div>
        <span :class="['w-10 h-5 rounded-full relative transition-colors flex-shrink-0', messagesEnabled ? 'bg-green-500' : 'bg-gray-300']">
          <span :class="['absolute w-4 h-4 rounded-full bg-white top-0.5 shadow transition-transform', messagesEnabled ? 'translate-x-5' : 'translate-x-0.5']"></span>
        </span>
      </button>

      <!-- Reset position -->
      <button @click="handleResetPosition"
        class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-gray-50 transition">
        <div class="flex items-center gap-2.5">
          <span class="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
            <i class="fas fa-map-pin text-gray-500 text-xs"></i>
          </span>
          <div class="text-left">
            <p class="text-xs font-medium text-gray-700">恢复默认位置</p>
            <p class="text-[10px] text-gray-400">重置到右下角</p>
          </div>
        </div>
        <i class="fas fa-redo text-gray-300 text-xs"></i>
      </button>
    </div>
  </div>
</template>
