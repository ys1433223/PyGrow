# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

PyGrow 是一个面向大学本科学生的 AI Python 自主学习平台（"启航教育在线"）。当前为纯前端原型阶段，尚未接入后端和数据库。

## 当前技术栈（现状）

- **前端**: 原生 HTML/CSS/JS + Vue 3 CDN（非构建工具版本）+ Tailwind CSS CDN + Font Awesome CDN
- **鉴权**: 纯前端 localStorage 模拟（`isLogin` + `userInfo`）
- **在线代码运行**: Skulpt（浏览器端 Python 解释器）
- **AI 助教**: Coze Web SDK（Bot ID: `7588874876988669958`）
- **主题切换**: 自定义 Web Component `<theme-button>`（`js/day-night_script.js`）
- **图标**: Lucide Icons (CDN)
- **无构建工具**：所有页面均为纯 HTML，直接通过文件或 Live Server 运行

## 规划技术栈（目标）

前端：Vue3 + Vite + Element Plus  
后端：FastAPI  
数据库：MySQL  
部署：Docker Compose + Nginx  
AI 接口：通过环境变量配置 API_KEY（不写死）

## 关键文件说明

### 核心脚本

| 文件 | 用途 |
|------|------|
| `js/auth.js` | 全站核心脚本：鉴权检查、用户头部渲染、页面加载动画、主题系统初始化、Coze AI 助教注入 |
| `js/day-night_script.js` | 自定义 `<theme-button>` Web Component，白天/黑夜模式切换 |
| `script.js`（根目录） | 登录页的 bobble 角色鼠标跟随动画 |
| `src/script.js` | 与根目录 `script.js` 相同功能的副本 |
| `auth.js`（根目录） | 旧版鉴权脚本，检查 `isLogin` 并踢回登录页 |

### 核心样式

| 文件 | 用途 |
|------|------|
| `css/style.css` | 登录/注册页面的 bobble 角色样式（`@property` 动画 + `:has()` 选择器交互） |
| `style.css`（根目录） | 同上，旧版 |

### 主要页面

| 文件 | 说明 |
|------|------|
| `main.html` | 首页仪表盘，Vue 3 应用，展示课程推荐、讨论区、工具推荐、学习中心入口 |
| `login.html` | 登录页，bobble 动画角色，邮箱/密码表单 |
| `sign_up.html` | 注册页，bobble 动画角色 |
| `clscenter.html` | 课程中心，展示所有课程列表 |
| `course1.html` ~ `course6.html` | 各课程详情页（基础/爬虫/数据分析/AI 等） |
| `practice.html` | 实战练习场，内嵌 Python 代码编辑器 + Skulpt 运行 |
| `comment.html` | 论坛/讨论区 |
| `profile.html` | 个人资料编辑（昵称、头像上传/选择） |
| `Transition.html` | 学习中心 |
| `resources.html` | 资源/工具推荐页 |
| `my_courses.html` | 我的课程/书架 |

### 开发规划文档（`后续开发建议/`）

| 文件 | 内容 |
|------|------|
| `01.md` | 项目总说明：定位、目标用户、核心价值、技术栈、MVP 主流程 |
| `02-功能模块说明.md` | 13 个功能模块的详细设计（首页、用户、测评、课程、练习、在线编程、项目挑战、AI 导师、学习报告、游戏化、社区、后台管理） |
| `03-数据库设计.md` | 16 张 MySQL 表的完整 DDL（users、courses、questions、posts 等） |
| `04-接口设计.md` | 12 个模块的 REST API 设计，统一返回格式 `{code, message, data}` |
| `05-前端页面结构.md` | 页面路由设计和各页面 UI 布局说明 |
| `06-开发任务拆分.md` | 四阶段开发计划：MVP（7 个任务）→ 增强（5 个任务）→ 扩展（4 个任务）→ 未来（3 个任务） |
| `07-开发规则.md` | Claude Code 开发规则：技术栈固定、开发顺序、禁止事项、代码风格要求 |

## 当前鉴权机制

所有"鉴权"均在 localStorage 中模拟：
- `localStorage.setItem('isLogin', 'true')` 表示已登录
- `localStorage.setItem('userInfo', JSON.stringify({name, avatar, loginTime}))` 存储用户信息
- `handleGlobalLogout()` 清除上述两项并跳转登录页
- 访问需要登录的页面时，`js/auth.js` 检查 `isLogin`，未登录则 `alert` 并跳转

## 运行方式

当前无构建步骤，直接用 Live Server 或浏览器打开 `main.html` 即可。推荐 VS Code Live Server 插件。

后续接入 FastAPI 后端和 Vue3+Vite 构建后，运行方式将变更为 `docker-compose up`。

## 开发规则（来自 07-开发规则.md）

1. **不要一次性实现所有功能**，严格按照 MVP → 增强 → 扩展 → 未来的顺序开发
2. **技术栈固定**：Vue3 + Vite + Element Plus / FastAPI / MySQL / Docker Compose + Nginx
3. **每完成一个模块**需保证：代码可运行、前后端通信正常、数据库表结构清晰、无明显报错、给出启动方式
4. **禁止事项**：不一次性生成整个项目、不随意更换技术栈、不删除已有功能、不使用复杂微服务、不一开始就实现扩展功能（编程农场、宠物养成等）、不在代码中写死 AI API Key、不忽略代码运行安全限制
5. **AI Key 必须通过环境变量配置**
6. **代码运行安全**：MVP 阶段 subprocess 需限制 3 秒超时，禁止危险导入和文件操作，预留 Docker 沙箱升级结构
