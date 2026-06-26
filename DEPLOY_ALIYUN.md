# PyGrow 阿里云 ECS 部署文档

适用于阿里云 ECS Ubuntu 22.04 服务器，采用 Nginx 托管前端 dist + systemd 托管 uvicorn 后端的方式部署。

---

## 目录

1. [阿里云 ECS 推荐配置](#1-阿里云-ecs-推荐配置)
2. [安全组端口配置](#2-安全组端口配置)
3. [SSH 连接服务器](#3-ssh-连接服务器)
4. [安装系统依赖](#4-安装系统依赖)
5. [上传项目到服务器](#5-上传项目到服务器)
6. [配置后端 .env](#6-配置后端-env)
7. [安装后端依赖并测试](#7-安装后端依赖并测试)
8. [创建 systemd 服务](#8-创建-systemd-服务)
9. [前端构建](#9-前端构建)
10. [Nginx 配置](#10-nginx-配置)
11. [静态资源路径检查](#11-静态资源路径检查)
12. [B站 Cookies 配置](#12-b站-cookies-配置)
13. [AI API Key 配置说明](#13-ai-api-key-配置说明)
14. [部署后验证](#14-部署后验证)
15. [常见报错排查](#15-常见报错排查)
16. [部署检查清单](#16-部署检查清单)

---

## 1. 阿里云 ECS 推荐配置

| 项目 | 推荐配置 | 说明 |
|------|----------|------|
| **实例规格** | 2 vCPU / 4 GB 内存 | Whisper 语音模型需要额外内存 |
| **系统盘** | 40 GB（高效云盘） | 含 Whisper base 模型（~140 MB）、Python 依赖、前端 dist |
| **操作系统** | Ubuntu 22.04 LTS | 项目在此系统上验证 |
| **带宽** | 按量付费 5 Mbps | B站视频下载至少需要 2 Mbps 以上 |

> **Whisper 模型大小参考：** `tiny` ~72 MB / `base` ~140 MB / `small` ~460 MB / `medium` ~1.5 GB。推荐使用 `base`，准确度与速度均衡。

---

## 2. 安全组端口配置

在阿里云 ECS 控制台 → 安全组 → 配置规则中，添加以下入方向规则：

| 端口 | 协议 | 授权对象 | 用途 |
|------|------|----------|------|
| 22 | TCP | 你的办公 IP（或 0.0.0.0/0） | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP（Nginx） |
| 443 | TCP | 0.0.0.0/0 | HTTPS（如配置 SSL） |

> **不要开放 8000 端口**。后端 uvicorn 只监听 127.0.0.1，由 Nginx 反向代理转发，不直接对外暴露。

---

## 3. SSH 连接服务器

```bash
# 获取服务器公网 IP（阿里云控制台 → ECS → 实例详情 → 公网 IP）
# 使用你创建 ECS 时生成的 .pem 密钥文件或 root 密码连接

# 密钥方式
chmod 400 /path/to/your-key.pem
ssh -i /path/to/your-key.pem root@<你的公网IP>

# 密码方式
ssh root@<你的公网IP>
```

**登录后建议创建一个普通用户来运行服务：**

```bash
adduser pygrow
usermod -aG sudo pygrow
su - pygrow
```

---

## 4. 安装系统依赖

### 4.1 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 4.2 安装 Python 3.12

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev -y

# 验证
python3.12 --version
```

### 4.3 安装 Node.js 22

```bash
# 使用 NodeSource 官方源
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install nodejs -y

# 验证
node --version   # 应显示 v22.x.x
npm --version
```

### 4.4 安装 Nginx

```bash
sudo apt install nginx -y

# 启动并设置开机自启
sudo systemctl enable nginx
sudo systemctl start nginx

# 验证
curl http://127.0.0.1
# 应返回 Nginx 默认欢迎页 HTML
```

### 4.5 安装 FFmpeg

```bash
sudo apt install ffmpeg -y

# 验证
ffmpeg -version
```

### 4.6 安装 yt-dlp

```bash
# 使用 apt 安装（推荐，自带依赖）
sudo apt install yt-dlp -y

# 或通过 pip 安装
# python3.12 -m pip install yt-dlp

# 验证
yt-dlp --version
```

### 4.7 安装 Git

```bash
sudo apt install git -y
```

---

## 5. 上传项目到服务器

### 方式一：通过 Git 拉取（推荐）

```bash
# 如果项目已托管在 GitHub/Gitee
cd /opt
sudo git clone <你的仓库地址> pygrow
sudo chown -R pygrow:pygrow /opt/pygrow
```

### 方式二：通过 SCP 上传

在本地 Windows/Mac 终端执行：

```bash
# 将本地项目上传到服务器（替换 IP）
scp -r D:\My_Program\codex\PyGrow root@<公网IP>:/opt/pygrow
```

### 方式三：通过 SFTP 工具

使用 FileZilla、WinSCP 等 SFTP 客户端上传到 `/opt/pygrow`。

**最终目录结构：**

```
/opt/pygrow/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   ├── .env.example
│   ├── .env                  # 手动创建
│   └── bilibili_cookies.txt  # 手动上传
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── nginx/
│   └── nginx.conf            # 参考用
└── docker-compose.yml        # 本次不用
```

---

## 6. 配置后端 .env

```bash
cd /opt/pygrow/backend

# 从模板创建 .env
cp .env.example .env

# 编辑 .env
vim .env
```

**完整的 .env 配置模板（将占位符替换为真实值）：**

```bash
# ── 数据库（必填） ─────────────────────
# SQLite 模式（无需额外安装数据库）：
DATABASE_URL=sqlite+aiosqlite:///pygrow.db

# MySQL 模式（需要 MySQL 服务）：
# DATABASE_URL=mysql+aiomysql://用户名:密码@主机:3306/数据库名

# ── JWT（必填，生产环境务必修改） ──────
JWT_SECRET=随机生成一串长字符串
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ── AI 大模型（必填） ──────────────────
# DeepSeek API（用于 AI 笔记生成、晋级赛出题）
AI_API_KEY=sk-你的-deepseek-key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL_NAME=deepseek-chat

# DeepSeek API（用于练习提示、项目评审、学习推荐）
DEEPSEEK_API_KEY=sk-你的-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# AI 宠物聊天（用于 /api/ai/chat 后端代理）
# 注：前端 PetAssistantChat 是直接调用 API 的，不走后端。
# 但如果前端选择通过后端 /api/ai/chat 代理，需要配置下面三个：
LLM_API_KEY=sk-你的-api-key
LLM_API_BASE=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# ── 语音识别（可选） ──────────────────
# 选项：mock / whisper / aliyun
ASR_PROVIDER=whisper
ASR_WHISPER_MODEL=base

# 阿里云 ASR（仅 ASR_PROVIDER=aliyun 时需要）
ALIYUN_ASR_ACCESS_KEY_ID=你的阿里云AccessKey
ALIYUN_ASR_ACCESS_KEY_SECRET=你的阿里云AccessKeySecret
ALIYUN_ASR_APP_KEY=你的语音交互AppKey

# ── B站 Cookie（视频下载必需） ─────────
# 两种配置方式，任选其一：
# 方式一：直接写 cookie 字符串
BILIBILI_COOKIE=SESSDATA=xxx; bili_jct=xxx; buvid3=xxx
# 方式二：指定 cookie 文件路径（与方式一互斥）
# BILIBILI_COOKIE_FILE=bilibili_cookies.txt
```

> **注意：** `.env.example` 模板中 `LLM_API_KEY`、`LLM_API_BASE`、`LLM_MODEL` 三个字段暂未加入（`ai_mentor.py` 为死代码），如需使用后端 AI 聊天代理需手动添加。`DEEPSEEK_API_KEY` 和 `DEEPSEEK_BASE_URL` 已加入 `.env.example`。

**生成安全的 JWT_SECRET：**

```bash
python3.12 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 7. 安装后端依赖并测试

### 7.1 创建虚拟环境

```bash
cd /opt/pygrow/backend
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### 7.2 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 7.3 初始化数据库

```bash
# seed.py 会创建所有表并插入初始数据（课程、题目、每日任务等）
python -m app.seed
```

预期输出：各表创建和种子数据插入成功的日志。

### 7.4 启动后端测试

```bash
# 前台启动，方便查看日志
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个 SSH 终端，验证：

```bash
# 测试 API
curl http://127.0.0.1:8000/api/courses
# 应返回 JSON：{"code":200,"message":"success","data":[...]}

# 查看 API 文档
# 在本地浏览器访问（需先开放安全组 8000 端口用于临时测试，测试完后关闭）
# http://<公网IP>:8000/docs
```

确认 API 正常后，按 `Ctrl+C` 停止前台进程。

### 7.5 预下载 Whisper 模型（可选）

```bash
cd /opt/pygrow/backend
source venv/bin/activate

# 设置 HuggingFace 镜像（国内加速）
export HF_ENDPOINT=https://hf-mirror.com

# 下载 base 模型（约 140 MB）
python -c "import whisper; whisper.load_model('base')"
```

---

## 8. 创建 systemd 服务

### 8.1 创建服务文件

```bash
sudo vim /etc/systemd/system/pygrow.service
```

写入以下内容：

```ini
[Unit]
Description=PyGrow Backend (Uvicorn)
After=network.target

[Service]
Type=simple
User=pygrow
Group=pygrow
WorkingDirectory=/opt/pygrow/backend
EnvironmentFile=/opt/pygrow/backend/.env
ExecStart=/opt/pygrow/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=pygrow

# 安全加固
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

> **说明：** `--workers 4` 启动 4 个 worker 进程，适合 2 核 4GB 服务器。可酌情调整。
> 生产环境也可以使用 gunicorn：
> `ExecStart=/opt/pygrow/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000`
> （需先 `pip install gunicorn`）

### 8.2 启动服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动
sudo systemctl start pygrow

# 设置开机自启
sudo systemctl enable pygrow

# 查看状态
sudo systemctl status pygrow

# 查看日志
sudo journalctl -u pygrow -f
```

### 8.3 常用管理命令

```bash
sudo systemctl stop pygrow       # 停止
sudo systemctl restart pygrow    # 重启
sudo systemctl status pygrow     # 查看状态
sudo journalctl -u pygrow -n 50  # 最近 50 行日志
sudo journalctl -u pygrow --since "10 min ago"  # 最近 10 分钟日志
```

---

## 9. 前端构建

### 9.1 安装依赖并构建

```bash
cd /opt/pygrow/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

构建产物在 `frontend/dist/` 目录。

### 9.2 部署到 Nginx

```bash
# 将 dist 复制到 Nginx 目录
sudo cp -r /opt/pygrow/frontend/dist/* /var/www/html/

# 或者创建项目专属目录
sudo mkdir -p /var/www/pygrow
sudo cp -r /opt/pygrow/frontend/dist/* /var/www/pygrow/
```

---

## 10. Nginx 配置

### 10.1 创建站点配置

```bash
sudo vim /etc/nginx/sites-available/pygrow
```

写入以下内容：

```nginx
server {
    listen 80;
    server_name <你的域名或公网IP>;

    # 前端根目录
    root /var/www/pygrow;
    index index.html;

    # gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 1000;

    # ── 前端 SPA 路由 ─────────────────
    location / {
        try_files $uri $uri/ /index.html;
    }

    # ── 后端 API 反向代理 ────────────
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置（AI 笔记生成、B站视频下载等耗时操作）
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;

        # 上传大小限制（项目提交可能有代码文件）
        client_max_body_size 10m;
    }

    # ── 后端静态资源代理（legacy 页面、章节资源等） ──
    location /api/resources/ {
        proxy_pass http://127.0.0.1:8000/api/resources/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # ── 前端静态资源缓存 ─────────────
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # ── 宠物 GIF 图片 ───────────────
    location /pets/ {
        alias /var/www/pygrow/pets/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # ── 插图图片 ────────────────────
    location /images/ {
        alias /var/www/pygrow/images/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # ── 字体图标 ────────────────────
    location /fonts/ {
        alias /var/www/pygrow/fonts/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 10.2 启用站点

```bash
# 创建符号链接
sudo ln -sf /etc/nginx/sites-available/pygrow /etc/nginx/sites-enabled/

# 删除默认站点（避免冲突）
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 11. 静态资源路径检查

以下静态资源目录需要确认存在于 `/var/www/pygrow/` 下：

| 路径 | 来源 | 内容 | 注意事项 |
|------|------|------|----------|
| `/pets/default/` | `frontend/public/pets/default/` | 36 个宠物 GIF 动画 | 文件名含中文（如 `坏笑.gif`），确保 Nginx 能正常处理中文路径 |
| `/pets/Scenery/` | `frontend/public/pets/Scenery/` | 8 张明信片风景图 | 文件名含中文（如 `埃及.png`），后端 `pet_service.py` 会读取此目录 |
| `/images/` | `frontend/public/images/` | 插图素材（如 `report/`、`empty-states/` 等）| — |
| `/de-image/` | `frontend/public/de-image/` | 德语相关图片素材 | 如果此目录存在 |
| `/legacy/` | `frontend/public/legacy/` | 旧版 HTML 页面 | 如果存在 |

**拷贝命令：**

```bash
# 确保所有 public 资源都在 dist 中
ls /opt/pygrow/frontend/dist/pets/
ls /opt/pygrow/frontend/dist/images/

# 如果缺失，手动拷贝
cp -r /opt/pygrow/frontend/public/pets /var/www/pygrow/
cp -r /opt/pygrow/frontend/public/images /var/www/pygrow/
```

**明信片图片的后端路径问题：**

后端 `pet_service.py` 中的 `_get_scenery_dir()` 函数通过相对路径 `../../frontend/public/pets/Scenery` 查找明信片图片。在服务器上，这个相对路径会解析到 `/opt/pygrow/frontend/public/pets/Scenery`。

**如果后端通过 systemd 运行（user=pygrow），需要确保这个目录可读：**

```bash
sudo chmod -R 755 /opt/pygrow/frontend/public/pets/
```

但更好的做法是：明信片图片的 URL 返回给前端后，由前端通过 Nginx 的 `/pets/Scenery/` 路径加载，不走后端文件系统。检查后端 `pet_service.py` 第 131 行返回的 URL 是 `/pets/Scenery/<filename>`，这种相对路径会被前端拼接为 `http://<域名>/pets/Scenery/<filename>`，由 Nginx 直接提供静态文件服务，**不经过后端**。

---

## 12. B站 Cookies 配置

AI 视频笔记功能下载 B站视频时，需要有效的 B站 Cookie，否则会报 HTTP 412 错误。

### 12.1 获取 Cookie

1. 在电脑浏览器中登录 [B站](https://www.bilibili.com)
2. 按 `F12` → `Application`（应用程序）→ `Cookies` → `bilibili.com`
3. 获取以下三个关键 Cookie 值：
   - `SESSDATA` — 登录态（约 3-6 个月有效期）
   - `bili_jct` — CSRF token
   - `buvid3` — 设备指纹

### 12.2 配置方式一：直接写入 .env

```bash
BILIBILI_COOKIE=SESSDATA=你的值; bili_jct=你的值; buvid3=你的值
```

### 12.3 配置方式二：使用 Cookie 文件

将 Netscape 格式的 cookie 文件放到 `/opt/pygrow/backend/bilibili_cookies.txt`：

```bash
# 本地生成（如果你有 yt-dlp）
yt-dlp --cookies-from-browser chrome --cookies bilibili_cookies.txt bilibili.com

# 上传到服务器
scp bilibili_cookies.txt root@<公网IP>:/opt/pygrow/backend/
```

然后在 `.env` 中配置：

```bash
BILIBILI_COOKIE_FILE=bilibili_cookies.txt
```

> **注意：** `download_service.py` 中 cookie 文件的查找路径是相对于 `backend/` 目录的。systemd 的 `WorkingDirectory` 已设为 `/opt/pygrow/backend`，所以文件直接放在 backend 目录下即可。

---

## 13. AI API Key 配置说明

### 13.1 所有需要配置的 API Key 汇总

| 环境变量 | 用途 | 对应服务 | 必填 |
|----------|------|----------|------|
| `AI_API_KEY` | AI 笔记生成、晋级赛出题 | `llm_service.py`、`promotion_service.py` | 是 |
| `AI_BASE_URL` | LLM API 地址 | 同上 | 是 |
| `AI_MODEL_NAME` | LLM 模型名称 | 同上 | 是 |
| `DEEPSEEK_API_KEY` | 练习提示、项目评审、学习推荐 | `hint_service.py`、`project_review_service.py`、`recommend_service.py` | 是 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | 同上（统一管理，不再硬编码） | 是 |
| `LLM_API_KEY` | 后端 AI 聊天 `/api/ai/chat` | `ai_mentor.py` | 按需 |
| `LLM_API_BASE` | 聊天 API 地址 | 同上 | 按需 |
| `LLM_MODEL` | 聊天模型名称 | 同上 | 按需 |
| `ALIYUN_ASR_ACCESS_KEY_ID` | 阿里云语音识别 | `speech_service.py` | 仅 `ASR_PROVIDER=aliyun` 时 |
| `ALIYUN_ASR_ACCESS_KEY_SECRET` | 阿里云 ASR 密钥 | 同上 | 同上 |
| `ALIYUN_ASR_APP_KEY` | 阿里云 ASR AppKey | 同上 | 同上 |

### 13.2 前端直接调用的 API（不经过后端）

以下两个前端的 AI 功能是**直接调用外部 API**，不经过后端，它们的 API Key 配置在浏览器端：

| 功能 | 位置 | API 地址 | Key 存储方式 |
|------|------|----------|------------|
| AI 宠物聊天 | `PetAssistantChat.vue` | 默认 `https://cn.happyapi.org` | localStorage `pet_chat_api_config` |
| AI 学习规划导师 | `ReportView.vue` 中的 `openAiMentor()` | 默认 `https://cn.happyapi.org` | 代码中硬编码 |

这两个功能在部署后**不需要额外配置**即可使用（使用默认的 HappyAPI）。如果想换成自己的 API，在宠物聊天的齿轮设置面板中修改即可。

---

## 14. 部署后验证

```bash
# 1. 检查 Nginx 状态
sudo systemctl status nginx

# 2. 检查后端状态
sudo systemctl status pygrow

# 3. 检查后端日志
sudo journalctl -u pygrow -n 20

# 4. 测试 API（服务器本地）
curl http://127.0.0.1:8000/api/courses

# 5. 测试通过 Nginx 代理的 API（服务器本地）
curl http://127.0.0.1/api/courses

# 6. 测试前端页面（服务器本地）
curl -I http://127.0.0.1/

# 7. 浏览器访问
# http://<你的公网IP>
```

**预期结果：**
- 浏览器打开后看到 PyGrow 首页
- 可以正常注册、登录
- 课程中心能看到课程列表
- 能力测评能加载题目并提交
- AI 笔记功能能正常处理（需 B站 Cookie 有效）
- 宠物动画正常显示

---

## 15. 常见报错排查

### 15.1 `sudo systemctl status pygrow` 显示 failed

```bash
# 查看详细错误
sudo journalctl -u pygrow -n 50 --no-pager

# 常见原因：
# 1. .env 文件不存在或路径错误 → 检查 /opt/pygrow/backend/.env
# 2. Python 虚拟环境路径错误 → 检查 /opt/pygrow/backend/venv/
# 3. 端口 8000 被占用 → sudo lsof -i :8000
# 4. 用户权限不足 → 检查 /opt/pygrow/ 目录权限
```

### 15.2 Nginx 502 Bad Gateway

```bash
# 后端没有运行
sudo systemctl status pygrow

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 检查后端是否在监听
sudo ss -tlnp | grep 8000
```

### 15.3 前端页面空白或 404

```bash
# 检查 dist 是否在正确位置
ls /var/www/pygrow/index.html

# 检查 Nginx root 指令
sudo nginx -T | grep "root"

# 重新构建前端
cd /opt/pygrow/frontend && npm run build
sudo cp -r dist/* /var/www/pygrow/
```

### 15.4 API 请求返回 401 或 CORS 错误

```bash
# Nginx 配置中 /api/ 代理路径是否正确
sudo nginx -T | grep -A5 "location /api"

# 检查 proxy_pass 末尾是否有斜杠
# 正确：proxy_pass http://127.0.0.1:8000/api/;
# 末尾不能缺少 /，否则路径拼接错误
```

### 15.5 AI 笔记生成失败 / FFmpeg 报错

```bash
# 确认 FFmpeg 已安装
ffmpeg -version

# 确认 yt-dlp 已安装
yt-dlp --version

# 检查 B站 Cookie 是否过期
# 后端日志中如果有 HTTP Error 412，说明 Cookie 无效
sudo journalctl -u pygrow | grep "412"
```

### 15.6 Whisper 模型下载失败 / 很慢

```bash
# 设置 HuggingFace 镜像加速
sudo mkdir -p /etc/systemd/system/pygrow.service.d
sudo tee /etc/systemd/system/pygrow.service.d/env.conf << 'EOF'
[Service]
Environment="HF_ENDPOINT=https://hf-mirror.com"
EOF
sudo systemctl daemon-reload
sudo systemctl restart pygrow
```

### 15.7 数据库表不存在 / seed 数据缺失

```bash
cd /opt/pygrow/backend
source venv/bin/activate
python -m app.seed
# seed.py 是幂等的——重复运行不会重复插入数据
```

### 15.8 AI 宠物聊天发不出消息

这是前端直连外部 API 的功能，不走后端：
- 检查浏览器控制台是否有网络错误
- 在宠物聊天面板点击齿轮图标 → 检查 API Base URL 和 API Key 是否正确
- 如果用的是默认 HappyAPI，确认 API Key 没有过期

### 15.9 宠物 GIF 图片不显示 / 中文文件名乱码

```bash
# 确认文件存在
ls /var/www/pygrow/pets/default/

# 中文文件名可能在不同系统间传输时损坏
# 使用 rsync 或 tar 打包传输可以保持文件名
# 本地打包：
tar -czf public-assets.tar.gz -C frontend/public pets images
# 上传后解压：
tar -xzf public-assets.tar.gz -C /var/www/pygrow/
```

### 15.10 明信片图片不显示

- 确认 `/var/www/pygrow/pets/Scenery/` 目录存在且包含图片
- 确认 Nginx 配置中有 `/pets/` 的 `location` 块
- 如果后端日志中有 `scenery directory not found` 相关错误，确认 `/opt/pygrow/frontend/public/pets/Scenery/` 目录存在

---

## 16. 部署检查清单

上线前逐项确认：

- [ ] ECS 安全组已开放 80（和 443）端口
- [ ] Python 3.12 已安装
- [ ] Node.js 22 已安装
- [ ] FFmpeg 已安装（`ffmpeg -version`）
- [ ] yt-dlp 已安装（`yt-dlp --version`）
- [ ] `.env` 已创建并填写真实配置
- [ ] `JWT_SECRET` 已修改（非 `change-me-in-production`）
- [ ] `AI_API_KEY` 已配置
- [ ] `DEEPSEEK_API_KEY` 已配置
- [ ] `DEEPSEEK_BASE_URL` 已配置
- [ ] `LLM_API_KEY` 已配置（如使用后端 AI 聊天）
- [ ] `BILIBILI_COOKIE` 或 `BILIBILI_COOKIE_FILE` 已配置
- [ ] `ASR_PROVIDER` 已选择（推荐 `whisper`）
- [ ] 后端依赖已安装（`pip install -r requirements.txt`）
- [ ] 数据库已初始化（`python -m app.seed`）
- [ ] 后端 API 可访问（`curl http://127.0.0.1:8000/api/courses`）
- [ ] systemd 服务已创建并正常运行（`sudo systemctl status pygrow`）
- [ ] 前端已构建（`npm run build`）
- [ ] dist 已复制到 `/var/www/pygrow/`
- [ ] 静态资源（pets/、images/）已就位
- [ ] Nginx 已配置并重载（`sudo nginx -t && sudo systemctl reload nginx`）
- [ ] 浏览器能正常打开网站
- [ ] 注册/登录流程正常
- [ ] 课程列表能加载
- [ ] 宠物动画能显示
- [ ] （可选）Whisper 模型已预下载
- [ ] （可选）SSL 证书已配置（建议使用 `certbot` + Let's Encrypt）

---

## 附录：快速部署脚本

将以下内容保存为 `/opt/pygrow/deploy.sh`，一键完成除 .env 配置外的所有部署步骤：

```bash
#!/bin/bash
set -e

echo "=== PyGrow Deploy Script ==="
PROJECT_DIR="/opt/pygrow"
WEB_DIR="/var/www/pygrow"

cd $PROJECT_DIR

# 后端
echo "[1/6] Installing Python dependencies..."
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "[2/6] Initializing database..."
python -m app.seed

echo "[3/6] Starting backend service..."
sudo cp -f /opt/pygrow/pygrow.service /etc/systemd/system/ 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl enable pygrow
sudo systemctl restart pygrow

# 前端
echo "[4/6] Building frontend..."
cd $PROJECT_DIR/frontend
npm install
npm run build

echo "[5/6] Deploying to Nginx..."
sudo mkdir -p $WEB_DIR
sudo cp -r dist/* $WEB_DIR/
sudo cp -r public/pets $WEB_DIR/ 2>/dev/null || true
sudo cp -r public/images $WEB_DIR/ 2>/dev/null || true

echo "[6/6] Reloading Nginx..."
sudo ln -sf /etc/nginx/sites-available/pygrow /etc/nginx/sites-enabled/ 2>/dev/null || true
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "=== Deployment complete ==="
echo "Visit: http://$(curl -s ifconfig.me)"
```

```bash
chmod +x /opt/pygrow/deploy.sh
./deploy.sh
```
