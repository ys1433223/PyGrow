<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { adventureApi } from '../api/adventure'
import { triggerPetState } from '../hooks/usePetCompanion'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const router = useRouter()

// ---- State ----
const loading = ref(true)
const petProfile = ref(null)
const adventureState = ref('idle') // idle | exploring | completed | reward
const countdown = ref(0)
const currentAdventure = ref(null)
const claimedReward = ref(null)
const logs = ref([])
const rewards = ref([])

let countdownTimer = null
let pollTimer = null

// ---- Computed ----
const cookies = computed(() => petProfile.value?.cookies || 0)
const canAdventure = computed(() => cookies.value >= 3 && adventureState.value === 'idle')
const shortage = computed(() => Math.max(0, 3 - cookies.value))
const statusLabel = computed(() => {
  if (adventureState.value === 'exploring') return '探险中'
  if (adventureState.value === 'completed') return '已归来'
  return '待机中'
})
const statusColor = computed(() => {
  if (adventureState.value === 'exploring') return 'text-amber-500 bg-amber-50'
  if (adventureState.value === 'completed') return 'text-green-500 bg-green-50'
  return 'text-gray-400 bg-gray-100'
})
const countdownPercent = computed(() => {
  if (!currentAdventure.value || adventureState.value !== 'exploring') return 100
  const total = 5
  return Math.max(0, Math.round((countdown.value / total) * 100))
})

// ---- API helpers ----
async function fetchProfile() {
  try {
    const res = await adventureApi.getProfile()
    if (res.data.code === 200) {
      petProfile.value = res.data.data
      // Determine current state
      if (res.data.data.status === 'exploring') {
        adventureState.value = 'exploring'
        await checkAdventureStatus()
      } else if (res.data.data.status === 'completed') {
        adventureState.value = 'completed'
        currentAdventure.value = {
          adventure_location: res.data.data.adventure_location,
          status: 'completed',
        }
      } else {
        adventureState.value = 'idle'
      }
    }
  } catch (e) {
    console.error('Failed to fetch pet profile:', e)
  }
}

async function checkAdventureStatus() {
  try {
    const res = await adventureApi.getCurrentAdventure()
    if (res.data.code === 200) {
      const data = res.data.data
      currentAdventure.value = data
      if (data.status === 'exploring') {
        adventureState.value = 'exploring'
        countdown.value = data.remaining_seconds || 0
        startCountdown()
      } else if (data.status === 'completed') {
        adventureState.value = 'completed'
        stopCountdown()
        triggerPetState('message')
      } else {
        adventureState.value = 'idle'
        stopCountdown()
      }
    }
  } catch (e) {
    console.error('Failed to check adventure:', e)
  }
}

async function fetchLogs() {
  try {
    const res = await adventureApi.getAdventureLogs(10)
    if (res.data.code === 200) {
      logs.value = res.data.data.logs || []
    }
  } catch {}
}

async function fetchRewards() {
  try {
    const res = await adventureApi.getRewards(null, 20)
    if (res.data.code === 200) {
      rewards.value = res.data.data.rewards || []
    }
  } catch {}
}

// ---- Countdown ----
function startCountdown() {
  stopCountdown()
  countdownTimer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    }
    if (countdown.value <= 0) {
      stopCountdown()
      checkAdventureStatus()
    }
  }, 1000)
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

// ---- Actions ----
async function handleStartAdventure() {
  if (!canAdventure.value) return

  triggerPetState('adventure')

  try {
    const res = await adventureApi.startAdventure()
    if (res.data.code === 200) {
      const data = res.data.data
      currentAdventure.value = {
        adventure_location: data.adventure_location,
        status: 'exploring',
        end_time: data.end_time,
      }
      adventureState.value = 'exploring'
      countdown.value = data.duration_seconds || 5
      cookies.value && (petProfile.value.cookies = data.remaining_cookies)
      startCountdown()

      // Set up polling as backup
      pollTimer = setInterval(() => {
        if (adventureState.value !== 'exploring') {
          clearInterval(pollTimer)
          pollTimer = null
          return
        }
        checkAdventureStatus()
      }, 2000)
    } else {
      const msg = res.data.message || '开始探险失败'
      alert(msg)
      if (res.data.data?.code === 'insufficient_cookies') {
        triggerPetState('thinking', 3000)
      }
    }
  } catch (e) {
    alert('网络错误，请稍后再试')
  }
}

async function handleClaimReward() {
  try {
    const res = await adventureApi.claimReward()
    if (res.data.code === 200) {
      const data = res.data.data
      claimedReward.value = data.reward
      adventureState.value = 'reward'
      triggerPetState('returnReward', 4000)

      // Refresh profile and logs
      await fetchProfile()
      await fetchLogs()
      await fetchRewards()
    } else {
      alert(res.data.message || '领取奖励失败')
    }
  } catch (e) {
    alert('网络错误，请稍后再试')
  }
}

function closeRewardCard() {
  claimedReward.value = null
  adventureState.value = 'idle'
  triggerPetState('idle')
}

function goToCollection(type) {
  router.push({ path: '/profile/collection', query: { type } })
}

// ---- Lifecycle ----
onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/login')
    return
  }
  await fetchProfile()
  await fetchLogs()
  await fetchRewards()
  loading.value = false

  if (adventureState.value === 'exploring') {
    triggerPetState('adventure')
  }
})

onUnmounted(() => {
  stopCountdown()
  if (pollTimer) clearInterval(pollTimer)
})

// Watch for adventure completing
watch(countdown, (val) => {
  if (val <= 0 && adventureState.value === 'exploring') {
    checkAdventureStatus()
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <AppHeader />
    <PageLoader v-if="loading" />

    <main v-if="!loading" class="flex-grow max-w-4xl mx-auto w-full px-4 py-8 space-y-6">
      <!-- Page Title -->
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow">
          <i class="fas fa-map-marked-alt text-white text-lg"></i>
        </div>
        <div>
          <h1 class="text-2xl font-bold text-gray-800">宠物探险</h1>
          <p class="text-xs text-gray-400">派小Py去探索世界，带回明信片和小礼物</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left column: Pet status + Adventure -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Pet Status Card -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="bg-gradient-to-r from-amber-400 via-orange-400 to-pink-400 px-6 py-4">
              <div class="flex items-center justify-between text-white">
                <div class="flex items-center gap-3">
                  <div class="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center backdrop-blur">
                    <i class="fas fa-paw text-2xl"></i>
                  </div>
                  <div>
                    <p class="font-bold text-lg">{{ petProfile?.pet_name || '小Py' }}</p>
                    <p class="text-white/80 text-xs">{{ petProfile?.pet_type || '默认' }}</p>
                  </div>
                </div>
                <span :class="['px-3 py-1 rounded-full text-xs font-bold', statusColor]">
                  {{ statusLabel }}
                </span>
              </div>
            </div>

            <div class="px-6 py-4 flex items-center justify-between">
              <div>
                <p class="text-xs text-gray-400">当前饼干</p>
                <p class="text-2xl font-bold text-amber-600">
                  <i class="fas fa-cookie text-amber-400 mr-1"></i>{{ cookies }}
                </p>
              </div>
              <div class="text-right">
                <p class="text-xs text-gray-400">探险消耗</p>
                <p class="text-lg font-bold text-gray-600">
                  <span class="text-amber-500">3</span> 饼干
                </p>
              </div>
            </div>
          </div>

          <!-- Adventure Area -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <!-- Idle: Start button -->
            <div v-if="adventureState === 'idle'" class="text-center py-8">
              <div class="w-24 h-24 mx-auto mb-4 bg-amber-50 rounded-full flex items-center justify-center">
                <i class="fas fa-compass text-amber-400 text-4xl"></i>
              </div>
              <h3 class="text-lg font-bold text-gray-700 mb-2">准备好了吗？</h3>
              <p class="text-sm text-gray-400 mb-2">派宠物去探险，带回明信片、知识点小纸条或小祝福</p>
              <p class="text-xs text-gray-300 mb-6">每次消耗 3 个饼干 · 探险时间约 5 秒</p>

              <button
                @click="handleStartAdventure"
                :disabled="!canAdventure"
                :class="[
                  'px-8 py-3 rounded-full text-white font-bold transition-all duration-300 shadow-lg',
                  canAdventure
                    ? 'bg-gradient-to-r from-amber-400 to-orange-500 hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0'
                    : 'bg-gray-300 cursor-not-allowed shadow-none'
                ]"
              >
                <i class="fas fa-paper-plane mr-2"></i>
                {{ canAdventure ? '派宠物去探险' : `还差 ${shortage} 个饼干` }}
              </button>

              <p v-if="!canAdventure" class="text-xs text-amber-500 mt-3">
                <i class="fas fa-info-circle mr-1"></i>
                通过答题、每日一练、项目等学习行为获取饼干
              </p>
            </div>

            <!-- Exploring: Countdown -->
            <div v-else-if="adventureState === 'exploring'" class="text-center py-6">
              <div class="w-24 h-24 mx-auto mb-4 relative">
                <div class="absolute inset-0 bg-amber-100 rounded-full animate-ping opacity-30"></div>
                <div class="relative w-24 h-24 bg-amber-50 rounded-full flex items-center justify-center">
                  <i class="fas fa-map-pin text-amber-400 text-4xl animate-bounce"></i>
                </div>
              </div>
              <h3 class="text-lg font-bold text-gray-700 mb-1">
                宠物正在「{{ currentAdventure?.adventure_location }}」探险中
              </h3>
              <p class="text-3xl font-bold text-amber-500 my-3">{{ countdown }}s</p>
              <div class="max-w-xs mx-auto h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full transition-all duration-1000 ease-linear"
                  :style="{ width: countdownPercent + '%' }"
                ></div>
              </div>
              <p class="text-xs text-gray-400 mt-3">探险中，请耐心等待...</p>
            </div>

            <!-- Completed: Claim -->
            <div v-else-if="adventureState === 'completed'" class="text-center py-6">
              <div class="w-24 h-24 mx-auto mb-4 bg-green-50 rounded-full flex items-center justify-center">
                <i class="fas fa-gift text-green-400 text-4xl"></i>
              </div>
              <h3 class="text-lg font-bold text-gray-700 mb-1">
                宠物从「{{ currentAdventure?.adventure_location }}」回来啦！
              </h3>
              <p class="text-sm text-gray-400 mb-6">探险完成，点击领取奖励</p>
              <button
                @click="handleClaimReward"
                class="px-8 py-3 rounded-full bg-gradient-to-r from-green-400 to-emerald-500 text-white font-bold shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300"
              >
                <i class="fas fa-gift mr-2"></i>领取奖励
              </button>
            </div>

            <!-- Reward card -->
            <div v-else-if="adventureState === 'reward' && claimedReward" class="py-4">
              <!-- Postcard -->
              <div v-if="claimedReward.reward_type === 'postcard'" class="text-center">
                <div class="relative mx-auto max-w-sm bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
                  <img
                    v-if="claimedReward.reward_image"
                    :src="claimedReward.reward_image"
                    class="w-full h-56 object-cover"
                    :alt="claimedReward.reward_name"
                  />
                  <div v-else class="w-full h-56 bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
                    <i class="fas fa-image text-amber-300 text-5xl"></i>
                  </div>
                  <div class="p-4">
                    <h4 class="font-bold text-gray-800 mb-2">{{ claimedReward.reward_name }}</h4>
                    <p class="text-sm text-gray-500 leading-relaxed">{{ claimedReward.reward_content }}</p>
                    <p v-if="claimedReward.source_location" class="text-xs text-gray-400 mt-2">
                      <i class="fas fa-map-pin mr-1"></i>{{ claimedReward.source_location }}
                    </p>
                  </div>
                </div>
                <div class="flex justify-center gap-3 mt-4">
                  <button @click="goToCollection('postcard')"
                    class="px-5 py-2.5 rounded-full bg-gradient-to-r from-blue-400 to-purple-500 text-white text-sm font-bold shadow hover:shadow-lg transition">
                    <i class="fas fa-images mr-1.5"></i>去图鉴查看
                  </button>
                  <button @click="closeRewardCard"
                    class="px-5 py-2.5 rounded-full bg-gray-100 text-gray-600 text-sm font-bold hover:bg-gray-200 transition">
                    知道啦
                  </button>
                </div>
              </div>

              <!-- Knowledge Note -->
              <div v-else-if="claimedReward.reward_type === 'knowledge_note'" class="text-center">
                <div class="max-w-sm mx-auto bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl shadow-lg border border-blue-100 p-6">
                  <div class="w-16 h-16 mx-auto mb-3 bg-blue-100 rounded-full flex items-center justify-center">
                    <i class="fas fa-lightbulb text-blue-400 text-2xl"></i>
                  </div>
                  <h4 class="font-bold text-gray-800 mb-3">{{ claimedReward.reward_name }}</h4>
                  <div class="bg-white rounded-xl p-4 shadow-inner">
                    <p class="text-sm text-gray-600 leading-relaxed">{{ claimedReward.reward_content }}</p>
                  </div>
                  <p v-if="claimedReward.source_location" class="text-xs text-gray-400 mt-2">
                    <i class="fas fa-map-pin mr-1"></i>{{ claimedReward.source_location }}
                  </p>
                </div>
                <div class="flex justify-center gap-3 mt-4">
                  <button @click="goToCollection('knowledge_note')"
                    class="px-5 py-2.5 rounded-full bg-gradient-to-r from-blue-400 to-purple-500 text-white text-sm font-bold shadow hover:shadow-lg transition">
                    <i class="fas fa-lightbulb mr-1.5"></i>去图鉴查看
                  </button>
                  <button @click="closeRewardCard"
                    class="px-5 py-2.5 rounded-full bg-gray-100 text-gray-600 text-sm font-bold hover:bg-gray-200 transition">
                    知道啦
                  </button>
                </div>
              </div>

              <!-- Blessing -->
              <div v-else-if="claimedReward.reward_type === 'blessing'" class="text-center">
                <div class="max-w-sm mx-auto bg-gradient-to-br from-pink-50 to-rose-50 rounded-2xl shadow-lg border border-pink-100 p-6">
                  <div class="w-16 h-16 mx-auto mb-3 bg-pink-100 rounded-full flex items-center justify-center">
                    <i class="fas fa-heart text-pink-400 text-2xl"></i>
                  </div>
                  <h4 class="font-bold text-gray-800 mb-3">{{ claimedReward.reward_name }}</h4>
                  <p class="text-sm text-gray-600 leading-relaxed italic">"{{ claimedReward.reward_content }}"</p>
                  <p v-if="claimedReward.source_location" class="text-xs text-gray-400 mt-2">
                    <i class="fas fa-map-pin mr-1"></i>{{ claimedReward.source_location }}
                  </p>
                </div>
                <div class="mt-4">
                  <button @click="closeRewardCard"
                    class="px-8 py-2.5 rounded-full bg-gradient-to-r from-pink-400 to-rose-500 text-white text-sm font-bold shadow hover:shadow-lg transition">
                    <i class="fas fa-heart mr-1.5"></i>知道啦
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right column: Rewards preview + Stats -->
        <div class="space-y-6">
          <!-- Recent rewards -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="px-5 py-3 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-100 flex items-center justify-between">
              <span class="text-sm font-bold text-gray-700"><i class="fas fa-gift text-amber-400 mr-1.5"></i>最近收获</span>
              <button @click="router.push('/profile/collection')" class="text-xs text-blue-500 hover:text-blue-700">
                查看图鉴 <i class="fas fa-arrow-right ml-0.5"></i>
              </button>
            </div>
            <div v-if="rewards.length === 0" class="p-6 text-center text-xs text-gray-400">
              <i class="fas fa-inbox text-2xl block mb-2"></i>
              还没有奖励，去探险吧
            </div>
            <div v-else class="divide-y divide-gray-50">
              <div v-for="r in rewards.slice(0, 5)" :key="r.id"
                class="px-5 py-3 flex items-center gap-3 hover:bg-gray-50 transition cursor-pointer"
                @click="router.push('/profile/collection?type=' + r.reward_type)">
                <span v-if="r.reward_type === 'postcard'" class="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <i class="fas fa-image text-amber-500 text-xs"></i>
                </span>
                <span v-else-if="r.reward_type === 'knowledge_note'" class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <i class="fas fa-lightbulb text-blue-500 text-xs"></i>
                </span>
                <span v-else class="w-8 h-8 bg-pink-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <i class="fas fa-heart text-pink-500 text-xs"></i>
                </span>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-gray-700 truncate">{{ r.reward_name }}</p>
                  <p class="text-[10px] text-gray-400">{{ r.source_location || '' }}</p>
                </div>
                <span v-if="r.is_new" class="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0"></span>
              </div>
            </div>
          </div>

          <!-- Quick stats -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
            <p class="text-xs font-bold text-gray-500 mb-3 uppercase tracking-wider">探险统计</p>
            <div class="grid grid-cols-2 gap-3">
              <div class="bg-amber-50 rounded-xl p-3 text-center">
                <p class="text-2xl font-bold text-amber-600">{{ logs.length }}</p>
                <p class="text-[10px] text-gray-400">探险次数</p>
              </div>
              <div class="bg-green-50 rounded-xl p-3 text-center">
                <p class="text-2xl font-bold text-green-600">{{ rewards.length }}</p>
                <p class="text-[10px] text-gray-400">获得奖励</p>
              </div>
              <div class="bg-blue-50 rounded-xl p-3 text-center">
                <p class="text-2xl font-bold text-blue-600">{{ rewards.filter(r => r.reward_type === 'postcard').length }}</p>
                <p class="text-[10px] text-gray-400">明信片</p>
              </div>
              <div class="bg-purple-50 rounded-xl p-3 text-center">
                <p class="text-2xl font-bold text-purple-600">{{ rewards.filter(r => r.reward_type === 'knowledge_note').length }}</p>
                <p class="text-[10px] text-gray-400">知识纸条</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Adventure Logs -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-100">
          <h3 class="font-bold text-gray-700"><i class="fas fa-history text-gray-400 mr-2"></i>探险日志</h3>
        </div>
        <div v-if="logs.length === 0" class="p-10 text-center text-sm text-gray-400">
          <i class="fas fa-scroll text-3xl block mb-2"></i>
          还没有探险记录，快去派宠物探险吧
        </div>
        <div v-else class="divide-y divide-gray-50">
          <div v-for="log in logs" :key="log.id"
            class="px-6 py-4 flex items-center gap-4 hover:bg-gray-50/50 transition">
            <div class="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
              <i class="fas fa-map-pin text-amber-500 text-sm"></i>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-700">
                宠物去了「{{ log.adventure_location }}」探险
                <template v-if="log.status === 'claimed' && log.reward_description">
                  ，带回了{{ log.reward_description }}
                </template>
              </p>
              <div class="flex items-center gap-3 mt-1">
                <span class="text-[10px] text-gray-400">
                  <i class="fas fa-clock mr-0.5"></i>{{ log.start_time?.slice(0, 16) }}
                </span>
                <span class="text-[10px] text-gray-400">
                  <i class="fas fa-cookie mr-0.5"></i>{{ log.cost_cookies }} 饼干
                </span>
                <span :class="[
                  'text-[10px] px-1.5 py-0.5 rounded-full',
                  log.status === 'claimed' ? 'bg-green-50 text-green-600' :
                  log.status === 'completed' ? 'bg-blue-50 text-blue-600' :
                  'bg-amber-50 text-amber-600'
                ]">
                  {{ log.status === 'claimed' ? '已领取' : log.status === 'completed' ? '已完成' : '探险中' }}
                </span>
              </div>
            </div>
            <button v-if="log.reward && log.reward.reward_type"
              @click="router.push('/profile/collection?type=' + log.reward.reward_type)"
              class="text-xs text-blue-500 hover:text-blue-700 flex-shrink-0">
              查看奖励 <i class="fas fa-arrow-right ml-0.5"></i>
            </button>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
