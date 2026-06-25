import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(localStorage.getItem('siteTheme') === 'dark')

  function toggle() {
    isDark.value = !isDark.value
    const theme = isDark.value ? 'dark' : 'light'
    localStorage.setItem('siteTheme', theme)
    if (isDark.value) {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }
  }

  function init() {
    if (isDark.value) {
      document.body.classList.add('dark-mode')
    }
  }

  return { isDark, toggle, init }
})
