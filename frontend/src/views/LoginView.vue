<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppHeader from '../components/layout/AppHeader.vue'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

let follow = true

onMounted(() => {
  const article = document.querySelector('.login-register-page article')
  if (!article) return
  const section = article.querySelector('section')

  const interactiveEls = section.querySelectorAll('input, button, a')
  interactiveEls.forEach(el => {
    el.addEventListener('focus', () => { follow = false; section.style = '' })
    el.addEventListener('blur', () => { follow = true })
  })

  section.addEventListener('mousemove', function (e) {
    if (follow) {
      const top = section.getBoundingClientRect().top
      const left = section.getBoundingClientRect().left
      const height = section.getBoundingClientRect().height
      const width = section.getBoundingClientRect().width
      section.style = `--x:${35 * (e.clientX - left) / width};--y:${-20 * (e.clientY - top) / height};`
    }
  })
  section.addEventListener('mouseleave', () => { follow = false; section.style = '' })
  section.addEventListener('mouseenter', () => { follow = true })
})

function togglePasswordVisibility(e) {
  const pwInput = document.getElementById('password-input')
  if (pwInput) pwInput.type = e.target.checked ? 'text' : 'password'
}

async function handleLogin() {
  errorMsg.value = ''
  if (!username.value || !password.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  const result = await auth.login(username.value, password.value)
  loading.value = false
  if (result.success) {
    router.push('/')
  } else {
    errorMsg.value = result.message || '登录失败'
  }
}
</script>

<template>
  <div class="login-register-page flex flex-col min-h-screen">
    <AppHeader />

    <article class="flex-grow flex items-center justify-center" style="min-height: auto; width: 100%;">
      <section>
        <div class="bobbles">
          <div class="bobble-1"></div>
          <div class="bobble-2"></div>
          <div class="bobble-3"></div>
          <div class="bobble-4"></div>
        </div>
        <form autocomplete="off" @submit.prevent="handleLogin">
          <h2>欢迎!</h2>
          <p>请输入账号/密码</p>

          <div>
            <label for="username-input">账号</label>
            <input type="text" id="username-input" name="username" v-model="username" required />
          </div>

          <div>
            <label for="password-input">密码</label>
            <input type="password" id="password-input" name="password" v-model="password" required />
            <input type="checkbox" @change="togglePasswordVisibility" />
          </div>

          <p v-if="errorMsg" class="text-red-500 text-sm text-center mb-2">{{ errorMsg }}</p>

          <div class="forgot">
            <a href="#">忘记了密码？</a>
          </div>

          <button type="submit" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>

          <p class="signup">
            还没有账号？ <a href="/register" @click.prevent="$router.push('/register')">注册</a>
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
