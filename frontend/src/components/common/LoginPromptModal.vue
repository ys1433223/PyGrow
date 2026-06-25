<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const props = defineProps({
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

function goToLogin() {
  emit('close')
  router.push('/login')
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      @click.self="emit('close')"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-8 text-center animate-scale-in">
        <!-- Pet sleeping image -->
        <div class="mb-5">
          <img
            src="/pets/default/纸箱休息.gif"
            alt="宠物在休息"
            class="w-32 h-32 mx-auto object-contain"
          />
        </div>

        <h2 class="text-lg font-bold text-gray-800 mb-2">请先登录</h2>
        <p class="text-gray-500 text-sm mb-6 leading-relaxed">
          登录后即可使用全部功能，和小宠物一起快乐学习 Python！
        </p>

        <div class="flex flex-col gap-3">
          <button @click="goToLogin"
            class="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-2.5 rounded-xl font-bold hover:shadow-lg transition-all hover:-translate-y-0.5">
            <i class="fas fa-sign-in-alt mr-1.5"></i>立即登录
          </button>
          <button @click="emit('close')"
            class="w-full text-gray-400 py-1.5 text-sm hover:text-gray-600 transition-colors">
            稍后再说
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
@keyframes scale-in {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
.animate-scale-in {
  animation: scale-in 0.25s ease-out;
}
</style>
