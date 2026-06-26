<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { adventureApi } from '../api/adventure'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const activeTab = ref('postcard')
const rewards = ref([])
const selectedReward = ref(null)

const tabs = [
  { key: 'postcard', label: '明信片图鉴', icon: 'fa-image', emptyMsg: '还没有收集到明信片，快去探险吧！' },
  { key: 'knowledge_note', label: '知识点小纸条', icon: 'fa-lightbulb', emptyMsg: '还没有收集到知识点小纸条，快去探险吧！' },
  { key: 'blessing', label: '祝福收集册', icon: 'fa-heart', emptyMsg: '还没有收到祝福，快去探险吧！' },
]

const filteredRewards = computed(() => rewards.value.filter(r => r.reward_type === activeTab.value))

const groupedByLocation = computed(() => {
  const map = {}
  for (const r of filteredRewards.value) {
    const loc = r.source_location || '未知地点'
    if (!map[loc]) map[loc] = []
    map[loc].push(r)
  }
  return map
})

async function fetchRewards() {
  try {
    const res = await adventureApi.getRewards(null, 200)
    if (res.data.code === 200) {
      rewards.value = res.data.data.rewards || []
    }
  } catch {}
}

function openDetail(reward) {
  selectedReward.value = reward
}

function closeDetail() {
  selectedReward.value = null
}

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/login')
    return
  }
  // Set initial tab from query param
  if (route.query.type && ['postcard', 'knowledge_note', 'blessing'].includes(route.query.type)) {
    activeTab.value = route.query.type
  }
  await fetchRewards()
  loading.value = false
})

watch(() => route.query.type, (val) => {
  if (val && ['postcard', 'knowledge_note', 'blessing'].includes(val)) {
    activeTab.value = val
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <AppHeader />
    <PageLoader v-if="loading" />

    <main v-if="!loading" class="flex-grow max-w-6xl mx-auto w-full px-4 py-8 space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button @click="router.back()"
            class="w-10 h-10 rounded-xl flex items-center justify-center bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition shadow-sm flex-shrink-0">
            <i class="fas fa-arrow-left text-gray-500"></i>
          </button>
          <div class="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-500 rounded-xl flex items-center justify-center shadow">
            <i class="fas fa-book-open text-white text-lg"></i>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-800">我的图鉴</h1>
            <p class="text-xs text-gray-400">收集探险中获得的明信片、知识点和祝福</p>
          </div>
        </div>
        <button @click="router.push('/adventure')"
          class="px-4 py-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 text-white text-sm font-bold shadow hover:shadow-lg hover:-translate-y-0.5 transition">
          <i class="fas fa-compass mr-1.5"></i>去探险
        </button>
      </div>

      <!-- Tab switcher -->
      <div class="flex gap-1 bg-white rounded-xl p-1 border border-gray-200 shadow-sm w-fit">
        <button v-for="tab in tabs" :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'px-5 py-2 rounded-lg text-sm font-bold transition-all duration-200 flex items-center gap-2',
            activeTab === tab.key
              ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
          ]">
          <i :class="['fas', tab.icon, activeTab === tab.key ? '' : 'text-gray-400']"></i>
          {{ tab.label }}
        </button>
      </div>

      <!-- Postcard Wall -->
      <div v-if="activeTab === 'postcard'">
        <div v-if="filteredRewards.length === 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-16 text-center">
          <div class="w-20 h-20 mx-auto mb-4 bg-amber-50 rounded-full flex items-center justify-center">
            <i class="fas fa-image text-amber-300 text-3xl"></i>
          </div>
          <p class="text-gray-500 font-medium mb-1">{{ tabs[0].emptyMsg }}</p>
          <button @click="router.push('/adventure')"
            class="mt-4 px-5 py-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 text-white text-sm font-bold shadow hover:shadow-lg transition">
            <i class="fas fa-compass mr-1.5"></i>派宠物去探险
          </button>
        </div>

        <div v-else>
          <div v-for="(items, location) in groupedByLocation" :key="location" class="mb-8">
            <h3 class="text-sm font-bold text-gray-600 mb-3 flex items-center gap-2">
              <i class="fas fa-map-pin text-amber-400"></i>{{ location }}
              <span class="text-xs text-gray-400 font-normal">({{ items.length }})</span>
            </h3>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              <div v-for="reward in items" :key="reward.id"
                class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden cursor-pointer hover:shadow-md hover:-translate-y-1 transition-all duration-300 group"
                @click="openDetail(reward)">
                <div class="aspect-[4/3] bg-gray-50 overflow-hidden">
                  <img v-if="reward.reward_image" :src="reward.reward_image"
                    class="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                    :alt="reward.reward_name" />
                  <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-amber-100 to-orange-100">
                    <i class="fas fa-image text-amber-300 text-3xl"></i>
                  </div>
                </div>
                <div class="p-3">
                  <p class="text-xs font-medium text-gray-700 truncate">{{ reward.reward_name }}</p>
                  <p class="text-[10px] text-gray-400 mt-1">{{ reward.created_at?.slice(0, 10) }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Knowledge Notes List -->
      <div v-if="activeTab === 'knowledge_note'">
        <div v-if="filteredRewards.length === 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-16 text-center">
          <div class="w-20 h-20 mx-auto mb-4 bg-blue-50 rounded-full flex items-center justify-center">
            <i class="fas fa-lightbulb text-blue-300 text-3xl"></i>
          </div>
          <p class="text-gray-500 font-medium mb-1">{{ tabs[1].emptyMsg }}</p>
          <button @click="router.push('/adventure')"
            class="mt-4 px-5 py-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 text-white text-sm font-bold shadow hover:shadow-lg transition">
            <i class="fas fa-compass mr-1.5"></i>派宠物去探险
          </button>
        </div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="reward in filteredRewards" :key="reward.id"
            class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 cursor-pointer"
            @click="openDetail(reward)">
            <div class="flex items-start gap-3">
              <img
                :src="'/pets/status/studying' + (Math.random() > 0.5 ? '2' : '') + '.png'"
                class="w-20 h-20 object-contain flex-shrink-0"
                alt="studying"
              />
              <div class="flex-1 min-w-0">
                <p class="text-xs font-bold text-gray-500 mb-2">{{ reward.reward_name }}</p>
                <p class="text-sm text-gray-700 leading-relaxed line-clamp-2">{{ reward.reward_content }}</p>
                <div class="flex items-center gap-3 mt-3">
                  <span class="text-[10px] text-gray-400">
                    <i class="fas fa-map-pin mr-0.5"></i>{{ reward.source_location || '未知' }}
                  </span>
                  <span class="text-[10px] text-gray-400">{{ reward.created_at?.slice(0, 10) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Blessings List -->
      <div v-if="activeTab === 'blessing'">
        <div v-if="filteredRewards.length === 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-16 text-center">
          <div class="w-20 h-20 mx-auto mb-4 bg-pink-50 rounded-full flex items-center justify-center">
            <i class="fas fa-heart text-pink-300 text-3xl"></i>
          </div>
          <p class="text-gray-500 font-medium mb-1">{{ tabs[2].emptyMsg }}</p>
          <button @click="router.push('/adventure')"
            class="mt-4 px-5 py-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 text-white text-sm font-bold shadow hover:shadow-lg transition">
            <i class="fas fa-compass mr-1.5"></i>派宠物去探险
          </button>
        </div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="reward in filteredRewards" :key="reward.id"
            class="bg-white rounded-xl shadow-sm border border-pink-100 p-5 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 cursor-pointer bg-gradient-to-br from-pink-50/30 to-rose-50/30"
            @click="openDetail(reward)">
            <div class="flex items-start gap-3">
              <img
                :src="'/pets/status/love' + (Math.random() > 0.5 ? '2' : '') + '.png'"
                class="w-28 h-28 object-contain flex-shrink-0"
                alt="love"
              />
              <div class="flex-1 min-w-0">
                <p class="text-xs font-bold text-gray-500 mb-2">{{ reward.reward_name }}</p>
                <p class="text-sm text-gray-700 leading-relaxed italic line-clamp-2">"{{ reward.reward_content }}"</p>
                <div class="flex items-center gap-3 mt-3">
                  <span class="text-[10px] text-gray-400">
                    <i class="fas fa-map-pin mr-0.5"></i>{{ reward.source_location || '未知' }}
                  </span>
                  <span class="text-[10px] text-gray-400">{{ reward.created_at?.slice(0, 10) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Detail Modal -->
    <Teleport to="body">
      <div v-if="selectedReward" class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="closeDetail">
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>

        <!-- Postcard detail -->
        <div v-if="selectedReward.reward_type === 'postcard'"
          class="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-scale-in">
          <button @click="closeDetail"
            class="absolute top-3 right-3 z-10 w-8 h-8 bg-white/80 backdrop-blur rounded-full flex items-center justify-center hover:bg-white transition shadow">
            <i class="fas fa-times text-gray-500 text-sm"></i>
          </button>
          <img v-if="selectedReward.reward_image" :src="selectedReward.reward_image"
            class="w-full h-64 object-cover" :alt="selectedReward.reward_name" />
          <div v-else class="w-full h-64 bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
            <i class="fas fa-image text-amber-300 text-5xl"></i>
          </div>
          <div class="p-6">
            <h3 class="text-lg font-bold text-gray-800 mb-2">{{ selectedReward.reward_name }}</h3>
            <p class="text-sm text-gray-500 leading-relaxed">{{ selectedReward.reward_content }}</p>
            <div class="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
              <span class="text-xs text-gray-400">
                <i class="fas fa-map-pin mr-1"></i>{{ selectedReward.source_location || '未知地点' }}
              </span>
              <span class="text-xs text-gray-400">
                <i class="fas fa-calendar mr-1"></i>{{ selectedReward.created_at?.slice(0, 10) }}
              </span>
              <span class="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 font-medium">
                {{ selectedReward.rarity === 'common' ? '普通' : selectedReward.rarity === 'rare' ? '稀有' : '史诗' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Knowledge note detail -->
        <div v-else-if="selectedReward.reward_type === 'knowledge_note'"
          class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-scale-in">
          <button @click="closeDetail"
            class="absolute top-3 right-3 z-10 w-8 h-8 bg-white/80 backdrop-blur rounded-full flex items-center justify-center hover:bg-white transition shadow">
            <i class="fas fa-times text-gray-500 text-sm"></i>
          </button>
          <div class="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-5">
            <div class="flex items-center gap-3 text-white">
              <div class="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur">
                <i class="fas fa-lightbulb text-lg"></i>
              </div>
              <span class="font-bold">{{ selectedReward.reward_name }}</span>
            </div>
          </div>
          <div class="p-6">
            <img
              :src="'/pets/status/studying' + (Math.random() > 0.5 ? '2' : '') + '.png'"
              class="w-36 h-36 mx-auto mb-4 object-contain"
              alt="studying"
            />
            <div class="bg-blue-50 rounded-xl p-5">
              <p class="text-sm text-gray-700 leading-relaxed">{{ selectedReward.reward_content }}</p>
            </div>
            <div class="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
              <span class="text-xs text-gray-400">
                <i class="fas fa-map-pin mr-1"></i>{{ selectedReward.source_location || '未知地点' }}
              </span>
              <span class="text-xs text-gray-400">
                <i class="fas fa-calendar mr-1"></i>{{ selectedReward.created_at?.slice(0, 10) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Blessing detail -->
        <div v-else-if="selectedReward.reward_type === 'blessing'"
          class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-scale-in">
          <button @click="closeDetail"
            class="absolute top-3 right-3 z-10 w-8 h-8 bg-white/80 backdrop-blur rounded-full flex items-center justify-center hover:bg-white transition shadow">
            <i class="fas fa-times text-gray-500 text-sm"></i>
          </button>
          <div class="bg-gradient-to-r from-pink-400 to-rose-500 px-6 py-5">
            <div class="flex items-center gap-3 text-white">
              <div class="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur">
                <i class="fas fa-heart text-lg"></i>
              </div>
              <span class="font-bold">{{ selectedReward.reward_name }}</span>
            </div>
          </div>
          <div class="p-6 text-center">
            <img
              :src="'/pets/status/love' + (Math.random() > 0.5 ? '2' : '') + '.png'"
              class="w-44 h-44 mx-auto mb-4 object-contain"
              alt="love"
            />
            <div class="bg-pink-50 rounded-xl p-5">
              <p class="text-sm text-gray-700 leading-relaxed italic">"{{ selectedReward.reward_content }}"</p>
            </div>
            <div class="flex items-center justify-center gap-4 mt-4 pt-4 border-t border-gray-100">
              <span class="text-xs text-gray-400">
                <i class="fas fa-map-pin mr-1"></i>{{ selectedReward.source_location || '未知地点' }}
              </span>
              <span class="text-xs text-gray-400">
                <i class="fas fa-calendar mr-1"></i>{{ selectedReward.created_at?.slice(0, 10) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <AppFooter />
  </div>
</template>

<style scoped>
@keyframes scale-in {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
.animate-scale-in {
  animation: scale-in 0.2s ease-out;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
