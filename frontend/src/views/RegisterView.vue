<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppHeader from '../components/layout/AppHeader.vue'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMsg = ref('')
const loading = ref(false)

async function handleRegister() {
  errorMsg.value = ''
  if (!username.value || !password.value || !confirmPassword.value) {
    errorMsg.value = '请填写所有字段'
    return
  }
  if (password.value.length < 6) {
    errorMsg.value = '密码至少需要6个字符'
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次密码不一致'
    return
  }
  loading.value = true
  const result = await auth.register(username.value, password.value, confirmPassword.value)
  loading.value = false
  if (result.success) {
    router.push('/')
  } else {
    errorMsg.value = result.message || '注册失败'
  }
}
</script>

<template>
  <div class="login-register-page flex flex-col min-h-screen">
    <AppHeader />

    <article class="flex-grow flex items-center justify-center" style="min-height: auto; width: 100%;">
      <section class="login-section">
        <div class="bobbles">
          <div class="bobble-1"></div>
          <div class="bobble-2"></div>
          <div class="bobble-3"></div>
          <div class="bobble-4"></div>
        </div>
        <form autocomplete="off" @submit.prevent="handleRegister">
          <h2>欢迎注册!</h2>
          <p>请输入账号和密码</p>

          <div>
            <label for="reg-username">账号</label>
            <input type="text" id="reg-username" name="username" v-model="username" required />
          </div>

          <div>
            <label for="reg-password">密码</label>
            <input type="password" id="reg-password" name="password" v-model="password" required />
          </div>

          <div>
            <label for="reg-confirm">确认密码</label>
            <input type="password" id="reg-confirm" name="confirm_password" v-model="confirmPassword" required />
          </div>

          <p v-if="errorMsg" class="text-red-500 text-sm text-center mb-2">{{ errorMsg }}</p>

          <button type="submit" :disabled="loading">
            {{ loading ? '注册中...' : '注册' }}
          </button>

          <p class="signup">
            已有账号？ <a href="/login" @click.prevent="$router.push('/login')">去登录</a>
          </p>
        </form>
      </section>
    </article>

    <footer class="bg-white border-t border-gray-200 py-8 mt-auto">
      <div class="container mx-auto px-4 text-center text-gray-500 text-sm">
        <p class="mb-2">&copy; 2025 启航教育在线. 保留所有权利.</p>
        <div class="flex justify-center space-x-6 mt-4">
          <a href="#" class="hover:text-blue-600">关于我们</a>
          <a href="#" class="hover:text-blue-600">联系我们</a>
          <a href="#" class="hover:text-blue-600">隐私政策</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Reuse same bobble CSS as LoginView - imported from parent */
</style>
