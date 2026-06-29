<script setup>
import { ref, onMounted } from 'vue'

const BASE = import.meta.env.BASE_URL

const LOADING_GIFS = [
  '端详.gif', '对手指.gif', '吐舌.gif', '思考.gif', '喜欢.gif',
  '点赞.gif', '鼓掌.gif', '戳戳.gif', '喜欢2.gif', '喜欢3.gif',
  '举牌100分.gif', '灵光.gif', 'yes.gif', '抱抱.gif',
]

const loading = ref(true)
const progress = ref(0)
const petGif = ref('')

onMounted(() => {
  const gif = LOADING_GIFS[Math.floor(Math.random() * LOADING_GIFS.length)]
  petGif.value = BASE + 'pets/default/' + gif

  const timer = setInterval(() => {
    progress.value += 10
    if (progress.value >= 100) {
      clearInterval(timer)
      setTimeout(() => { loading.value = false }, 300)
    }
  }, 30)
})
</script>

<template>
  <div v-if="loading" class="fixed inset-0 z-[100] bg-blue-600 flex flex-col items-center justify-center text-white transition-opacity duration-500">
    <div class="relative mb-8 animate-bounce">
      <img
        :src="petGif"
        alt="loading"
        class="w-24 h-24 object-contain drop-shadow-lg"
      />
    </div>
    <h2 class="text-3xl font-bold mb-2 tracking-widest">Python学习营地</h2>
    <p class="text-blue-100 mb-8 text-sm">正在前往知识宇宙...</p>
    <div class="w-64 h-2 bg-blue-800 rounded-full overflow-hidden relative">
      <div class="h-full bg-white transition-all duration-100 ease-out shadow-[0_0_10px_rgba(255,255,255,0.5)]" :style="{ width: progress + '%' }"></div>
    </div>
    <div class="mt-2 font-mono text-xs opacity-70">{{ progress }}%</div>
  </div>
</template>
