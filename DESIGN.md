# PyGrow（启航教育在线）— 项目设计风格与功能说明

## 项目定位

面向大学本科学生的 AI Python 自主学习平台。通过课程学习、在线编程、智能练习、游戏化激励和宠物陪伴，打造完整的 Python 学习闭环。

---

## 技术栈（当前实际）

| 层 | 技术 |
|---|------|
| 前端框架 | Vue 3（Composition API + `<script setup>`）+ Vite 构建 |
| UI 样式 | Tailwind CSS（原子类，无 UI 框架依赖） |
| 图标 | Font Awesome 6（CDN） |
| 路由 | Vue Router 4（懒加载） |
| 状态管理 | Pinia |
| HTTP | Axios（`/api` base，JWT Bearer 自动注入） |
| 后端 | FastAPI（Python）+ SQLAlchemy 异步 |
| 数据库 | SQLite（开发）/ MySQL（生产） |
| AI | DeepSeek API（OpenAI 兼容协议）+ 本地 mock fallback |
| 鉴权 | JWT（access_token + localStorage 持久化） |
| 代码运行 | Skulpt（浏览器端 Python 解释器，预留 Docker 沙箱） |

---

## 设计语言

### 色彩系统

| 用途 | 色值 |
|------|------|
| 主色 | `blue-600`（#2563EB） |
| 渐变主色 | `from-blue-500 to-purple-600` |
| 成功 | `green-500` / `green-600` |
| 警告 | `amber-500` / `orange-500` |
| 危险 | `red-500` / `red-600` |
| 宠物/探险 | `amber-400` → `orange-500`（暖色系） |
| 智能推荐 | `indigo-100` / `indigo-600`（AI 主题） |

### 视觉风格

- **卡片化**：所有内容区域使用 `bg-white rounded-2xl shadow-sm border border-gray-100`
- **圆角**：卡片 `rounded-2xl`（16px）、按钮 `rounded-full` / `rounded-xl`、图标容器 `rounded-[1.5rem]`
- **渐变**：header 区常用 `bg-gradient-to-r from-blue-500 to-purple-600`，按钮/标签用渐变色
- **过渡**：全局 `transition-all duration-300`，hover 时 `-translate-y-0.5` 或 `-translate-y-1`
- **阴影**：`shadow-sm` 用于卡片、`shadow-lg` 用于悬浮态、`shadow-md` 用于按钮
- **毛玻璃**：导航栏使用 `bg-white/90 backdrop-blur-md`
- **装饰元素**：卡片右上角大圆形模糊色块（`bg-*-100/40 rounded-bl-full`）
- **背景**：页面底色 `bg-gray-50`

### 字体

- 系统字体栈：`PingFang SC, Microsoft YaHei, system-ui, sans-serif`
- 等宽字体（代码）：`Consolas, Monaco, monospace`
- 标题 `font-bold`，正文 `font-medium` 或默认

### 暗色模式

通过 `<theme-button>` Web Component 切换，`body` 加 `.dark-mode` class，CSS 变量全局覆盖。

---

## 页面路由（22 个视图）

### 公开页面

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | `HomeView` | 首页仪表盘：欢迎区 + 段位经验条 + 今日任务 + 学习中心入口 + 社区热帖 + 快捷功能入口 |
| `/login` | `LoginView` | 登录页 |
| `/register` | `RegisterView` | 注册页 |
| `/courses` | `CourseCenterView` | 课程中心：6 门课程列表 + AI 笔记浮窗 |
| `/learning-center` | `LearningCenterView` | 学习中心：路线图 + 知识点树 + 学习资源 |
| `/resources` | `ResourcesView` | 资源中心：工具推荐 + 学习资料 |

### 需登录页面（`meta.requiresAuth`）

| 路径 | 视图 | 说明 |
|------|------|------|
| `/courses/:id` | `CourseDetailView` | 课程详情：视频播放 + 章节列表 + AI 笔记生成 + 练一练入口 |
| `/assessment` | `AssessmentView` | 能力测评：20 题，逐题作答 |
| `/assessment/result` | `AssessmentResultView` | 测评结果：分数 + 等级 + 薄弱点 + 推荐课程 |
| `/practice` | `PracticeView` | 练习中心：章节练习 + 错题本 + **智能推荐** |
| `/daily-practice` | `DailyPracticeView` | 每日一练：5 题，即时反馈 + AI 提示 |
| `/code-runner` | `CodeRunnerView` | 在线编程：Python 编辑器 + Skulpt 运行 + Web 开发模式 |
| `/projects` | `ProjectCenterView` | 项目挑战：40 个项目 + AI 评审 + 提交 |
| `/community` | `CommunityView` | 学习社区：发帖 + 评论 + 点赞 + 标签筛选 |
| `/profile` | `ProfileView` | 个人中心：资料编辑 + 头像 + 快捷入口（宠物探险/我的图鉴） |
| `/report` | `ReportView` | 学习报告：统计数据 + 知识点掌握度 + AI 建议 |
| `/favorites` | `FavoritesView` | 收藏夹：课程 + 题目 |
| `/adventure` | `AdventureView` | 宠物探险：派宠物探索收集明信片 + 知识纸条 |
| `/profile/collection` | `CollectionView` | 我的图鉴：明信片 + 知识点小纸条 |
| `/ai-mentor` | `AIMentorView` | AI 导师对话（保留，未在导航栏展示） |
| `/admin` | `AdminView` | 后台管理 |
| `/leaderboard` | `LeaderboardView` | 排行榜（保留路由） |

---

## 组件架构

### 布局组件（`components/layout/`）

| 组件 | 说明 |
|------|------|
| `AppHeader.vue` | 全站导航栏：Logo + 6 个导航链接 + 主题切换 + 用户下拉菜单（测评/个人中心/学习报告/退出） |
| `AppFooter.vue` | 全站页脚 |
| `PageLoader.vue` | 页面加载动画 |

### 通用组件（`components/common/`）

| 组件 | 说明 |
|------|------|
| `AssessmentModal.vue` | 能力测评弹窗（首次登录引导） |
| `LoginPromptModal.vue` | 未登录提示弹窗（纸箱休息.gif + 登录按钮） |
| `ExpBar.vue` | 经验值进度条（段位 + 经验 + 晋级入口） |
| `AiHintCard.vue` | AI 提示卡片（可展开，5 种知识类型 × 3 级提示 + 补习卡） |

### 宠物组件（`components/`）

| 组件 | 说明 |
|------|------|
| `PetCompanion.vue` | 宠物主组件：拖拽 + 菜单 + 动画状态机，全局渲染 |
| `PetMenu.vue` | 宠物菜单：AI 对话 + 消息 + 设置 + 探险入口 |
| `PetAssistantChat.vue` | AI 对话面板（OpenAI 兼容 API，多模型，历史记录） |
| `PetMessagePanel.vue` | 系统消息面板 |
| `PetSettingsPanel.vue` | 宠物设置面板 |
| `PetAiNotesTaskPanel.vue` | AI 笔记进度浮窗 |

---

## 功能模块

### 1. 课程系统

- 6 门课程（Python 基础 → 爬虫 → 数据分析 → Django → 机器学习 → PyTorch）
- B 站视频嵌入 + 章节导航
- AI 笔记生成：下载视频 → 提取音频 → 语音转文字 → AI 总结（DeepSeek）
- 课程进度追踪 + 收藏
- 课程详情页"练一练"按钮直达相关章节练习

### 2. 练习系统

- **每日一练**：按知识点顺序推进，每天 5 题，即时反馈
- **章节练习**：三级阶段（初级/中级/高级），章节树展开，知识点子标签筛选，题型/难度过滤
- **错题本**：自动收录错题，按知识点重做
- **智能推荐**（最新升级）：
  - 掌握度分析：按 `knowledge_tag` 聚合正确率/错误次数/AI提示次数/最近练习时间
  - 9 维加权评分排序（薄弱+30 / 最近错题+25 / 未做+25 / 已学章节+15 / 难度匹配+10 / AI提示多+10 / 久未复习+8 / 做对多次-30 / 超出阶段-50）
  - 冷启动（<10 条记录）→ 基础巩固模式
  - 题库不足 → DeepSeek AI 生成新题（保存到 DB，`source='ai_generated'`）
  - AI 失败 → 随机 fallback，不影响使用

### 3. 能力测评

- 新用户引导测评（20 题多选题，覆盖核心知识点）
- 测评结果：段位评级 + 薄弱知识点 + 推荐课程
- 首次登录延迟 800ms 弹窗，动画过渡

### 4. 游戏化系统

- **8 段位**：萌新小白 → 勤学学徒 → 达标选手 → 稳扎玩家 → 进阶干将 → 学科达人 → 专业先锋 → 满级学神
- **经验值**：答题正确 +8、代码题通过 +15、完成课程 +10，每日上限 140
- **晋级赛**：经验满格后解锁，10 题 ≥80% 通过晋级
- **饼干货币**：答对 +1、代码题 +2、每日全对 +3、晋级通过 +8，每日上限 30
- **徽章系统**：首次登录/完成测评/连续 7 天/完成课程/积分达标等

### 5. 宠物陪伴系统

- 全局悬浮宠物，可拖拽，多套 GIF 动画
- 根据学习状态自动切换动画（active/silent/simplified/excellent/happy/thinking/comfort）
- 菜单：AI 对话 + 消息通知 + 宠物设置
- **宠物探险**：派宠物出去探险（消耗饼干），收集明信片和知识纸条
- 探险图鉴：明信片图鉴 + 知识点小纸条，支持筛选和详情查看

### 6. 在线编程

- 浏览器端 Python 运行（Skulpt）
- Web 开发模式（HTML/CSS/JS 实时预览）
- 代码模板 + 运行输出

### 7. 项目挑战

- 40 个分级项目（入门/基础/进阶/挑战）
- 提交代码/文字，DeepSeek AI 自动评审打分
- 反刷分机制（只奖励超过历史最高分的增量）

### 8. 学习社区

- 发帖/评论/点赞
- 标签筛选 + 热门排序
- 首页社区热帖直链

### 9. AI 导师

- 宠物内嵌 AI 对话（OpenAI 兼容 API，多模型切换）
- 对话历史管理（多会话）
- AI 提示系统（5 种知识类型 × 4 级提示深度）

### 10. 学习报告

- 统计概览：学习时长/完成课程/练习正确率/错题数/当前段位
- 知识点掌握度横向条形图
- AI 学习建议

---

## 后端 API 模块（21 个 Router）

| Router | Prefix | 说明 |
|--------|--------|------|
| `auth` | `/api/auth` | 登录/注册/Token |
| `users` | `/api/user` | 用户资料 CRUD |
| `courses` | `/api/courses` | 课程 + 章节 + 进度 |
| `assessment` | `/api/assessment` | 测评题目 + 提交 + 结果 |
| `practice` | `/api/practice` | 每日一练/章节/错题/推荐/晋级赛/AI提示 |
| `gamification` | `/api/gamification` | 段位/经验/徽章/每日任务 |
| `reports` | `/api/report` | 学习报告数据 |
| `home` | `/api/home` | 首页仪表盘聚合数据 |
| `code_runner` | `/api/code` | 代码运行 |
| `ai_mentor` | `/api/ai` | AI 导师对话 |
| `projects` | `/api/projects` | 项目挑战 + AI 评审 |
| `notes` | `/api/notes` | 学习笔记 |
| `community` | `/api/community` | 社区帖子/评论/点赞 |
| `leaderboard` | `/api/leaderboard` | 排行榜 |
| `admin` | `/api/admin` | 后台管理 |
| `reviews` | `/api/reviews` | 课程评价 |
| `favorites` | `/api/favorites` | 收藏夹 |
| `ai_notes` | `/api` | AI 笔记生成任务 |
| `debug` | `/api` | 调试工具 |
| `pet` | `/api/pet` | 宠物探险/饼干/奖励/图鉴 |

统一返回格式：`{ code: 200, message: "...", data: {...} }`

---

## 导航栏结构

```
Logo(启航教育在线) → 首页 | 课程中心 | 在线编程 | 社区 | 学习中心 | 资源中心 | [主题切换] | [用户头像下拉]
```

用户下拉菜单：
```
能力测评 → 个人中心 → 学习报告 → 退出登录
```

（AI 导师已从导航栏移除，功能整合到宠物对话中；项目挑战已从导航栏移除，保留路由可访问）

---

## 关键设计决策

1. **不使用 Element Plus**：全部 UI 用 Tailwind CSS 手写，保持完全控制
2. **宠物是全局入口**：聊天/消息/设置/探险均通过宠物触发，App.vue 级别渲染
3. **题库优先**：练习推荐始终优先从题库抽题，AI 生成只是兜底
4. **Mock fallback**：所有 AI 调用（提示/评分/生成题/笔记）都有本地 mock 降级
5. **双经验系统**：legacy `experience` + 新 `current_exp`/`total_exp`，段位系统基于新字段
6. **每日上限**：经验值每日上限 140、饼干每日上限 30，防止无限制刷分

---

## 启动方式

```bash
# 后端
cd backend
uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev

# 生产
docker-compose up -d
```
