<script setup>
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import PageLoader from '../components/layout/PageLoader.vue'

const tools = [
  { name: 'PyCharm', icon: 'fas fa-python', desc: '专业 Python IDE，智能代码补全与调试', color: 'from-green-400 to-emerald-500', link: 'https://www.jetbrains.com/pycharm/' },
  { name: 'VS Code', icon: 'fas fa-code', desc: '轻量级编辑器，丰富的 Python 插件生态', color: 'from-blue-400 to-cyan-500', link: 'https://code.visualstudio.com/' },
  { name: 'Jupyter', icon: 'fas fa-book', desc: '交互式数据分析与可视化笔记本', color: 'from-orange-400 to-amber-500', link: 'https://jupyter.org/' },
  { name: 'Anaconda', icon: 'fas fa-shield-alt', desc: 'Python 发行版，预装数据科学工具包', color: 'from-green-500 to-teal-500', link: 'https://www.anaconda.com/' },
  { name: 'Pip', icon: 'fas fa-box', desc: 'Python 官方包管理工具', color: 'from-yellow-400 to-orange-400', link: 'https://pip.pypa.io/' },
  { name: 'Docker', icon: 'fas fa-dharmachakra', desc: '容器化部署，环境一键构建', color: 'from-blue-500 to-indigo-600', link: 'https://www.docker.com/' },
]

const websites = [
  { name: 'Python 官方文档', icon: 'fas fa-file-alt', desc: '最权威的 Python 中文参考资料', color: 'from-yellow-400 to-amber-500', link: 'https://docs.python.org/zh-cn/3/' },
  { name: '菜鸟教程', icon: 'fas fa-graduation-cap', desc: '编程语言零基础入门教程', color: 'from-green-400 to-teal-500', link: 'https://www.runoob.com/python3/' },
  { name: 'LeetCode 中国', icon: 'fas fa-laptop-code', desc: '算法与数据结构刷题平台', color: 'from-orange-400 to-red-500', link: 'https://leetcode.cn/' },
  { name: 'B站 Python 教程', icon: 'fab fa-bilibili', desc: '海量免费 Python 视频教程', color: 'from-pink-400 to-rose-500', link: 'https://search.bilibili.com/all?keyword=Python教程' },
  { name: 'CSDN', icon: 'fas fa-blog', desc: '中国最大IT技术社区', color: 'from-red-400 to-orange-500', link: 'https://www.csdn.net/' },
  { name: '掘金', icon: 'fas fa-gem', desc: '前端与 Python 技术文章', color: 'from-blue-500 to-indigo-600', link: 'https://juejin.cn/' },
  { name: '知乎', icon: 'fab fa-zhihu', desc: '编程问答与经验分享', color: 'from-blue-400 to-blue-600', link: 'https://www.zhihu.com/topic/19552808' },
  { name: '博客园', icon: 'fas fa-pen-nib', desc: '老牌技术博客社区', color: 'from-teal-400 to-green-500', link: 'https://www.cnblogs.com/' },
  { name: 'Gitee 码云', icon: 'fas fa-code-branch', desc: '国内开源代码托管平台', color: 'from-red-500 to-pink-600', link: 'https://gitee.com/' },
  { name: '思否 SegmentFault', icon: 'fas fa-question-circle', desc: '中文技术问答社区', color: 'from-green-500 to-teal-600', link: 'https://segmentfault.com/' },
  { name: '中国大学MOOC', icon: 'fas fa-university', desc: '国内名校免费计算机课程', color: 'from-purple-400 to-indigo-500', link: 'https://www.icourse163.org/' },
  { name: '阿里云开发者', icon: 'fas fa-cloud', desc: '阿里云技术文档与社区', color: 'from-orange-500 to-amber-600', link: 'https://developer.aliyun.com/' },
]
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <PageLoader />
    <AppHeader />

    <main class="flex-grow container mx-auto px-4 py-8">
      <!-- Header -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">资源中心</h1>
        <p class="text-gray-500">开发工具、学习资源、推荐网站一站式导航</p>
      </div>

      <!-- Tools -->
      <section class="mb-10">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-2 h-8 bg-blue-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">开发工具</h2>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <a v-for="tool in tools" :key="tool.name" :href="tool.link" target="_blank" rel="noopener"
            class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all">
            <div :class="['w-10 h-10 bg-gradient-to-r rounded-lg flex items-center justify-center text-white text-lg mb-3 group-hover:scale-110 transition-transform', tool.color]">
              <i :class="tool.icon"></i>
            </div>
            <h3 class="font-bold text-gray-800 mb-0.5">{{ tool.name }}</h3>
            <p class="text-gray-400 text-sm">{{ tool.desc }}</p>
          </a>
        </div>
      </section>

      <!-- Online Resources -->
      <section class="mb-10">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-2 h-8 bg-purple-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">在线资源</h2>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <a v-for="site in websites" :key="site.name" :href="site.link" target="_blank" rel="noopener"
            class="group bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg hover:-translate-y-1 transition-all">
            <div :class="['w-10 h-10 bg-gradient-to-r rounded-lg flex items-center justify-center text-white text-lg mb-3 group-hover:scale-110 transition-transform', site.color]">
              <i :class="site.icon"></i>
            </div>
            <h3 class="font-bold text-gray-800 mb-0.5">{{ site.name }}</h3>
            <p class="text-gray-400 text-sm">{{ site.desc }}</p>
          </a>
        </div>
      </section>

      <!-- Community -->
      <section>
        <div class="flex items-center gap-3 mb-6">
          <div class="w-2 h-8 bg-green-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">推荐社区</h2>
        </div>
        <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-[2rem] p-8 md:p-12 text-center">
          <p class="text-xl font-bold text-gray-800 mb-3">🤝 加入 Python学习营地 学习社区</p>
          <p class="text-gray-500 mb-6 max-w-lg mx-auto">在社区中讨论问题、分享学习心得、参与项目协作</p>
          <router-link to="/community" class="inline-block bg-blue-600 text-white px-8 py-3 rounded-full font-bold hover:bg-blue-700 transition shadow-lg">
            进入社区
          </router-link>
        </div>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
