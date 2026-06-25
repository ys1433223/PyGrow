<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { userApi } from '../api/user'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const router = useRouter()
const auth = useAuthStore()

const seeds = ['Felix', 'Aneka', 'Bob', 'Coco', 'Dave', 'Granny', 'Jack', 'Lola', 'Milo', 'Nala']
const nickname = ref('')
const currentAvatar = ref('')

onMounted(async () => {
  if (!auth.isLoggedIn) {
    if (window.__openLoginPrompt) window.__openLoginPrompt()
    return
  }
  try {
    const res = await userApi.getProfile()
    if (res.data.code === 200) {
      const profile = res.data.data
      nickname.value = profile.nickname || ''
      currentAvatar.value = profile.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=User'
    }
  } catch {
    // Fallback to store data
    if (auth.user) {
      nickname.value = auth.user.name || ''
      currentAvatar.value = auth.user.avatar || ''
    }
  }
})

function selectAvatar(url) {
  currentAvatar.value = url
  const imgs = document.querySelectorAll('.avatar-option')
  imgs.forEach(img => img.classList.remove('selected'))
}

function generateRandomAvatar() {
  const randomSeed = Math.random().toString(36).substring(7)
  currentAvatar.value = `https://api.dicebear.com/7.x/avataaars/svg?seed=${randomSeed}`
}

function triggerFileUpload() {
  document.getElementById('avatarUploadInput').click()
}

function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  if (file.size > 1024 * 1024) {
    alert('图片太大了！为了保证网站速度，请上传小于 1MB 的图片。')
    return
  }
  const reader = new FileReader()
  reader.onload = function (e) {
    currentAvatar.value = e.target.result
    const imgs = document.querySelectorAll('.avatar-option')
    imgs.forEach(img => img.classList.remove('selected'))
  }
  reader.readAsDataURL(file)
}

async function saveProfile(e) {
  e.preventDefault()
  const newName = nickname.value.trim()
  if (!newName) {
    alert('昵称不能为空哦！')
    return
  }
  try {
    await userApi.updateProfile({ nickname: newName, avatar: currentAvatar.value })
    auth.updateUser({ name: newName, avatar: currentAvatar.value })
    alert('✅ 个人资料保存成功！')
    router.push('/')
  } catch (err) {
    if (err.name === 'QuotaExceededError') {
      alert('保存失败：图片文件太大，超出了浏览器存储限制。请换一张小一点的图片试试！')
    } else {
      alert('保存失败，请稍后再试。')
    }
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <div class="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
        <div class="h-32 bg-gradient-to-r from-blue-500 to-purple-600 relative">
          <div class="absolute -bottom-12 left-1/2 -translate-x-1/2">
            <div class="relative group">
              <img :src="currentAvatar"
                   class="w-24 h-24 rounded-full border-4 border-white shadow-md bg-gray-100 object-cover">
              <div class="absolute bottom-0 right-0 bg-white rounded-full p-2 shadow-md border border-gray-200 cursor-pointer hover:bg-gray-50 transition transform hover:scale-110"
                   @click="triggerFileUpload" title="上传本地图片">
                <i class="fas fa-camera text-gray-600 text-sm"></i>
              </div>
            </div>
          </div>
        </div>

        <input type="file" id="avatarUploadInput" accept="image/*" class="hidden" @change="handleFileUpload">

        <div class="pt-16 pb-8 px-8">
          <h1 class="text-2xl font-bold text-center text-gray-800 mb-8">编辑个人资料</h1>

          <form @submit="saveProfile" class="space-y-8">
            <div>
              <label class="block text-sm font-bold text-gray-700 mb-2">我的昵称</label>
              <div class="relative">
                <i class="fas fa-user absolute left-3 top-3 text-gray-400"></i>
                <input type="text" v-model="nickname" required maxlength="12"
                       class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition"
                       placeholder="给自己起个好听的名字">
              </div>
              <p class="text-xs text-gray-400 mt-1">昵称长度限制在 12 个字符以内。</p>
            </div>

            <div>
              <div class="flex justify-between items-center mb-3">
                <label class="block text-sm font-bold text-gray-700">推荐头像</label>
                <button type="button" @click="generateRandomAvatar" class="text-xs text-blue-600 hover:underline">
                  <i class="fas fa-random mr-1"></i> 随机生成
                </button>
              </div>
              <div class="grid grid-cols-4 sm:grid-cols-6 gap-3 mb-4">
                <div v-for="seed in seeds" :key="seed" class="cursor-pointer relative group">
                  <img :src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}`"
                       class="avatar-option w-full aspect-square rounded-full bg-gray-50 p-1 hover:scale-110 transition"
                       :class="{ 'border-3 border-blue-500 scale-110 shadow-md': currentAvatar === `https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}` }"
                       @click="selectAvatar(`https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}`)">
                </div>
              </div>
            </div>

            <div class="flex items-center space-x-4 pt-4 border-t border-gray-100">
              <button type="submit" class="flex-1 bg-blue-600 text-white py-2.5 rounded-lg font-bold hover:bg-blue-700 transition shadow-md hover:-translate-y-0.5">
                保存修改
              </button>
              <a href="/" @click.prevent="$router.push('/')" class="flex-1 text-center bg-gray-100 text-gray-600 py-2.5 rounded-lg font-medium hover:bg-gray-200 transition">
                取消
              </a>
            </div>
          </form>

          <!-- Quick entry links -->
          <div class="pt-6 border-t border-gray-100 mt-6">
            <p class="text-sm font-bold text-gray-500 mb-3 uppercase tracking-wider">快捷入口</p>
            <div class="grid grid-cols-2 gap-3">
              <button @click="$router.push('/adventure')"
                class="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-100 hover:shadow-md hover:-translate-y-0.5 transition group">
                <div class="w-9 h-9 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center shadow">
                  <i class="fas fa-compass text-white text-sm"></i>
                </div>
                <div class="text-left">
                  <p class="text-sm font-bold text-gray-700 group-hover:text-amber-600 transition">宠物探险</p>
                  <p class="text-[10px] text-gray-400">派宠物去探险</p>
                </div>
              </button>
              <button @click="$router.push('/profile/collection')"
                class="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 hover:shadow-md hover:-translate-y-0.5 transition group">
                <div class="w-9 h-9 bg-gradient-to-br from-purple-400 to-pink-500 rounded-lg flex items-center justify-center shadow">
                  <i class="fas fa-book-open text-white text-sm"></i>
                </div>
                <div class="text-left">
                  <p class="text-sm font-bold text-gray-700 group-hover:text-purple-600 transition">我的图鉴</p>
                  <p class="text-[10px] text-gray-400">明信片 & 知识纸条</p>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
