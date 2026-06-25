<script setup>
import { ref, watch, onMounted, onUpdated } from 'vue'
import { useAuthStore } from './stores/auth'
import { initThemeSystem } from './utils/core'
import AssessmentModal from './components/common/AssessmentModal.vue'
import LoginPromptModal from './components/common/LoginPromptModal.vue'
import PetCompanion from './components/PetCompanion.vue'

const auth = useAuthStore()

// Delayed assessment prompt — wait for page transition to finish
const showAssessment = ref(false)
let assessTimer = null

watch(() => auth.showAssessmentPrompt, (val) => {
  clearTimeout(assessTimer)
  if (val) {
    assessTimer = setTimeout(() => { showAssessment.value = true }, 800)
  } else {
    showAssessment.value = false
  }
}, { immediate: true })

// Login prompt modal
const showLoginPrompt = ref(false)

function openLoginPrompt() {
  showLoginPrompt.value = true
}

function closeLoginPrompt() {
  showLoginPrompt.value = false
}

// Expose to window for global access
if (typeof window !== 'undefined') {
  window.__openLoginPrompt = openLoginPrompt
}

onMounted(() => {
  auth.checkAuth()
  initThemeSystem()
})

onUpdated(() => {
  if (typeof lucide !== 'undefined') lucide.createIcons()
})
</script>

<template>
  <router-view />
  <AssessmentModal v-if="showAssessment" />
  <PetCompanion v-if="auth.isLoggedIn" />
  <LoginPromptModal :show="showLoginPrompt" @close="closeLoginPrompt" />
</template>
