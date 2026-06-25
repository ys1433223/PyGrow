import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const user = ref(null)
  const showAssessmentPrompt = ref(false)

  const isLoggedIn = computed(() => !!token.value)

  function checkAuth() {
    const savedToken = localStorage.getItem('access_token')
    const savedUser = localStorage.getItem('userInfo')
    if (savedToken && savedUser) {
      token.value = savedToken
      try {
        user.value = JSON.parse(savedUser)
        if (!user.value.avatar) {
          user.value.avatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + (user.value.name || 'User')
        }
        // Show assessment prompt if user hasn't taken it yet
        if (user.value.has_assessment === false) {
          showAssessmentPrompt.value = true
        }
      } catch {
        user.value = null
      }
    }
  }

  async function login(username, password) {
    try {
      const res = await authApi.login(username, password)
      if (res.data.code === 200 && res.data.data) {
        const d = res.data.data
        token.value = d.access_token
        user.value = d.user
        localStorage.setItem('access_token', d.access_token)
        localStorage.setItem('userInfo', JSON.stringify(d.user))
        if (!d.user.has_assessment) showAssessmentPrompt.value = true
        return { success: true }
      }
      return { success: false, message: res.data.message }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || '网络请求失败'
      return { success: false, message: msg }
    }
  }

  async function register(username, password, confirmPassword) {
    try {
      const res = await authApi.register(username, password, confirmPassword)
      if (res.data.code === 200 && res.data.data) {
        const d = res.data.data
        token.value = d.access_token
        user.value = d.user
        localStorage.setItem('access_token', d.access_token)
        localStorage.setItem('userInfo', JSON.stringify(d.user))
        if (!d.user.has_assessment) showAssessmentPrompt.value = true
        return { success: true }
      }
      return { success: false, message: res.data.message }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || '网络请求失败'
      return { success: false, message: msg }
    }
  }

  function dismissAssessmentPrompt() {
    showAssessmentPrompt.value = false
  }

  function markAssessmentDone() {
    showAssessmentPrompt.value = false
    if (user.value) {
      user.value.has_assessment = true
      localStorage.setItem('userInfo', JSON.stringify(user.value))
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('userInfo')
  }

  function updateUser(updates) {
    if (user.value) {
      user.value = { ...user.value, ...updates }
      localStorage.setItem('userInfo', JSON.stringify(user.value))
    }
  }

  return { token, user, isLoggedIn, showAssessmentPrompt, checkAuth, login, register, logout, updateUser, dismissAssessmentPrompt, markAssessmentDone }
})
