# PyGrow 后端部署指南

## 最快方式：一键脚本

服务器 CMD 中执行（FTP 根目录下已有）：

```cmd
setup_server.bat
```

自动检查 Python / pip / 依赖 / MySQL / FFmpeg，缺什么装什么。脚本跑完如果全部 OK，直接 `cd backend` 启动。

---

## 服务器环境

| 项目 | 信息 |
|------|------|
| 操作系统 | Windows（phpStudy for Windows） |
| Web 服务器 | Apache（phpStudy 自带） |
| 数据库 | MySQL 5.7.26（root/root，已运行） |
| 网站目录 | `D:\phpstudy_pro\WWW\jyjs2313\`（估计，以 phpStudy 面板显示为准） |
| FTP 目录 | 与 FTP 账号 jyjs2313 对应 |

---

## 零、快速检查总览（一条命令看全貌）

在服务器 CMD 中一次性执行，看看缺什么：

```cmd
echo ===== Python ===== && python --version 2>&1 && pip --version 2>&1 && echo. && echo ===== pip 镜像源 ===== && pip config list 2>&1 && echo. && echo ===== 已安装 Python 包 ===== && pip list 2>&1 | findstr /C:"fastapi" /C:"uvicorn" /C:"sqlalchemy" /C:"aiomysql" /C:"pydantic-settings" /C:"python-jose" /C:"passlib" /C:"python-multipart" /C:"alembic" /C:"httpx" && echo. && echo ===== MySQL ===== && mysql -uroot -proot -e "SHOW DATABASES LIKE 'jyjs2313'; SELECT VERSION();" 2>&1 && echo. && echo ===== FFmpeg ===== && ffmpeg -version 2>&1 | head -1 && echo. && echo ===== 后端代码 ===== && dir backend\app\main.py 2>&1 && dir .env 2>&1 && echo. && echo ===== 端口占用 ===== && netstat -ano 2>&1 | findstr ":8000 :3306 :80 "
```

根据输出，有就跳过，没有就按对应章节安装。

---

## 一、安装 Python

**要求：Python 3.12 或更高版本**（本地开发环境为 3.14.4，服务器推荐 3.12.8 稳定版）。

### 1.0 先检查是否已安装

```cmd
python --version
pip --version
```

- 如果输出 `Python 3.12.x` 或更高 → **已安装，跳过本节**
- 如果输出 `Python 3.11` 或更低 → 需要升级
- 如果提示 `'python' 不是内部或外部命令` → 没装，按下面步骤安装

### 1.1 下载安装

在服务器上打开浏览器，下载 Python 3.12：

```
https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
```

如果服务器方便装更新版本，也可以用 3.13/3.14。

**安装时注意：**
- 勾选 **"Add Python to PATH"**（底部复选框）
- 选择 **"Install Now"** 或自定义安装路径（默认 `C:\Users\管理员\AppData\Local\Programs\Python\Python312`）

### 1.2 验证安装

```cmd
python --version
pip --version
```

预期输出 `Python 3.12.x`（或更高）和 `pip 24.x`。

---

## 二、配置 pip 镜像源（国内服务器必做）

先检查当前镜像源：

```cmd
pip config list
```

如果输出包含 `global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'` → **已配置，跳过本节**。

没配置的话执行：

```cmd
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
```

---

## 三、上传后端代码到服务器

### 方式一：FTP 上传（已经传了）

之前上传的 `dist/` 是前端构建产物。**后端代码还没传**。需要用同样方式把整个 `backend/` 目录上传到服务器。

在本地（你的电脑）打包后端代码：

```bash
cd D:\My_Program\codex\PyGrow
# 删除不需要的目录
rm -rf backend/__pycache__ backend/runtime backend/.env

# 打包
tar -czf backend.tar.gz backend/
```

用 FTP 客户端上传 `backend.tar.gz` 到服务器。

### 方式二：U盘拷贝

把 `D:\My_Program\codex\PyGrow\backend\` 整个目录复制到 U 盘，然后粘贴到服务器上。

### 解压（如果用 tar.gz）

```cmd
tar -xzf backend.tar.gz
```

> 最终后端代码放在服务器某个目录，例如 `D:\web\backend\` 或 `C:\Users\管理员\Desktop\backend\`。

---

## 四、安装 Python 依赖

### 4.0 先检查已安装的包

```cmd
pip list | findstr "fastapi uvicorn sqlalchemy aiomysql pydantic-settings python-jose passlib python-multipart alembic httpx"
```

如果大部分包都列出来了 → **依赖已装，跳过本节**（个别缺失再单独装）。

### 4.1 安装

在服务器 CMD 中，进入后端目录（`requirements.txt` 所在目录），执行：

```cmd
cd D:\web\backend   （改成实际路径）

pip install -r requirements.txt
```

### 依赖清单及说明

| 包名 | 版本 | 用途 |
|------|------|------|
| `fastapi` | 0.115.0 | Web 框架 |
| `uvicorn[standard]` | 0.30.0 | ASGI 服务器，跑 FastAPI |
| `sqlalchemy[asyncio]` | 2.0.35 | 数据库 ORM |
| `aiomysql` | 0.2.0 | MySQL 异步驱动 |
| `pydantic-settings` | 2.5.0 | 读取 .env 配置文件 |
| `python-jose[cryptography]` | 3.3.0 | JWT 鉴权 |
| `passlib[bcrypt]` | 1.7.4 | 密码加密 |
| `python-multipart` | 0.0.12 | 表单/文件上传 |
| `alembic` | 1.13.0 | 数据库迁移 |
| `httpx` | 0.27.0 | HTTP 客户端（调用外部 API） |
| `openai-whisper` | latest | 语音识别（AI 笔记） |
| `yt-dlp` | latest | B站视频下载 |

### 可能遇到的问题

**openai-whisper 安装失败：**

Whisper 依赖 PyTorch（约 2GB），如果服务器磁盘不够或下载慢，可以暂时不装：

```cmd
pip install -r requirements.txt --ignore-installed openai-whisper
```

然后在 `.env` 中把 `ASR_PROVIDER` 改为 `mock`（跳过语音识别功能）。

---

## 五、环境变量配置

### 5.0 检查 .env 是否已配置

```cmd
cd D:\web\backend
type .env
```

如果能看到 `DATABASE_URL=mysql+aiomysql://...` 和 JWT/AI 等配置 → **已配置，跳过本节**。

### 5.1 创建配置

```cmd
copy .env.example .env
```

然后用记事本编辑 `.env`，填入以下内容：

```env
# ============ 数据库（必填）============
DATABASE_URL=mysql+aiomysql://jyjs2313:13131313@127.0.0.1:3306/jyjs2313

# ============ JWT（生产环境请改掉）============
JWT_SECRET=pygrow-production-secret-2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============ AI / LLM ============
AI_API_KEY=sk-你的api-key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL_NAME=deepseek-chat

# ============ AI Chat（宠物助手）============
CHAT_API_KEY=sk-你的api-key
CHAT_BASE_URL=https://cn.happyapi.org
CHAT_MODEL_NAME=gpt-4o-mini

# ============ ASR 语音识别 ============
ASR_PROVIDER=mock

# ============ DeepSeek API ============
DEEPSEEK_API_KEY=sk-你的api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# ============ B站下载 ============
BILIBILI_COOKIE=
```

> **重要：** AI_API_KEY、CHAT_API_KEY、DEEPSEEK_API_KEY 需要填入你自己的 API Key。如果暂时没有，先留空，相关功能会降级或报错但不影响核心功能。

---

## 六、创建 MySQL 数据库

### 6.0 检查数据库是否已存在

先看看 `mysql` 命令能不能用、数据库在不在：

```cmd
# 检查 mysql 命令
where mysql

# 检查数据库是否已存在
mysql -uroot -proot -e "SHOW DATABASES LIKE 'jyjs2313';"
```

- 如果 mysql 命令找不到 → 到 phpStudy 面板添加 MySQL 的 bin 目录到 PATH，或者用 phpMyAdmin 操作
- 如果 `SHOW DATABASES LIKE 'jyjs2313'` 有输出 → **数据库已存在，跳过本节**

### 6.1 创建数据库

```cmd
mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS jyjs2313 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

> 如果 mysql 命令找不到，在 phpStudy 面板 → 环境 → 找到 MySQL 安装路径，或使用 phpMyAdmin。

**PyGrow 启动时会自动创建所有表**（`Base.metadata.create_all` + seed 数据），不需要手动执行 SQL。

---

## 七、启动后端

### 7.1 先测试是否能启动

在 CMD 中进入后端目录，执行：

```cmd
cd D:\web\backend

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

看到以下输出说明成功：

```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

打开浏览器访问 `http://127.0.0.1:8000/docs`，看到 Swagger 文档页就说明启动成功。

按 `Ctrl+C` 停掉。

### 7.2 设置 Windows 开机自启（推荐）

创建一个批处理文件 `start_backend.bat`，内容：

```bat
@echo off
cd /d D:\web\backend
call uvicorn app.main:app --host 127.0.0.1 --port 8000
```

然后用 Windows 任务计划程序设置开机启动：

1. 按 `Win+R`，输入 `taskschd.msc`，回车
2. 右侧 "创建基本任务" → 名称：`PyGrow Backend`
3. 触发器：计算机启动时
4. 操作：启动程序 → 浏览选择 `start_backend.bat`
5. 勾选 "单击完成时打开此任务属性的对话框"
6. 在属性中：勾选 "不管用户是否登录都要运行"，勾选 "使用最高权限运行"

---

## 八、配置 Apache 反向代理

后端在 8000 端口运行，前端在 Apache 的 80 端口。需要让 `/api/*` 请求转发到后端。

### 8.1 启用 Apache 代理模块

在 phpStudy 面板中：

1. 点击 "环境" → 找到 Apache 配置
2. 或者直接编辑 Apache 配置文件

在 Apache 的 `httpd.conf` 中，确保以下行没有被注释（去掉前面的 `#`）：

```apache
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
```

phpStudy 面板中通常可以直接勾选 `proxy_module` 和 `proxy_http_module`。

### 8.2 添加反向代理规则

找到你站点（172.23.11.126）的虚拟主机配置（phpStudy 面板 → 网站 → 点击站点 → 修改 → 伪静态/配置文件）。

在 `<VirtualHost>` 标签内添加：

```apache
# 反向代理：将 /api/ 开头的请求转发到后端
ProxyPass /api/ http://127.0.0.1:8000/api/
ProxyPassReverse /api/ http://127.0.0.1:8000/api/

# WebSocket（CodeRunner 会用到）
ProxyPass /api/code/ws ws://127.0.0.1:8000/api/code/ws
ProxyPassReverse /api/code/ws ws://127.0.0.1:8000/api/code/ws
```

### 8.3 重启 Apache

在 phpStudy 面板中重启 Apache 使配置生效。

验证：浏览器访问 `http://172.23.11.126/api/auth/me`，如果返回 JSON 而不是 404，说明代理成功。

---

## 九、验证部署

全部配置完成后，按以下步骤验证：

1. 确保 MySQL 运行中
2. 确保后端 uvicorn 已启动（`http://127.0.0.1:8000/docs` 可访问）
3. 确保 Apache 已重启
4. 浏览器访问 `http://172.23.11.126/jyjs2313/` 看前端页面
5. 检查 F12 控制台，API 请求应返回正常数据而非 404

---

## 十、快速命令速查

```cmd
# 安装依赖
pip install -r requirements.txt

# 启动后端（前台，用于测试）
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动后端（后台运行，推荐生产用）
uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning

# 查看端口占用
netstat -ano | findstr :8000

# 杀端口
taskkill /PID 进程号 /F

# 测试 API
curl http://127.0.0.1:8000/api/auth/me
```

## 十一、补充：FFmpeg（AI 笔记视频处理）

### 11.0 检查是否已安装

```cmd
ffmpeg -version
```

输出 `ffmpeg version ...` → **已安装，跳过本节**。提示找不到 → 按下面安装。

不需要 AI 笔记的 B站视频下载/音频提取功能的话也可以直接跳过。

### 11.1 安装

1. 下载：https://ffmpeg.org/download.html → Windows → gyan.dev → `ffmpeg-release-essentials.zip`
2. 解压到 `C:\ffmpeg\`
3. 添加 `C:\ffmpeg\bin` 到系统 PATH 环境变量
4. 验证：`ffmpeg -version`
