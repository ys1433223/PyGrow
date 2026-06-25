<script setup>
import { ref, nextTick, onMounted } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { chatWithMentor } from '../api/ai_mentor'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const chatContainer = ref(null)

const history = ref([])  // [{role, content}] for API context

async function sendMessage() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true

  await nextTick()
  scrollToBottom()

  try {
    const res = await chatWithMentor(text, history.value)
    const reply = res.data.reply || '抱歉，我现在无法回答这个问题。'
    messages.value.push({ role: 'assistant', content: reply })
    history.value.push({ role: 'user', content: text })
    history.value.push({ role: 'assistant', content: reply })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: 'AI 服务暂时不可用，请稍后再试。', error: true })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <AppHeader />
    <PageLoader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <div class="max-w-4xl mx-auto">
        <div class="mb-6">
          <h1 class="text-2xl font-bold text-gray-800">AI 代码导师</h1>
          <p class="text-gray-500 mt-1">向 AI 助教提问编程问题，获得逐步指导和代码解释</p>
        </div>

        <!-- Quick prompts -->
        <div v-if="messages.length === 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 class="text-sm font-medium text-gray-500 mb-3">可以尝试问我：</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              v-for="q in ['Python 列表和元组有什么区别？', '帮我解释一下递归函数的工作原理', '如何在 Python 中读写文件？', '什么是面向对象编程？给我个简单例子']"
              :key="q"
              @click="input = q; sendMessage()"
              class="text-left px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-600 hover:border-blue-300 hover:bg-blue-50 transition-all"
            >{{ q }}</button>
          </div>
        </div>

        <!-- Chat messages -->
        <div ref="chatContainer" class="bg-white rounded-2xl shadow-sm border border-gray-100 mb-4 overflow-y-auto" style="max-height: 55vh; min-height: 300px;">
          <div v-if="messages.length === 0" class="flex items-center justify-center h-64 text-gray-400">
            <div class="text-center">
              <i class="fas fa-robot text-4xl mb-3"></i>
              <p>向 AI 助教提问，获取编程帮助</p>
            </div>
          </div>

          <div v-for="(msg, i) in messages" :key="i" class="px-6 py-4" :class="{ 'bg-gray-50': msg.role === 'assistant' }">
            <div class="flex items-start space-x-3">
              <div v-if="msg.role === 'assistant'" class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white flex-shrink-0">
                <i class="fas fa-robot text-xs"></i>
              </div>
              <div v-else class="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-white flex-shrink-0">
                <i class="fas fa-user text-xs"></i>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-400 mb-1">{{ msg.role === 'assistant' ? 'AI 助教' : '你' }}</p>
                <div class="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap" :class="{ 'text-red-500': msg.error }">{{ msg.content }}</div>
              </div>
            </div>
          </div>

          <div v-if="loading" class="px-6 py-4 bg-gray-50">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white"><i class="fas fa-robot text-xs"></i></div>
              <div class="flex space-x-1">
                <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input area -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
          <div class="flex items-end space-x-3">
            <textarea
              v-model="input"
              @keydown="handleKeydown"
              class="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm outline-none focus:border-blue-400 resize-none"
              rows="2"
              placeholder="输入你的编程问题..."
            ></textarea>
            <button
              @click="sendMessage"
              :disabled="loading || !input.trim()"
              class="bg-blue-600 text-white px-5 py-3 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-all flex-shrink-0"
            >
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
