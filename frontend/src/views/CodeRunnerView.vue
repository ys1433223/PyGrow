<script setup>
import { ref, computed, watch } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { runCode } from '../api/code_runner'

const mode = ref('python') // 'python' | 'web'

// ---- Project Management ----
const showProjectPanel = ref(true)
const projects = ref([])
const currentProjectId = ref(null)
const currentProjectName = ref('未命名项目')

function loadProjects() {
  try {
    projects.value = JSON.parse(localStorage.getItem('pygrow_projects') || '[]')
  } catch { projects.value = [] }
}

function saveProjectsToStorage() {
  localStorage.setItem('pygrow_projects', JSON.stringify(projects.value))
}

function getCurrentCodeSnapshot() {
  if (mode.value === 'python') {
    return { pythonCode: code.value }
  } else {
    return { htmlCode: htmlCode.value, cssCode: cssCode.value, jsCode: jsCode.value }
  }
}

function restoreCodeFromProject(proj) {
  if (proj.type === 'python') {
    code.value = proj.pythonCode || ''
  } else {
    htmlCode.value = proj.htmlCode || ''
    cssCode.value = proj.cssCode || ''
    jsCode.value = proj.jsCode || ''
    runPreview()
  }
}

function newProject() {
  const name = prompt('请输入项目名称：', `项目_${projects.value.length + 1}`)
  if (!name || !name.trim()) return
  const proj = {
    id: Date.now(),
    name: name.trim(),
    type: mode.value,
    ...getCurrentCodeSnapshot(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  projects.value.unshift(proj)
  currentProjectId.value = proj.id
  currentProjectName.value = proj.name
  saveProjectsToStorage()
}

function saveProject() {
  if (!currentProjectId.value) {
    // No current project, create one
    const name = prompt('请输入项目名称：', `项目_${projects.value.length + 1}`)
    if (!name || !name.trim()) return
    const proj = {
      id: Date.now(),
      name: name.trim(),
      type: mode.value,
      ...getCurrentCodeSnapshot(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    projects.value.unshift(proj)
    currentProjectId.value = proj.id
    currentProjectName.value = proj.name
    saveProjectsToStorage()
    return
  }
  const idx = projects.value.findIndex(p => p.id === currentProjectId.value)
  if (idx === -1) return
  projects.value[idx] = {
    ...projects.value[idx],
    type: mode.value,
    ...getCurrentCodeSnapshot(),
    updatedAt: new Date().toISOString(),
  }
  saveProjectsToStorage()
}

function loadProject(proj) {
  currentProjectId.value = proj.id
  currentProjectName.value = proj.name
  mode.value = proj.type
  restoreCodeFromProject(proj)
}

function deleteProject(id) {
  if (!confirm('确定删除这个项目吗？')) return
  projects.value = projects.value.filter(p => p.id !== id)
  if (currentProjectId.value === id) {
    currentProjectId.value = null
    currentProjectName.value = '未命名项目'
  }
  saveProjectsToStorage()
}

function formatProjDate(iso) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

// ---- Python mode ----
const code = ref(`# 在这里编写你的 Python 代码
print("Hello, PyGrow!")

for i in range(5):
    print(f"第 {i+1} 次循环")
`)
const stdout = ref('')
const stderr = ref('')
const loading = ref(false)
const error = ref('')

async function handleRun() {
  loading.value = true
  error.value = ''
  stdout.value = ''
  stderr.value = ''
  try {
    const res = await runCode(code.value)
    stdout.value = res.data.stdout || ''
    stderr.value = res.data.stderr || ''
  } catch (e) {
    error.value = e.response?.data?.message || e.message || '运行失败'
  } finally {
    loading.value = false
  }
}

// ---- Web Dev mode ----
const webTab = ref('html') // 'html' | 'css' | 'js'
const htmlCode = ref(`<!-- HTML -->
<h1>Hello, PyGrow!</h1>
<p>欢迎来到网页开发练习模式</p>
<button onclick="document.getElementById('msg').textContent = '你点击了按钮！'">点击试试</button>
<p id="msg"></p>
`)
const cssCode = ref(`/* CSS */
body {
  font-family: 'Microsoft YaHei', sans-serif;
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  background: #f0f4f8;
}
h1 { color: #3b82f6; }
button {
  background: #3b82f6; color: white; border: none;
  padding: 10px 20px; border-radius: 8px; cursor: pointer;
  font-size: 14px;
}
button:hover { background: #2563eb; }
#msg { margin-top: 15px; font-weight: bold; color: #10b981; }
`)
const jsCode = ref(`// JavaScript
console.log('网页开发模式已就绪');
`)
const previewTrigger = ref(0)

const previewDoc = computed(() => {
  void previewTrigger.value
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>${cssCode.value}</style>
</head>
<body>
${htmlCode.value}
<script>${jsCode.value}<\/script>
</body>
</html>`
})

function runPreview() {
  previewTrigger.value++
}

// ---- Save / Load Web Works (localStorage) ----
const showSaveDialog = ref(false)
const showLoadDialog = ref(false)
const saveName = ref('')
const savedList = ref([])

function loadSavedList() {
  try {
    savedList.value = JSON.parse(localStorage.getItem('pygrow_web_works') || '[]')
  } catch { savedList.value = [] }
}

function openSaveDialog() {
  loadSavedList()
  const d = new Date()
  saveName.value = `作品_${d.getMonth() + 1}月${d.getDate()}日_${d.getHours()}时${d.getMinutes()}分`
  showSaveDialog.value = true
}

function doSave() {
  const name = saveName.value.trim() || '未命名作品'
  const work = {
    id: Date.now(),
    name,
    html: htmlCode.value,
    css: cssCode.value,
    js: jsCode.value,
    savedAt: new Date().toISOString(),
  }
  const list = JSON.parse(localStorage.getItem('pygrow_web_works') || '[]')
  list.unshift(work)
  if (list.length > 20) list.length = 20
  localStorage.setItem('pygrow_web_works', JSON.stringify(list))
  showSaveDialog.value = false
}

function openLoadDialog() {
  loadSavedList()
  showLoadDialog.value = true
}

function doLoad(work) {
  htmlCode.value = work.html
  cssCode.value = work.css
  jsCode.value = work.js
  showLoadDialog.value = false
  runPreview()
}

function deleteWork(id) {
  const list = JSON.parse(localStorage.getItem('pygrow_web_works') || '[]')
  const filtered = list.filter(w => w.id !== id)
  localStorage.setItem('pygrow_web_works', JSON.stringify(filtered))
  loadSavedList()
}

function formatDate(iso) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

// Init
loadProjects()
loadSavedList()
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow flex flex-col px-4 py-6" style="max-height: calc(100vh - 4rem);">
      <!-- Header + Mode Toggle -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4 flex-shrink-0">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">在线编程</h1>
          <p class="text-gray-500 text-sm mt-1">{{ mode === 'python' ? '无需配置本地环境，直接在线运行 Python 代码' : 'HTML + CSS + JavaScript 网页开发练习' }}</p>
        </div>
        <div class="flex items-center gap-3">
          <div class="flex bg-gray-200 rounded-full p-0.5">
            <button @click="mode = 'python'"
                    :class="['px-5 py-2 rounded-full text-sm font-medium transition', mode === 'python' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']">
              <i class="fab fa-python mr-1.5"></i>Python编程
            </button>
            <button @click="mode = 'web'"
                    :class="['px-5 py-2 rounded-full text-sm font-medium transition', mode === 'web' ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']">
              <i class="fas fa-globe mr-1.5"></i>网页开发
            </button>
          </div>
          <button @click="showProjectPanel = !showProjectPanel"
                  :class="['w-9 h-9 rounded-full flex items-center justify-center text-sm transition border', showProjectPanel ? 'bg-blue-100 border-blue-200 text-blue-600' : 'bg-white border-gray-200 text-gray-400 hover:text-gray-600']"
                  title="项目面板">
            <i class="fas fa-folder-tree"></i>
          </button>
        </div>
      </div>

      <div class="flex gap-4 flex-grow min-h-0">
        <!-- ============ PROJECT PANEL (shared) ============ -->
        <transition name="slide">
          <div v-if="showProjectPanel" class="w-60 flex-shrink-0 bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
            <div class="px-4 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
              <span class="text-sm font-bold text-gray-700">项目列表</span>
              <button @click="newProject"
                      class="w-7 h-7 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center justify-center text-xs"
                      title="新建项目">
                <i class="fas fa-plus"></i>
              </button>
            </div>

            <!-- Project list -->
            <div class="flex-grow overflow-y-auto">
              <div v-if="projects.length === 0" class="text-center py-12 px-4">
                <i class="fas fa-folder-open text-3xl text-gray-300 mb-3 block"></i>
                <p class="text-xs text-gray-400 mb-3">还没有项目</p>
                <button @click="newProject"
                        class="text-xs bg-blue-600 text-white px-4 py-1.5 rounded-full hover:bg-blue-700 transition font-medium">
                  新建第一个项目
                </button>
              </div>
              <div v-else class="py-2">
                <div v-for="proj in projects" :key="proj.id"
                     @click="loadProject(proj)"
                     :class="['group flex items-center gap-2 px-4 py-2.5 mx-2 rounded-xl cursor-pointer transition text-sm', proj.id === currentProjectId ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50 border border-transparent']">
                  <!-- Type icon -->
                  <div :class="['w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs', proj.type === 'python' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600']">
                    <i :class="proj.type === 'python' ? 'fab fa-python' : 'fas fa-globe'"></i>
                  </div>
                  <div class="flex-grow min-w-0">
                    <p class="text-sm font-medium text-gray-700 truncate">{{ proj.name }}</p>
                    <p class="text-[10px] text-gray-400">{{ formatProjDate(proj.updatedAt || proj.createdAt) }}</p>
                  </div>
                  <button @click.stop="deleteProject(proj.id)"
                          class="w-6 h-6 bg-red-50 text-red-400 rounded-md hover:bg-red-100 hover:text-red-500 transition flex items-center justify-center text-[10px] opacity-0 group-hover:opacity-100 flex-shrink-0">
                    <i class="fas fa-trash-alt"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- Current project info + save -->
            <div class="px-4 py-3 border-t border-gray-100 bg-gray-50">
              <div class="flex items-center gap-2">
                <div class="flex-grow min-w-0">
                  <p class="text-xs text-gray-400 truncate">当前项目</p>
                  <p class="text-sm font-bold text-gray-700 truncate">{{ currentProjectName }}</p>
                </div>
                <button @click="saveProject"
                        class="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-full hover:bg-green-700 transition flex items-center gap-1 flex-shrink-0">
                  <i class="fas fa-save text-[10px]"></i>保存
                </button>
              </div>
            </div>
          </div>
        </transition>

        <!-- ==================== PYTHON MODE ==================== -->
        <template v-if="mode === 'python'">
          <div class="flex-grow grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
            <!-- Code Editor -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
              <div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex-shrink-0">
                <span class="text-sm font-medium text-gray-600">Python 代码编辑器</span>
                <button @click="handleRun" :disabled="loading"
                        class="bg-green-600 text-white px-5 py-1.5 rounded-full text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-all flex items-center space-x-1.5">
                  <i class="fas fa-play text-xs"></i>
                  <span>{{ loading ? '运行中...' : '运行' }}</span>
                </button>
              </div>
              <textarea v-model="code"
                        class="flex-grow w-full p-4 font-mono text-sm bg-gray-900 text-green-400 outline-none resize-none"
                        placeholder="在这里输入 Python 代码..." spellcheck="false"></textarea>
            </div>

            <!-- Output -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
              <div class="px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex-shrink-0">
                <span class="text-sm font-medium text-gray-600">运行输出</span>
              </div>
              <div class="flex-grow overflow-auto p-4 font-mono text-sm bg-gray-900 text-gray-200">
                <div v-if="error" class="text-red-400 mb-2">{{ error }}</div>
                <div v-if="stdout">
                  <div class="text-gray-400 text-xs mb-1">stdout:</div>
                  <pre class="text-green-400 whitespace-pre-wrap">{{ stdout }}</pre>
                </div>
                <div v-if="stderr">
                  <div class="text-gray-400 text-xs mb-1 mt-2">stderr:</div>
                  <pre class="text-red-400 whitespace-pre-wrap">{{ stderr }}</pre>
                </div>
                <div v-if="!stdout && !stderr && !error && !loading" class="text-gray-500 italic">
                  点击"运行"按钮查看输出结果
                </div>
              </div>
            </div>
          </div>

          <!-- Safety tips (Python mode only) -->
          <div class="mt-4 bg-white rounded-2xl shadow-sm border border-gray-100 p-4 flex-shrink-0" v-if="false">
            <!-- hidden, keep for reference -->
          </div>
        </template>

        <!-- ==================== WEB DEV MODE ==================== -->
        <template v-else>
          <div class="flex-grow grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
            <!-- Left: Code Editors -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col min-h-0">
              <!-- Tab Bar -->
              <div class="flex border-b border-gray-200 bg-gray-50 flex-shrink-0">
                <button @click="webTab = 'html'"
                        :class="['flex-1 py-2.5 text-xs font-medium transition border-b-2', webTab === 'html' ? 'border-orange-500 text-orange-600 bg-white' : 'border-transparent text-gray-400 hover:text-gray-600']">
                  <i class="fab fa-html5 mr-1"></i>HTML
                </button>
                <button @click="webTab = 'css'"
                        :class="['flex-1 py-2.5 text-xs font-medium transition border-b-2', webTab === 'css' ? 'border-blue-500 text-blue-600 bg-white' : 'border-transparent text-gray-400 hover:text-gray-600']">
                  <i class="fab fa-css3-alt mr-1"></i>CSS
                </button>
                <button @click="webTab = 'js'"
                        :class="['flex-1 py-2.5 text-xs font-medium transition border-b-2', webTab === 'js' ? 'border-yellow-500 text-yellow-600 bg-white' : 'border-transparent text-gray-400 hover:text-gray-600']">
                  <i class="fab fa-js mr-1"></i>JS
                </button>
              </div>

              <!-- Editor Areas -->
              <div class="flex-grow relative min-h-0">
                <textarea v-show="webTab === 'html'" v-model="htmlCode"
                          class="absolute inset-0 w-full h-full p-4 font-mono text-sm bg-gray-900 text-orange-300 outline-none resize-none"
                          placeholder="HTML 代码..." spellcheck="false"></textarea>
                <textarea v-show="webTab === 'css'" v-model="cssCode"
                          class="absolute inset-0 w-full h-full p-4 font-mono text-sm bg-gray-900 text-blue-300 outline-none resize-none"
                          placeholder="CSS 样式..." spellcheck="false"></textarea>
                <textarea v-show="webTab === 'js'" v-model="jsCode"
                          class="absolute inset-0 w-full h-full p-4 font-mono text-sm bg-gray-900 text-yellow-300 outline-none resize-none"
                          placeholder="JavaScript 代码..." spellcheck="false"></textarea>
              </div>

              <!-- Action Bar -->
              <div class="flex items-center gap-2 px-4 py-2.5 border-t border-gray-100 bg-gray-50 flex-shrink-0">
                <button @click="runPreview"
                        class="bg-purple-600 text-white px-5 py-1.5 rounded-full text-sm font-medium hover:bg-purple-700 transition flex items-center gap-1.5">
                  <i class="fas fa-play text-xs"></i>预览
                </button>
                <button @click="openSaveDialog"
                        class="bg-blue-600 text-white px-4 py-1.5 rounded-full text-sm font-medium hover:bg-blue-700 transition flex items-center gap-1.5">
                  <i class="fas fa-save text-xs"></i>保存作品
                </button>
                <button @click="openLoadDialog"
                        class="bg-white border border-gray-300 text-gray-600 px-4 py-1.5 rounded-full text-sm font-medium hover:bg-gray-100 transition flex items-center gap-1.5">
                  <i class="fas fa-folder-open text-xs"></i>加载作品
                </button>
              </div>
            </div>

            <!-- Right: Preview -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col min-h-0">
              <div class="px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex-shrink-0">
                <span class="text-sm font-medium text-gray-600">实时预览</span>
                <span class="text-xs text-gray-400 ml-2">点击"预览"按钮刷新</span>
              </div>
              <div class="flex-grow bg-white min-h-0">
                <iframe
                  :key="previewTrigger"
                  :srcdoc="previewDoc"
                  class="w-full h-full border-0"
                  sandbox="allow-scripts allow-modals"
                  title="网页预览"
                ></iframe>
              </div>
            </div>
          </div>

          <!-- Tips bar -->
          <div class="mt-4 bg-white rounded-2xl shadow-sm border border-gray-100 p-4 flex-shrink-0" v-if="false">
            <!-- hidden -->
          </div>

          <!-- Save Dialog -->
          <Teleport to="body">
            <div v-if="showSaveDialog" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="showSaveDialog = false">
              <div class="bg-white rounded-2xl p-6 w-96 shadow-xl">
                <h3 class="font-bold text-lg text-gray-800 mb-4">保存作品</h3>
                <input v-model="saveName" placeholder="作品名称" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-300 mb-4" @keyup.enter="doSave">
                <div class="flex justify-end gap-2">
                  <button @click="showSaveDialog = false" class="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition">取消</button>
                  <button @click="doSave" class="px-5 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">保存</button>
                </div>
              </div>
            </div>
          </Teleport>

          <!-- Load Dialog -->
          <Teleport to="body">
            <div v-if="showLoadDialog" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="showLoadDialog = false">
              <div class="bg-white rounded-2xl p-6 w-[28rem] max-h-[70vh] flex flex-col shadow-xl">
                <h3 class="font-bold text-lg text-gray-800 mb-4">加载作品</h3>
                <div v-if="savedList.length === 0" class="text-center py-8 text-gray-400 text-sm">
                  <i class="fas fa-inbox text-4xl mb-3 block"></i>暂无保存的作品
                </div>
                <div v-else class="flex-grow overflow-y-auto space-y-2 mb-4">
                  <div v-for="work in savedList" :key="work.id"
                       class="flex items-center justify-between p-3 bg-gray-50 rounded-xl hover:bg-blue-50 transition group cursor-pointer" @click="doLoad(work)">
                    <div class="flex-grow min-w-0">
                      <p class="text-sm font-medium text-gray-700 truncate">{{ work.name }}</p>
                      <p class="text-xs text-gray-400">{{ formatDate(work.savedAt) }}</p>
                    </div>
                    <button @click.stop="deleteWork(work.id)"
                            class="w-7 h-7 bg-red-50 text-red-400 rounded-lg hover:bg-red-100 hover:text-red-500 transition flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 flex-shrink-0 ml-2">
                      <i class="fas fa-trash-alt"></i>
                    </button>
                  </div>
                </div>
                <button @click="showLoadDialog = false" class="w-full py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition">关闭</button>
              </div>
            </div>
          </Teleport>
        </template>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  width: 0;
  opacity: 0;
  overflow: hidden;
}
</style>
