// auth.js - 门卫脚本

// 1. 检查有没有“通行证”
const isLogin = localStorage.getItem('isLogin');

// 2. 如果没有登录，直接踢回登录页
if (isLogin !== 'true') {
    alert('您还没有登录，请先登录！');
    // 跳转回登录页 (根据你的文件路径调整)
    window.location.href = 'login.html'; 
}

// 3. (选做) 如果登录了，把页面右上角的“登录”按钮改成“用户名/注销”
// 等页面加载完再执行
window.addEventListener('DOMContentLoaded', () => {
    updateHeaderStatus();
});

function updateHeaderStatus() {
    // 读取用户信息
    const userStr = localStorage.getItem('userInfo');
    if (!userStr) return;
    
    const user = JSON.parse(userStr);
    
    // 找到 Header 里那个原本是 "登录/注册" 的按钮/链接
    // 假设你给那个 a 标签加个 id="loginBtn" 会更方便找，这里我们尝试用内容找
    // 建议你去 Header 代码里给那个登录链接加个 id="headerAuthBtn"
    
    const loginBtn = document.querySelector('a[href="login.html"]');
    
    if (loginBtn) {
        // 把“登录”换成“头像 + 名字 + 退出”
        // 这里直接替换 HTML
        const parent = loginBtn.parentElement;
        parent.innerHTML = `
            <div class="flex items-center space-x-3 cursor-pointer group relative">
                <img src="${user.avatar}" class="w-8 h-8 rounded-full border border-gray-200">
                <span class="text-gray-700 font-bold text-sm">${user.name}</span>
                
                <button onclick="logout()" class="text-xs text-red-500 hover:underline ml-2">退出</button>
            </div>
        `;
    }
}

// 4. 注销函数
function logout() {
    if(confirm("确定要退出登录吗？")) {
        // 撕掉通行证
        localStorage.removeItem('isLogin');
        localStorage.removeItem('userInfo');
        // 刷新页面或跳回首页
        window.location.href = '首页.html';
    }
}