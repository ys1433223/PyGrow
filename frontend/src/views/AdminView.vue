<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { getAdminStats, getAdminUsers, toggleAdmin, getAdminCourses, deleteAdminCourse, getAdminQuestions, deleteAdminQuestion, getAdminProjects, deleteAdminProject, getAdminPosts, deleteAdminPost } from '../api/admin'

const router = useRouter()
const activeTab = ref('stats')
const loading = ref(false)
const error = ref('')
const stats = ref({})

const tabs = [
  { key: 'stats', label: '数据总览', icon: 'fa-chart-pie' },
  { key: 'users', label: '用户管理', icon: 'fa-users' },
  { key: 'courses', label: '课程管理', icon: 'fa-book' },
  { key: 'questions', label: '题库管理', icon: 'fa-question-circle' },
  { key: 'projects', label: '项目管理', icon: 'fa-code' },
  { key: 'posts', label: '帖子管理', icon: 'fa-comments' },
]

// Data per tab
const users = ref([])
const courses = ref([])
const questions = ref([])
const projects = ref([])
const posts = ref([])

async function loadTab() {
  loading.value = true
  error.value = ''
  try {
    if (activeTab.value === 'stats') {
      const res = await getAdminStats()
      stats.value = res.data
    } else if (activeTab.value === 'users') {
      const res = await getAdminUsers()
      users.value = res.data.users || []
    } else if (activeTab.value === 'courses') {
      const res = await getAdminCourses()
      courses.value = res.data || []
    } else if (activeTab.value === 'questions') {
      const res = await getAdminQuestions()
      questions.value = res.data.questions || []
    } else if (activeTab.value === 'projects') {
      const res = await getAdminProjects()
      projects.value = res.data || []
    } else if (activeTab.value === 'posts') {
      const res = await getAdminPosts()
      posts.value = res.data.posts || []
    }
  } catch (e) {
    error.value = e.response?.status === 403 ? '无管理员权限' : '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleToggleAdmin(userId) {
  await toggleAdmin(userId)
  loadTab()
}

async function handleDelete(endpoint, id) {
  if (!confirm('确定删除？')) return
  try {
    if (endpoint === 'course') await deleteAdminCourse(id)
    else if (endpoint === 'question') await deleteAdminQuestion(id)
    else if (endpoint === 'project') await deleteAdminProject(id)
    else if (endpoint === 'post') await deleteAdminPost(id)
    loadTab()
  } catch {}
}

function switchTab(key) { activeTab.value = key; loadTab() }

onMounted(loadTab)
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <AppHeader /><PageLoader />
    <main class="flex-grow container mx-auto px-4 py-8">
      <div class="max-w-6xl mx-auto">
        <h1 class="text-2xl font-bold text-gray-800 mb-6">后台管理</h1>

        <div class="flex flex-wrap gap-2 mb-6">
          <button v-for="t in tabs" :key="t.key" @click="switchTab(t.key)"
            :class="activeTab === t.key ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'"
            class="px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center space-x-1.5">
            <i :class="`fas ${t.icon} text-xs`"></i><span>{{ t.label }}</span>
          </button>
        </div>

        <div v-if="loading" class="flex justify-center py-20"><div class="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full"></div></div>

        <div v-else-if="error" class="text-center py-20 text-red-500">{{ error }}</div>

        <!-- Stats -->
        <div v-else-if="activeTab === 'stats'" class="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div v-for="(val, key) in stats" :key="key" class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 text-center">
            <p class="text-2xl font-bold text-blue-600">{{ val }}</p>
            <p class="text-xs text-gray-400 mt-1">{{ { users:'用户', courses:'课程', questions:'题目', projects:'项目', posts:'帖子' }[key] }}</p>
          </div>
        </div>

        <!-- Users -->
        <div v-else-if="activeTab === 'users'" class="space-y-3">
          <div v-for="u in users" :key="u.id" class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-center justify-between">
            <div>
              <p class="font-medium text-gray-800">{{ u.username }} <span v-if="u.is_admin" class="text-xs text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded-full">管理员</span></p>
              <p class="text-xs text-gray-400">{{ u.level }} · {{ u.experience }} 经验</p>
            </div>
            <button @click="handleToggleAdmin(u.id)" :class="u.is_admin ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'" class="px-3 py-1 rounded-full text-xs font-medium hover:opacity-80 transition">{{ u.is_admin ? '取消管理员' : '设为管理员' }}</button>
          </div>
        </div>

        <!-- Courses / Questions / Projects / Posts -->
        <div v-else class="space-y-2">
          <div v-for="item in activeTab === 'courses' ? courses : activeTab === 'questions' ? questions : activeTab === 'projects' ? projects : posts" :key="item.id"
            class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-center justify-between">
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-800 truncate">{{ item.title }}</p>
              <p class="text-xs text-gray-400">
                <span v-if="activeTab === 'courses'">{{ item.category }}</span>
                <span v-else-if="activeTab === 'questions'">{{ item.type }} · {{ item.knowledge_point }} · {{ item.difficulty }}</span>
                <span v-else-if="activeTab === 'projects'">{{ item.level }} · {{ item.category }}</span>
                <span v-else>{{ item.category }} · {{ item.created_at?.slice(0, 10) }}</span>
              </p>
            </div>
            <button @click="handleDelete(activeTab === 'courses' ? 'course' : activeTab === 'questions' ? 'question' : activeTab === 'projects' ? 'project' : 'post', item.id)" class="text-red-400 hover:text-red-600 text-sm ml-4"><i class="fas fa-trash"></i></button>
          </div>
        </div>
      </div>
    </main>
    <AppFooter />
  </div>
</template>
