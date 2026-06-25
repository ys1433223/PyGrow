// ==========================================
// auth.js - 全站核心脚本 (V8.0 纯净修复版)
// ==========================================

// 页面加载入口
document.addEventListener("DOMContentLoaded", function() {
    // 1. 环境检测
    if (window.location.protocol === 'file:') {
        console.warn("⚠️ 建议使用 VS Code Live Server 打开，以获得最佳 AI 体验。");
    }

    // 2. 初始化核心模块
    renderHeaderUser();    // 用户头像
    runPageLoader();       // 加载动画
    initThemeSystem();     // 黑夜模式
    
    // 3. 启动 AI 助教 (延时 1 秒，确保页面加载完毕)
    setTimeout(injectCozeAI, 1000);
});

// ==========================================
// 🤖 模块一：Coze AI 助教 (强制显示版)
// ==========================================
function injectCozeAI() {
    // 防止重复注入
    if (document.getElementById('coze-web-sdk')) return;

    console.log("正在启动 Coze AI...");

    // 1. 引入 SDK
    const script = document.createElement('script');
    script.src = "https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.19/libs/cn/index.js";
    script.id = "coze-web-sdk";
    script.defer = true;
    
    script.onload = () => {
        console.log("✅ Coze SDK 就绪，开始初始化...");
        initCozeClient();
    };
    
    script.onerror = () => console.error("❌ Coze SDK 加载失败 (请检查网络)");
    
    document.body.appendChild(script);

    // 2. 强制样式修正 (确保气泡不被遮挡)
    const style = document.createElement('style');
    style.innerHTML = `
        /* 容器定位 */
        div[class^="CozeWebSDK"], .coze-web-chat-app {
            position: fixed !important; 
            bottom: 20px !important; 
            right: 20px !important;
            z-index: 2147483647 !important; /* 强制最顶层 */
            width: 0 !important; 
            height: 0 !important;
            background: transparent !important; 
            overflow: visible !important;
        }
        /* 悬浮球按钮 */
        .coze-trigger-button {
            position: fixed !important; 
            bottom: 30px !important; 
            right: 30px !important;
            width: 50px !important; 
            height: 50px !important; 
            z-index: 2147483647 !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }
        /* 聊天窗口 */
        .coze-web-chat-window {
            position: fixed !important; 
            bottom: 90px !important; 
            right: 30px !important;
            width: 360px !important; 
            height: 600px !important; 
            max-height: 80vh !important;
            z-index: 2147483647 !important;
            border-radius: 12px !important;
        }
    `;
    document.head.appendChild(style);
}

function initCozeClient() {
    try {
        new CozeWebSDK.WebChatClient({
            config: {
                // 你的 Bot ID
                bot_id: '7588874876988669958', 
            },
            componentProps: {
                title: '启航 AI 助教',
            },
            auth: {
                type: 'token',
                // ✅ 这里我已经帮你填好了之前的真实 Token，直接用即可
                token: 'pat_213i5EY9aR90nLZ7SUicMq1Ha2QgPyMPh3Cyrt4rTOcsESO2Sto3c0QfKO8NmApX', 
                onRefreshToken: function () {
                    return 'pat_213i5EY9aR90nLZ7SUicMq1Ha2QgPyMPh3Cyrt4rTOcsESO2Sto3c0QfKO8NmApX';
                }
            }
        });
        console.log("✅ AI 助教初始化成功！");
    } catch (e) {
        console.error("Coze 初始化报错:", e);
    }
}

// ==========================================
// 🌙 模块二：黑夜模式系统
// ==========================================
function initThemeSystem() {
    // 注入 CSS 变量
    const style = document.createElement('style');
    style.innerHTML = `
        body.dark-mode { background-color: #1a202c !important; color: #e2e8f0 !important; }
        body.dark-mode header { background-color: rgba(26, 32, 44, 0.95) !important; border-bottom: 1px solid #2d3748 !important; }
        body.dark-mode .bg-white { background-color: #2d3748 !important; border-color: #4a5568 !important; color: #e2e8f0 !important; }
        body.dark-mode .text-gray-900, body.dark-mode .text-gray-800, body.dark-mode .text-black { color: #f7fafc !important; }
        body.dark-mode .text-gray-600, body.dark-mode .text-gray-500 { color: #a0aec0 !important; }
        body.dark-mode input, body.dark-mode textarea { background-color: #4a5568 !important; border-color: #718096 !important; color: white !important; }
    `;
    document.head.appendChild(style);

    // 读取并应用状态
    const savedTheme = localStorage.getItem('siteTheme');
    const toggleBtn = document.querySelector('theme-button');

    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (toggleBtn) setTimeout(() => toggleBtn.setAttribute('value', 'dark'), 100);
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('change', (e) => {
            if (e.detail === 'dark') {
                document.body.classList.add('dark-mode');
                localStorage.setItem('siteTheme', 'dark');
            } else {
                document.body.classList.remove('dark-mode');
                localStorage.setItem('siteTheme', 'light');
            }
        });
    }
}

// ==========================================
// 👤 模块三：用户鉴权与头部渲染
// ==========================================
function renderHeaderUser() {
    const authArea = document.getElementById('header-auth-area');
    if (!authArea) return;

    const isLogin = localStorage.getItem('isLogin');
    const userInfoStr = localStorage.getItem('userInfo');

    if (isLogin === 'true' && userInfoStr) {
        const user = JSON.parse(userInfoStr);
        const avatar = user.avatar || "https://api.dicebear.com/7.x/avataaars/svg?seed=" + user.name;
        
        authArea.innerHTML = `
            <div class="relative group flex items-center space-x-3 cursor-pointer">
                <div class="flex items-center space-x-2">
                    <img src="${avatar}" class="w-8 h-8 rounded-full border border-gray-200">
                    <span class="text-gray-700 font-bold text-sm hidden md:block">${user.name}</span>
                </div>
                <div class="absolute right-0 top-full pt-2 w-32 hidden group-hover:block z-50">
                    <div class="bg-white rounded-lg shadow-xl border border-gray-100 overflow-hidden">
                        <a href="/profile" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 transition">
                            <i class="fas fa-user mr-2"></i>个人设置
                        </a>
                        <button onclick="handleGlobalLogout()" class="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-red-50 transition">
                            <i class="fas fa-sign-out-alt mr-2"></i>退出
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        authArea.innerHTML = `
            <a href="/login" class="bg-blue-600 text-white px-5 py-2 rounded-full text-sm font-medium hover:bg-blue-700 transition shadow-sm">
                登录 / 注册
            </a>
        `;
    }
}

window.handleGlobalLogout = function() {
    if(confirm("确定要退出登录吗？")) {
        localStorage.removeItem('isLogin');
        localStorage.removeItem('userInfo');
        window.location.href = "/login"; 
    }
};

// ==========================================
// 🚀 模块四：加载动画
// ==========================================
function runPageLoader() {
    const loader = document.getElementById('page-loader');
    const progressBar = document.getElementById('loader-progress');
    const progressText = document.getElementById('loader-text');

    if (!loader) return;

    let progress = 0;
    const timer = setInterval(() => {
        progress += Math.floor(Math.random() * 10) + 2; 
        if (progress > 100) progress = 100;
        
        if (progressBar) progressBar.style.width = progress + '%';
        if (progressText) progressText.innerText = progress + '%';
        
        if (progress >= 100) {
            clearInterval(timer);
            setTimeout(() => {
                loader.style.opacity = '0'; 
                loader.style.pointerEvents = 'none';
                setTimeout(() => { if(loader) loader.remove(); }, 500);
            }, 300);
        }
    }, 50);
}