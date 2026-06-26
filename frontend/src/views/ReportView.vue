<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { reportsApi } from '../api/reports'
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'
import ExpBar from '../components/common/ExpBar.vue'
import RadarChart from '../components/common/RadarChart.vue'
import { courseLevels } from '../data/courseData'

// Build flat course list from courseLevels
function getAllCourses() {
  const courses = []
  for (const level of courseLevels) {
    for (const ch of (level.chapters || [])) {
      courses.push({ id: ch.id || ch.title, title: ch.title, chapterCount: (ch.lessons || []).length })
    }
  }
  return courses
}
const allCourses = getAllCourses()

const router = useRouter()

const summary = ref(null)
const knowledge = ref([])
const radar = ref(null)
const loading = ref(true)

// ---- AI Mentor Modal ----
const aiModalVisible = ref(false)
const aiLoading = ref(false)
const aiContent = ref('')
const aiError = ref('')

const API_BASE = 'https://cn.happyapi.org'
const API_KEY = 'sk-REErmFJXTB26SIsGEmVZJw1f7YtMwiJ2k80XunEdaV3B7ZFZ'

function handleImageError(event) {
  event.currentTarget.classList.add('asset-hidden')
}

function statCards(summaryData) {
  return [
    { label: '完成课程', value: summaryData.completed_courses, icon: 'fas fa-book-open', accent: '#2563eb', soft: '#eaf2ff' },
    { label: '练习总数', value: summaryData.total_practice, icon: 'fas fa-clipboard-check', accent: '#22c55e', soft: '#eafbf1' },
    { label: '正确率', value: `${summaryData.accuracy}%`, icon: 'fas fa-bullseye', accent: '#7c3aed', soft: '#f3e8ff' },
    { label: '错题数', value: summaryData.wrong_count, icon: 'fas fa-triangle-exclamation', accent: '#ef4444', soft: '#fff1f2' },
    { label: '学习中课程', value: summaryData.in_progress_courses, icon: 'fas fa-route', accent: '#6366f1', soft: '#eef2ff' },
    { label: '总经验值', value: summaryData.experience, icon: 'fas fa-bolt', accent: '#f59e0b', soft: '#fff7e6' },
    { label: '总积分', value: summaryData.points, icon: 'fas fa-star', accent: '#14b8a6', soft: '#ecfeff' },
  ]
}

function masteryClass(percent) {
  if (percent < 40) return 'is-low'
  if (percent < 70) return 'is-mid'
  return 'is-high'
}

function suggestionTitle(summaryData) {
  if (summaryData.accuracy >= 80) return '继续冲刺高阶项目'
  if (summaryData.accuracy >= 60) return '用错题巩固薄弱点'
  if (summaryData.completed_courses > 0) return '先把基础练习做扎实'
  return '从能力测评开始规划路径'
}

// ---- AI Analysis ----
function buildCourseList() {
  return allCourses.map(c =>
    `- [${c.id}] ${c.title}（共${c.chapterCount || 0}课时）`
  ).join('\n')
}

function buildWeakPoints() {
  if (!knowledge.value.length) return '暂无数据'
  return knowledge.value
    .filter(k => k.mastery_percent < 60)
    .map(k => `- ${k.knowledge_point}：掌握度 ${k.mastery_percent}%（${k.correct}/${k.total}）`)
    .join('\n') || '无明显薄弱知识点'
}

async function openAiMentor() {
  if (!summary.value) return
  aiModalVisible.value = true
  aiContent.value = ''
  aiError.value = ''
  aiLoading.value = true

  await nextTick()

  const courseList = buildCourseList()
  const weakPoints = buildWeakPoints()

  const systemPrompt = `你是一个专业的Python学习规划导师，名叫"PyGrow AI导师"。你的任务是根据学生的学习数据，给出个性化的学习建议和课程推荐。

回复格式要求（用Markdown）：
1. 先给出学习情况总结（2-3句话，鼓励性语气）
2. 然后给出2-3条具体的学习建议
3. 最后推荐2-3门网站内的课程，说明推荐理由

课程列表如下（只能推荐列表中的课程）：
${courseList}

注意：课程推荐格式为【课程名】，例如"推荐你先学习【Python概述】"。`

  const userPrompt = `请根据以下学习数据给我学习建议：

- 等级：${summary.value.level}
- 总经验值：${summary.value.experience}
- 完成课程数：${summary.value.completed_courses}
- 学习中课程数：${summary.value.in_progress_courses}
- 练习总数：${summary.value.total_practice}
- 正确率：${summary.value.accuracy}%
- 错题数：${summary.value.wrong_count}

薄弱知识点：
${weakPoints}

请帮我分析并给出学习建议和课程推荐。`

  try {
    const resp = await fetch(`${API_BASE}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        max_tokens: 800,
        temperature: 0.7,
      }),
    })

    if (!resp.ok) {
      const errText = await resp.text()
      throw new Error(`API ${resp.status}: ${errText.slice(0, 200)}`)
    }

    const data = await resp.json()
    aiContent.value = data.choices[0].message.content
  } catch (e) {
    console.error('AI mentor error:', e)
    aiError.value = 'AI分析请求失败，请稍后再试。'
    aiContent.value = ''
  } finally {
    aiLoading.value = false
  }
}

function closeAiModal() {
  aiModalVisible.value = false
  aiContent.value = ''
  aiError.value = ''
}

function renderAiContent(text) {
  if (!text) return ''
  // Bold
  let html = text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold text-gray-800">$1</strong>')
    .replace(/\n/g, '<br>')
  // Make 【课程名】clickable — find course by name and link
  html = html.replace(/【(.+?)】/g, (_m, name) => {
    const course = allCourses.find(c => c.title === name)
    if (course) {
      return `<span class="ai-course-link" data-course-id="${course.id}" data-course-title="${course.title}">【${name}】</span>`
    }
    return `【${name}】`
  })
  return html
}

function handleAiContentClick(e) {
  const link = e.target.closest('.ai-course-link')
  if (link) {
    const id = link.dataset.courseId
    if (id) {
      closeAiModal()
      router.push(`/courses/${id}`)
    }
  }
}

onMounted(async () => {
  try {
    const [sRes, kRes, rRes] = await Promise.all([
      reportsApi.getSummary(),
      reportsApi.getKnowledgePoints(),
      reportsApi.getRadarData(),
    ])
    if (sRes.data.code === 200) summary.value = sRes.data.data
    if (kRes.data.code === 200) knowledge.value = kRes.data.data
    if (rRes.data.code === 200) radar.value = rRes.data.data
  } catch (e) {
    console.error('Failed to load report:', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <button @click="$router.push('/learning-center')" class="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mb-3 transition"><i class="fas fa-arrow-left"></i> 返回学习中心</button>
      <div class="report-shell mx-auto">
        <div class="report-hero mb-8">
          <div class="report-hero-copy">
            <span class="section-kicker">学习报告</span>
            <h1>学习报告</h1>
            <p>把等级、经验、练习表现和知识点掌握度整理成一份可行动的成长记录。</p>
          </div>
          <div class="report-hero-visual" aria-hidden="true">
            <div class="visual-fallback"><i class="fas fa-chart-line"></i></div>
            <img src="/images/report/growth-insights.png" alt="" loading="lazy" @error="handleImageError">
          </div>
        </div>

        <div v-if="loading" class="loading-card">
          <div class="animate-spin-slow w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full mx-auto mb-4"></div>
          <p class="text-gray-400">加载中...</p>
        </div>

        <template v-else-if="summary">
          <!-- Level & XP -->
          <div class="level-card mb-6">
            <div class="level-title">
              <span><i class="fas fa-trophy"></i> 当前等级</span>
              <span class="point-pill"><i class="fas fa-star"></i>{{ summary.points }} 积分</span>
            </div>
            <div class="level-body">
              <div class="level-avatar">
                {{ summary.level.charAt(0) }}
              </div>
              <div class="level-progress">
                <ExpBar
                  :experience="summary.current_xp"
                  :next-level-xp="summary.next_level_xp || summary.nextLevelXp || 100"
                  :current-level="summary.level"
                  :major-level="summary.major_level"
                  :progress-percent="summary.progress_percent || summary.progressPercent || 0"
                />
              </div>
            </div>
          </div>

          <!-- Stats grid -->
          <div class="report-stats mb-6">
            <div
              v-for="stat in statCards(summary)"
              :key="stat.label"
              class="report-stat-card"
              :style="{ '--stat-accent': stat.accent, '--stat-soft': stat.soft }"
            >
              <div class="stat-icon"><i :class="stat.icon"></i></div>
              <p class="stat-value">{{ stat.value }}</p>
              <p class="stat-label">{{ stat.label }}</p>
            </div>
          </div>

          <!-- Radar chart -->
          <div v-if="radar && radar.dimensions" class="radar-card mb-6">
            <div class="card-heading">
              <div>
                <span class="section-kicker">Profile</span>
                <h3><i class="fas fa-chart-radar"></i> 学习能力画像</h3>
              </div>
              <span class="knowledge-count">{{ radar.dimensions.length }} 个维度</span>
            </div>
            <RadarChart :dimensions="radar.dimensions" />
            <p class="radar-note" v-if="radar.description">{{ radar.description }}</p>
          </div>

          <!-- Knowledge mastery -->
          <div v-if="knowledge.length > 0" class="knowledge-card mb-6">
            <div class="card-heading">
              <div>
                <span class="section-kicker">Mastery</span>
                <h3><i class="fas fa-chart-bar"></i> 知识点掌握度</h3>
              </div>
              <span class="knowledge-count">{{ knowledge.length }} 个知识点</span>
            </div>
            <div class="knowledge-list">
              <div v-for="kp in knowledge" :key="kp.knowledge_point" class="knowledge-row">
                <div class="knowledge-row-top">
                  <span>{{ kp.knowledge_point }}</span>
                  <strong>{{ kp.correct }}/{{ kp.total }} · {{ kp.mastery_percent }}%</strong>
                </div>
                <div class="mastery-track">
                  <div
                    :class="['mastery-bar', masteryClass(kp.mastery_percent)]"
                    :style="{ width: kp.mastery_percent + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- AI suggestion card (clickable) -->
          <div class="ai-suggestion-card mb-8" @click="openAiMentor">
            <div class="ai-icon"><i class="fas fa-robot"></i></div>
            <div class="flex-1 min-w-0">
              <span class="section-kicker">AI Mentor</span>
              <h3>{{ suggestionTitle(summary) }}</h3>
              <p v-if="summary.accuracy >= 80">
              你的正确率非常优秀！建议挑战更高难度的练习题目，尝试完成项目挑战，进一步提升实战能力。
              </p>
              <p v-else-if="summary.accuracy >= 60">
              基础扎实，继续加油！重点关注错题本中的薄弱知识点，多做专项练习来巩固。
              </p>
              <p v-else-if="summary.completed_courses > 0">
              建议多花时间在基础练习上，特别是错题本中的知识点。每天坚持"每日一练"可以有效提升正确率。
              </p>
              <p v-else>
              欢迎来到 PyGrow！建议先从能力测评开始，了解自己的水平，然后按照推荐课程系统地学习 Python。
              </p>
              <div class="mt-3 flex items-center gap-1 text-xs text-purple-600 font-bold">
                <i class="fas fa-magic"></i> 点击让AI深度分析你的学习数据
              </div>
            </div>
          </div>
        </template>

        <div v-else class="report-empty-card">
          <img src="/images/empty-states/learning-empty.png" alt="" loading="lazy" @error="handleImageError">
          <div class="visual-fallback"><i class="fas fa-chart-pie"></i></div>
          <h3>暂无学习数据</h3>
          <p>先完成课程或练习，报告会自动整理你的成长轨迹。</p>
        </div>
      </div>
    </main>

    <!-- AI Mentor Modal -->
    <Teleport to="body">
      <div v-if="aiModalVisible" class="fixed inset-0 z-[10000] flex items-center justify-center p-4" @click.self="closeAiModal">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col animate-scale-in">
          <!-- Header -->
          <div class="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-500 px-6 py-4 flex items-center justify-between flex-shrink-0">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur">
                <i class="fas fa-robot text-white text-lg"></i>
              </div>
              <div>
                <p class="text-white font-bold text-lg">AI 学习规划导师</p>
                <p class="text-white/70 text-xs">基于你的学习数据，给出个性化学习路径</p>
              </div>
            </div>
            <button @click="closeAiModal" class="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition">
              <i class="fas fa-times text-sm"></i>
            </button>
          </div>

          <!-- Body -->
          <div class="p-6 overflow-y-auto flex-1">
            <!-- Loading -->
            <div v-if="aiLoading" class="flex flex-col items-center justify-center py-16">
              <div class="relative w-20 h-20 mb-6">
                <div class="absolute inset-0 bg-purple-200 rounded-full animate-ping opacity-30"></div>
                <div class="relative w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center">
                  <i class="fas fa-robot text-purple-500 text-3xl"></i>
                </div>
              </div>
              <p class="text-gray-600 font-bold text-lg mb-1">AI 正在分析你的学习数据...</p>
              <p class="text-gray-400 text-sm">综合评估练习正确率、知识点掌握度、课程进度等</p>
              <div class="mt-6 flex gap-1">
                <span class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0s"></span>
                <span class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></span>
                <span class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></span>
              </div>
            </div>

            <!-- Error -->
            <div v-else-if="aiError" class="text-center py-12">
              <div class="w-16 h-16 mx-auto mb-4 bg-red-50 rounded-full flex items-center justify-center">
                <i class="fas fa-exclamation-triangle text-red-400 text-2xl"></i>
              </div>
              <p class="text-gray-700 font-bold mb-2">分析请求失败</p>
              <p class="text-gray-400 text-sm mb-4">{{ aiError }}</p>
              <button @click="openAiMentor" class="px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-bold text-sm hover:shadow-lg transition">
                <i class="fas fa-redo mr-1.5"></i>重新分析
              </button>
            </div>

            <!-- Content -->
            <div v-else-if="aiContent" class="ai-mentor-content prose prose-sm max-w-none" @click="handleAiContentClick" v-html="renderAiContent(aiContent)"></div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between flex-shrink-0">
            <p class="text-xs text-gray-400"><i class="fas fa-shield-alt mr-1"></i>AI建议仅供参考，实际学习请结合自身情况</p>
            <button @click="closeAiModal" class="px-5 py-2 bg-gray-200 text-gray-600 rounded-xl text-sm font-bold hover:bg-gray-300 transition">
              关闭
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <AppFooter />
  </div>
</template>

<style scoped>
.report-shell {
  max-width: 1120px;
}

.section-kicker {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  background: #eaf2ff;
  color: #2563eb;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0;
  padding: 0.35rem 0.75rem;
}

.report-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 500px);
  gap: 2rem;
  align-items: center;
  overflow: hidden;
  border: 1px solid rgba(191, 219, 254, 0.85);
  border-radius: 2.2rem;
  background:
    radial-gradient(circle at 82% 18%, rgba(167, 139, 250, 0.16), transparent 32%),
    linear-gradient(135deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
  box-shadow: 0 22px 55px rgba(37, 99, 235, 0.1);
  padding: clamp(1.5rem, 4vw, 3rem);
}

.report-hero-copy h1 {
  color: #111827;
  font-size: clamp(2.35rem, 5vw, 4rem);
  font-weight: 950;
  margin: 0.9rem 0 0.65rem;
}

.report-hero-copy p {
  max-width: 34rem;
  color: #64748b;
  line-height: 1.8;
}

.report-hero-visual {
  position: relative;
  min-height: 250px;
  overflow: hidden;
  border-radius: 1.6rem;
  background: linear-gradient(145deg, #dbeafe, #f5f3ff);
}

.report-hero-visual img {
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
  font-size: 3rem;
  background: linear-gradient(145deg, #eff6ff, #f5f3ff);
}

.loading-card,
.level-card,
.knowledge-card,
.ai-suggestion-card,
.report-empty-card {
  border: 1px solid #e5e7eb;
  border-radius: 2rem;
  background: #fff;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
}

.loading-card {
  text-align: center;
  padding: 5rem 1.5rem;
}

.level-card {
  padding: 1.5rem;
}

.level-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.level-title > span:first-child {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #1f2937;
  font-weight: 950;
  font-size: 1.1rem;
}

.level-title i {
  color: #f59e0b;
}

.point-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border-radius: 999px;
  background: #fff7e6;
  color: #d97706;
  font-size: 0.82rem;
  font-weight: 850;
  padding: 0.42rem 0.75rem;
}

.level-body {
  display: flex;
  align-items: center;
  gap: 1.2rem;
}

.level-avatar {
  display: grid;
  place-items: center;
  width: 4.4rem;
  height: 4.4rem;
  flex: 0 0 auto;
  border-radius: 1.45rem;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 1.55rem;
  font-weight: 950;
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.24);
}

.level-progress {
  flex: 1;
  min-width: 0;
}

.report-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.report-stat-card {
  position: relative;
  overflow: hidden;
  min-height: 150px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 1.45rem;
  background:
    radial-gradient(circle at 84% 18%, var(--stat-soft), transparent 38%),
    #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.055);
  padding: 1rem;
}

.stat-icon {
  display: grid;
  place-items: center;
  width: 2.9rem;
  height: 2.9rem;
  border-radius: 1rem;
  background: var(--stat-soft);
  color: var(--stat-accent);
  margin-bottom: 0.85rem;
}

.stat-value {
  color: var(--stat-accent);
  font-size: clamp(1.65rem, 3vw, 2.1rem);
  font-weight: 950;
  line-height: 1;
}

.stat-label {
  color: #64748b;
  font-size: 0.8rem;
  font-weight: 750;
  margin-top: 0.42rem;
}

.knowledge-card {
  padding: clamp(1.25rem, 3vw, 1.75rem);
}

.card-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.card-heading h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 950;
  margin-top: 0.7rem;
}

.card-heading h3 i {
  color: #2563eb;
}

.knowledge-count {
  flex: 0 0 auto;
  border-radius: 999px;
  background: #f8fafc;
  color: #64748b;
  font-size: 0.82rem;
  font-weight: 800;
  padding: 0.45rem 0.7rem;
}

.knowledge-list {
  display: grid;
  gap: 1rem;
}

.knowledge-row {
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  background: #f8fafc;
  padding: 0.95rem;
}

.knowledge-row-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.7rem;
}

.knowledge-row-top span {
  color: #334155;
  font-size: 0.92rem;
  font-weight: 850;
}

.knowledge-row-top strong {
  color: #94a3b8;
  font-size: 0.78rem;
}

.mastery-track {
  overflow: hidden;
  height: 0.65rem;
  border-radius: 999px;
  background: #e5e7eb;
}

.mastery-bar {
  height: 100%;
  border-radius: 999px;
  transition: width 0.7s ease;
}

.mastery-bar.is-low {
  background: linear-gradient(90deg, #fb7185, #ef4444);
}

.mastery-bar.is-mid {
  background: linear-gradient(90deg, #fbbf24, #f59e0b);
}

.mastery-bar.is-high {
  background: linear-gradient(90deg, #34d399, #22c55e);
}

.ai-suggestion-card {
  display: flex;
  gap: 1.1rem;
  align-items: flex-start;
  background:
    radial-gradient(circle at 88% 16%, rgba(124, 58, 237, 0.12), transparent 35%),
    linear-gradient(135deg, #eff6ff, #fff);
  border-color: #bfdbfe;
  padding: 1.35rem;
  cursor: pointer;
  transition: all 0.25s;
}
.ai-suggestion-card:hover {
  border-color: #a78bfa;
  box-shadow: 0 18px 44px rgba(124, 58, 237, 0.13);
  transform: translateY(-2px);
}

.ai-icon {
  display: grid;
  place-items: center;
  width: 3.6rem;
  height: 3.6rem;
  flex: 0 0 auto;
  border-radius: 1.2rem;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 1.35rem;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.22);
}

.ai-suggestion-card h3 {
  color: #1f2937;
  font-size: 1.2rem;
  font-weight: 950;
  margin: 0.65rem 0 0.35rem;
}

.ai-suggestion-card p {
  color: #64748b;
  font-size: 0.92rem;
  line-height: 1.75;
}

.report-empty-card {
  position: relative;
  overflow: hidden;
  text-align: center;
  padding: 2.4rem 1.5rem;
}

.report-empty-card img {
  position: relative;
  z-index: 2;
  width: min(280px, 72%);
  height: auto;
  margin: 0 auto 1rem;
}

.report-empty-card .visual-fallback {
  position: relative;
  height: 170px;
  border-radius: 1.5rem;
  margin-bottom: 1rem;
}

.report-empty-card img:not(.asset-hidden) + .visual-fallback {
  display: none;
}

.report-empty-card h3 {
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 950;
}

.report-empty-card p {
  color: #64748b;
  margin-top: 0.35rem;
}

/* AI Mentor content */
.ai-mentor-content {
  color: #374151;
  line-height: 1.85;
}
.ai-mentor-content :deep(strong) {
  color: #1f2937;
}
.ai-course-link {
  display: inline-block;
  background: linear-gradient(135deg, #dbeafe, #ede9fe);
  color: #4f46e5;
  padding: 0.15rem 0.6rem;
  border-radius: 0.5rem;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  border: 1px solid #c7d2fe;
  transition: all 0.2s;
}
.ai-course-link:hover {
  background: linear-gradient(135deg, #c7d2fe, #ddd6fe);
  color: #3730a3;
  border-color: #a5b4fc;
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}
.animate-scale-in {
  animation: scale-in 0.25s ease-out;
}

.radar-card {
  border: 1px solid #e5e7eb;
  border-radius: 2rem;
  background: #fff;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
  padding: clamp(1.25rem, 3vw, 1.75rem);
}

.radar-note {
  text-align: center;
  color: #94a3b8;
  font-size: 0.8rem;
  margin-top: 1rem;
  line-height: 1.7;
  padding: 0 1rem;
}

@media (max-width: 980px) {
  .report-hero {
    grid-template-columns: 1fr;
  }

  .report-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .report-hero-visual {
    min-height: 210px;
  }

  .level-body,
  .ai-suggestion-card {
    flex-direction: column;
  }

  .report-stats {
    grid-template-columns: 1fr;
  }
}
</style>
