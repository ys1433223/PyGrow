<script setup>
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function goToAssessment() {
  auth.dismissAssessmentPrompt()
  router.push('/assessment')
}

function skipForNow() {
  auth.dismissAssessmentPrompt()
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 animate-in">
        <div class="text-center mb-6">
          <div class="w-16 h-16 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
            <i class="fas fa-clipboard-check"></i>
          </div>
          <h2 class="text-xl font-bold text-gray-800 mb-2">能力测评还未完成</h2>
          <p class="text-gray-500 text-sm leading-relaxed">
            完成一次简单的 Python 能力测评（20题），系统会根据你的水平推荐最合适的学习路径，帮助你更高效地进步。
          </p>
        </div>

        <div class="flex flex-col gap-3">
          <button @click="goToAssessment"
            class="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-xl font-bold hover:shadow-lg transition-all hover:-translate-y-0.5">
            开始测评（约5分钟）
          </button>
          <button @click="skipForNow"
            class="w-full text-gray-400 py-2 text-sm hover:text-gray-600 transition-colors">
            暂不测评，稍后再说
          </button>
        </div>

        <p class="text-center text-xs text-gray-400 mt-4">
          测评入口可在头像下拉菜单中找到 · 随时可以进行
        </p>
      </div>
    </div>
  </Teleport>
</template>
