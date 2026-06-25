# PyGrow 部署文档

## 目录

1. [服务器环境要求](#1-服务器环境要求)
2. [本地开发环境](#2-本地开发环境)
3. [Docker Compose 一键部署（推荐）](#3-docker-compose-一键部署)
4. [手动部署](#4-手动部署)
5. [环境变量配置](#5-环境变量配置)
6. [AI 服务配置](#6-ai-服务配置)
7. [常见问题](#7-常见问题)

---

## 1. 服务器环境要求

### 操作系统

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+（推荐 Ubuntu 22.04 LTS）
- 阿里云 ECS 最低配置：2 核 4GB，40GB 系统盘（Whisper 模型需要额外磁盘空间）

### 必须安装的系统组件

| 组件 | 用途 | 安装命令 |
|------|------|----------|
| **FFmpeg** | AI 笔记 — 从视频中提取音频 | `sudo apt install ffmpeg -y` |
| **yt-dlp** | AI 笔记 — 下载 B站视频 | `pip install yt-dlp`（或 `sudo apt install yt-dlp -y`） |
| **Docker** | 容器化部署（推荐方式） | 见下方 Docker 安装步骤 |
| **Docker Compose** | 多容器编排 | `sudo apt install docker-compose-plugin -y` |
| **Python 3.12+** | 后端运行时（仅手动部署需要） | `sudo apt install python3.12 -y` |
| **Node.js 22+** | 前端构建（仅手动部署需要） | 使用 nvm 或官方安装脚本 |
| **Git** | 拉取代码 | `sudo apt install git -y` |

### FFmpeg 安装（必须）

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg -y

# CentOS / RHEL
sudo yum install epel-release -y
sudo yum install ffmpeg -y

# 验证安装
ffmpeg -version
```

> **说明**：AI 视频笔记功能依赖 FFmpeg 提取视频中的音频。未安装 FFmpeg 时，提取音频阶段会报错：`当前环境未安装 FFmpeg，请先安装 FFmpeg`。

### yt-dlp 安装（必须）

```bash
# Ubuntu / Debian（推荐 apt 安装，自带依赖）
sudo apt update && sudo apt install yt-dlp -y

# 或通过 pip 安装（所有平台通用）
pip install yt-dlp

# macOS
brew install yt-dlp

# 验证安装
yt-dlp --version
```

> **说明**：AI 视频笔记功能依赖 yt-dlp 下载 B站课程视频。未安装 yt-dlp 时，下载阶段会报错。

### Docker 安装（Ubuntu 示例）

```bash
# 卸载旧版本
sudo apt remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt update
sudo apt install -y ca-certificates curl gnupg

# 添加 Docker GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 验证
docker --version
docker compose version
```

---

## 2. 本地开发环境

### Windows

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env          # 编辑 .env 填入你的 API Key
python -m uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### macOS

同 Linux，额外需要安装 FFmpeg：
```bash
brew install ffmpeg
```

---

## 3. Docker Compose 一键部署

### 3.1 项目结构

```
PyGrow/
├── backend/
│   ├── Dockerfile            # 后端镜像（含 FFmpeg）
│   └── .env                  # 环境变量（需手动创建）
├── frontend/
│   └── Dockerfile            # 前端镜像
├── nginx/
│   └── nginx.conf            # Nginx 反向代理配置
├── docker-compose.yml        # 编排文件
└── Deployment.md             # 本文档
```

### 3.2 部署步骤

```bash
# 1. 拉取代码
git clone <your-repo-url> /opt/pygrow
cd /opt/pygrow

# 2. 配置环境变量
cp backend/.env.example backend/.env
vim backend/.env   # 填入真实的 API Key、ASR 配置等

# 3. 构建并启动
docker compose build
docker compose up -d

# 4. 查看状态
docker compose ps
docker compose logs -f backend
```

### 3.3 停止和维护

```bash
# 停止
docker compose down

# 更新代码后重新部署
git pull
docker compose build backend
docker compose up -d

# 查看日志
docker compose logs -f --tail=100 backend
```

### 3.4 数据持久化

默认使用 SQLite 数据库，数据文件位于容器内的 `/app/pygrow.db`。如需持久化数据，在 `docker-compose.yml` 中添加 volumes：

```yaml
services:
  backend:
    volumes:
      - ./backend/pygrow.db:/app/pygrow.db
```

如需使用 MySQL，在 `.env` 中修改 `DATABASE_URL` 为 MySQL 连接串：

```bash
DATABASE_URL=mysql+aiomysql://root:password@db:3306/pygrow
```

---

## 4. 手动部署

### 4.1 后端

```bash
# 服务端安装依赖
sudo apt install ffmpeg python3.12 python3.12-venv -y

cd /opt/pygrow/backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env   # 填入真实 Key

# 初始化数据库（首次运行）
python -m app.seed

# 启动（使用 gunicorn + uvicorn workers，生产模式）
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --daemon
```

### 4.2 前端

```bash
cd /opt/pygrow/frontend
npm install
npm run build   # 产出到 dist/ 目录

# 用 Nginx 托管静态文件
sudo cp -r dist/* /usr/share/nginx/html/
```

### 4.3 Nginx 反向代理配置

```nginx
# /etc/nginx/sites-available/pygrow
server {
    listen 80;
    server_name your-domain.com;   # 替换为你的域名或服务器 IP

    # 前端静态文件
    root /usr/share/nginx/html;
    index index.html;

    # SPA 路由 — 所有非文件请求回退到 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/pygrow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5. 环境变量配置

将 `backend/.env.example` 复制为 `backend/.env`，按实际环境填写：

```bash
# ── 必填 ──────────────────────────────

# LLM 大模型（用于 AI 笔记生成）
AI_API_KEY=sk-your-deepseek-key         # DeepSeek API Key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL_NAME=deepseek-chat

# ── 可选 ──────────────────────────────

# 语音识别方案
#   whisper — 本地 Whisper 模型，离线可用，需先下载模型
#   aliyun  — 阿里云智能语音交互，需要配合 OSS 使用
#   mock    — 返回模拟文稿（开发调试用）
ASR_PROVIDER=whisper
ASR_WHISPER_MODEL=base                  # tiny / base / small / medium / large

# 阿里云 ASR（仅 ASR_PROVIDER=aliyun 时需要）
# 注意：阿里云 ASR 要求音频文件上传到 OSS 并提供公网 URL
ALIYUN_ASR_ACCESS_KEY_ID=your_aliyun_key
ALIYUN_ASR_ACCESS_KEY_SECRET=your_aliyun_secret
ALIYUN_ASR_APP_KEY=your_aliyun_app_key

# B站 Cookie（用于下载B站视频，部署到服务器时必填）
# 获取方式：浏览器登录B站 → F12 → Application → Cookies → bilibili.com
# 复制所有 cookie 拼接为一行，仅需 SESSDATA, bili_jct, buvid3 三个即可
BILIBILI_COOKIE=SESSDATA=xxx; bili_jct=xxx; buvid3=xxx

# 数据库
DATABASE_URL=sqlite+aiosqlite:///pygrow.db

# JWT
JWT_SECRET=your-random-secret-string     # 生产环境务必修改
```

---

## 6. AI 服务配置

### 6.1 DeepSeek（大模型笔记生成）

1. 注册 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 获取 API Key
3. 填入 `.env` 的 `AI_API_KEY`

### 6.2 Whisper（语音识别）

模型首次使用时自动下载到 `~/.cache/whisper/`，服务器需要约 2GB 额外磁盘空间（base 模型约 140MB、small 约 460MB、medium 约 1.5GB）。

```bash
# 手动预下载模型（可选，避免首次调用时等待）
cd /opt/pygrow/backend
source venv/bin/activate
python -c "import whisper; whisper.load_model('base')"
```

### 6.3 阿里云智能语音交互（可选）

如果选择 `ASR_PROVIDER=aliyun`：
1. 开通 [智能语音交互服务](https://www.aliyun.com/product/nls)
2. 在控制台创建项目，获取 AppKey
3. 音频文件需先上传到 OSS，生成公网 URL
4. 当前 pipeline 中阿里云为后备方案，未配置则自动回退到 Whisper

### 6.4 B站 Cookie（视频下载必需）

部署到服务器时必须配置，否则下载 B站视频会报 HTTP 412 错误。

**获取 Cookie 步骤**：
1. 在 Chrome/Edge 中登录 [B站](https://www.bilibili.com)
2. 按 F12 → Application → Cookies → `bilibili.com`
3. 复制以下三个关键 cookie 的值：
   - `SESSDATA` — 登录态
   - `bili_jct` — CSRF token
   - `buvid3` — 设备指纹
4. 在 `.env` 中拼成一行：
```bash
BILIBILI_COOKIE=SESSDATA=你的值; bili_jct=你的值; buvid3=你的值
```

> **Cookie 有效期**：`SESSDATA` 通常有效期 3-6 个月。如果下载突然报 412，先检查 Cookie 是否过期。

---

## 7. 常见问题

### Q: 容器启动后报 "ffmpeg: command not found"

确认 Dockerfile 中已包含 `apt-get install ffmpeg`。如果手动部署，在宿主机上运行：
```bash
sudo apt install ffmpeg -y
```

### Q: Whisper 模型下载很慢

模型从 HuggingFace 下载，国内服务器可能较慢。可以设置镜像：
```bash
export HF_ENDPOINT=https://hf-mirror.com
```
或在 Dockerfile 中添加：
```dockerfile
ENV HF_ENDPOINT=https://hf-mirror.com
```

### Q: 下载 B站视频报 HTTP Error 412

B站反爬要求携带登录 Cookie。解决方案：

1. 在 `.env` 中设置 `BILIBILI_COOKIE`（参见 [6.4 B站 Cookie](#64-b站-cookie视频下载必需)）
2. 如果已设置仍报 412，说明 Cookie 已过期，重新获取即可
3. 没有 Cookie 时，pipeline 会跳过下载，使用 mock 文稿生成笔记

### Q: 生成 AI 笔记时提示"视频文件不存在"或下载失败

确认课程在数据库中有正确的 `bvid`（B站 BV 号）和 `bilibili_page`（分P页码）。确认服务器已安装 yt-dlp 和 FFmpeg：

```bash
yt-dlp --version
ffmpeg -version
```

### Q: 如何更换 MySQL 数据库

修改 `.env` 中的 `DATABASE_URL`：
```bash
# SQLite（默认，无需额外配置）
DATABASE_URL=sqlite+aiosqlite:///pygrow.db

# MySQL
DATABASE_URL=mysql+aiomysql://user:password@host:3306/pygrow
```
MySQL 模式下需确保 `docker-compose.yml` 中 `db` 服务已启动。

### Q: HTTP 访问出现 CORS 错误

前端 dev server (`npm run dev`) 已配置代理到 `http://127.0.0.1:8000`。服务端部署时 Nginx 反向代理已处理跨域，无需额外配置。

### Q: 后端无法访问 /docs

检查防火墙是否开放 8000 端口：
```bash
# 阿里云 ECS 需在安全组中放行端口
# 本地测试：
curl http://127.0.0.1:8000/api/courses
```

---

## 部署检查清单

上线前逐项确认：

- [ ] FFmpeg 已安装（`ffmpeg -version`）
- [ ] yt-dlp 已安装（`yt-dlp --version`）
- [ ] `BILIBILI_COOKIE` 已配置（服务器部署必需）
- [ ] `.env` 文件已从 `.env.example` 创建并填写真实配置
- [ ] `AI_API_KEY` 已配置（DeepSeek API Key）
- [ ] `ASR_PROVIDER` 已选择（推荐 `whisper`）
- [ ] `JWT_SECRET` 已修改为随机字符串
- [ ] Nginx 反向代理已配置并重载
- [ ] 防火墙已放行 80/443 端口
- [ ] （可选）Whisper 模型已预下载
- [ ] （可选）MySQL 数据库已替换 SQLite
- [ ] （可选）SSL 证书已配置（推荐 certbot + Let's Encrypt）
