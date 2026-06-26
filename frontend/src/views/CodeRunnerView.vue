<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { runCode } from '../api/code_runner'
import { startFlask, stopFlask, getFlaskStatus } from '../api/flask'

const mode = ref('python') // 'python' | 'web' | 'flask'

// ---- Flask project files ----
const flaskFiles = ref({
  'app.py': `from flask import Flask, render_template\n\napp = Flask(__name__)\n\n@app.route("/")\ndef index():\n    return render_template("index.html")\n`,
  'templates/index.html': `<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>PyGrow Flask Demo</title>\n    <link rel="stylesheet" href="static/style.css">\n</head>\n<body>\n    <h1>Hello, Flask!</h1>\n    <p>这是我的第一个 Flask 小项目。</p>\n</body>\n</html>\n`,
  'static/style.css': `body {\n    font-family: sans-serif;\n    background: #f5f7ff;\n    padding: 40px;\n}\n\nh1 {\n    color: #4f46e5;\n}\n`
})
const flaskActiveFile = ref('app.py')

// ---- Flask run state ----
const flaskRunId = ref(null)
const flaskRunStatus = ref('idle') // 'idle' | 'starting' | 'running' | 'stopping' | 'stopped' | 'error'
const flaskLogs = ref([])
const flaskPreviewUrl = ref('')
const flaskLoading = ref(false)
const flaskError = ref('')
const flaskElapsed = ref(0)
const showFlaskLogs = ref(false)
let flaskPollTimer = null

function getAuthToken() {
  return localStorage.getItem('access_token') || ''
}

function buildFlaskPreviewSrc() {
  if (!flaskRunId.value) return ''
  const token = getAuthToken()
  return `/api/code/flask/proxy/${flaskRunId.value}/?token=${token}`
}

async function runFlaskProject() {
  saveProject()
  const files = Object.entries(flaskFiles.value).map(([path, content]) => ({ path, content }))
  flaskLoading.value = true
  flaskError.value = ''
  flaskRunStatus.value = 'starting'
  flaskLogs.value = []
  flaskPreviewUrl.value = ''
  try {
    const res = await startFlask(files)
    const d = res.data?.data || res.data || {}
    flaskRunId.value = d.run_id
    flaskPreviewUrl.value = buildFlaskPreviewSrc()
    flaskRunStatus.value = 'running'
    flaskLogs.value = d.logs || []
    flaskElapsed.value = 0
    showFlaskLogs.value = false
    startFlaskPolling()
  } catch (e) {
    flaskRunStatus.value = 'error'
    flaskError.value = e.response?.data?.message || e.message || '启动失败'
    const logs = e.response?.data?.data?.logs
    if (logs && logs.length) {
      flaskLogs.value = logs
      showFlaskLogs.value = true
    }
  } finally {
    flaskLoading.value = false
  }
}

async function stopFlaskProject() {
  if (!flaskRunId.value) return
  flaskRunStatus.value = 'stopping'
  try {
    await stopFlask(flaskRunId.value)
  } catch {
    // force stop even if API call fails
  }
  flaskRunStatus.value = 'stopped'
  flaskPreviewUrl.value = ''
  stopFlaskPolling()
}

function refreshFlaskPreview() {
  if (flaskRunStatus.value !== 'running' || !flaskRunId.value) return
  const token = getAuthToken()
  flaskPreviewUrl.value = `/api/code/flask/proxy/${flaskRunId.value}/?token=${token}&_t=${Date.now()}`
}

function startFlaskPolling() {
  stopFlaskPolling()
  flaskPollTimer = setInterval(async () => {
    if (!flaskRunId.value) return
    try {
      const res = await getFlaskStatus(flaskRunId.value)
      const d = res.data?.data || {}
      flaskLogs.value = d.logs || []
      flaskElapsed.value = d.elapsed || 0
      if (d.status === 'exited' || d.status === 'stopped') {
        flaskRunStatus.value = 'stopped'
        flaskPreviewUrl.value = ''
        stopFlaskPolling()
        showFlaskLogs.value = true
      }
    } catch {
      // ignore poll errors
    }
  }, 3000)
}

function stopFlaskPolling() {
  if (flaskPollTimer) {
    clearInterval(flaskPollTimer)
    flaskPollTimer = null
  }
}

onBeforeUnmount(() => {
  stopFlaskPolling()
})

// ---- Project Type Selection Dialog ----
const showNewProjectDialog = ref(false)
const newProjectName = ref('')
const newProjectType = ref('python')

const FLASK_FILE_LABELS = {
  'app.py': { label: 'app.py', icon: 'fab fa-python', color: 'text-green-500' },
  'templates/index.html': { label: 'index.html', icon: 'fab fa-html5', color: 'text-orange-500' },
  'static/style.css': { label: 'style.css', icon: 'fab fa-css3-alt', color: 'text-blue-500' },
}

const FLASK_DEFAULT_CONTENT = {
  'app.py': `from flask import Flask, render_template\n\napp = Flask(__name__)\n\n@app.route("/")\ndef index():\n    return render_template("index.html")\n`,
  'templates/index.html': `<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>PyGrow Flask Demo</title>\n    <link rel="stylesheet" href="static/style.css">\n</head>\n<body>\n    <h1>Hello, Flask!</h1>\n    <p>这是我的第一个 Flask 小项目。</p>\n</body>\n</html>\n`,
  'static/style.css': `body {\n    font-family: sans-serif;\n    background: #f5f7ff;\n    padding: 40px;\n}\n\nh1 {\n    color: #4f46e5;\n}\n`
}

function resetFlaskFiles() {
  flaskFiles.value = {
    'app.py': FLASK_DEFAULT_CONTENT['app.py'],
    'templates/index.html': FLASK_DEFAULT_CONTENT['templates/index.html'],
    'static/style.css': FLASK_DEFAULT_CONTENT['static/style.css'],
  }
  flaskActiveFile.value = 'app.py'
}

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
  } else if (mode.value === 'web') {
    return { htmlCode: htmlCode.value, cssCode: cssCode.value, jsCode: jsCode.value }
  } else if (mode.value === 'flask') {
    return { files: { ...flaskFiles.value }, activeFile: flaskActiveFile.value }
  }
}

function restoreCodeFromProject(proj) {
  if (proj.type === 'python') {
    code.value = proj.pythonCode || ''
  } else if (proj.type === 'web') {
    htmlCode.value = proj.htmlCode || ''
    cssCode.value = proj.cssCode || ''
    jsCode.value = proj.jsCode || ''
    runPreview()
  } else if (proj.type === 'flask') {
    if (proj.files) {
      flaskFiles.value = { ...proj.files }
      flaskActiveFile.value = proj.activeFile || 'app.py'
    } else {
      resetFlaskFiles()
    }
  }
}

function openNewProjectDialog() {
  newProjectName.value = `项目_${projects.value.length + 1}`
  newProjectType.value = mode.value
  showNewProjectDialog.value = true
}

function confirmNewProject() {
  const name = newProjectName.value.trim()
  if (!name) return
  showNewProjectDialog.value = false

  // Set defaults based on type
  if (newProjectType.value === 'flask') {
    resetFlaskFiles()
  } else if (newProjectType.value === 'python') {
    code.value = `# 在这里编写你的 Python 代码\nprint("Hello, PyGrow!")\n\nfor i in range(5):\n    print(f"第 {i+1} 次循环")\n`
  } else if (newProjectType.value === 'web') {
    htmlCode.value = `<!-- HTML -->\n<h1>Hello, PyGrow!</h1>\n<p>欢迎来到网页开发练习模式</p>\n<button onclick="document.getElementById('msg').textContent = '你点击了按钮！'">点击试试</button>\n<p id="msg"></p>\n`
    cssCode.value = `/* CSS */\nbody {\n  font-family: 'Microsoft YaHei', sans-serif;\n  max-width: 600px;\n  margin: 40px auto;\n  padding: 20px;\n  background: #f0f4f8;\n}\nh1 { color: #3b82f6; }\nbutton {\n  background: #3b82f6; color: white; border: none;\n  padding: 10px 20px; border-radius: 8px; cursor: pointer;\n  font-size: 14px;\n}\nbutton:hover { background: #2563eb; }\n#msg { margin-top: 15px; font-weight: bold; color: #10b981; }\n`
    jsCode.value = `// JavaScript\nconsole.log('网页开发模式已就绪');\n`
  }

  const proj = {
    id: Date.now(),
    name,
    type: newProjectType.value,
    ...getCurrentCodeSnapshot(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  mode.value = newProjectType.value
  projects.value.unshift(proj)
  currentProjectId.value = proj.id
  currentProjectName.value = proj.name
  saveProjectsToStorage()
}

function saveProject() {
  if (!currentProjectId.value) {
    // No current project, create one — use dialog for type selection
    openNewProjectDialog()
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
const execTime = ref(null)
const images = ref([])
const tables = ref([])

async function handleRun() {
  loading.value = true
  error.value = ''
  stdout.value = ''
  stderr.value = ''
  execTime.value = null
  images.value = []
  tables.value = []
  try {
    const res = await runCode(code.value)
    const d = res.data?.data || res.data || {}
    stdout.value = d.stdout || ''
    stderr.value = d.stderr || ''
    execTime.value = d.execution_time ?? null
    images.value = d.images || []
    tables.value = d.tables || []
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
      <button @click="$router.push('/learning-center')" class="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mb-2 transition flex-shrink-0"><i class="fas fa-arrow-left"></i> 返回学习中心</button>
      <!-- Header + Mode Toggle -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4 flex-shrink-0">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">在线编程</h1>
          <p class="text-gray-500 text-sm mt-1">{{ mode === 'python' ? '无需配置本地环境，直接在线运行 Python 代码' : mode === 'web' ? 'HTML + CSS + JavaScript 网页开发练习' : '多文件 Flask 项目开发练习' }}</p>
        </div>
        <div class="flex items-center gap-3">
          <div class="flex bg-gray-200 rounded-full p-0.5">
            <button @click="mode = 'python'"
                    :class="['px-4 py-2 rounded-full text-sm font-medium transition', mode === 'python' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']">
              <i class="fab fa-python mr-1.5"></i>Python
            </button>
            <button @click="mode = 'web'"
                    :class="['px-4 py-2 rounded-full text-sm font-medium transition', mode === 'web' ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']">
              <i class="fas fa-globe mr-1.5"></i>Web
            </button>
            <button @click="mode = 'flask'"
                    :class="['px-4 py-2 rounded-full text-sm font-medium transition', mode === 'flask' ? 'bg-white text-green-600 shadow-sm' : 'text-gray-500 hover:text-gray-700']">
              <i class="fas fa-flask mr-1.5"></i>Flask
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
              <button @click="openNewProjectDialog"
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
                <button @click="openNewProjectDialog"
                        class="text-xs bg-blue-600 text-white px-4 py-1.5 rounded-full hover:bg-blue-700 transition font-medium">
                  新建第一个项目
                </button>
              </div>
              <div v-else class="py-2">
                <div v-for="proj in projects" :key="proj.id"
                     @click="loadProject(proj)"
                     :class="['group flex items-center gap-2 px-4 py-2.5 mx-2 rounded-xl cursor-pointer transition text-sm', proj.id === currentProjectId ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50 border border-transparent']">
                  <!-- Type icon -->
                  <div :class="['w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs', proj.type === 'python' ? 'bg-blue-100 text-blue-600' : proj.type === 'web' ? 'bg-purple-100 text-purple-600' : 'bg-green-100 text-green-600']">
                    <i :class="proj.type === 'python' ? 'fab fa-python' : proj.type === 'web' ? 'fas fa-globe' : 'fas fa-flask'"></i>
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
              <div class="px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex-shrink-0 flex items-center justify-between">
                <span class="text-sm font-medium text-gray-600">运行输出</span>
                <span v-if="execTime !== null && !loading" class="text-xs text-gray-400">
                  <i class="fas fa-clock mr-1"></i>{{ execTime }}s
                </span>
              </div>
              <div class="flex-grow overflow-auto p-4 font-mono text-sm bg-gray-900 text-gray-200">
                <!-- Error banner -->
                <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 mb-3 text-red-400 text-sm">
                  <i class="fas fa-exclamation-triangle mr-2"></i>{{ error }}
                </div>

                <!-- Status badge -->
                <div v-if="!loading && (stdout || stderr || images.length || tables.length || error)" class="flex items-center gap-2 mb-3">
                  <span v-if="!stderr && !error" class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/30">
                    <i class="fas fa-check text-[10px]"></i>运行成功
                  </span>
                  <span v-else class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/30">
                    <i class="fas fa-times text-[10px]"></i>运行失败
                  </span>
                </div>

                <!-- stdout -->
                <div v-if="stdout" class="mb-3">
                  <div class="flex items-center gap-2 text-gray-400 text-xs mb-1.5">
                    <i class="fas fa-terminal"></i>标准输出
                  </div>
                  <pre class="text-green-400 whitespace-pre-wrap bg-gray-950 rounded-lg p-3">{{ stdout }}</pre>
                </div>

                <!-- Images -->
                <div v-if="images.length" class="mb-3">
                  <div class="flex items-center gap-2 text-gray-400 text-xs mb-2">
                    <i class="fas fa-chart-line"></i>图像输出 ({{ images.length }})
                  </div>
                  <div class="space-y-3">
                    <div v-for="(img, i) in images" :key="'img-'+i" class="bg-white rounded-xl p-3 border border-gray-200">
                      <div class="text-xs text-gray-400 mb-2 font-sans">图 {{ i + 1 }}</div>
                      <img :src="img.data" :alt="'Chart '+(i+1)" class="max-w-full h-auto rounded-lg mx-auto" />
                    </div>
                  </div>
                </div>

                <!-- Tables -->
                <div v-if="tables.length" class="mb-3">
                  <div class="flex items-center gap-2 text-gray-400 text-xs mb-2">
                    <i class="fas fa-table"></i>表格输出 ({{ tables.length }})
                  </div>
                  <div class="space-y-3">
                    <div v-for="(tbl, i) in tables" :key="'tbl-'+i" class="bg-white rounded-xl p-3 border border-gray-200 overflow-x-auto">
                      <div class="text-xs text-gray-400 mb-2 font-sans">
                        表 {{ i + 1 }}
                        <span v-if="tbl.shape" class="ml-2">({{ tbl.shape[0] }} 行 x {{ tbl.shape[1] }} 列)</span>
                      </div>
                      <div v-html="tbl.html" class="pygrow-table"></div>
                    </div>
                  </div>
                </div>

                <!-- stderr -->
                <div v-if="stderr" class="mb-3">
                  <div class="flex items-center gap-2 text-red-400/70 text-xs mb-1.5">
                    <i class="fas fa-exclamation-circle"></i>错误输出
                  </div>
                  <pre class="text-red-400 whitespace-pre-wrap bg-gray-950 rounded-lg p-3">{{ stderr }}</pre>
                </div>

                <!-- Empty state -->
                <div v-if="!stdout && !stderr && !images.length && !tables.length && !error && !loading" class="text-gray-500 italic text-center py-8">
                  <i class="fas fa-play text-2xl mb-3 block opacity-50"></i>
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

        <!-- ==================== FLASK MODE ==================== -->
        <template v-if="mode === 'flask'">
          <div class="flex-grow grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
            <!-- Left: File tabs + Editor -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col min-h-0">
              <!-- File Tabs -->
              <div class="flex border-b border-gray-200 bg-gray-50 flex-shrink-0">
                <button v-for="(meta, path) in FLASK_FILE_LABELS" :key="path"
                        @click="flaskActiveFile = path"
                        :class="['flex-1 py-2.5 text-xs font-medium transition border-b-2', flaskActiveFile === path ? 'border-green-500 text-green-600 bg-white' : 'border-transparent text-gray-400 hover:text-gray-600']">
                  <i :class="meta.icon" class="mr-1"></i>{{ meta.label }}
                </button>
              </div>

              <!-- Editor -->
              <textarea v-model="flaskFiles[flaskActiveFile]"
                        :class="[
                          'flex-grow w-full p-4 font-mono text-sm bg-gray-900 outline-none resize-none',
                          flaskActiveFile.endsWith('.py') ? 'text-green-400' : flaskActiveFile.endsWith('.html') ? 'text-orange-300' : 'text-blue-300'
                        ]"
                        :placeholder="'编辑 ' + flaskActiveFile + ' ...'" spellcheck="false"></textarea>
            </div>

            <!-- Right: Preview + Controls -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col min-h-0">
              <!-- Header with controls -->
              <div class="px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex-shrink-0 flex items-center justify-between gap-2">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="text-sm font-medium text-gray-600">Flask 项目预览</span>
                  <span v-if="flaskRunStatus === 'running'" class="w-2 h-2 rounded-full bg-green-500 animate-pulse flex-shrink-0" title="运行中"></span>
                  <span v-else-if="flaskRunStatus === 'starting'" class="w-2 h-2 rounded-full bg-yellow-500 animate-pulse flex-shrink-0" title="启动中"></span>
                  <span v-else-if="flaskRunStatus === 'error'" class="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" title="启动失败"></span>
                  <span v-else-if="flaskRunStatus === 'stopped'" class="w-2 h-2 rounded-full bg-gray-400 flex-shrink-0" title="已停止"></span>
                </div>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                  <button v-if="flaskRunStatus === 'idle' || flaskRunStatus === 'stopped' || flaskRunStatus === 'error'"
                          @click="runFlaskProject" :disabled="flaskLoading"
                          class="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-full hover:bg-green-700 disabled:opacity-50 transition flex items-center gap-1">
                    <i :class="flaskLoading ? 'fas fa-spinner fa-spin' : 'fas fa-play'"></i>
                    {{ flaskLoading ? '启动中...' : '运行 Flask 项目' }}
                  </button>
                  <button v-if="flaskRunStatus === 'running'"
                          @click="stopFlaskProject"
                          class="px-3 py-1.5 bg-red-500 text-white text-xs font-medium rounded-full hover:bg-red-600 transition flex items-center gap-1">
                    <i class="fas fa-stop"></i>停止
                  </button>
                  <button v-if="flaskRunStatus === 'running'"
                          @click="refreshFlaskPreview"
                          class="px-3 py-1.5 bg-blue-500 text-white text-xs font-medium rounded-full hover:bg-blue-600 transition flex items-center gap-1">
                    <i class="fas fa-sync-alt"></i>刷新
                  </button>
                  <button @click="showFlaskLogs = !showFlaskLogs"
                          :class="['px-2 py-1.5 text-xs rounded-full transition', showFlaskLogs ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200']"
                          title="查看日志">
                    <i class="fas fa-terminal"></i>
                  </button>
                </div>
              </div>

              <!-- Preview / Status area -->
              <div class="flex-grow flex flex-col min-h-0">
                <!-- iframe preview (running) -->
                <div v-if="flaskRunStatus === 'running' && flaskPreviewUrl" class="flex-grow bg-white min-h-0">
                  <iframe :src="flaskPreviewUrl"
                          class="w-full h-full border-0"
                          sandbox="allow-scripts allow-forms allow-same-origin"
                          title="Flask 项目预览"></iframe>
                </div>

                <!-- Idle / stopped state -->
                <div v-else-if="flaskRunStatus === 'idle' || flaskRunStatus === 'stopped' || flaskRunStatus === 'stopping'"
                     class="flex-grow flex items-center justify-center bg-gray-50">
                  <div class="text-center px-6">
                    <div :class="['w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4', flaskRunStatus === 'stopped' ? 'bg-gray-100' : 'bg-green-100']">
                      <i :class="['text-2xl', flaskRunStatus === 'stopped' ? 'fas fa-check-circle text-gray-400' : 'fas fa-flask text-green-500']"></i>
                    </div>
                    <p class="text-gray-500 font-medium mb-1">
                      {{ flaskRunStatus === 'stopped' ? '项目已停止' : flaskRunStatus === 'stopping' ? '正在停止...' : '点击运行 Flask 项目后，在这里预览页面' }}
                    </p>
                    <p class="text-xs text-gray-400">{{ flaskRunStatus === 'idle' ? '编辑左侧文件后点击上方按钮启动' : '可再次点击运行按钮重新启动' }}</p>
                  </div>
                </div>

                <!-- Starting state -->
                <div v-else-if="flaskRunStatus === 'starting'"
                     class="flex-grow flex items-center justify-center bg-gray-50">
                  <div class="text-center px-6">
                    <div class="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <i class="fas fa-spinner fa-spin text-2xl text-yellow-500"></i>
                    </div>
                    <p class="text-gray-500 font-medium mb-1">Flask 项目启动中...</p>
                    <p class="text-xs text-gray-400">正在分配端口并启动服务，请稍候</p>
                  </div>
                </div>

                <!-- Error state -->
                <div v-else-if="flaskRunStatus === 'error'"
                     class="flex-grow flex items-center justify-center bg-gray-50">
                  <div class="text-center px-6 max-w-sm">
                    <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <i class="fas fa-exclamation-triangle text-2xl text-red-500"></i>
                    </div>
                    <p class="text-gray-700 font-medium mb-2">启动失败</p>
                    <div class="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-600 mb-3 text-left">
                      {{ flaskError }}
                    </div>
                    <p class="text-xs text-gray-400 mb-3">请检查代码是否有语法错误，修改后重新运行</p>
                    <button @click="runFlaskProject" :disabled="flaskLoading"
                            class="px-4 py-1.5 bg-green-600 text-white text-xs font-medium rounded-full hover:bg-green-700 transition">
                      重试
                    </button>
                  </div>
                </div>
              </div>

              <!-- Logs (collapsible) -->
              <div v-if="showFlaskLogs && flaskLogs.length" class="border-t border-gray-200 bg-gray-900 flex-shrink-0" style="max-height: 160px;">
                <div class="flex items-center justify-between px-4 py-1.5 bg-gray-800">
                  <span class="text-xs text-gray-400 font-mono">
                    <i class="fas fa-terminal mr-1"></i>运行日志
                    <span v-if="flaskRunStatus === 'running'" class="text-green-400 ml-2">运行中 · {{ flaskElapsed }}s</span>
                    <span v-else-if="flaskRunStatus === 'error'" class="text-red-400 ml-2">启动失败</span>
                  </span>
                  <button @click="showFlaskLogs = false" class="text-gray-500 hover:text-gray-300 text-xs">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
                <div class="overflow-y-auto px-4 py-2 text-xs font-mono text-green-400" style="max-height: 120px;">
                  <div v-for="(line, i) in flaskLogs" :key="i" class="whitespace-pre-wrap break-all">{{ line }}</div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ==================== WEB DEV MODE ==================== -->
        <template v-else-if="mode === 'web'">
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

      <!-- ============ New Project Dialog ============ -->
      <Teleport to="body">
        <div v-if="showNewProjectDialog" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="showNewProjectDialog = false">
          <div class="bg-white rounded-2xl p-6 w-[28rem] shadow-xl">
            <h3 class="font-bold text-lg text-gray-800 mb-4">新建项目</h3>

            <!-- Project name -->
            <label class="block text-sm font-medium text-gray-600 mb-1.5">项目名称</label>
            <input v-model="newProjectName" placeholder="输入项目名称..."
                   class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-300 mb-4"
                   @keyup.enter="confirmNewProject">

            <!-- Project type -->
            <label class="block text-sm font-medium text-gray-600 mb-2">项目类型</label>
            <div class="grid grid-cols-3 gap-3 mb-5">
              <button @click="newProjectType = 'python'"
                      :class="['p-3 rounded-xl border-2 text-center transition', newProjectType === 'python' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300']">
                <i class="fab fa-python text-2xl text-blue-600 mb-1 block"></i>
                <span class="text-xs font-bold text-gray-700">Python</span>
                <p class="text-[10px] text-gray-400 mt-0.5">脚本编程</p>
              </button>
              <button @click="newProjectType = 'web'"
                      :class="['p-3 rounded-xl border-2 text-center transition', newProjectType === 'web' ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-gray-300']">
                <i class="fas fa-globe text-2xl text-purple-600 mb-1 block"></i>
                <span class="text-xs font-bold text-gray-700">Web</span>
                <p class="text-[10px] text-gray-400 mt-0.5">网页开发</p>
              </button>
              <button @click="newProjectType = 'flask'"
                      :class="['p-3 rounded-xl border-2 text-center transition', newProjectType === 'flask' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300']">
                <i class="fas fa-flask text-2xl text-green-600 mb-1 block"></i>
                <span class="text-xs font-bold text-gray-700">Flask</span>
                <p class="text-[10px] text-gray-400 mt-0.5">Web 小项目</p>
              </button>
            </div>

            <div class="flex justify-end gap-2">
              <button @click="showNewProjectDialog = false"
                      class="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition">取消</button>
              <button @click="confirmNewProject" :disabled="!newProjectName.trim()"
                      class="px-5 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50">创建项目</button>
            </div>
          </div>
        </div>
      </Teleport>
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

/* Pandas DataFrame table styling (rendered via v-html) */
:deep(.pygrow-table) table {
  width: 100%;
  font-size: 12px;
  font-family: 'Microsoft YaHei', ui-sans-serif, sans-serif;
  border-collapse: collapse;
}
:deep(.pygrow-table) thead th {
  background: #f1f5f9;
  color: #334155;
  font-weight: 600;
  padding: 8px 12px;
  text-align: left;
  border-bottom: 2px solid #cbd5e1;
  white-space: nowrap;
}
:deep(.pygrow-table) tbody td {
  padding: 6px 12px;
  border-bottom: 1px solid #e2e8f0;
  color: #1e293b;
}
:deep(.pygrow-table) tbody tr:nth-child(even) td {
  background: #f8fafc;
}
:deep(.pygrow-table) tbody tr:hover td {
  background: #eef2ff;
}
</style>
