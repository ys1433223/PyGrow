<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(true)
const progress = ref(0)

onMounted(() => {
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
      <div class="w-20 h-20 bg-white rounded-full flex items-center justify-center text-blue-600 shadow-xl">
        <span class="text-3xl font-bold">@</span>
      </div>
    </div>
    <h2 class="text-3xl font-bold mb-2 tracking-widest">启航教育</h2>
    <p class="text-blue-100 mb-8 text-sm">正在前往知识宇宙...</p>
    <div class="w-64 h-2 bg-blue-800 rounded-full overflow-hidden relative">
      <div class="h-full bg-white transition-all duration-100 ease-out shadow-[0_0_10px_rgba(255,255,255,0.5)]" :style="{ width: progress + '%' }"></div>
    </div>
    <div class="mt-2 font-mono text-xs opacity-70">{{ progress }}%</div>
  </div>
</template>
