<script setup>
import { ref } from 'vue'

const props = defineProps({
  mode: { type: String, default: 'active' }, // 'active' | 'simplified'
  interactionsEnabled: Boolean,
  messagesEnabled: Boolean,
})

const emit = defineEmits([
  'toggleInteractions',
  'toggleMessages',
  'resetPosition',
  'hidePet',
  'restPet',
  'openChat',
  'openMessages',
  'openSettings',
  'openAiNotes',
  'requestHint',
  'showProgress',
])

// ---- Simplified mode (daily practice) ----
</script>

<template>
  <!-- Active mode menu -->
  <div v-if="mode === 'active'" class="bg-white rounded-xl shadow-xl border border-gray-200 p-1.5 min-w-[148px]">
    <button @click.stop="$emit('openChat')"
      class="w-full text-left px-3 py-2.5 text-xs rounded-lg hover:bg-purple-50 transition flex items-center gap-2.5 whitespace-nowrap">
      <span class="w-7 h-7 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
        <i class="fas fa-robot text-purple-500 text-[11px]"></i>
      </span>
      <span>
        <span class="font-medium text-gray-700 block leading-tight">Python AI助手</span>
        <span class="text-[10px] text-gray-400">答疑 · 报错解释 · 建议</span>
      </span>
    </button>

    <button @click.stop="$emit('openMessages')"
      class="w-full text-left px-3 py-2.5 text-xs rounded-lg hover:bg-blue-50 transition flex items-center gap-2.5 whitespace-nowrap">
      <span class="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <i class="fas fa-bell text-blue-500 text-[11px]"></i>
      </span>
      <span>
        <span class="font-medium text-gray-700 block leading-tight">消息中心</span>
        <span class="text-[10px] text-gray-400">通知 · 回复 · 提醒</span>
      </span>
    </button>

    <hr class="my-1 border-gray-100">

    <button @click.stop="$emit('openAiNotes')"
      class="w-full text-left px-3 py-2.5 text-xs rounded-lg hover:bg-purple-50 transition flex items-center gap-2.5 whitespace-nowrap">
      <span class="w-7 h-7 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
        <i class="fas fa-file-alt text-purple-500 text-[11px]"></i>
      </span>
      <span>
        <span class="font-medium text-gray-700 block leading-tight">智能笔记生成记录</span>
        <span class="text-[10px] text-gray-400">查看进度 · 已生成笔记</span>
      </span>
    </button>

    <button @click.stop="$emit('openSettings')"
      class="w-full text-left px-3 py-2.5 text-xs rounded-lg hover:bg-gray-50 transition flex items-center gap-2.5 whitespace-nowrap">
      <span class="w-7 h-7 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
        <i class="fas fa-cog text-gray-500 text-[11px]"></i>
      </span>
      <span>
        <span class="font-medium text-gray-700 block leading-tight">宠物设置</span>
        <span class="text-[10px] text-gray-400">互动 · 消息 · 位置</span>
      </span>
    </button>
  </div>

  <!-- Simplified mode menu (daily practice) -->
  <div v-else-if="mode === 'simplified'" class="bg-white rounded-xl shadow-xl border border-gray-200 p-1.5 min-w-[130px]">
    <button @click.stop="$emit('requestHint')"
      class="w-full text-left px-3 py-2.5 text-xs rounded-lg hover:bg-purple-50 transition flex items-center gap-2.5 whitespace-nowrap">
      <span class="w-7 h-7 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
        <i class="fas fa-robot text-purple-500 text-[11px]"></i>
      </span>
      <span>
        <span class="font-medium text-gray-700 block leading-tight">AI提示</span>
        <span class="text-[10px] text-gray-400">思路 · 知识点</span>
      </span>
    </button>

    <button @click.stop="$emit('showProgress')"
      class="w-full text-left px-3 py-2.5 text-xs rounded-lg hover:bg-blue-50 transition flex items-center gap-2.5 whitespace-nowrap">
      <span class="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <i class="fas fa-tasks text-blue-500 text-[11px]"></i>
      </span>
      <span>
        <span class="font-medium text-gray-700 block leading-tight">当前进度</span>
        <span class="text-[10px] text-gray-400">第 X/Y 题</span>
      </span>
    </button>

    <hr class="my-1 border-gray-100">

    <button @click.stop="$emit('toggleInteractions')"
      class="w-full text-left px-3 py-2.5 text-xs rounded-lg hover:bg-gray-50 transition flex items-center gap-2.5 whitespace-nowrap">
      <span class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
        :class="interactionsEnabled ? 'bg-green-100' : 'bg-gray-100'">
        <i :class="[interactionsEnabled ? 'fas fa-toggle-on text-green-500' : 'fas fa-toggle-off text-gray-400', 'text-[11px]']"></i>
      </span>
      <span>
        <span class="font-medium text-gray-700 block leading-tight">关闭互动效果</span>
        <span class="text-[10px] text-gray-400">{{ interactionsEnabled ? '已开启' : '已关闭' }}</span>
      </span>
    </button>
  </div>
</template>
