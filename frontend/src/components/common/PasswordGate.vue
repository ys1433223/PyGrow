<script setup>
import { ref } from 'vue'

const PWD = '终极无敌噼里啪啦py社区'
const input = ref('')
const err = ref(false)
const show = ref(!localStorage.getItem('pygrow_unlocked'))

function submit() {
  if (input.value === PWD) {
    localStorage.setItem('pygrow_unlocked', '1')
    show.value = false
  } else {
    err.value = true
    input.value = ''
  }
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-[9999] bg-gradient-to-br from-indigo-900 via-blue-900 to-slate-900 flex items-center justify-center">
    <div class="bg-white/10 backdrop-blur-md rounded-2xl p-10 w-full max-w-md mx-4 text-center border border-white/20 shadow-2xl">
      <i class="fas fa-lock text-5xl text-blue-300 mb-4"></i>
      <h2 class="text-2xl font-bold text-white mb-2">访问验证</h2>
      <p class="text-blue-200 text-sm mb-6">请输入访问密码以继续</p>
      <input v-model="input" type="password" placeholder="请输入密码..."
        :class="['w-full px-4 py-3 rounded-lg bg-white/5 border text-white placeholder-blue-300/50 focus:outline-none focus:ring-2 transition-all text-center', err ? 'border-red-400' : 'border-white/20 focus:ring-blue-400']"
        @keyup.enter="submit" />
      <p v-if="err" class="text-red-400 text-sm mt-3">密码错误，请重试</p>
      <button @click="submit" class="mt-5 w-full py-3 bg-blue-500 hover:bg-blue-400 text-white font-bold rounded-lg transition-colors cursor-pointer">验证</button>
    </div>
  </div>
</template>
