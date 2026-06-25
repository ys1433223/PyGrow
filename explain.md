# PyGrow 资源配置说明

本文件说明项目中所有可修改的资源配置位置和方式。

---

## 1. 环境变量（`.env` / 系统环境变量）

配置文件：`backend/app/config.py`  
模板文件：`.env.example`

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///pygrow.db` | 数据库连接。生产环境改为 MySQL，如 `mysql+aiomysql://root:密码@db:3306/pygrow` |
| `JWT_SECRET` | `change-me-in-production` | JWT 签名密钥，生产环境必须更换为随机字符串 |
| `LLM_API_KEY` | （空） | AI 导师使用的 API Key（OpenAI 或其他兼容 API） |
| `LLM_API_BASE` | `https://api.openai.com/v1` | AI 接口地址，可换成国内代理或其他兼容服务 |
| `LLM_MODEL` | `gpt-3.5-turbo` | 使用的模型名称，可换成 `gpt-4o`、`deepseek-chat` 等 |
| `COZE_BOT_ID` | （空） | Coze AI 助教 Bot ID（前端聊天窗使用） |
| `COZE_TOKEN` | （空） | Coze 平台访问令牌 |

**修改方式：** 复制 `.env.example` 为 `.env`，填写实际值。

---

## 2. 课程资源（视频、课程结构）

配置文件：`backend/app/seed.py` → `COURSES_DATA`

| 字段 | 说明 |
|------|------|
| `title` | 课程名称 |
| `description` | 课程简介 |
| `category` | 课程分类（Basic / Spider / Data / Web / AI） |
| `bvid` | B 站视频 BV 号，如 `BV1WD4y1v7uk` |
| `cover_color` | 课程卡片渐变色（Tailwind CSS 类） |
| `icon` | Font Awesome 图标类名 |
| `lessons` | 课时列表，每项包含：章节名、标题、时长、B 站分 P 页码 |

**修改方式：** 编辑 `COURSES_DATA` 列表，增加/修改/删除课程字典。新部署时通过 `cd backend && python -m app.seed` 写入数据库。

---

## 3. 题库（测评题 + 练习题）

配置文件：`backend/app/seed.py` → `QUESTIONS_DATA` + `PRACTICE_DATA`

每道题结构：

| 字段 | 说明 |
|------|------|
| `title` | 题目标题 |
| `content` | 题目内容 |
| `type` | 题目类型：`single`（单选）/ `multi`（多选，答案逗号分隔）/ `tf`（判断）/ `fill`（填空） |
| `options` | 选项数组，如 `["A", "B", "C", "D"]` |
| `answer` | 正确答案 |
| `analysis` | 答案解析（学生答完后展示） |
| `knowledge_point` | 知识点标签 |
| `difficulty` | 难度：`easy` / `medium` / `hard` |
| `level` | 对应等级：`入门级` / `初级` / `中级` / `高级` |

**修改方式：** 编辑对应列表后重新执行 seed。

---

## 4. 段位 / 经验值系统

配置文件：`backend/app/services/gamification.py`

| 内容 | 说明 |
|------|------|
| `LEVEL_TIERS` | 9 个段位的经验值范围（黑铁 0-199 → 至尊 4500+） |
| `MAJOR_LEVELS` | 大段位与小段位的映射关系（初级/中级/高级） |

**积分规则（分散在各 router 中）：**

| 行为 | 经验值 | 修改位置 |
|------|--------|----------|
| 单题答对 | +3 | `routers/practice.py` L84 |
| 完成测评 | +20 | `routers/assessment.py` L95 |
| 完成课程 | +10 | `routers/courses.py` 进度接口 |
| 每日任务奖励 | 5-20 | `seed.py` → `DAILY_TASKS_DATA` |
| 项目提交 | 50-150 | `seed.py` → `PROJECTS_DATA` |

---

## 5. 徽章系统

配置文件：`backend/app/seed.py` → `BADGES_DATA`

| 字段 | 说明 |
|------|------|
| `name` | 徽章名称 |
| `description` | 徽章描述 |
| `condition_type` | 触发条件类型：`login_first` / `assessment_complete` / `streak_days` / `correct_count` / `course_complete` / `points_total` / `level_reach` / `assessment_perfect` |
| `condition_value` | 触发阈值 |

**修改方式：** 编辑列表增删徽章。徽章自动检测逻辑在 `app/services/gamification.py` 的 `award_badge_if_earned()`。

---

## 6. 每日任务

配置文件：`backend/app/seed.py` → `DAILY_TASKS_DATA`

| 任务类型 | 说明 |
|----------|------|
| `watch_video` | 观看课程视频 |
| `do_practice` | 完成练习题 |
| `run_code` | 运行代码 |
| `daily_checkin` | 学习打卡 |
| `challenge_question` | 挑战题目 |

任务奖励的 `reward_exp` 和 `reward_points` 均在此处配置。

---

## 7. 项目挑战

配置文件：`backend/app/seed.py` → `PROJECTS_DATA`

| 字段 | 说明 |
|------|------|
| `title` / `description` / `content` | 项目名称、简介、详细要求（Markdown） |
| `level` | 项目等级：`入门` / `初级` / `中级` / `高级` |
| `difficulty` | 难度：`easy` / `medium` / `hard` |
| `reward_exp` / `reward_points` | 完成奖励 |
| `icon` / `cover_color` | 图标和卡片渐变色 |

---

## 8. AI 导师

### 后端 LLM 接口

配置文件：通过 `.env` 的 `LLM_API_KEY`、`LLM_API_BASE`、`LLM_MODEL`

接口位于 `backend/app/routers/ai_mentor.py`，调用 OpenAI 兼容格式的 `/chat/completions` 端点。

如需修改系统提示词（角色设定），编辑该文件中的 `SYSTEM_PROMPT` 变量。

### 前端 Coze 聊天窗

Coze Bot ID 配置在 `frontend/src/utils/core.js` L39，可通过环境变量 `VITE_COZE_BOT_ID` 覆盖。

---

## 9. 代码运行沙箱

配置文件：`backend/app/routers/code_runner.py`

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `TIMEOUT_SECONDS` | 5 | 单次执行超时（秒） |
| `MAX_CODE_LENGTH` | 5000 | 最大代码字符数 |
| `FORBIDDEN_IMPORTS` | os, subprocess, sys, ... | 禁止导入的模块 |
| `FORBIDDEN_FUNCS` | exec, eval, compile, ... | 禁止使用的函数 |

---

## 10. 前端配置

### API 代理地址

开发代理：`frontend/vite.config.js` 中 `proxy: { '/api': 'http://localhost:8000' }`

生产环境由 Nginx 反向代理，配置在 `nginx/nginx.conf`。

### 主题 / 暗色模式

主题切换组件：`frontend/src/utils/day-night_script.js`  
主题系统初始化：`frontend/src/utils/core.js` → `initThemeSystem()`  
暗色模式全局样式：`frontend/src/assets/styles/global.css` L25-31

### 首页内容

首页仪表盘数据来自 `GET /api/home/dashboard`（`backend/app/routers/home.py`），展示内容：等级、经验条、今日任务、继续学习、推荐课程。

---

## 11. 数据库

当前使用 SQLite（本地开发）：
- 文件位置：`backend/pygrow.db`（自动生成）
- 表结构由 SQLAlchemy 模型定义，启动时自动创建

切换 MySQL（Docker 部署）：
- `docker-compose up -d` 启动 MySQL 容器
- 后端自动读取 `docker-compose.yml` 中设置的 `DATABASE_URL` 环境变量

重置数据库：删除 `backend/pygrow.db` 后重启后端，seed 数据会自动写入。

---

## 12. Nginx / Docker 部署

- Docker Compose：`docker-compose.yml`（根目录）
- Nginx 配置：`nginx/nginx.conf`
- 后端 Dockerfile：`backend/Dockerfile`

端口映射：
- 前端（Nginx）：`80`
- 后端（FastAPI）：内部 `8000`，由 Nginx 代理
- 数据库（MySQL）：`3307:3306`（宿主机可用 3307 端口连接）

---

## 快速索引

| 想改什么 | 去哪里改 |
|----------|----------|
| 课程/视频 | `backend/app/seed.py` → `COURSES_DATA` |
| 题库 | `backend/app/seed.py` → `QUESTIONS_DATA` / `PRACTICE_DATA` |
| 段位边界 | `backend/app/services/gamification.py` → `LEVEL_TIERS` |
| 徽章 | `backend/app/seed.py` → `BADGES_DATA` |
| 每日任务 | `backend/app/seed.py` → `DAILY_TASKS_DATA` |
| 项目挑战 | `backend/app/seed.py` → `PROJECTS_DATA` |
| AI 对话 | `.env` → `LLM_API_KEY` + `LLM_API_BASE` + `LLM_MODEL` |
| AI 角色设定 | `backend/app/routers/ai_mentor.py` → `SYSTEM_PROMPT` |
| 代码沙箱限制 | `backend/app/routers/code_runner.py` 顶部常量 |
| 积分奖励数值 | 各 router 文件中的 XP 赋值 + seed.py 中的 reward 字段 |
| 前端页面内容 | `frontend/src/views/` 各 `.vue` 文件 |
| 导航栏 | `frontend/src/components/layout/AppHeader.vue` |
| JWT/数据库连接 | `.env` |
| 暗色模式样式 | `frontend/src/assets/styles/global.css` L25-31 |
