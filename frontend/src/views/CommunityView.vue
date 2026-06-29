<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import { getPosts, getHotPosts, getPostDetail, createPost, addComment, toggleLike, toggleFavorite, toggleCommentLike } from '../api/community'
import { getXPLeaderboard, getProjectsLeaderboard, getStreakLeaderboard } from '../api/leaderboard'
import { useAuthStore } from '../stores/auth'
import { asset } from '../utils/assets'
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
const SECTION_META = {
  '技术分享区': {
    icon: 'fas fa-code',
    desc: '代码经验、学习笔记',
    accent: '#2563eb',
    soft: '#eaf2ff',
  },
  '问答专区': {
    icon: 'fas fa-circle-question',
    desc: '报错求助、思路讨论',
    accent: '#ef4444',
    soft: '#fff1f2',
  },
  '资源分享': {
    icon: 'fas fa-folder-open',
    desc: '课程资料、工具路线',
    accent: '#22c55e',
    soft: '#eafbf1',
  },
  '我要吐槽': {
    icon: 'fas fa-mug-hot',
    desc: '学习日常、轻松交流',
    accent: '#f59e0b',
    soft: '#fff7e6',
  },
}
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
  { key: 'xp', label: '经验排行', short: '经验', unit: 'XP', icon: 'fas fa-star', accent: '#2563eb' },
  { key: 'projects', label: '项目完成', short: '项目', unit: '个', icon: 'fas fa-tasks', accent: '#7c3aed' },
  { key: 'streak', label: '学习活跃', short: '活跃', unit: '天', icon: 'fas fa-fire', accent: '#f59e0b' },
]
const lbTiers = ['全部', '初级', '中级', '高级']
const activeLbDimension = computed(() => lbDimensions.find(d => d.key === lbDimension.value) || lbDimensions[0])

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
const showCodeInput = ref(false)
const codeLanguage = ref('python')
const codeContent = ref('')

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

function getSectionMeta(section) {
  return SECTION_META[section] || SECTION_META['问答专区']
}

function getRankClass(rank) {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return 'rank-normal'
}

function getHonorMeta(honor) {
  if (!honor) return null
  const t = HONOR_TITLES.findLast(h => honor.level >= h.min)
  if (!t) return null
  const map = {
    '冒泡新星': { icon: 'fa-seedling', cls: 'honor-new' },
    '点赞收割机': { icon: 'fa-heart', cls: 'honor-like' },
    '话题制造者': { icon: 'fa-comments', cls: 'honor-topic' },
    '镇站之宝': { icon: 'fa-crown', cls: 'honor-treasure' },
  }
  return { name: honor.name || t.name, ...(map[t.name] || map['冒泡新星']) }
}

function handleImageError(event) {
  event.currentTarget.classList.add('asset-hidden')
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
  const title = newTitle.value.trim()
  const content = newContent.value.trim()
  if (title.length < 2) { createError.value = '标题至少 2 个字'; return }
  if (content.length < 10) { createError.value = '内容不少于 10 个字'; return }
  // 检查单一字符重复刷屏（如 "啊啊啊啊啊啊啊啊啊"）
  if (content.length >= 8 && new Set(content).size <= 2) {
    createError.value = '请认真填写内容，不要重复刷屏'; return
  }
  // 检查有效文字占比
  const meaningful = (content.match(/[一-鿿＀-￯a-zA-Z0-9]/g) || []).length
  if (meaningful < 5) {
    createError.value = '有效文字不足，请补充具体的描述或问题'; return
  }
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

function insertCodeBlock() {
  showCodeInput.value = true
  codeLanguage.value = 'python'
  codeContent.value = ''
}

function confirmInsertCode() {
  const lang = codeLanguage.value.trim() || 'plaintext'
  const code = codeContent.value.trim() || '在此编写代码...'
  const codeBlock = '\n```' + lang + '\n' + code + '\n```\n'
  newContent.value += codeBlock
  showCodeInput.value = false
  codeContent.value = ''
}

function copyCodeBlock(event) {
  const btn = event.currentTarget
  const pre = btn.closest('.code-block-wrapper').querySelector('pre')
  const text = pre.textContent
  navigator.clipboard.writeText(text).then(() => {
    btn.innerHTML = '<i class="fas fa-check"></i> 已复制'
    btn.classList.add('text-green-600')
    setTimeout(() => {
      btn.innerHTML = '<i class="far fa-copy"></i> 复制'
      btn.classList.remove('text-green-600')
    }, 2000)
  }).catch(() => {})
}

const parsedContent = computed(() => {
  if (!currentPost.value?.content) return []
  const text = currentPost.value.content
  const segments = []
  const regex = /```(\w*)\n([\s\S]*?)```/g
  let lastIndex = 0
  let match
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    segments.push({ type: 'code', lang: match[1] || 'plaintext', content: match[2].replace(/\n$/, '') })
    lastIndex = regex.lastIndex
  }
  if (lastIndex < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIndex) })
  }
  return segments.length > 0 ? segments : [{ type: 'text', content: text }]
})

const previewContent = computed(() => {
  if (!newContent.value) return []
  const text = newContent.value
  const segments = []
  const regex = /```(\w*)\n([\s\S]*?)```/g
  let lastIndex = 0
  let match
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    segments.push({ type: 'code', lang: match[1] || 'plaintext', content: match[2].replace(/\n$/, '') })
    lastIndex = regex.lastIndex
  }
  if (lastIndex < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIndex) })
  }
  return segments.length > 0 ? segments : [{ type: 'text', content: text }]
})

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
      <div v-if="view !== 'detail'" class="community-hero mb-6">
        <div class="community-hero-copy">
          <span class="section-kicker">学习社区</span>
          <h1>
            <span v-if="view !== 'list'" class="cursor-pointer hover:text-blue-600 transition" @click="backToList">学习社区</span>
            <span v-else>学习社区</span>
          </h1>
          <p v-if="view === 'list'">交流学习心得，分享编程经验，把每个 Python 问题都变成下一次进步。</p>
          <p v-else>写下你的问题、笔记或项目心得，让同学们一起参与讨论。</p>
          <div class="hero-stats" v-if="view === 'list'">
            <span><i class="fas fa-layer-group"></i>{{ sections.length }} 个分区</span>
            <span><i class="fas fa-fire"></i>{{ hotPosts.length || 0 }} 条热门</span>
            <span><i class="fas fa-trophy"></i>{{ leaderboard.length || 0 }} 位上榜</span>
          </div>
        </div>
        <div class="community-hero-visual" aria-hidden="true">
          <div class="visual-fallback"><i class="fas fa-comments"></i></div>
          <img :src="asset('/images/community/community-hero.png')" alt="" loading="lazy" @error="handleImageError">
        </div>
        <button v-if="view === 'list'" @click="view = 'create'" class="publish-button">
          <i class="fas fa-pen mr-1.5"></i>发布帖子
        </button>
      </div>

      <!-- ====== List View: 3-column layout ====== -->
      <div v-if="view === 'list'" class="flex gap-5">
        <!-- LEFT: Leaderboard sidebar -->
        <aside class="hidden lg:block w-60 flex-shrink-0">
          <div class="leaderboard-card sticky top-20">
            <div class="leaderboard-visual" aria-hidden="true">
              <div class="visual-fallback"><i class="fas fa-trophy"></i></div>
              <img :src="asset('/images/community/leaderboard-podium.png')" alt="" loading="lazy" @error="handleImageError">
            </div>
            <div class="leaderboard-heading">
              <div>
                <span class="section-kicker">排行榜</span>
                <h3><i class="fas fa-trophy"></i>排行榜</h3>
              </div>
              <span class="lb-unit">{{ activeLbDimension.unit }}</span>
            </div>

            <!-- Tier switcher -->
            <div class="tier-switcher">
              <button v-for="t in lbTiers" :key="t" @click="switchLbTier(t)"
                :class="{ active: (t === '全部' ? !lbTier : lbTier === t) }"
                type="button">{{ t }}</button>
            </div>

            <!-- Dimension tabs -->
            <div class="lb-dimensions">
              <button v-for="d in lbDimensions" :key="d.key" @click="switchLbDim(d.key)"
                :class="{ active: lbDimension === d.key }"
                :style="{ '--lb-accent': d.accent }"
                type="button">
                <i :class="d.icon"></i><span>{{ d.short }}</span>
              </button>
            </div>

            <!-- Rank list -->
            <div v-if="leaderboard.length === 0" class="leaderboard-empty">暂无数据</div>
            <div v-else class="rank-list">
              <div v-for="item in leaderboard.slice(0, 10)" :key="item.user_id"
                class="rank-row"
                :class="getRankClass(item.rank)">
                <span class="rank-medal">{{ item.rank }}</span>
                <div class="rank-user">
                  <span class="rank-name">{{ item.username }}</span>
                  <span class="rank-level">{{ item.level || '学习者' }}</span>
                </div>
                <span class="rank-value">{{ getLbValue(item) }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- CENTER: Posts -->
        <div class="flex-1 min-w-0">
          <!-- Section tabs -->
          <div class="section-grid mb-4">
            <button
              v-for="s in sections"
              :key="s"
              @click="switchSection(s)"
              :class="{ active: activeSection === s }"
              :style="{ '--section-accent': getSectionMeta(s).accent, '--section-soft': getSectionMeta(s).soft }"
              class="section-card"
              type="button"
            >
              <span class="section-icon"><i :class="getSectionMeta(s).icon"></i></span>
              <span class="section-copy">
                <strong>{{ s }}</strong>
                <small>{{ getSectionMeta(s).desc }}</small>
              </span>
              <i data-lucide="arrow-right" width="15" class="section-arrow"></i>
            </button>
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
              class="post-card">
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
                  <span class="author-dot">{{ (p.user_name || '学').charAt(0) }}</span>
                  <span class="post-author">{{ p.user_name }}</span>
                  <span v-if="getHonorMeta(p.honor_title)" :class="['honor-badge', getHonorMeta(p.honor_title).cls]">
                    <i :class="['fas', getHonorMeta(p.honor_title).icon]"></i>{{ getHonorMeta(p.honor_title).name }}
                  </span>
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
      <div v-if="view === 'detail' && currentPost" class="max-w-5xl mx-auto">
        <button @click="backToList" class="text-sm text-gray-500 hover:text-blue-600 mb-4 flex items-center gap-1 transition-colors">
          <i class="fas fa-arrow-left text-xs"></i> 返回列表
        </button>

        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
          <div class="flex items-center gap-2 mb-4 flex-wrap">
            <span :class="['text-sm px-2 py-0.5 rounded-full', currentPost.category === '问答专区' ? 'bg-red-100 text-red-600' : currentPost.category === '技术分享区' ? 'bg-blue-100 text-blue-600' : currentPost.category === '资源分享' ? 'bg-green-100 text-green-600' : currentPost.category === '我要吐槽' ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-500']">{{ currentPost.category }}</span>
            <span v-if="currentPost.tags" v-for="t in (currentPost.tags || '').split(',').filter(Boolean)" :key="t"
              :class="['text-sm px-1.5 py-0.5 rounded-full', getTagColor(t)]">{{ t }}</span>
            <span class="text-sm text-gray-400">
              {{ currentPost.author_name }}
              <span v-if="getHonorMeta(currentPost.author_honor_title)" :class="['honor-badge ml-1', getHonorMeta(currentPost.author_honor_title).cls]">
                <i :class="['fas', getHonorMeta(currentPost.author_honor_title).icon]"></i>{{ getHonorMeta(currentPost.author_honor_title).name }}
              </span>
              · {{ currentPost.created_at?.slice(0, 10) }}
            </span>
          </div>
          <h2 class="text-2xl font-bold text-gray-800 mb-4">{{ currentPost.title }}</h2>
          <div class="text-base text-gray-700 leading-relaxed">
            <template v-for="(seg, i) in parsedContent" :key="i">
              <p v-if="seg.type === 'text'" class="whitespace-pre-wrap mb-3">{{ seg.content }}</p>
              <div v-else class="code-block-wrapper relative bg-gray-900 rounded-xl mb-4 overflow-hidden">
                <div class="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                  <span class="text-xs text-gray-400 font-mono">{{ seg.lang }}</span>
                  <button @click="copyCodeBlock"
                    class="text-xs text-gray-400 hover:text-white transition flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-700">
                    <i class="far fa-copy"></i> 复制
                  </button>
                </div>
                <pre class="p-4 overflow-x-auto"><code class="text-sm text-green-300 font-mono">{{ seg.content }}</code></pre>
              </div>
            </template>
          </div>
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
                  <span v-if="getHonorMeta(c.honor_title)" :class="['honor-badge', getHonorMeta(c.honor_title).cls]">
                    <i :class="['fas', getHonorMeta(c.honor_title).icon]"></i>{{ getHonorMeta(c.honor_title).name }}
                  </span>
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
      <div v-if="view === 'create'" class="max-w-5xl mx-auto">
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 class="text-lg font-bold text-gray-800 mb-4">发布新帖子</h2>

          <!-- Category -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-600 mb-2">选择分区</label>
            <div class="section-grid compact">
              <button
                v-for="s in sections"
                :key="s"
                @click="newCategory = s; newTags = []; showTagPicker = false"
                :class="{ active: newCategory === s }"
                :style="{ '--section-accent': getSectionMeta(s).accent, '--section-soft': getSectionMeta(s).soft }"
                class="section-card"
                type="button"
              >
                <span class="section-icon"><i :class="getSectionMeta(s).icon"></i></span>
                <span class="section-copy">
                  <strong>{{ s }}</strong>
                  <small>{{ getSectionMeta(s).desc }}</small>
                </span>
              </button>
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
          <div class="relative">
            <textarea v-model="newContent" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-400 resize-none" rows="8" placeholder="内容（不少于 10 个字）"></textarea>
            <button @click="insertCodeBlock" type="button"
              class="absolute bottom-2 right-2 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg transition flex items-center gap-1"
              title="插入代码块">
              <i class="fas fa-code"></i> 插入代码
            </button>
          </div>
          <!-- Code input dialog -->
          <div v-if="showCodeInput" class="bg-gray-50 rounded-xl p-4 mb-4 border border-gray-200">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-bold text-gray-700">插入代码块</span>
              <button @click="showCodeInput = false" class="text-gray-400 hover:text-gray-600"><i class="fas fa-times"></i></button>
            </div>
            <div class="flex items-center gap-2 mb-2">
              <label class="text-xs text-gray-500">语言:</label>
              <select v-model="codeLanguage" class="text-xs border border-gray-200 rounded px-2 py-1 bg-white">
                <option value="python">Python</option>
                <option value="html">HTML</option>
                <option value="css">CSS</option>
                <option value="javascript">JavaScript</option>
                <option value="sql">SQL</option>
                <option value="bash">Bash</option>
                <option value="plaintext">纯文本</option>
              </select>
            </div>
            <textarea v-model="codeContent" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono outline-none focus:border-blue-400 resize-none bg-white" rows="5" placeholder="在此粘贴代码..."></textarea>
            <div class="flex justify-end gap-2 mt-2">
              <button @click="showCodeInput = false" class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700">取消</button>
              <button @click="confirmInsertCode" class="px-4 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">插入代码</button>
            </div>
          </div>
          <!-- Live preview -->
          <div v-if="newContent.trim() && previewContent.some(s => s.type === 'code')" class="bg-white rounded-xl border border-gray-200 p-4 mt-3">
            <p class="text-xs font-bold text-gray-400 mb-2 uppercase tracking-wider"><i class="fas fa-eye mr-1"></i>预览效果</p>
            <div class="text-sm text-gray-700 leading-relaxed">
              <template v-for="(seg, i) in previewContent" :key="i">
                <p v-if="seg.type === 'text'" class="whitespace-pre-wrap mb-2">{{ seg.content }}</p>
                <div v-else class="code-block-wrapper relative bg-gray-900 rounded-lg mb-2 overflow-hidden">
                  <div class="flex items-center justify-between px-3 py-1.5 bg-gray-800 border-b border-gray-700">
                    <span class="text-xs text-gray-400 font-mono">{{ seg.lang }}</span>
                  </div>
                  <pre class="p-3 overflow-x-auto"><code class="text-xs text-green-300 font-mono">{{ seg.content }}</code></pre>
                </div>
              </template>
            </div>
          </div>
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

<style scoped>
.section-kicker {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  background: #eaf2ff;
  color: #2563eb;
  font-size: 0.72rem;
  font-weight: 850;
  letter-spacing: 0;
  padding: 0.32rem 0.68rem;
}

.community-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 440px);
  gap: 1.6rem;
  align-items: center;
  overflow: hidden;
  border: 1px solid rgba(191, 219, 254, 0.85);
  border-radius: 2rem;
  background:
    radial-gradient(circle at 82% 18%, rgba(167, 139, 250, 0.16), transparent 32%),
    linear-gradient(135deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
  box-shadow: 0 22px 55px rgba(37, 99, 235, 0.1);
  padding: clamp(1.35rem, 3vw, 2.5rem);
}

.community-hero-copy h1 {
  color: #111827;
  font-size: clamp(2.15rem, 4vw, 3.35rem);
  font-weight: 950;
  margin: 0.75rem 0 0.45rem;
}

.community-hero-copy p {
  max-width: 34rem;
  color: #64748b;
  line-height: 1.75;
  padding-right: 6rem;
}

.hero-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 1.2rem;
}

.hero-stats span {
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: #475569;
  font-size: 0.82rem;
  font-weight: 750;
  padding: 0.52rem 0.78rem;
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.65);
}

.community-hero-visual {
  position: relative;
  min-height: 190px;
  overflow: hidden;
  border-radius: 1.45rem;
  background: linear-gradient(145deg, #dbeafe, #f5f3ff);
}

.community-hero-visual img,
.leaderboard-visual img {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.asset-hidden {
  display: none !important;
}

.visual-fallback {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: grid;
  place-items: center;
  color: #2563eb;
  font-size: 2.4rem;
  background: linear-gradient(145deg, #eff6ff, #f5f3ff);
}

.publish-button {
  position: absolute;
  right: 1.5rem;
  top: 1.5rem;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 850;
  padding: 0.72rem 1.05rem;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.22);
  transition: transform 0.22s ease, background 0.22s ease;
  z-index: 4;
}

.publish-button:hover {
  transform: translateY(-2px);
  background: #1d4ed8;
}

.leaderboard-card {
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 1.6rem;
  background: #fff;
  box-shadow: 0 16px 38px rgba(15, 23, 42, 0.07);
  padding: 0.85rem;
}

.leaderboard-visual {
  position: relative;
  height: 112px;
  overflow: hidden;
  border-radius: 1.1rem;
  background: linear-gradient(145deg, #dbeafe, #fef3c7);
  margin-bottom: 0.85rem;
}

.leaderboard-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.leaderboard-heading h3 {
  display: flex;
  align-items: center;
  gap: 0.42rem;
  color: #1f2937;
  font-size: 1rem;
  font-weight: 950;
  margin-top: 0.5rem;
}

.leaderboard-heading h3 i {
  color: #f59e0b;
}

.lb-unit {
  flex: 0 0 auto;
  border-radius: 999px;
  background: #fff7e6;
  color: #d97706;
  font-size: 0.72rem;
  font-weight: 850;
  padding: 0.35rem 0.55rem;
}

.tier-switcher,
.lb-dimensions {
  display: grid;
  gap: 0.35rem;
  border-radius: 1rem;
  background: #f1f5f9;
  padding: 0.25rem;
  margin-bottom: 0.65rem;
}

.tier-switcher {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.lb-dimensions {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.tier-switcher button,
.lb-dimensions button {
  border-radius: 0.78rem;
  color: #64748b;
  font-size: 0.68rem;
  font-weight: 850;
  padding: 0.45rem 0.2rem;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.tier-switcher button.active {
  background: #fff;
  color: #1f2937;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

.lb-dimensions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.lb-dimensions button.active {
  background: #fff;
  color: var(--lb-accent);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

.leaderboard-empty {
  border-radius: 1rem;
  background: #f8fafc;
  color: #94a3b8;
  font-size: 0.78rem;
  text-align: center;
  padding: 1.4rem 0.5rem;
}

.rank-list {
  display: grid;
  gap: 0.38rem;
}

.rank-row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  border: 1px solid transparent;
  border-radius: 1rem;
  padding: 0.55rem;
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.rank-row:hover {
  transform: translateX(2px);
  background: #f8fafc;
  border-color: #e5e7eb;
}

.rank-medal {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  color: #64748b;
  background: #f1f5f9;
  font-size: 0.72rem;
  font-weight: 950;
}

.rank-gold .rank-medal {
  color: #92400e;
  background: linear-gradient(135deg, #fde68a, #f59e0b);
}

.rank-silver .rank-medal {
  color: #475569;
  background: linear-gradient(135deg, #f8fafc, #cbd5e1);
}

.rank-bronze .rank-medal {
  color: #9a3412;
  background: linear-gradient(135deg, #fed7aa, #fb923c);
}

.rank-user {
  min-width: 0;
  flex: 1;
}

.rank-name {
  display: block;
  overflow: hidden;
  color: #334155;
  font-size: 0.8rem;
  font-weight: 850;
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-level {
  color: #94a3b8;
  font-size: 0.66rem;
}

.rank-value {
  flex: 0 0 auto;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 900;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
}

.section-grid.compact {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.section-card {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 76px;
  gap: 0.72rem;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 1.25rem;
  background:
    radial-gradient(circle at 86% 16%, var(--section-soft), transparent 34%),
    #fff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
  padding: 0.85rem;
  text-align: left;
  transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
}

.section-card:hover,
.section-card.active {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--section-accent) 34%, #dbeafe);
  box-shadow: 0 18px 38px rgba(37, 99, 235, 0.1);
}

.section-card.active {
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--section-accent) 10%, #fff), #fff),
    #fff;
}

.section-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.95rem;
  background: var(--section-soft);
  color: var(--section-accent);
  font-size: 1rem;
}

.section-copy {
  min-width: 0;
}

.section-copy strong {
  display: block;
  color: #1f2937;
  font-size: 0.9rem;
  font-weight: 950;
}

.section-copy small {
  display: block;
  overflow: hidden;
  color: #64748b;
  font-size: 0.68rem;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-arrow {
  position: absolute;
  right: 0.72rem;
  top: 0.72rem;
  color: var(--section-accent);
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.section-card:hover .section-arrow,
.section-card.active .section-arrow {
  opacity: 1;
  transform: translateX(0);
}

.post-card {
  cursor: pointer;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 1.25rem;
  background: #fff;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.055);
  padding: 1.25rem;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.post-card:hover {
  transform: translateY(-3px);
  border-color: #bfdbfe;
  box-shadow: 0 18px 42px rgba(37, 99, 235, 0.1);
}

.author-dot {
  display: grid;
  place-items: center;
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 0.52rem;
  background: linear-gradient(135deg, #60a5fa, #a78bfa);
  color: #fff;
  font-size: 0.68rem;
  font-weight: 950;
}

.post-author {
  color: #475569;
  font-weight: 800;
}

.honor-badge {
  display: inline-flex;
  align-items: center;
  max-width: 10rem;
  gap: 0.28rem;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 950;
  line-height: 1;
  padding: 0.26rem 0.5rem;
  vertical-align: middle;
  white-space: nowrap;
}

.honor-badge i {
  font-size: 0.62rem;
}

.honor-new {
  color: #475569;
  border-color: #cbd5e1;
  background: #f8fafc;
}

.honor-like {
  color: #2563eb;
  border-color: #bfdbfe;
  background: #eff6ff;
}

.honor-topic {
  color: #7c3aed;
  border-color: #ddd6fe;
  background: #f5f3ff;
}

.honor-treasure {
  color: #b45309;
  border-color: #fde68a;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  box-shadow: 0 8px 18px rgba(245, 158, 11, 0.12);
}

@media (max-width: 1180px) {
  .section-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .community-hero {
    grid-template-columns: 1fr;
  }

  .community-hero-copy p {
    padding-right: 0;
  }

  .publish-button {
    position: static;
    width: fit-content;
  }
}

@media (max-width: 640px) {
  .section-grid,
  .section-grid.compact {
    grid-template-columns: 1fr;
  }

  .community-hero-visual {
    min-height: 170px;
  }
}
</style>
