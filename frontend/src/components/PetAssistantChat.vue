<script setup>
import { ref, computed, nextTick } from 'vue'
import { renderMarkdown } from '../utils/markdown'

const emit = defineEmits(['close'])

// ---- API Config (stored in localStorage) ----
const API_CONFIG_KEY = 'pet_chat_api_config'
const DEFAULT_BASE_URL = 'https://cn.happyapi.org'
const DEFAULT_API_KEY = 'sk-REErmFJXTB26SIsGEmVZJw1f7YtMwiJ2k80XunEdaV3B7ZFZ'

const AVAILABLE_MODELS = [
  'gpt-4o',
  'gpt-4o-mini',
  'gpt-4-turbo',
  'gpt-3.5-turbo',
  'claude-3.5-sonnet',
  'claude-3-haiku',
  'gemini-2.0-flash',
  'gemini-1.5-flash',
  'deepseek-chat',
  'deepseek-reasoner',
]

function loadApiConfig() {
  try {
    return JSON.parse(localStorage.getItem(API_CONFIG_KEY) || '{}')
  } catch { return {} }
}

function saveApiConfig(cfg) {
  localStorage.setItem(API_CONFIG_KEY, JSON.stringify(cfg))
}

const savedConfig = loadApiConfig()
const apiBaseUrl = ref(savedConfig.baseUrl || DEFAULT_BASE_URL)
const apiKey = ref(savedConfig.apiKey || DEFAULT_API_KEY)
const selectedModel = ref(savedConfig.model || 'gpt-4o-mini')
const showSettings = ref(false)

function onSaveSettings() {
  saveApiConfig({
    baseUrl: apiBaseUrl.value,
    apiKey: apiKey.value,
    model: selectedModel.value,
  })
  showSettings.value = false
}

const SYSTEM_INSTRUCTION = `你是 Python学习营地 学习平台的 Python AI 助教，专门帮助大学本科生学习 Python 编程。

你的特点：
- 耐心友好，用通俗易懂的语言解释复杂概念
- 鼓励学生独立思考，不给完整的作业答案
- 擅长分析 Python 报错信息，帮助学生定位问题
- 提供学习建议和编程技巧
- 回答简洁

重要规则：
- 不帮学生写完整的作业代码，只给思路和框架
- 如果学生问的是考试或测评题，只解释概念不直接给答案
- 用鼓励的语气帮助学生建立信心`

const DEFAULT_WELCOME = { role: 'assistant', content: '你好！我是 Python AI 助教 🐍\n\n可以帮你：\n• 解答 Python 语法和概念问题\n• 分析代码报错信息\n• 提供学习路径建议\n• 解释编程思路\n\n有什么想了解的吗？' }

// ---- Conversation management ----
const STORAGE_KEY = 'pet_chat_conversations'
const ACTIVE_KEY = 'pet_chat_active_conv'

function loadConversations() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
}
function saveConversations(convs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convs))
}
function loadActiveId() {
  return localStorage.getItem(ACTIVE_KEY) || null
}
function saveActiveId(id) {
  localStorage.setItem(ACTIVE_KEY, id)
}

const conversations = ref(loadConversations())
const activeConvId = ref(loadActiveId())
const showHistory = ref(false)

function ensureActiveConv() {
  if (!activeConvId.value || !conversations.value.find(c => c.id === activeConvId.value)) {
    if (conversations.value.length > 0) {
      activeConvId.value = conversations.value[0].id
    } else {
      const conv = {
        id: Date.now().toString(),
        title: '新对话',
        messages: [{ ...DEFAULT_WELCOME }],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      }
      conversations.value.push(conv)
      activeConvId.value = conv.id
      saveConversations(conversations.value)
    }
    saveActiveId(activeConvId.value)
  }
}
ensureActiveConv()

const activeConv = computed(() => conversations.value.find(c => c.id === activeConvId.value))
const messages = computed({
  get: () => activeConv.value?.messages || [{ ...DEFAULT_WELCOME }],
  set: () => {},
})

function persist() {
  const conv = activeConv.value
  if (conv) {
    conv.updatedAt = Date.now()
    if (conv.title === '新对话' && conv.messages.length > 1) {
      const firstUser = conv.messages.find(m => m.role === 'user')
      if (firstUser) conv.title = firstUser.content.slice(0, 30) + (firstUser.content.length > 30 ? '...' : '')
    }
    saveConversations(conversations.value)
  }
}

function newConversation() {
  const conv = {
    id: Date.now().toString(),
    title: '新对话',
    messages: [{ ...DEFAULT_WELCOME }],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
  conversations.value.unshift(conv)
  activeConvId.value = conv.id
  saveActiveId(activeConvId.value)
  saveConversations(conversations.value)
  showHistory.value = false
}

function switchConversation(id) {
  activeConvId.value = id
  saveActiveId(id)
  showHistory.value = false
  nextTick(() => scrollToBottom())
}

function deleteConversation(id) {
  conversations.value = conversations.value.filter(c => c.id !== id)
  if (activeConvId.value === id) {
    if (conversations.value.length > 0) {
      activeConvId.value = conversations.value[0].id
    } else {
      newConversation()
      return
    }
  }
  saveActiveId(activeConvId.value)
  saveConversations(conversations.value)
}

const input = ref('')
const loading = ref(false)
const chatBody = ref(null)

// ---- panel resize ----
const panelSize = ref({ w: 400, h: 520 })
const resizing = ref(false)
const resizeStart = ref({ x: 0, y: 0, w: 0, h: 0 })

function onResizeStart(e) {
  resizing.value = true
  resizeStart.value = { x: e.clientX, y: e.clientY, w: panelSize.value.w, h: panelSize.value.h }
  e.preventDefault()
  e.stopPropagation()
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', onResizeEnd)
}
function onResizeMove(e) {
  if (!resizing.value) return
  panelSize.value = {
    w: Math.max(320, Math.min(750, resizeStart.value.w + (e.clientX - resizeStart.value.x))),
    h: Math.max(380, Math.min(850, resizeStart.value.h + (e.clientY - resizeStart.value.y))),
  }
}
function onResizeEnd() {
  resizing.value = false
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', onResizeEnd)
}

// ---- OpenAI-compatible API ----
async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  const conv = activeConv.value
  if (!conv) return
  conv.messages.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  persist()
  await nextTick()
  scrollToBottom()

  try {
    const apiMessages = [
      { role: 'system', content: SYSTEM_INSTRUCTION },
      ...conv.messages.map(m => ({
        role: m.role === 'model' ? 'assistant' : m.role,
        content: m.content,
      })),
    ]

    const resp = await fetch(`${apiBaseUrl.value.replace(/\/+$/, '')}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey.value}`,
      },
      body: JSON.stringify({
        model: selectedModel.value,
        messages: apiMessages,
        temperature: 0.7,
        max_tokens: 800,
      }),
    })

    if (resp.ok) {
      const data = await resp.json()
      const reply = data.choices?.[0]?.message?.content || '抱歉，我暂时无法回复，请稍后再试。'
      conv.messages.push({ role: 'assistant', content: reply })
    } else {
      const errData = await resp.json().catch(() => ({}))
      const errMsg = errData.error?.message || `请求失败 (${resp.status})`
      conv.messages.push({ role: 'assistant', content: `抱歉，AI 服务暂时不可用：${errMsg}` })
    }
  } catch {
    conv.messages.push({ role: 'assistant', content: '网络连接失败，请检查网络后重试。' })
  }

  loading.value = false
  persist()
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

// ---- Copy helpers ----
const copiedId = ref('')

async function copyText(id, text) {
  try {
    await navigator.clipboard.writeText(text)
    copiedId.value = id
    setTimeout(() => { copiedId.value = '' }, 1500)
  } catch {
    // Fallback
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copiedId.value = id
    setTimeout(() => { copiedId.value = '' }, 1500)
  }
}

// Parse code blocks from markdown content
function parseContent(content) {
  const parts = []
  const regex = /```(\w*)\n?([\s\S]*?)```/g
  let lastIdx = 0
  let match
  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIdx) {
      parts.push({ type: 'text', content: content.slice(lastIdx, match.index) })
    }
    parts.push({ type: 'code', lang: match[1] || 'plaintext', content: match[2].replace(/\n$/, '') })
    lastIdx = match.index + match[0].length
  }
  if (lastIdx < content.length) {
    parts.push({ type: 'text', content: content.slice(lastIdx) })
  }
  return parts.length > 0 ? parts : [{ type: 'text', content }]
}

const modelDisplayName = computed(() => {
  if (selectedModel.value.length <= 14) return selectedModel.value
  return selectedModel.value.slice(0, 12) + '...'
})
</script>

<template>
  <div
    class="bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden relative"
    :style="{ width: panelSize.w + 'px', height: panelSize.h + 'px' }"
    @click.stop
  >
    <!-- Header -->
    <div
      class="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white select-none flex-shrink-0"
    >
      <div class="flex items-center gap-2">
        <span class="w-7 h-7 bg-white/20 rounded-full flex items-center justify-center">
          <i class="fas fa-robot text-sm"></i>
        </span>
        <div>
          <p class="text-sm font-bold leading-tight">Python AI 助教</p>
          <p class="text-[10px] text-white/70 leading-tight">{{ modelDisplayName }} · 答疑 · 报错分析</p>
        </div>
      </div>
      <div class="flex items-center gap-1">
        <!-- Model selector -->
        <select v-model="selectedModel" @click.stop
                class="text-[10px] bg-white/10 text-white rounded-md px-1.5 py-1 border border-white/20 outline-none cursor-pointer max-w-[100px]"
                :title="selectedModel">
          <option v-for="m in AVAILABLE_MODELS" :key="m" :value="m" class="text-gray-800">{{ m }}</option>
        </select>
        <button @click.stop="showSettings = !showSettings"
                class="text-white/60 hover:text-white transition text-xs" title="API 设置">
          <i class="fas fa-cog"></i>
        </button>
        <button @click.stop="newConversation"
                class="text-white/60 hover:text-white transition text-xs" title="新对话">
          <i class="fas fa-plus"></i>
        </button>
        <button @click.stop="showHistory = !showHistory"
                :class="['text-white/60 hover:text-white transition text-xs', showHistory ? 'text-white' : '']" title="历史对话">
          <i class="fas fa-history"></i>
        </button>
        <button @click.stop="$emit('close')" class="text-white/70 hover:text-white transition">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- API Settings panel -->
    <div v-if="showSettings" class="absolute top-12 left-0 right-0 bg-white z-20 border-b border-gray-200 p-3 shadow-lg" @click.stop>
      <p class="text-xs font-bold text-gray-700 mb-2">API 设置</p>
      <div class="space-y-2">
        <div>
          <label class="text-[10px] text-gray-500">API Base URL</label>
          <input v-model="apiBaseUrl" class="w-full text-xs px-2 py-1.5 border border-gray-200 rounded-lg outline-none focus:border-purple-400" placeholder="https://api.openai.com">
        </div>
        <div>
          <label class="text-[10px] text-gray-500">API Key</label>
          <input v-model="apiKey" type="password" class="w-full text-xs px-2 py-1.5 border border-gray-200 rounded-lg outline-none focus:border-purple-400" placeholder="sk-...">
        </div>
        <button @click="onSaveSettings" class="w-full py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700 transition">
          保存设置
        </button>
      </div>
    </div>

    <!-- History sidebar -->
    <div v-if="showHistory" class="absolute top-12 left-0 right-0 bottom-0 bg-white z-20 flex flex-col" @click.stop>
      <div class="px-4 py-2 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
        <span class="text-xs font-bold text-gray-600">历史对话 ({{ conversations.length }})</span>
        <button @click="showHistory = false" class="text-gray-400 hover:text-gray-600 text-xs"><i class="fas fa-times"></i></button>
      </div>
      <div class="flex-1 overflow-y-auto">
        <div v-for="conv in conversations" :key="conv.id"
             :class="['px-4 py-3 border-b border-gray-50 cursor-pointer hover:bg-purple-50/50 transition flex items-center justify-between gap-2',
                      conv.id === activeConvId ? 'bg-purple-50 border-l-2 border-l-purple-500' : '']"
             @click="switchConversation(conv.id)">
          <div class="flex-grow min-w-0">
            <p class="text-xs font-medium text-gray-700 truncate">{{ conv.title }}</p>
            <p class="text-[10px] text-gray-400">{{ new Date(conv.updatedAt).toLocaleString('zh-CN', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' }) }}</p>
          </div>
          <button @click.stop="deleteConversation(conv.id)" class="text-gray-300 hover:text-red-400 transition flex-shrink-0">
            <i class="fas fa-trash-alt text-[10px]"></i>
          </button>
        </div>
        <div v-if="conversations.length === 0" class="text-center py-8 text-xs text-gray-400">暂无历史对话</div>
      </div>
    </div>

    <!-- Messages -->
    <div ref="chatBody" class="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50">
      <div v-for="(m, i) in messages" :key="i" :class="['flex gap-2 group/msg', m.role === 'user' ? 'justify-end' : '']">
        <div v-if="m.role === 'assistant' || m.role === 'model'"
          class="w-6 h-6 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
          <i class="fas fa-robot text-white text-[8px]"></i>
        </div>
        <div :class="['max-w-[82%]', m.role === 'user' ? '' : '']">
          <!-- User message -->
          <div v-if="m.role === 'user'"
               class="text-xs px-3 py-2 rounded-2xl rounded-br-md bg-blue-600 text-white leading-relaxed whitespace-pre-wrap relative group/copy">
            {{ m.content }}
            <button @click="copyText('u'+i, m.content)"
                    class="absolute -bottom-1 right-1 opacity-0 group-hover/copy:opacity-100 transition bg-white text-gray-500 hover:text-blue-600 rounded-full w-5 h-5 flex items-center justify-center shadow text-[8px]"
                    :title="copiedId === 'u'+i ? '已复制' : '复制'">
              <i :class="copiedId === 'u'+i ? 'fas fa-check text-green-500' : 'far fa-copy'"></i>
            </button>
          </div>
          <!-- AI message with code blocks -->
          <div v-else class="text-xs px-3 py-2 rounded-2xl rounded-bl-md bg-white text-gray-700 border border-gray-200 shadow-sm leading-relaxed whitespace-pre-wrap relative group/copy">
            <template v-for="(part, pi) in parseContent(m.content)" :key="pi">
              <span v-if="part.type === 'text'" v-html="renderMarkdown(part.content)"></span>
              <div v-else class="my-2 -mx-2 rounded-lg overflow-hidden border border-gray-300 bg-gray-900 relative group/code">
                <div class="flex items-center justify-between px-3 py-1.5 bg-gray-800 text-gray-400 text-[10px]">
                  <span>{{ part.lang || 'code' }}</span>
                  <button @click="copyText('c'+i+'-'+pi, part.content)"
                          class="text-gray-400 hover:text-white transition text-[10px] flex items-center gap-1">
                    <i :class="copiedId === 'c'+i+'-'+pi ? 'fas fa-check text-green-400' : 'far fa-copy'"></i>
                    {{ copiedId === 'c'+i+'-'+pi ? '已复制' : '复制代码' }}
                  </button>
                </div>
                <pre class="px-3 py-2 text-xs text-green-300 overflow-x-auto"><code>{{ part.content }}</code></pre>
              </div>
            </template>
            <button @click="copyText('a'+i, m.content)"
                    class="absolute -bottom-1 right-1 opacity-0 group-hover/copy:opacity-100 transition bg-gray-100 text-gray-500 hover:text-purple-600 rounded-full w-5 h-5 flex items-center justify-center shadow text-[8px]"
                    :title="copiedId === 'a'+i ? '已复制' : '复制'">
              <i :class="copiedId === 'a'+i ? 'fas fa-check text-green-500' : 'far fa-copy'"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Typing indicator -->
      <div v-if="loading" class="flex items-center gap-1.5 px-1">
        <span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce"></span>
        <span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></span>
        <span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></span>
        <span class="text-[10px] text-gray-400 ml-1">{{ selectedModel }} 思考中...</span>
      </div>
    </div>

    <!-- Quick prompts -->
    <div v-if="messages.length <= 1" class="px-3 py-2 bg-white border-t border-gray-100 flex gap-1.5 flex-wrap flex-shrink-0">
      <button v-for="prompt in ['Python 列表怎么用？', '帮我分析这段报错', 'for 循环的用法']" :key="prompt"
        @click="input = prompt; send()"
        class="text-[10px] px-2 py-1 bg-purple-50 text-purple-600 rounded-full hover:bg-purple-100 transition border border-purple-100">
        {{ prompt }}
      </button>
    </div>

    <!-- Input -->
    <div class="p-3 bg-white border-t border-gray-100 flex-shrink-0">
      <div class="flex items-end gap-2">
        <textarea v-model="input" @keydown="onKeydown"
          placeholder="输入 Python 问题..."
          rows="1"
          class="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-400 resize-none bg-gray-50"
          :disabled="loading"></textarea>
        <button @click="send" :disabled="loading || !input.trim()"
          class="px-3.5 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl text-xs font-medium hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 transition flex-shrink-0 shadow">
          <i v-if="!loading" class="fas fa-paper-plane"></i>
          <i v-else class="fas fa-spinner fa-spin"></i>
        </button>
      </div>
    </div>

    <!-- Resize handle -->
    <div class="absolute bottom-0 right-0 w-5 h-5 cursor-se-resize z-30"
         @mousedown="onResizeStart" @click.stop>
      <svg width="16" height="16" viewBox="0 0 16 16" class="text-gray-400 hover:text-gray-600 transition">
        <path d="M2 14 L14 14 L14 2" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.animate-bounce {
  animation: bounce 1.2s infinite;
}
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-4px); }
}
:deep(.inline-code) {
  background: #f1f5f9;
  color: #e11d48;
  padding: 1px 5px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.85em;
}
:deep(p) {
  margin: 0;
}
:deep(p + p) {
  margin-top: 0.5em;
}
</style>
