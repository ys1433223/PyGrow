import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue') },
  { path: '/profile', name: 'profile', component: () => import('../views/ProfileView.vue'), meta: { requiresAuth: true } },
  { path: '/courses', name: 'courses', component: () => import('../views/CourseCenterView.vue') },
  { path: '/courses/:id', name: 'courseDetail', component: () => import('../views/CourseDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/assessment', name: 'assessment', component: () => import('../views/AssessmentView.vue'), meta: { requiresAuth: true } },
  { path: '/assessment/result', name: 'assessmentResult', component: () => import('../views/AssessmentResultView.vue'), meta: { requiresAuth: true } },
  { path: '/practice', name: 'practice', component: () => import('../views/PracticeView.vue'), meta: { requiresAuth: true } },
  { path: '/daily-practice', name: 'dailyPractice', component: () => import('../views/DailyPracticeView.vue'), meta: { requiresAuth: true } },
  { path: '/report', name: 'report', component: () => import('../views/ReportView.vue'), meta: { requiresAuth: true } },
  { path: '/code-runner', name: 'codeRunner', component: () => import('../views/CodeRunnerView.vue'), meta: { requiresAuth: true } },
  { path: '/projects', name: 'projects', component: () => import('../views/ProjectCenterView.vue'), meta: { requiresAuth: true } },
  { path: '/community', name: 'community', component: () => import('../views/CommunityView.vue'), meta: { requiresAuth: true } },
  { path: '/admin', name: 'admin', component: () => import('../views/AdminView.vue'), meta: { requiresAuth: true } },
  { path: '/learning-center', name: 'learningCenter', component: () => import('../views/LearningCenterView.vue') },
  { path: '/resources', name: 'resources', component: () => import('../views/ResourcesView.vue') },
  { path: '/favorites', name: 'favorites', component: () => import('../views/FavoritesView.vue'), meta: { requiresAuth: true } },
  { path: '/adventure', name: 'adventure', component: () => import('../views/AdventureView.vue'), meta: { requiresAuth: true } },
  { path: '/profile/collection', name: 'collection', component: () => import('../views/CollectionView.vue'), meta: { requiresAuth: true } },
  { path: '/leaderboard', name: 'leaderboard', component: () => import('../views/LeaderboardView.vue'), meta: { requiresAuth: true } },
  { path: '/promotion', name: 'promotion', component: () => import('../views/PromotionView.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('access_token')
    if (!token) {
      // Show login prompt popup instead of redirect
      if (window.__openLoginPrompt) {
        window.__openLoginPrompt()
      }
      return next(from.path || '/')
    }
  }
  next()
})

export default router
