<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { userApi } from '../api/user'
import { getMyPosts, deletePost } from '../api/community'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const router = useRouter()
const auth = useAuthStore()

const seeds = ['Cat', 'Dog', 'Panda', 'Fox', 'Koala', 'Owl', 'Frog', 'Bear', 'Tiger', 'Lion']
const nickname = ref('')
const currentAvatar = ref('')
const myPosts = ref([])
const loadingMyPosts = ref(false)
const deletingPostId = ref(null)

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
      currentAvatar.value = profile.avatar || 'https://api.dicebear.com/9.x/fun-emoji/svg?seed=User'
    }
  } catch {
    // Fallback to store data
    if (auth.user) {
      nickname.value = auth.user.name || ''
      currentAvatar.value = auth.user.avatar || ''
    }
  }
  loadMyPosts()
})

function selectAvatar(url) {
  currentAvatar.value = url
  const imgs = document.querySelectorAll('.avatar-option')
  imgs.forEach(img => img.classList.remove('selected'))
}

function generateRandomAvatar() {
  const randomSeed = Math.random().toString(36).substring(7)
  currentAvatar.value = `https://api.dicebear.com/9.x/fun-emoji/svg?seed=${randomSeed}`
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

async function loadMyPosts() {
  loadingMyPosts.value = true
  try {
    const res = await getMyPosts()
    myPosts.value = res.data?.data || []
  } catch {} finally { loadingMyPosts.value = false }
}

async function handleDeletePost(postId) {
  if (!confirm('确定要删除这个帖子吗？删除后无法恢复。')) return
  deletingPostId.value = postId
  try {
    await deletePost(postId)
    myPosts.value = myPosts.value.filter(p => p.id !== postId)
  } catch {} finally { deletingPostId.value = null }
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8 max-w-6xl">
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <!-- Left: Profile card -->
        <div class="lg:col-span-2 bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100 h-fit">
          <div class="h-28 bg-gradient-to-r from-blue-500 to-purple-600 relative">
            <div class="absolute -bottom-10 left-1/2 -translate-x-1/2">
              <div class="relative group">
                <img :src="currentAvatar"
                     class="w-20 h-20 rounded-full border-4 border-white shadow-md bg-gray-100 object-cover">
                <div class="absolute bottom-0 right-0 bg-white rounded-full p-1.5 shadow-md border border-gray-200 cursor-pointer hover:bg-gray-50 transition transform hover:scale-110"
                     @click="triggerFileUpload" title="上传本地图片">
                  <i class="fas fa-camera text-gray-600 text-xs"></i>
                </div>
              </div>
            </div>
          </div>

          <input type="file" id="avatarUploadInput" accept="image/*" class="hidden" @change="handleFileUpload">

          <div class="pt-12 pb-6 px-6">
            <h1 class="text-lg font-bold text-center text-gray-800 mb-6">编辑个人资料</h1>

            <form @submit="saveProfile" class="space-y-5">
              <div>
                <label class="block text-sm font-bold text-gray-700 mb-1.5">我的昵称</label>
                <div class="relative">
                  <i class="fas fa-user absolute left-3 top-2.5 text-gray-400 text-sm"></i>
                  <input type="text" v-model="nickname" required maxlength="12"
                         class="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition text-sm"
                         placeholder="给自己起个好听的名字">
                </div>
                <p class="text-xs text-gray-400 mt-1">昵称长度限制在 12 个字符以内。</p>
              </div>

              <div>
                <div class="flex justify-between items-center mb-2">
                  <label class="text-sm font-bold text-gray-700">推荐头像</label>
                  <button type="button" @click="generateRandomAvatar" class="text-xs text-blue-600 hover:underline">
                    <i class="fas fa-random mr-1"></i> 随机生成
                  </button>
                </div>
                <div class="grid grid-cols-5 gap-2">
                  <div v-for="seed in seeds" :key="seed" class="cursor-pointer relative group">
                    <img :src="`https://api.dicebear.com/9.x/fun-emoji/svg?seed=${seed}`"
                         class="avatar-option w-full aspect-square rounded-full bg-gray-50 p-1 hover:scale-110 transition"
                         :class="{ 'border-3 border-blue-500 scale-110 shadow-md': currentAvatar === `https://api.dicebear.com/9.x/fun-emoji/svg?seed=${seed}` }"
                         @click="selectAvatar(`https://api.dicebear.com/9.x/fun-emoji/svg?seed=${seed}`)">
                  </div>
                </div>
              </div>

              <div class="flex items-center space-x-3 pt-4 border-t border-gray-100">
                <button type="submit" class="flex-1 bg-blue-600 text-white py-2 rounded-lg font-bold text-sm hover:bg-blue-700 transition shadow-md hover:-translate-y-0.5">
                  保存修改
                </button>
                <a href="/" @click.prevent="$router.push('/')" class="flex-1 text-center bg-gray-100 text-gray-600 py-2 rounded-lg font-medium text-sm hover:bg-gray-200 transition">
                  取消
                </a>
              </div>
            </form>

            <!-- Quick entry links -->
            <div class="pt-5 border-t border-gray-100 mt-5">
              <p class="text-xs font-bold text-gray-400 mb-2 uppercase tracking-wider">快捷入口</p>
              <div class="grid grid-cols-2 gap-2">
                <button @click="$router.push('/adventure')"
                  class="flex items-center gap-2 p-2.5 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-100 hover:shadow-md hover:-translate-y-0.5 transition group">
                  <div class="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center shadow flex-shrink-0">
                    <i class="fas fa-compass text-white text-xs"></i>
                  </div>
                  <div class="text-left min-w-0">
                    <p class="text-xs font-bold text-gray-700 group-hover:text-amber-600 transition">宠物探险</p>
                    <p class="text-[10px] text-gray-400">派宠物去探险</p>
                  </div>
                </button>
                <button @click="$router.push('/profile/collection')"
                  class="flex items-center gap-2 p-2.5 rounded-xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 hover:shadow-md hover:-translate-y-0.5 transition group">
                  <div class="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-500 rounded-lg flex items-center justify-center shadow flex-shrink-0">
                    <i class="fas fa-book-open text-white text-xs"></i>
                  </div>
                  <div class="text-left min-w-0">
                    <p class="text-xs font-bold text-gray-700 group-hover:text-purple-600 transition">我的图鉴</p>
                    <p class="text-[10px] text-gray-400">明信片 & 知识纸条</p>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: My Posts -->
        <div class="lg:col-span-3 bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden h-fit min-h-[400px]">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div class="flex items-center gap-2">
              <i class="fas fa-newspaper text-blue-500"></i>
              <p class="text-sm font-bold text-gray-700">我的发布</p>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-xs text-gray-400">{{ myPosts.length }} 篇帖子</span>
              <button @click="$router.push('/community')" class="text-xs text-blue-600 hover:underline font-medium">
                <i class="fas fa-plus mr-0.5"></i>发帖
              </button>
            </div>
          </div>
          <div class="p-4">
            <div v-if="loadingMyPosts" class="text-center py-12">
              <div class="animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
            </div>
            <div v-else-if="myPosts.length === 0" class="text-center py-16">
              <div class="w-16 h-16 mx-auto mb-3 bg-gray-50 rounded-full flex items-center justify-center">
                <i class="fas fa-pen-to-square text-gray-300 text-xl"></i>
              </div>
              <p class="text-gray-400 text-sm mb-2">还没有发布过帖子</p>
              <button @click="$router.push('/community')" class="text-blue-600 text-sm hover:underline">去社区发布</button>
            </div>
            <div v-else class="space-y-2">
              <div v-for="post in myPosts" :key="post.id"
                class="flex items-start justify-between bg-gray-50 rounded-xl p-3.5 hover:bg-gray-100 transition group">
                <div class="min-w-0 flex-1 cursor-pointer" @click="$router.push(`/community?post=${post.id}`)">
                  <div class="flex items-center gap-2 mb-1">
                    <span :class="['text-[10px] px-1.5 py-0.5 rounded-full font-medium', post.category === '问答专区' ? 'bg-red-100 text-red-600' : post.category === '技术分享区' ? 'bg-blue-100 text-blue-600' : post.category === '资源分享' ? 'bg-green-100 text-green-600' : post.category === '我要吐槽' ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-500']">{{ post.category }}</span>
                    <span class="text-[10px] text-gray-400">{{ post.created_at?.slice(0, 10) }}</span>
                  </div>
                  <p class="text-sm font-bold text-gray-700 truncate">{{ post.title }}</p>
                  <div class="flex items-center gap-3 text-xs text-gray-400 mt-1">
                    <span><i class="far fa-heart mr-0.5"></i>{{ post.like_count }}</span>
                    <span><i class="far fa-comment mr-0.5"></i>{{ post.comment_count }}</span>
                  </div>
                </div>
                <button @click.stop="handleDeletePost(post.id)" :disabled="deletingPostId === post.id"
                  class="flex-shrink-0 ml-3 text-xs text-gray-400 hover:text-red-500 transition px-2 py-1 rounded-lg hover:bg-red-50 disabled:opacity-50"
                  title="删除帖子">
                  <i v-if="deletingPostId === post.id" class="fas fa-spinner animate-spin"></i>
                  <i v-else class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
