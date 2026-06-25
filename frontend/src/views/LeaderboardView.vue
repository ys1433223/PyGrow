<script setup>
import { ref, onMounted } from 'vue'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { getXPLeaderboard, getProjectsLeaderboard, getStreakLeaderboard } from '../api/leaderboard'

const activeTab = ref('xp')
const leaderboard = ref([])
const loading = ref(true)
const myRank = ref(null)
const myProjectCount = ref(null)

const tabs = [
  { key: 'xp', label: '经验值排行', icon: 'fa-star' },
  { key: 'projects', label: '项目完成', icon: 'fa-code' },
  { key: 'streak', label: '学习活跃', icon: 'fa-fire' },
]

async function loadLeaderboard() {
  loading.value = true
  myRank.value = null
  myProjectCount.value = null
  try {
    let res
    if (activeTab.value === 'xp') {
      res = await getXPLeaderboard()
      myRank.value = res.data.my_rank
    } else if (activeTab.value === 'projects') {
      res = await getProjectsLeaderboard()
      myProjectCount.value = res.data.my_project_count
    } else {
      res = await getStreakLeaderboard()
    }
    leaderboard.value = res.data.leaderboard || []
  } finally {
    loading.value = false
  }
}

function switchTab(key) {
  activeTab.value = key
  loadLeaderboard()
}

const rankColors = ['text-yellow-500', 'text-gray-400', 'text-orange-400']

onMounted(loadLeaderboard)
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <AppHeader /><PageLoader />
    <main class="flex-grow container mx-auto px-4 py-8">
      <div class="max-w-3xl mx-auto">
        <h1 class="text-2xl font-bold text-gray-800 mb-6">排行榜</h1>

        <div class="flex bg-white rounded-2xl shadow-sm border border-gray-100 p-1.5 mb-6">
          <button v-for="t in tabs" :key="t.key" @click="switchTab(t.key)"
            :class="activeTab === t.key ? 'bg-blue-600 text-white shadow' : 'text-gray-500 hover:text-gray-700'"
            class="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center space-x-2">
            <i :class="`fas ${t.icon} text-xs`"></i><span>{{ t.label }}</span>
          </button>
        </div>

        <div v-if="loading" class="flex justify-center py-20"><div class="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full"></div></div>

        <div v-else class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <!-- My rank header -->
          <div v-if="myRank" class="px-6 py-3 bg-blue-50 border-b border-blue-100 flex items-center justify-between text-sm">
            <span class="text-blue-700">我的排名：第 {{ myRank.rank }} 名</span>
            <span class="text-blue-600">{{ myRank.experience }} XP</span>
          </div>
          <div v-if="myProjectCount !== null" class="px-6 py-3 bg-blue-50 border-b border-blue-100 text-sm text-blue-700">
            我已提交 {{ myProjectCount }} 个项目
          </div>

          <div v-if="leaderboard.length === 0" class="text-center py-20 text-gray-400">暂无排行数据</div>

          <div v-for="(item, i) in leaderboard" :key="item.user_id"
            :class="i < 3 ? 'bg-gradient-to-r from-yellow-50 to-white' : i % 2 === 0 ? 'bg-gray-50' : 'bg-white'"
            class="flex items-center px-6 py-3.5">
            <span class="w-10 font-bold text-lg" :class="i < 3 ? rankColors[i] : 'text-gray-400'">
              <i v-if="i === 0" class="fas fa-crown text-yellow-500"></i>
              <template v-else>{{ item.rank }}</template>
            </span>
            <div class="w-9 h-9 rounded-full bg-gray-200 flex-shrink-0 overflow-hidden mr-3">
              <img :src="item.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=User'" class="w-full h-full object-cover" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-800 truncate">{{ item.username }}</p>
              <p class="text-xs text-gray-400">{{ item.level }}</p>
            </div>
            <div class="text-right flex-shrink-0">
              <span v-if="activeTab === 'xp'" class="text-sm font-bold text-blue-600">{{ item.experience }} XP</span>
              <span v-else-if="activeTab === 'projects'" class="text-sm font-bold text-purple-600">{{ item.project_count }} 个项目</span>
              <span v-else class="text-sm font-bold text-orange-600">{{ item.active_days }} 天活跃</span>
            </div>
          </div>
        </div>
      </div>
    </main>
    <AppFooter />
  </div>
</template>
