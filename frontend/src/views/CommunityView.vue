<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { getPosts, getHotPosts, getPostDetail, createPost, addComment, toggleLike, toggleFavorite, toggleCommentLike } from '../api/community'
import { getXPLeaderboard, getProjectsLeaderboard, getStreakLeaderboard } from '../api/leaderboard'
import { useAuthStore } from '../stores/auth'
const route = useRoute()
import { calcMajorLevel } from '../utils/levels'

// ---- tag system ----
const TAG_CATEGORIES = {
  '知识点标签': ['变量', '数据类型', '字符串', '输入输出', 'if判断', 'for循环', 'while循环', '列表', '字典', '函数', '模块', '文件操作', '面向对象', '爬虫', '数据分析'],
  '错误类型标签': ['SyntaxError', 'IndentationError', 'NameError', 'TypeError', 'IndexError', '缺少冒号', '缩进问题', '变量未定义', '类型转换错误', '死循环', '运行无输出'],
  '学习阶段标签': ['入门级', '初级', '中级', '高级'],
  '内容类型标签': ['代码求助', '报错求助', '思路求助', '经验分享', '学习笔记', '项目展示', '资源推荐', '课程反馈', '功能建议', '学习吐槽'],
  '资源类型标签': ['视频课程', '图文教程', '项目案例', '练习题', '代码模板', '工具网站', '电子书', '学习路线'],
}

const SECTION_TAGS = {
  '技术分享区': ['知识点标签', '内容类型标签'],
  '问答专区': ['知识点标签', '错误类型标签', '学习阶段标签', '内容类型标签'],
  '资源分享': ['知识点标签', '资源类型标签'],
  '我要吐槽': ['内容类型标签', '学习阶段标签'],
}

const sections = Object.keys(SECTION_TAGS)
const allTags = computed(() => {
  if (!activeSection.value) return Object.values(TAG_CATEGORIES).flat()
  return SECTION_TAGS[activeSection.value].flatMap(k => TAG_CATEGORIES[k])
})

// Honor title config
const HONOR_TITLES = [
  { min: 5, name: '冒泡新星', cls: 'text-gray-500 border-gray-300 bg-gray-50' },
  { min: 40, name: '点赞收割机', cls: 'text-blue-600 border-blue-300 bg-blue-50' },
  { min: 100, name: '话题制造者', cls: 'text-purple-600 border-purple-300 bg-purple-50' },
  { min: 500, name: '镇站之宝', cls: 'text-amber-600 border-amber-400 bg-amber-50' },
]

function getHonorStyle(honor) {
  if (!honor) return ''
  const t = HONOR_TITLES.findLast(h => honor.level >= h.min)
  return t ? t.cls : ''
}

const auth = useAuthStore()

// ---- state ----
const posts = ref([])
const hotPosts = ref([])
const leaderboard = ref([])
const activeSection = ref(null)

// ---- leaderboard controls ----
const lbDimension = ref('xp')
const lbTier = ref('')
const lbDimensions = [
  { key: 'xp', label: '经验排行', icon: 'fas fa-star' },
  { key: 'projects', label: '项目完成', icon: 'fas fa-tasks' },
  { key: 'streak', label: '学习活跃', icon: 'fas fa-fire' },
]
const lbTiers = ['全部', '初级', '中级', '高级']

const myMajorLevel = computed(() => {
  if (!auth.user?.level) return '初级'
  return calcMajorLevel(auth.user.level)
})
const view = ref('list')
const currentPost = ref(null)
const page = ref(1)
const keyword = ref('')
const selectedTag = ref('')
const loading = ref(true)

// create
const newTitle = ref('')
const newContent = ref('')
const newCategory = ref('问答专区')
const newTags = ref([])
const creating = ref(false)
const createError = ref('')
const showTagPicker = ref(false)
const tagsExpanded = ref(false)

const groupedTags = computed(() => {
  const active = allTags.value
  const groups = []
  for (const [category, tags] of Object.entries(TAG_CATEGORIES)) {
    const relevant = tags.filter(t => active.includes(t))
    if (relevant.length > 0) groups.push({ category, tags: relevant })
  }
  return groups
})

// comment
const commentInput = ref('')
const commenting = ref(false)

// computed tags available for the selected category in create form
const createAvailableTags = computed(() => {
  const cat = newCategory.value
  if (!SECTION_TAGS[cat]) return []
  return SECTION_TAGS[cat].map(k => ({ group: k, tags: TAG_CATEGORIES[k] }))
})

function getTagColor(tag) {
  const colors = { '知识点标签': 'bg-blue-100 text-blue-700', '错误类型标签': 'bg-red-100 text-red-700', '学习阶段标签': 'bg-purple-100 text-purple-700', '内容类型标签': 'bg-green-100 text-green-700', '资源类型标签': 'bg-amber-100 text-amber-700' }
  for (const [group, t] of Object.entries(TAG_CATEGORIES)) {
    if (t.includes(tag)) return colors[group] || 'bg-gray-100 text-gray-600'
  }
  return 'bg-gray-100 text-gray-600'
}

function toggleNewTag(tag) {
  const idx = newTags.value.indexOf(tag)
  if (idx >= 0) newTags.value.splice(idx, 1)
  else newTags.value.push(tag)
}

// ---- data loading ----
async function loadPosts() {
  loading.value = true
  try {
    const res = await getPosts(page.value, activeSection.value, keyword.value || null, selectedTag.value || null)
    posts.value = res.data?.data || []
  } finally { loading.value = false }
}

async function loadHotPosts() {
  try {
    const res = await getHotPosts(8)
    hotPosts.value = res.data?.data || []
  } catch {}
}

async function loadLeaderboard() {
  const level = lbTier.value || undefined
  try {
    let res
    if (lbDimension.value === 'projects') {
      res = await getProjectsLeaderboard(10, level)
    } else if (lbDimension.value === 'streak') {
      res = await getStreakLeaderboard(10, level)
    } else {
      res = await getXPLeaderboard(10, level)
    }
    leaderboard.value = res.data?.data?.leaderboard || []
  } catch {}
}

function switchLbDim(dim) {
  lbDimension.value = dim
  loadLeaderboard()
}

function switchLbTier(tier) {
  lbTier.value = tier === '全部' ? '' : tier
  loadLeaderboard()
}

function getLbValue(item) {
  if (lbDimension.value === 'projects') return item.project_count
  if (lbDimension.value === 'streak') return item.active_days
  return item.experience
}

function switchSection(section) {
  activeSection.value = activeSection.value === section ? null : section
  selectedTag.value = ''
  page.value = 1
  loadPosts()
}

function doSearch() {
  page.value = 1
  loadPosts()
}

function clearSearch() {
  keyword.value = ''
  selectedTag.value = ''
  page.value = 1
  loadPosts()
}

function selectTag(tag) {
  selectedTag.value = selectedTag.value === tag ? '' : tag
  page.value = 1
  loadPosts()
}

async function openDetail(post) {
  try {
    const res = await getPostDetail(post.id)
    currentPost.value = res.data.data
    view.value = 'detail'
  } catch {}
}

function backToList() {
  view.value = 'list'
  currentPost.value = null
}

function openHotPost(postId) {
  // find the post in posts or fetch detail
  getPostDetail(postId).then(res => {
    currentPost.value = res.data.data
    view.value = 'detail'
  }).catch(() => {})
}

async function handleCreate() {
  createError.value = ''
  if (newTitle.value.trim().length < 2) { createError.value = '标题至少 2 个字'; return }
  if (newContent.value.trim().length < 10) { createError.value = '内容不少于 10 个字'; return }
  creating.value = true
  try {
    await createPost(newTitle.value, newContent.value, newCategory.value, newTags.value.join(','))
    newTitle.value = ''
    newContent.value = ''
    newTags.value = []
    activeSection.value = newCategory.value
    selectedTag.value = ''
    view.value = 'list'
    page.value = 1
    loadPosts()
  } catch (e) {
    createError.value = e.response?.data?.message || '发布失败'
  } finally { creating.value = false }
}

async function handleLike(post) {
  try {
    const res = await toggleLike(post.id)
    const d = res.data.data
    post.like_count = d.like_count
    post.is_liked = d.liked
  } catch {}
}

async function handleComment() {
  if (!commentInput.value.trim() || !currentPost.value) return
  commenting.value = true
  try {
    const res = await addComment(currentPost.value.id, commentInput.value)
    currentPost.value.comments.push({
      id: res.data.data.id, content: commentInput.value, created_at: new Date().toISOString(),
      user_name: '我', user_avatar: '', like_count: 0, is_liked: false, honor_title: null,
    })
    currentPost.value.comment_count++
    commentInput.value = ''
  } catch {} finally { commenting.value = false }
}

async function handleCommentLike(comment) {
  try {
    const res = await toggleCommentLike(comment.id)
    const d = res.data.data
    comment.like_count = d.like_count
    comment.is_liked = d.liked
  } catch {}
}

onMounted(() => {
  lbTier.value = myMajorLevel.value
  loadPosts()
  loadHotPosts()
  loadLeaderboard()
  // Auto-open post detail from query param
  const postId = route.query.post
  if (postId) {
    getPostDetail(Number(postId)).then(res => {
      if (res.data.code === 200) {
        currentPost.value = res.data.data
        view.value = 'detail'
      }
    }).catch(() => {})
  }
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <AppHeader />
    <PageLoader />

    <main class="flex-grow container mx-auto px-4 py-6">
      <!-- Page header -->
      <div v-if="view !== 'detail'" class="flex items-center justify-between mb-5">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">
            <span v-if="view !== 'list'" class="cursor-pointer hover:text-blue-600 transition" @click="backToList">学习社区</span>
            <span v-else>学习社区</span>
          </h1>
          <p v-if="view === 'list'" class="text-gray-500 text-sm mt-1">交流学习心得，分享编程经验</p>
        </div>
        <button v-if="view === 'list'" @click="view = 'create'" class="bg-blue-600 text-white px-5 py-2.5 rounded-full text-sm font-medium hover:bg-blue-700 transition-all shadow-sm">
          <i class="fas fa-pen mr-1.5"></i>发布帖子
        </button>
      </div>

      <!-- ====== List View: 3-column layout ====== -->
      <div v-if="view === 'list'" class="flex gap-5">
        <!-- LEFT: Leaderboard sidebar -->
        <aside class="hidden lg:block w-60 flex-shrink-0">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sticky top-20">
            <h3 class="font-bold text-gray-800 text-sm mb-3 flex items-center">
              <i class="fas fa-trophy text-amber-500 mr-2"></i>排行榜
            </h3>

            <!-- Tier switcher -->
            <div class="flex gap-1 mb-3 bg-gray-100 rounded-lg p-0.5">
              <button v-for="t in lbTiers" :key="t" @click="switchLbTier(t)"
                :class="(t === '全部' ? !lbTier : lbTier === t) ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
                class="flex-1 text-[11px] py-1 rounded-md font-medium transition-all">{{ t }}</button>
            </div>

            <!-- Dimension tabs -->
            <div class="flex gap-1 mb-3">
              <button v-for="d in lbDimensions" :key="d.key" @click="switchLbDim(d.key)"
                :class="lbDimension === d.key ? 'bg-blue-50 text-blue-700' : 'text-gray-500 hover:text-gray-700'"
                class="flex-1 text-[10px] py-1.5 rounded-md font-medium transition-all flex items-center justify-center gap-1">
                <i :class="d.icon"></i>{{ d.label.slice(0, 2) }}
              </button>
            </div>

            <!-- Rank list -->
            <div v-if="leaderboard.length === 0" class="text-xs text-gray-400 text-center py-6">暂无数据</div>
            <div v-else class="space-y-1">
              <div v-for="item in leaderboard.slice(0, 10)" :key="item.user_id"
                class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-50 transition-colors text-xs">
                <span class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                  :class="{
                    'bg-amber-100 text-amber-700': item.rank === 1,
                    'bg-gray-200 text-gray-500': item.rank === 2,
                    'bg-orange-100 text-orange-700': item.rank === 3,
                    'text-gray-400': item.rank > 3,
                  }">{{ item.rank }}</span>
                <div class="flex-1 min-w-0">
                  <span class="text-gray-700 font-medium truncate block leading-tight">{{ item.username }}</span>
                  <span class="text-gray-400 text-[10px]">{{ item.level || '' }}</span>
                </div>
                <span class="text-gray-400 flex-shrink-0 text-[10px] font-medium">{{ getLbValue(item) }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- CENTER: Posts -->
        <div class="flex-1 min-w-0">
          <!-- Section tabs -->
          <div class="flex flex-wrap gap-2 mb-4">
            <button v-for="s in sections" :key="s" @click="switchSection(s)"
              :class="activeSection === s ? 'bg-blue-600 text-white shadow' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'"
              class="px-4 py-2 rounded-full text-sm font-medium transition-all">{{ s }}</button>
          </div>

          <!-- Search & filter bar -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-100 mb-4 overflow-hidden">
            <!-- Search row -->
            <div class="flex items-center gap-3 p-3">
              <div class="flex items-center flex-1 min-w-[200px]">
                <input v-model="keyword" @keyup.enter="doSearch" placeholder="搜索帖子标题或内容..."
                  class="flex-1 border-0 outline-none text-sm px-2 py-1" />
                <button @click="doSearch" class="text-blue-600 hover:text-blue-700 px-2">
                  <i class="fas fa-search"></i>
                </button>
                <button v-if="keyword || selectedTag" @click="clearSearch" class="text-gray-400 hover:text-gray-600 px-2">
                  <i class="fas fa-times"></i>
                </button>
              </div>
              <button @click="tagsExpanded = !tagsExpanded"
                class="flex items-center gap-1 text-xs text-gray-500 hover:text-blue-600 transition-colors flex-shrink-0 px-2 py-1">
                <i class="fas fa-tags"></i> 标签筛选
                <i :class="tagsExpanded ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
              </button>
            </div>
            <!-- Tag filter panel (collapsible) -->
            <div v-if="tagsExpanded" class="border-t border-gray-100 p-3 bg-gray-50/50 max-h-64 overflow-y-auto">
              <div v-if="selectedTag" class="mb-2 flex items-center gap-1">
                <span class="text-xs text-gray-400">已选:</span>
                <span :class="['text-xs px-2 py-0.5 rounded-full cursor-pointer', getTagColor(selectedTag)]" @click="selectedTag = ''; page = 1; loadPosts()">
                  {{ selectedTag }} <i class="fas fa-times ml-1 text-[10px]"></i>
                </span>
              </div>
              <div v-for="group in groupedTags" :key="group.category" class="mb-3 last:mb-0">
                <p class="text-[10px] font-bold text-gray-400 uppercase mb-1.5">{{ group.category }}</p>
                <div class="flex flex-wrap gap-1.5">
                  <button v-for="tag in group.tags" :key="tag" @click="selectTag(tag)"
                    :class="selectedTag === tag ? 'ring-1 ring-blue-300 ' + getTagColor(tag) : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300 hover:bg-gray-50'"
                    class="px-2 py-0.5 rounded-full text-xs transition-all">{{ tag }}</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Post list -->
          <div v-if="loading" class="flex justify-center py-20">
            <div class="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full"></div>
          </div>
          <div v-else-if="posts.length === 0" class="text-center py-20 text-gray-400 bg-white rounded-2xl shadow-sm border border-gray-100">
            <p class="text-4xl mb-3">📝</p>
            <p>暂无帖子</p>
            <p class="text-sm mt-1">成为第一个发帖的人吧!</p>
          </div>
          <div v-else class="space-y-3">
            <div v-for="p in posts" :key="p.id" @click="openDetail(p)"
              class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 cursor-pointer hover:shadow-md transition-all">
              <div class="flex items-center gap-2 mb-2 flex-wrap">
                <span :class="['text-xs px-2 py-0.5 rounded-full', p.category === '问答专区' ? 'bg-red-100 text-red-600' : p.category === '技术分享区' ? 'bg-blue-100 text-blue-600' : p.category === '资源分享' ? 'bg-green-100 text-green-600' : p.category === '我要吐槽' ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-500']">{{ p.category }}</span>
                <span v-if="p.tags" v-for="t in (p.tags || '').split(',').filter(Boolean)" :key="t"
                  :class="['text-xs px-1.5 py-0.5 rounded-full', getTagColor(t)]">{{ t }}</span>
                <span v-if="p.is_pinned" class="text-xs text-red-400 font-bold">📌 置顶</span>
              </div>
              <h3 class="font-bold text-gray-800 mb-1.5">{{ p.title }}</h3>
              <p class="text-sm text-gray-500 line-clamp-2 mb-3">{{ p.content }}</p>
              <div class="flex items-center justify-between text-xs text-gray-400">
                <div class="flex items-center gap-2">
                  <span>{{ p.user_name }}</span>
                  <span v-if="p.honor_title" :class="['text-[10px] px-1.5 py-0.5 rounded-full border font-bold', getHonorStyle(p.honor_title)]">{{ p.honor_title.name }}</span>
                  <span>{{ p.created_at?.slice(0, 10) }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <span @click.stop="handleLike(p)" class="flex items-center gap-1 cursor-pointer" :class="{ 'text-red-500': p.is_liked }">
                    <i :class="p.is_liked ? 'fas fa-heart' : 'far fa-heart'"></i>{{ p.like_count }}
                  </span>
                  <span><i class="far fa-comment mr-1"></i>{{ p.comment_count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: Hot posts sidebar -->
        <aside class="hidden xl:block w-60 flex-shrink-0">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sticky top-20">
            <h3 class="font-bold text-gray-800 text-sm mb-3 flex items-center">
              <i class="fas fa-fire text-red-500 mr-2"></i>热门帖子
            </h3>
            <div v-if="hotPosts.length === 0" class="text-xs text-gray-400 text-center py-6">暂无数据</div>
            <div v-else class="space-y-0.5">
              <div v-for="(hp, i) in hotPosts" :key="hp.id"
                @click="openHotPost(hp.id)"
                class="flex items-start gap-2 px-2 py-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                <span class="text-xs font-bold flex-shrink-0 w-5"
                  :class="i < 3 ? 'text-red-500' : 'text-gray-400'">{{ i + 1 }}</span>
                <span class="text-xs text-gray-700 leading-snug line-clamp-2 flex-1">{{ hp.title }}</span>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <!-- ====== Detail View ====== -->
      <div v-if="view === 'detail' && currentPost" class="max-w-3xl mx-auto">
        <button @click="backToList" class="text-sm text-gray-500 hover:text-blue-600 mb-4 flex items-center gap-1 transition-colors">
          <i class="fas fa-arrow-left text-xs"></i> 返回列表
        </button>

        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
          <div class="flex items-center gap-2 mb-4 flex-wrap">
            <span :class="['text-xs px-2 py-0.5 rounded-full', currentPost.category === '问答专区' ? 'bg-red-100 text-red-600' : currentPost.category === '技术分享区' ? 'bg-blue-100 text-blue-600' : currentPost.category === '资源分享' ? 'bg-green-100 text-green-600' : currentPost.category === '我要吐槽' ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-500']">{{ currentPost.category }}</span>
            <span v-if="currentPost.tags" v-for="t in (currentPost.tags || '').split(',').filter(Boolean)" :key="t"
              :class="['text-xs px-1.5 py-0.5 rounded-full', getTagColor(t)]">{{ t }}</span>
            <span class="text-xs text-gray-400">
              {{ currentPost.author_name }}
              <span v-if="currentPost.author_honor_title" :class="['text-[10px] px-1.5 py-0.5 rounded-full border font-bold ml-1', getHonorStyle(currentPost.author_honor_title)]">{{ currentPost.author_honor_title.name }}</span>
              · {{ currentPost.created_at?.slice(0, 10) }}
            </span>
          </div>
          <h2 class="text-xl font-bold text-gray-800 mb-4">{{ currentPost.title }}</h2>
          <div class="text-gray-700 leading-relaxed whitespace-pre-wrap">{{ currentPost.content }}</div>
          <div class="flex items-center gap-4 mt-6 pt-4 border-t border-gray-100">
            <button @click="handleLike({ id: currentPost.id, like_count: currentPost.like_count, is_liked: currentPost.is_liked }); currentPost.like_count = currentPost.is_liked ? currentPost.like_count - 1 : currentPost.like_count + 1; currentPost.is_liked = !currentPost.is_liked"
              class="flex items-center gap-1.5 text-sm" :class="currentPost.is_liked ? 'text-red-500' : 'text-gray-500'">
              <i :class="currentPost.is_liked ? 'fas fa-heart' : 'far fa-heart'"></i>{{ currentPost.like_count }}
            </button>
            <button @click="toggleFavorite(currentPost.id); currentPost.is_favorited = !currentPost.is_favorited"
              class="text-sm" :class="currentPost.is_favorited ? 'text-yellow-500' : 'text-gray-500 hover:text-yellow-500'">
              <i :class="currentPost.is_favorited ? 'fas fa-star' : 'far fa-star'"></i> 收藏
            </button>
            <span class="text-sm text-gray-400"><i class="far fa-comment mr-1"></i>{{ currentPost.comment_count }}</span>
          </div>
        </div>

        <!-- Comments -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 class="font-bold text-gray-800 mb-4">评论 ({{ currentPost.comment_count }})</h3>
          <div class="flex items-start gap-3 mb-6">
            <textarea v-model="commentInput" class="flex-1 border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-blue-400 resize-none" rows="2" placeholder="写下你的评论..."></textarea>
            <button @click="handleComment" :disabled="commenting || !commentInput.trim()"
              class="bg-blue-600 text-white px-4 py-2.5 rounded-xl text-sm hover:bg-blue-700 disabled:opacity-50 transition">{{ commenting ? '...' : '评论' }}</button>
          </div>
          <div v-if="currentPost.comments.length === 0" class="text-center py-8 text-gray-400">暂无评论</div>
          <div v-else class="space-y-4">
            <div v-for="c in currentPost.comments" :key="c.id" class="flex gap-3 pb-4 border-b border-gray-50 last:border-0">
              <div class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-500 flex-shrink-0"><i class="fas fa-user text-xs"></i></div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1 flex-wrap">
                  <span class="text-sm font-medium text-gray-700">{{ c.user_name }}</span>
                  <span v-if="c.honor_title" :class="['text-[10px] px-1.5 py-0.5 rounded-full border font-bold', getHonorStyle(c.honor_title)]">{{ c.honor_title.name }}</span>
                  <span class="text-xs text-gray-400">{{ c.created_at?.slice(0, 10) }}</span>
                </div>
                <p class="text-sm text-gray-600">{{ c.content }}</p>
                <div class="flex items-center gap-3 mt-1.5">
                  <button @click="handleCommentLike(c)" class="flex items-center gap-1 text-xs" :class="c.is_liked ? 'text-red-500' : 'text-gray-400 hover:text-red-400'">
                    <i :class="c.is_liked ? 'fas fa-heart' : 'far fa-heart'"></i>{{ c.like_count || 0 }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== Create View ====== -->
      <div v-if="view === 'create'" class="max-w-2xl mx-auto">
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 class="text-lg font-bold text-gray-800 mb-4">发布新帖子</h2>

          <!-- Category -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-600 mb-2">选择分区</label>
            <div class="flex flex-wrap gap-2">
              <button v-for="s in sections" :key="s" @click="newCategory = s; newTags = []; showTagPicker = false"
                :class="newCategory === s ? 'bg-blue-600 text-white shadow' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                class="px-4 py-2 rounded-full text-sm font-medium transition-all">{{ s }}</button>
            </div>
          </div>

          <!-- Tags -->
          <div class="mb-4">
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-gray-600">选择标签</label>
              <button @click="showTagPicker = !showTagPicker" class="text-xs text-blue-600 hover:text-blue-700">
                {{ showTagPicker ? '收起' : '展开' }} <i :class="showTagPicker ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
              </button>
            </div>
            <!-- Selected tags -->
            <div v-if="newTags.length > 0" class="flex flex-wrap gap-1.5 mb-2">
              <span v-for="t in newTags" :key="t" @click="toggleNewTag(t)"
                :class="['text-xs px-2 py-0.5 rounded-full cursor-pointer', getTagColor(t)]">{{ t }} ✕</span>
            </div>
            <!-- Tag picker -->
            <div v-if="showTagPicker" class="bg-gray-50 rounded-xl p-3 space-y-2 max-h-48 overflow-y-auto">
              <div v-for="group in createAvailableTags" :key="group.group">
                <p class="text-xs text-gray-400 mb-1">{{ group.group }}</p>
                <div class="flex flex-wrap gap-1.5">
                  <button v-for="tag in group.tags" :key="tag" @click="toggleNewTag(tag)"
                    :class="newTags.includes(tag) ? getTagColor(tag) + ' ring-1 ring-current' : 'bg-white text-gray-500 border border-gray-200 hover:border-gray-300'"
                    class="px-2 py-0.5 rounded-full text-xs transition-all">{{ tag }}</button>
                </div>
              </div>
            </div>
          </div>

          <input v-model="newTitle" class="w-full border border-gray-200 rounded-lg px-3 py-2 mb-3 text-sm outline-none focus:border-blue-400" placeholder="标题（至少 2 个字）" />
          <textarea v-model="newContent" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none" rows="6" placeholder="内容（不少于 10 个字）"></textarea>
          <p v-if="createError" class="text-red-500 text-sm mt-2">{{ createError }}</p>
          <div class="flex justify-end gap-3 mt-4">
            <button @click="view = 'list'" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">取消</button>
            <button @click="handleCreate" :disabled="creating" class="bg-blue-600 text-white px-6 py-2 rounded-full text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-all">{{ creating ? '发布中...' : '发布' }}</button>
          </div>
        </div>
      </div>
    </main>
    <AppFooter />
  </div>
</template>
