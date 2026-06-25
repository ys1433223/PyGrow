// ==========================================
// Part 1: 原有的视觉动画 (眼球跟随 + 密码显示)
// ==========================================

let follow = true;
const section = document.querySelector("section");
const form = document.querySelector("form");
// 修正了你原来的拼写错误 (passwword -> passwordInput)
const usernameInput = document.querySelector("#username");
const passwordInput = document.querySelector("#password");
const forgot = document.querySelector(".forgot a");
const button = document.querySelector("button");
const signup = document.querySelector(".signup a");

function disableFollow() {
  follow = false;
  section.style = "";
}

function allowFollow() {
  follow = true;
}

// 让交互元素获得焦点时停止眼球跟随
const interactiveElements = document.querySelectorAll("section input, section button, section a");
interactiveElements.forEach(el => {
  el.addEventListener("focus", disableFollow);
  el.addEventListener("blur", allowFollow);
});

// 鼠标移动时的眼球动画计算
section.addEventListener("mousemove", function(e) {
  if (follow) {
    const top = section.getBoundingClientRect().top;
    const left = section.getBoundingClientRect().left;
    const height = section.getBoundingClientRect().height;
    const width = section.getBoundingClientRect().width;
    
    // 计算眼球转动角度
    section.style = `--x:${35 * (e.clientX - left) / width};--y:${-20 * (e.clientY - top) / height};`;
  }
});

section.addEventListener("mouseleave", disableFollow);
section.addEventListener("mouseenter", allowFollow);

// 密码显示/隐藏切换
document.querySelector("input[type='checkbox']").addEventListener("change", function() { // 改用 change 事件更标准
  passwordInput.type = passwordInput.type === "password" ? "text" : "password";
});


// ==========================================
// Part 2: 新增的登录逻辑 (核心修改)
// ==========================================

// 监听表单的提交事件 (这样按回车键也能登录)
form.addEventListener("submit", function(e) {
    // 1. 阻止表单默认的刷新行为
    e.preventDefault(); 

    // 2. 获取用户输入的值
    const user = usernameInput.value;
    const pass = passwordInput.value;
    if (user === 'yanshui' && pass === '1433223cyn') {
        
        // --- 登录成功 ---
        
        // 准备用户信息
        const userInfo = {
            name: "王大力", 
            avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=King",
            loginTime: new Date().toLocaleString()
        };

        // 存入 LocalStorage (这就是你的“本地通行证”)
        localStorage.setItem('isLogin', 'true');
        localStorage.setItem('userInfo', JSON.stringify(userInfo));

        // 提示并跳转
        alert('登录成功！欢迎回来，' + userInfo.name);
        window.location.href = 'learning.html'; // 跳转到学习中心

    } else {
        // --- 登录失败 ---
        alert('账号或密码错误！\n(提示：测试账号 admin，密码 123456)');
        
        // 可以在这里加个简单的抖动动画效果，或者清空密码框
        passwordInput.value = "";
        passwordInput.focus();
    }
});