<script setup>
import { ref, watch, onMounted, onUpdated } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { initThemeSystem } from './utils/core'
import AssessmentModal from './components/common/AssessmentModal.vue'
import LoginPromptModal from './components/common/LoginPromptModal.vue'
import PasswordGate from './components/common/PasswordGate.vue'
import PetCompanion from './components/PetCompanion.vue'

const router = useRouter()
const auth = useAuthStore()

// Delayed assessment prompt — wait for initial route to finish loading
const showAssessment = ref(false)
let assessTimer = null
let routerReady = false

// Wait for router to be ready before allowing assessment modal
router.isReady().then(() => {
  routerReady = true
  // If assessment was already requested, start the timer now
  if (auth.showAssessmentPrompt) {
    assessTimer = setTimeout(() => { showAssessment.value = true }, 800)
  }
})

watch(() => auth.showAssessmentPrompt, (val) => {
  clearTimeout(assessTimer)
  if (val && routerReady) {
    assessTimer = setTimeout(() => { showAssessment.value = true }, 800)
  } else {
    showAssessment.value = false
  }
})

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

// Run immediately (not in onMounted) so child components see restored auth state
auth.checkAuth()

onMounted(() => {
  initThemeSystem()
})

onUpdated(() => {
  if (typeof lucide !== 'undefined') lucide.createIcons()
})
</script>

<template>
  <PasswordGate />
  <router-view />
  <AssessmentModal v-if="showAssessment" />
  <PetCompanion v-if="auth.isLoggedIn" />
  <LoginPromptModal :show="showLoginPrompt" @close="closeLoginPrompt" />
</template>
