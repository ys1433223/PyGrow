# PyGrow 悬浮桌宠组件说明文档

> 路径：`frontend/public/pets/default/`  
> 组件：`src/components/PetCompanion.vue`  
> 状态映射：`src/data/petAnimationMap.js`  
> 全局钩子：`src/hooks/usePetCompanion.js`

---

## 1. 识别到的 GIF 文件（共 36 个）

| | | | |
|---|---|---|---|
| yes.gif | 上工.gif | 举牌100分.gif | 傻眼流口水.gif |
| 吃薯片.gif | 吐舌.gif | 哼哼.gif | 喜欢.gif |
| 喜欢2.gif | 喜欢3.gif | 喝奶茶休息.gif | 喝茶休息.gif |
| 噗呲偷笑.gif | 坏笑.gif | 对手指.gif | 尴尬扣脸.gif |
| 思考.gif | 慌.gif | 我擦屏幕.gif | 戳戳.gif |
| 抱抱.gif | 拉泪.gif | 拖动捏脸.gif | 捏鼻.gif |
| 无语.gif | 比x.gif | 浇水.gif | 灵光.gif |
| 点赞.gif | 生气.gif | 疑惑.gif | 端详.gif |
| 纸箱休息.gif | 震惊.gif | 鼓掌.gif | |

---

## 2. 每个 GIF 归入的状态池

| 状态池 | GIF 文件 | 触发场景 |
|--------|----------|----------|
| **idle** 默认待机 | yes.gif, 无语.gif, 吐舌.gif, 吃薯片.gif, 浇水.gif | 页面加载、无事件时 |
| **happy** 正反馈 | 点赞.gif, 鼓掌.gif, 喜欢.gif, 喜欢2.gif, 喜欢3.gif, 对手指.gif, 噗呲偷笑.gif | 答对、任务完成、AI笔记成功 |
| **excellent** 强正反馈 | 举牌100分.gif, 鼓掌.gif, 喜欢3.gif, 灵光.gif | 正确率>=90%、晋级通过、满分 |
| **thinking** 思考/生成中 | 思考.gif, 疑惑.gif, 端详.gif | AI批改中、AI笔记解析中、视频观看 |
| **wrong** 错误/失败 | 傻眼流口水.gif, 尴尬扣脸.gif, 拉泪.gif, 慌.gif, 比x.gif | 答错、AI笔记失败、批改失败 |
| **comfort** 安慰 | 抱抱.gif, 拉泪.gif, 捏鼻.gif | 正确率<60%、晋级失败 |
| **rest** 休息 | 喝茶休息.gif, 喝奶茶休息.gif, 纸箱休息.gif, 吃薯片.gif | 所有任务完成、手动休息 |
| **work** 学习/工作 | 上工.gif, 灵光.gif, 我擦屏幕.gif | 打开课程、选择课时 |
| **message** 消息提醒 | 震惊.gif, 疑惑.gif, 点赞.gif | 收到系统通知、社区回复 |
| **adventure** 探险中 | 上工.gif, 纸箱休息.gif, 戳戳.gif | 宠物探险出发 |
| **returnReward** 探险归来 | 喜欢.gif, 点赞.gif, 举牌100分.gif, 鼓掌.gif | 宠物探险返回、获得奖励 |
| **click** 点击互动 | 抱抱.gif, 捏鼻.gif, 戳戳.gif, 坏笑.gif | 点击宠物触发 |
| **drag** 拖动 | 拖动捏脸.gif | 拖动宠物时 |
| **annoyed** 连续点击 | 生气.gif, 无语.gif, 尴尬扣脸.gif, 哼哼.gif | 连续点击>=5次 |

---

## 3. 桌宠在哪些页面可用

| 页面 | 路由 | 模式 |
|------|------|------|
| 首页 | `/` | active |
| 课程中心 | `/courses` | active |
| 学习中心 | `/learning-center` | active |
| 社区 | `/community` | active |
| 资源中心 | `/resources` | active |
| 个人中心 | `/profile` | active |
| 能力测评 | `/assessment` | active |
| 测评结果 | `/assessment/result` | active |
| 学习报告 | `/report` | active |
| AI导师 | `/ai-mentor` | active |
| 在线编程 | `/code-runner` | active |
| 收藏 | `/favorites` | active |
| 每日一练答题页 | `/daily-practice` | simplified |
| 每日一练报告页 | `/daily-practice`（提交后） | active |
| 练习结算页 | `/practice`（提交后） | active |
| 综合项目 AI批改/结果页 | `/projects`（提交后） | active |

---

## 4. 哪些页面禁用或静默

| 页面 | 模式 | 说明 |
|------|------|------|
| 登录页 `/login` | hidden | 完全隐藏，不显示恢复按钮 |
| 注册页 `/register` | hidden | 完全隐藏 |
| 章节练习答题过程 | silent | 灰显、不可点击、不响应事件 |
| 专项练习答题过程 | silent | 同上 |
| 错题本练习答题过程 | silent | 同上 |
| 晋级赛答题过程 | silent | 同上 |
| 综合项目编辑/提交页 | silent | 同上 |

---

## 5. 每日一练中如何触发宠物即时反馈

每日一练提交答卷后，根据整体正确率触发：

```js
// DailyPracticeView.vue — submitAnswers()
const pct = res.data.data.score_percent
if (pct >= 90) triggerPetState('excellent', 5000)
else if (pct >= 75) triggerPetState('happy', 4000)
else if (pct >= 60) triggerPetState('thinking', 4000)
else triggerPetState('comfort', 4000)
```

**菜单规则：** 每日一练答题过程中点击桌宠，显示简化菜单：
- AI提示（调用 `POST /api/practice/ai-hint`）
- 当前进度（显示"第 X/5 题"）
- 关闭互动效果

**重要：** 每日一练中不显示"Python AI助手"自由对话入口，只允许分层AI提示。

---

## 6. 其他练习结算页如何触发宠物反馈

**PracticeView**（章节/错题/智能推荐）提交后使用相同的正确率→状态映射规则。

**综合项目 AI 批改结果页** 根据评分触发：

```js
// ProjectCenterView.vue — handleSubmit()
const score = res.data.data.total_score
if (score >= 90) triggerPetState('excellent', 5000)
else if (score >= 75) triggerPetState('happy', 4000)
else if (score >= 60) triggerPetState('thinking', 4000)
else triggerPetState('comfort', 4000)
```

---

## 7. 综合项目练习页为什么禁用桌宠

1. 综合项目属于正式练习场景，需要学生专注编写代码
2. 项目练习过程中不允许打开 AI 助手（保证独立完成）
3. 不允许弹出消息中心（避免干扰）
4. 不根据编辑行为切换动图（避免分散注意力）
5. 学生在提交后进入 AI 批改结果页时恢复桌宠，可以：
   - 查看批改反馈时与 AI 助手讨论薄弱知识点
   - 根据评分获得鼓励性宠物反馈

---

## 8. 如何触发宠物状态变化

任何组件中导入即用，无需 setup：

```js
import { triggerPetState, setPetMode, addPetMessage } from '../hooks/usePetCompanion'

// 切换动图状态（2-5秒后自动恢复idle，adventure/rest除外）
triggerPetState('happy', 4000)        // 开心
triggerPetState('thinking')           // 思考（默认3秒）
triggerPetState('adventure')          // 探险（不自动恢复）

// 切换显示模式
setPetMode('silent')                  // 静默不可交互
setPetMode('active')                  // 恢复完全交互
setPetMode('simplified')              // 每日一练简化模式
setPetMode('hidden')                  // 完全隐藏

// 添加消息（自动存入localStorage，消息开启时触发message状态）
addPetMessage({
  title: '你的帖子收到了新回复',
  body: '用户XXX回复了你的帖子"Python缩进问题"',
  category: 'community',              // system|community|task|promotion|adventure|farm
})
```

**全部可用状态名：**
`idle, happy, excellent, thinking, wrong, comfort, rest, work, message, adventure, returnReward, click, drag, annoyed`

---

## 9. 如何关闭互动效果

1. **点击桌宠 → 宠物设置 → 关闭"互动效果"开关**
2. 关闭后宠物固定显示 idle 池的默认 GIF，不再根据学习场景切换
3. 设置保存在 `localStorage` 的 `petInteractions` 键中
4. 代码中也可以直接操作：
```js
localStorage.setItem('petInteractions', 'false')  // 关闭
localStorage.setItem('petInteractions', 'true')   // 开启
```

---

## 10. 如何恢复默认位置

1. **点击桌宠 → 宠物设置 → 恢复默认位置**
2. 点击后确认，宠物回到页面右下角
3. 本质是删除 `localStorage` 中的 `petPosition` 键
4. 代码中可以直接操作：
```js
localStorage.removeItem('petPosition')
// 刷新或重新挂载PetCompanion后生效
```

---

## 11. 后续新增 GIF 的加入方式

### 步骤

1. **放置 GIF 文件** 到 `public/pets/default/` 目录

2. **编辑 `src/data/petAnimationMap.js`**，将新文件名加入对应状态池：

```js
// 例如：新增了一个 "跳舞.gif" 想加入 happy 状态池
export const PET_STATE_POOLS = {
  // ...
  happy: ['点赞.gif', '鼓掌.gif', '喜欢.gif', /* ... */, '跳舞.gif'], // 加在这里
  // ...
}
```

3. **如果是全新状态**（例如需要新增 `sleep` 状态），需要：
   - 在 `PET_STATE_POOLS` 中添加新状态池
   - 在 `TMP_STATE_DEFAULTS` 中添加默认持续时间
   - 在代码中调用 `triggerPetState('sleep')` 触发

4. **自动完成：** `pickGif(state)` 会从对应状态池中随机选取一个 GIF 返回完整路径 `/pets/default/xxx.gif`

5. **无需其他配置**，构建工具会自动包含 `public/` 目录下的文件

### 注意事项
- GIF 文件名建议使用中文描述动作（如 `跳舞.gif`），方便后续维护
- 每个状态池至少保留 1 个 GIF（idle 作为全局兜底）
- 如果某个状态池为空，`pickGif()` 会自动回退到 idle 池
- GIF 建议尺寸约 200×200 像素，组件渲染时会缩放到 130×130

---

## 技术架构

```
App.vue
  └── <PetCompanion />               (z-index: 9999)
        ├── <img :src="currentGif">  宠物动图 (130×130px)
        ├── <PetMenu />              点击弹出菜单
        │     ├── Python AI助手
        │     ├── 消息中心
        │     └── 宠物设置
        ├── <PetAssistantChat />     小型AI聊天窗口 (320×420px)
        ├── <PetMessagePanel />      消息中心面板 (300×380px)
        └── <PetSettingsPanel />     设置面板 (260px宽)
```

**全局事件总线**（CustomEvent）：
```
window dispatch 'pet:state'    → triggerPetState()
window dispatch 'pet:mode'     → setPetMode()
window dispatch 'pet:message'  → addPetMessage()
```
