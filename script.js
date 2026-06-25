let follow = true;
const section = document.querySelector("section");
const form = document.querySelector("form");
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

const interactiveElements = document.querySelectorAll("section input, section button, section a");
interactiveElements.forEach(el => {
  el.addEventListener("focus", disableFollow);
  el.addEventListener("blur", allowFollow);
});

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
document.querySelector("input[type='checkbox']").addEventListener("change", function() { //change 事件
  passwordInput.type = passwordInput.type === "password" ? "text" : "password";
});


form.addEventListener("submit", function(e) {
    e.preventDefault(); 

    const user = usernameInput.value;
    const pass = passwordInput.value;

 
    if (user === 'yanshui' && pass === '1433223') {
        
        const userInfo = {
            name: "yanshui", 
            avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=King",
            loginTime: new Date().toLocaleString()
        };
        localStorage.setItem('isLogin', 'true');
        localStorage.setItem('userInfo', JSON.stringify(userInfo));

        alert('登录成功！欢迎回来，' + userInfo.name);
        window.location.href = 'main.html'; 

    } else {
        // --- 登录失败 ---
		alert('账号或密码错误！');
       
        passwordInput.value = "";
        passwordInput.focus();
    }
});