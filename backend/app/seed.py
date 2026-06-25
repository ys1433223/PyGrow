import asyncio
import json
import os
from pathlib import Path
from sqlalchemy import select
from app.database import async_session, engine, Base
from app.models.user import User
from app.models.course import Course, Lesson
from app.models.gamification import Question, Badge, DailyTask
from app.models.project import Project
from app.models.community import Post


COURSES_DATA = [
    {
        "id": 1, "title": "Python3.11零基础快速入门", "description": "从变量到面向对象，夯实编程根基。",
        "category": "Basic", "category_color": "bg-blue-100 text-blue-500",
        "icon": "fab fa-python", "cover_color": "bg-gradient-to-r from-blue-500 to-cyan-400",
        "bvid": "BV1WD4y1v7uk", "sort_order": 1,
        "lessons": [
            ("第一章：环境搭建", "Python简介与环境搭建", "12:30", 1),
            ("第一章：环境搭建", "安装解释器与PyCharm", "15:45", 2),
            ("第二章：基础语法", "数值类型", "10:20", 5),
            ("第二章：基础语法", "转义字符_原始字符串", "08:15", 33),
            ("第二章：基础语法", "多行字符串", "06:40", 34),
            ("第二章：基础语法", "模运算", "09:10", 40),
            ("第二章：基础语法", "赋值运算符_优先级", "11:30", 41),
            ("第二章：基础语法", "bool_比较运算", "07:50", 42),
            ("第二章：基础语法", "if_的基本使用", "13:20", 44),
            ("第二章：基础语法", "if else_基本使用", "10:40", 46),
            ("第二章：基础语法", "条件表达式", "08:30", 51),
            ("第二章：基础语法", "布尔运算基本使用", "09:00", 53),
            ("第二章：基础语法", "选择结构基本使用", "11:15", 56),
            ("第二章：基础语法", "while基本使用", "14:20", 61),
            ("第二章：基础语法", "for基本使用", "12:50", 68),
            ("第二章：基础语法", "break_continue基本使用", "15:10", 61),
            ("第三章：数据容器", "列表 (List) 的使用", "18:30", 79),
            ("第三章：数据容器", "字典 (Dictionary) 详解", "16:40", 7),
            ("第三章：数据容器", "元组与集合", "14:20", 8),
            ("第四章：函数与模块", "函数定义与参数", "20:10", 9),
            ("第四章：函数与模块", "模块导入与包管理", "15:30", 10),
            ("第四章：函数与模块", "异常处理 try-except", "12:40", 11),
            ("第五章：面向对象", "类与对象基础", "22:10", 12),
            ("第五章：面向对象", "继承与多态", "18:50", 13),
            ("第五章：面向对象", "魔术方法详解", "16:30", 14),
            ("第五章：面向对象", "总结与实战预告", "10:20", 15),
        ]
    },
    {
        "id": 2, "title": "Scrapy分布式爬虫", "description": "数据采集、自动化脚本与反爬攻防。",
        "category": "Spider", "category_color": "bg-pink-100 text-pink-500",
        "icon": "fas fa-spider", "cover_color": "bg-gradient-to-r from-purple-500 to-pink-500",
        "bvid": "BV1uN4y1W7Du", "sort_order": 2,
        "lessons": [
            ("第一章：基础与请求", "爬虫概述-1", "09:34", 1),
            ("第一章：基础与请求", "本课程使用的软件-1", "09:41", 2),
            ("第一章：基础与请求", "手刃一个小爬虫（上）", "07:31", 3),
            ("第一章：基础与请求", "手刃一个小爬虫（下）", "04:16", 4),
            ("第一章：基础与请求", "Web请求过程剖析（上）", "11:01", 5),
            ("第一章：基础与请求", "Web请求过程剖析（下）", "06:07", 6),
            ("第一章：基础与请求", "Http协议（上）", "07:01", 7),
            ("第一章：基础与请求", "Http协议（下）", "06:18", 8),
            ("第一章：基础与请求", "Requests入门（上）", "07:01", 9),
            ("第一章：基础与请求", "Requests入门（下）", "08:20", 10),
            ("第一章：基础与请求", "Requests入门-1", "06:21", 11),
            ("第一章：基础与请求", "Requests入门（上）", "08:01", 12),
            ("第一章：基础与请求", "Requests入门（下）", "08:37", 13),
            ("第一章：基础与请求", "补充 关闭resp-1", "02:16", 14),
            ("第一章：基础与请求", "补充_py基础_字符集的问题", "05:56", 15),
            ("第二章：数据解析", "数据解析概述-1", "02:19", 16),
            ("第二章：数据解析", "Re解析 正则表达式 01（上）", "10:01", 17),
            ("第二章：数据解析", "Re解析 正则表达式 01（下）", "09:17", 18),
            ("第二章：数据解析", "Re解析 正则表达式 02（上）", "08:01", 19),
            ("第二章：数据解析", "Re解析 正则表达式 02（下）", "09:28", 20),
            ("第二章：数据解析", "Python的re模块使用（1）", "10:01", 21),
            ("第二章：数据解析", "Python的re模块使用（2）", "11:00", 22),
            ("第二章：数据解析", "手刃豆瓣top250电影排行（1）", "10:01", 23),
            ("第二章：数据解析", "手刃豆瓣top250电影排行（2）", "09:32", 24),
            ("第二章：数据解析", "屠戮盗版天堂电影信息（1）", "10:01", 25),
            ("第二章：数据解析", "屠戮盗版天堂电影信息（2）", "10:15", 26),
            ("第二章：数据解析", "屠戮盗版天堂电影信息（3）", "10:57", 27),
            ("第二章：数据解析", "Bs4解析前戏-Html语法规则-1", "11:55", 28),
            ("第二章：数据解析", "Bs4解析入门-搞搞菜价（1）", "10:01", 29),
            ("第二章：数据解析", "Bs4解析入门-搞搞菜价（2）", "10:09", 30),
            ("第二章：数据解析", "Bs4解析案例-抓取优美图库图片（1）", "12:01", 31),
            ("第二章：数据解析", "Bs4解析案例-抓取优美图库图片（2）", "12:36", 32),
            ("第二章：数据解析", "Xpath入门 01（1）", "08:01", 33),
            ("第二章：数据解析", "Xpath入门 01（2）", "08:50", 34),
            ("第二章：数据解析", "Xpath入门 02（1）", "07:01", 35),
            ("第二章：数据解析", "Xpath入门 02（2）", "09:10", 36),
            ("第二章：数据解析", "Xpath实战 抓取猪八戒网信息（1）", "10:01", 37),
            ("第二章：数据解析", "Xpath实战 抓取猪八戒网信息（2）", "10:13", 38),
            ("第二章：数据解析", "Xpath实战 抓取猪八戒网信息（3）", "06:29", 39),
            ("第三章：进阶", "Requests进阶概述-1", "02:55", 40),
            ("第三章：进阶", "处理cookie 登录小说网（1）", "10:01", 41),
            ("第三章：进阶", "处理cookie 登录小说网（2）", "08:59", 42),
            ("第三章：进阶", "防盗链 抓取梨视频（1）", "12:01", 43),
            ("第三章：进阶", "防盗链 抓取梨视频（2）", "13:04", 44),
            ("第三章：进阶", "代理-1", "09:59", 45),
            ("第三章：进阶", "综合训练 抓取网易云音乐评论信息（1）", "10:01", 46),
            ("第三章：进阶", "综合训练 抓取网易云音乐评论信息（2）", "10:07", 47),
            ("第三章：进阶", "综合训练 抓取网易云音乐评论信息（3）", "10:12", 48),
            ("第三章：进阶", "综合训练 抓取网易云音乐评论信息（4）", "10:11", 49),
            ("第三章：进阶", "综合训练 抓取网易云音乐评论信息（5）", "10:10", 50),
            ("第三章：进阶", "综合训练 抓取网易云音乐评论信息（6）", "10:01", 51),
            ("第三章：进阶", "综合训练 抓取网易云音乐评论信息（7）", "06:38", 52),
            ("第三章：进阶", "第四章概述-1", "04:50", 53),
            ("第三章：进阶", "多线程（1）", "08:01", 54),
            ("第三章：进阶", "多线程（2）", "07:17", 55),
            ("第三章：进阶", "多进程-1", "06:13", 56),
            ("第三章：进阶", "线程池和进程池入门", "07:00", 57),
            ("第三章：进阶", "线程池案例_抓取新发地菜价（上）", "09:01", 58),
            ("第三章：进阶", "线程池案例_抓取新发地菜价（下）", "09:42", 59),
            ("第三章：进阶", "协程概念", "11:32", 60),
            ("第三章：进阶", "多任务异步协程（上）", "12:01", 61),
            ("第三章：进阶", "多任务异步协程（下）", "11:55", 62),
            ("第三章：进阶", "补充-关于异步协程-过时警告", "07:10", 63),
            ("第三章：进阶", "异步http请求aiohttp模块讲解（上）", "08:01", 64),
            ("第三章：进阶", "异步http请求aiohttp模块讲解（下）", "07:45", 65),
            ("第三章：进阶", "异步爬虫实战-扒光一部小说（上）", "12:01", 66),
            ("第三章：进阶", "异步爬虫实战-扒光一部小说（下）", "12:15", 67),
            ("第三章：进阶", "综合训练_视频网站的工作原理（上）", "09:01", 68),
            ("第三章：进阶", "综合训练_视频网站的工作原理（下）", "10:03", 69),
            ("第三章：进阶", "抓取91看剧_简单版（上）", "07:01", 70),
            ("第三章：进阶", "抓取91看剧_简单版（下）", "07:40", 71),
            ("第三章：进阶", "抓取91看剧_简单版（上）", "10:01", 72),
            ("第三章：进阶", "抓取91看剧_简单版（下）", "11:14", 73),
            ("第三章：进阶", "抓取91看剧_复杂版_1_概述（上）", "06:01", 74),
            ("第三章：进阶", "抓取91看剧_复杂版_1_概述（下）", "07:41", 75),
            ("第三章：进阶", "抓取91看剧_复杂版_2_拿到m3u8路径", "11:01", 76),
            ("第三章：进阶", "看剧_复杂版_3_下载m3u8（上）", "08:01", 77),
            ("第三章：进阶", "看剧_复杂版_3_下载m3u8（下）", "07:37", 78),
            ("第三章：进阶", "抓取91看剧_复杂版_4_下载视频（上）", "09:01", 79),
            ("第三章：进阶", "抓取91看剧_复杂版_4_下载视频（下）", "09:02", 80),
            ("第三章：进阶", "抓取91看剧_复杂版_5_解密（上）", "08:01", 81),
            ("第三章：进阶", "抓取91看剧_复杂版_5_解密（下）", "08:17", 82),
            ("第三章：进阶", "抓取91看剧_复杂版_6_合并视频（上）", "06:01", 83),
            ("第三章：进阶", "抓取91看剧_复杂版_6_合并视频（下）", "07:32", 84),
        ]
    },
    {
        "id": 3, "title": "Python操作Excel与邮件自动化", "description": "使用Pandas自动化处理办公数据，提升工作效率。",
        "category": "Data", "category_color": "bg-yellow-100 text-yellow-600",
        "icon": "fas fa-laptop-code", "cover_color": "bg-gradient-to-r from-yellow-400 to-orange-500",
        "bvid": "BV1hk4y1C73S", "sort_order": 3,
        "lessons": [
            ("全套课程", "如何创建数据的'粮仓'", "08:47", 1),
            ("全套课程", "门道颇多的数据读取", "15:56", 2),
            ("全套课程", "如何在pandas里自由如风", "15:33", 3),
            ("全套课程", "好用到爆的自动填充功能", "14:48", 4),
            ("全套课程", "有点小费周折的年、月、日", "09:58", 5),
            ("全套课程", "一行代码走江湖", "09:50", 6),
            ("全套课程", "只要你乐意，怎么排都行", "09:02", 7),
            ("全套课程", "掌握绘图前的必备功课", "08:53", 8),
            ("全套课程", "高大上的数据可视化", "11:18", 9),
            ("全套课程", "拼颜值年代连做个图都不能例外", "11:50", 10),
            ("全套课程", "再苛刻的需求我都能满足你", "06:42", 11),
            ("全套课程", "画饼虽然不能充饥，但可以炫技", "10:14", 12),
            ("全套课程", "公司是走是留", "09:08", 13),
            ("全套课程", "业余队向专业队转化的分水岭", "07:55", 14),
            ("全套课程", "雕虫小技到奇门遁甲", "09:06", 15),
            ("全套课程", "把七零八碎的数据拼凑成一张完整的表", "13:09", 16),
            ("全套课程", "不是月亮惹的祸纯粹是数据出了错", "07:33", 17),
            ("全套课程", "是分？是合？随机应变", "08:37", 18),
            ("全套课程", "叩开统计大门把函数一网打尽", "12:21", 19),
            ("全套课程", "今天带你玩数据消消乐", "08:32", 20),
            ("全套课程", "旋转表格就能搞定的事", "03:06", 21),
            ("全套课程", "面试工作中重点—读取CSV、TSV、TXT", "05:04", 22),
            ("全套课程", "透视表、分组、聚合", "10:21", 23),
            ("全套课程", "数据分析师真能预测未来", "07:52", 24),
            ("全套课程", "数据一目了然你得给它点儿颜色看看", "10:17", 25),
            ("全套课程", "问你爱我有多深，色彩代表我的心", "04:12", 26),
            ("全套课程", "在数据表上'移花接木'", "18:02", 27),
            ("全套课程", "为啥数据分析又叫'搬砖侠'", "13:01", 28),
            ("全套课程", "链接SQL.Server数据库", "11:42", 29),
            ("全套课程", "数据列编织成的交响曲", "07:25", 30),
        ]
    },
    {
        "id": 4, "title": "Pandas &Matplotlib数据可视化", "description": "像处理 Excel 一样高效处理海量数据。",
        "category": "Data", "category_color": "bg-purple-100 text-purple-500",
        "icon": "fas fa-chart-line", "cover_color": "bg-gradient-to-r from-green-400 to-teal-500",
        "bvid": "BV1ps411x7rm", "sort_order": 4,
        "lessons": [
            ("第一章：基础与图表", "课程简介和环境搭建", "16:26", 1),
            ("第一章：基础与图表", "Numpy简介", "12:47", 2),
            ("第一章：基础与图表", "散点图", "12:16", 3),
            ("第一章：基础与图表", "折线图", "11:14", 4),
            ("第一章：基础与图表", "条形图", "10:23", 5),
            ("第一章：基础与图表", "直方图", "09:30", 6),
            ("第一章：基础与图表", "饼状图", "06:39", 7),
            ("第一章：基础与图表", "箱形图", "07:35", 8),
            ("第二章：样式与布局", "颜色和样式", "12:40", 9),
            ("第二章：样式与布局", "面向对象 vs matlab style", "09:18", 10),
            ("第二章：样式与布局", "子图 subplot", "07:46", 11),
            ("第二章：样式与布局", "多图 figure", "03:03", 12),
            ("第二章：样式与布局", "网格", "08:03", 13),
            ("第二章：样式与布局", "图例 legend", "12:09", 14),
            ("第二章：样式与布局", "坐标轴范围", "06:09", 15),
            ("第二章：样式与布局", "坐标轴刻度", "14:56", 16),
            ("第二章：样式与布局", "添加坐标轴", "09:15", 17),
            ("第二章：样式与布局", "注释", "09:30", 18),
            ("第二章：样式与布局", "文字", "10:40", 19),
            ("第二章：样式与布局", "Tex公式", "16:33", 20),
            ("第二章：样式与布局", "工具栏", "04:49", 21),
            ("第二章：样式与布局", "区域填充", "11:21", 22),
            ("第二章：样式与布局", "形状", "10:26", 23),
            ("第二章：样式与布局", "样式 美化", "13:41", 24),
            ("第二章：样式与布局", "极坐标", "09:03", 25),
            ("第三章：高级应用", "函数积分图一", "14:09", 26),
            ("第三章：高级应用", "函数积分图二", "17:29", 27),
            ("第三章：高级应用", "散点 条形图一", "14:53", 28),
            ("第三章：高级应用", "散点 条形图二", "14:41", 29),
            ("第三章：高级应用", "球员能力图一", "15:37", 30),
            ("第三章：高级应用", "球员能力图二", "15:34", 31),
        ]
    },
    {
        "id": 5, "title": "Django/Flask企业级开发实战", "description": "从零搭建Web应用，掌握企业级开发全流程。",
        "category": "Web", "category_color": "bg-indigo-100 text-indigo-600",
        "icon": "fas fa-server", "cover_color": "bg-gradient-to-r from-indigo-500 to-blue-600",
        "bvid": "BV1N1421U76L", "sort_order": 5,
        "lessons": [
            ("第一章：介绍与准备", "django视频介绍", "11:03", 1),
            ("第一章：介绍与准备", "Django介绍", "05:17", 2),
            ("第一章：介绍与准备", "软件准备工作", "06:16", 3),
            ("第二章：Django入门", "URL组成部分详解", "11:06", 4),
            ("第二章：Django入门", "第一个Django项目", "16:04", 5),
            ("第二章：Django入门", "URL与视图函数的映射", "09:41", 6),
            ("第二章：Django入门", "URL的两种传参方式", "17:21", 7),
            ("第二章：Django入门", "path函数详解", "10:34", 8),
            ("第二章：Django入门", "路由模块化", "10:47", 9),
            ("第二章：Django入门", "路由反转", "10:17", 10),
            ("第三章：模板渲染", "模板渲染初步", "12:40", 11),
            ("第三章：模板渲染", "模板查找路径配置", "09:05", 12),
            ("第三章：模板渲染", "模板变量渲染", "11:00", 13),
            ("第三章：模板渲染", "模板常用标签（1）", "18:42", 14),
            ("第三章：模板渲染", "模板常用标签（2）", "11:56", 15),
            ("第三章：模板渲染", "模板常用过滤器", "19:13", 16),
            ("第三章：模板渲染", "模板结构", "16:33", 17),
            ("第三章：模板渲染", "静态文件加载配置", "17:27", 18),
            ("第四章：数据库与ORM", "MySQL8软件安装", "14:55", 19),
            ("第四章：数据库与ORM", "数据库操作相关软件安装", "09:10", 20),
            ("第四章：数据库与ORM", "Django连接数据库配置", "14:39", 21),
            ("第四章：数据库与ORM", "ORM模型创建与映射", "15:32", 22),
            ("第四章：数据库与ORM", "ORM实现基本CURD操作", "18:41", 23),
            ("第四章：数据库与ORM", "模型常见的Field", "13:38", 24),
            ("第四章：数据库与ORM", "Field的常用参数", "17:26", 25),
            ("第四章：数据库与ORM", "模型中Meta的配置", "07:29", 26),
            ("第四章：数据库与ORM", "Book app的调整", "03:04", 27),
            ("第四章：数据库与ORM", "外键使用（1）", "15:51", 28),
            ("第四章：数据库与ORM", "外键使用（2）", "08:20", 29),
            ("第四章：数据库与ORM", "表之间的三种关系", "19:06", 30),
            ("第四章：数据库与ORM", "查询操作", "32:45", 31),
            ("第四章：数据库与ORM", "聚合函数准备工作", "05:13", 32),
            ("第四章：数据库与ORM", "聚合函数详解", "15:27", 33),
            ("第四章：数据库与ORM", "F表达式和Q表达式", "11:38", 34),
            ("第四章：数据库与ORM", "表单概述", "26:45", 35),
            ("第四章：数据库与ORM", "表单验证", "22:05", 36),
            ("第四章：数据库与ORM", "ModelForm", "18:12", 37),
            ("第四章：数据库与ORM", "cookie和session原理", "11:11", 38),
            ("第四章：数据库与ORM", "操作cookie和session", "29:51", 39),
            ("第四章：数据库与ORM", "CSRF攻击原理和防御", "21:33", 40),
            ("第五章：博客项目实战", "Bootstrap5实现导航条", "21:39", 41),
            ("第五章：博客项目实战", "Bootstrap实现首页布局", "18:27", 42),
            ("第五章：博客项目实战", "Bootstrap实现详情页布局", "19:02", 43),
            ("第五章：博客项目实战", "Bootstrap实现发布博客页面布局", "15:34", 44),
            ("第五章：博客项目实战", "Bootstrap实现发登录和注册布局", "14:02", 45),
            ("第五章：博客项目实战", "改造成django模板", "09:28", 46),
            ("第五章：博客项目实战", "邮件发送功能实现", "19:40", 47),
            ("第五章：博客项目实战", "数据库配置和验证码存储", "11:15", 48),
            ("第五章：博客项目实战", "验证码按钮倒计时", "12:34", 49),
            ("第五章：博客项目实战", "验证码发送功能完成", "04:25", 50),
            ("第五章：博客项目实战", "注册功能实现", "22:33", 51),
            ("第五章：博客项目实战", "登录功能实现", "12:48", 52),
            ("第五章：博客项目实战", "登录和非登录状态切换", "11:36", 53),
            ("第五章：博客项目实战", "退出登录功能实现", "02:19", 54),
            ("第五章：博客项目实战", "发布博客访问限制", "07:06", 55),
            ("第五章：博客项目实战", "博客相关模型和表创建", "06:13", 56),
            ("第五章：博客项目实战", "Admin系统使用讲解", "15:38", 57),
            ("第五章：博客项目实战", "发布博客后端功能实现", "07:53", 58),
            ("第五章：博客项目实战", "发布博客前端功能完成", "17:24", 59),
            ("第五章：博客项目实战", "博客详情页数据动态展示", "04:52", 60),
            ("第五章：博客项目实战", "博客评论功能完成", "11:38", 61),
            ("第五章：博客项目实战", "代码高亮功能完成", "06:07", 62),
            ("第五章：博客项目实战", "搜索功能完成", "11:08", 63),
        ]
    },
    {
        "id": 6, "title": "PyTorch深度学习与神经网络", "description": "迈入人工智能大门，实战图像识别。",
        "category": "AI", "category_color": "bg-orange-100 text-orange-500",
        "icon": "fas fa-brain", "cover_color": "bg-gradient-to-r from-red-500 to-pink-600",
        "bvid": "BV1hE411t7RN", "sort_order": 6,
        "lessons": [
            ("第一章：环境与工具", "环境的配置及安装", "14:26", 1),
            ("第一章：环境与工具", "编辑器的选择与配置", "12:42", 2),
            ("第一章：环境与工具", "FAQ: CUDA不可用?", "05:53", 3),
            ("第一章：环境与工具", "学习中的两大法宝函数", "09:12", 4),
            ("第一章：环境与工具", "PyCharm及Jupyter对比", "16:39", 5),
            ("第二章：数据加载与处理", "加载数据初认识", "11:11", 6),
            ("第二章：数据加载与处理", "Dataset类代码实战", "25:17", 7),
            ("第二章：数据加载与处理", "TensorBoard的使用(一)", "16:31", 8),
            ("第二章：数据加载与处理", "TensorBoard的使用(二)", "11:16", 9),
            ("第二章：数据加载与处理", "Transforms的使用(一)", "18:28", 10),
            ("第二章：数据加载与处理", "Transforms的使用(二)", "08:03", 11),
            ("第二章：数据加载与处理", "常见的Transforms(一)", "18:20", 12),
            ("第二章：数据加载与处理", "常见的Transforms(二)", "21:24", 13),
            ("第二章：数据加载与处理", "torchvision数据集使用", "22:51", 14),
            ("第二章：数据加载与处理", "DataLoader的使用", "22:16", 15),
            ("第三章：神经网络组件", "基本骨架-nn.Module", "15:57", 16),
            ("第三章：神经网络组件", "土堆说卷积操作", "26:37", 17),
            ("第三章：神经网络组件", "神经网络-卷积层", "28:46", 18),
            ("第三章：神经网络组件", "神经网络-最大池化", "24:26", 19),
            ("第三章：神经网络组件", "神经网络-非线性激活", "13:23", 20),
            ("第三章：神经网络组件", "线性层及其他层介绍", "23:22", 21),
            ("第三章：神经网络组件", "Sequential的使用实战", "26:00", 22),
            ("第四章：训练核心组件", "损失函数与反向传播", "31:58", 23),
            ("第四章：训练核心组件", "优化器（一）", "17:38", 24),
            ("第四章：训练核心组件", "现有网络模型使用及修改", "23:29", 25),
            ("第四章：训练核心组件", "网络模型的保存与读取", "16:49", 26),
            ("第五章：完整训练流程", "完整模型训练套路(一)", "27:34", 27),
            ("第五章：完整训练流程", "完整模型训练套路(二)", "22:22", 28),
            ("第五章：完整训练流程", "完整模型训练套路(三)", "05:22", 29),
            ("第五章：完整训练流程", "利用GPU训练(一)", "15:21", 30),
            ("第五章：完整训练流程", "利用GPU训练(二)", "08:11", 31),
            ("第五章：完整训练流程", "完整的模型验证套路", "18:41", 32),
        ]
    },
]


# ========== Load questions from parsed JSON ==========
def _load_questions_from_json():
    """Load questions from the parsed JSON file, fall back to empty list."""
    json_paths = [
        Path(__file__).resolve().parent / "app" / "data" / "questions.json",
        Path(__file__).resolve().parent / "data" / "questions.json",
    ]
    for p in json_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    print("WARNING: questions.json not found, using empty question bank.")
    return []


def _question_to_model(q):
    """Convert parsed question dict to Question model fields."""
    options = q.get("options", [])
    # Map to the format the existing frontend expects
    return Question(
        question_id=q.get("question_id", 0),
        title=q.get("question", q.get("title", ""))[:500],
        content=q.get("question", q.get("content", ""))[:500],
        type=q.get("question_type", q.get("type", "single_choice")),
        options=options,
        answer=str(q.get("answer", "")),
        analysis=q.get("analysis", ""),
        knowledge_point=q.get("knowledge_tag", q.get("knowledge_point", "")),
        knowledge_tag=q.get("knowledge_tag", q.get("knowledge_point", "")),
        difficulty=q.get("difficulty", "medium"),
        level=q.get("stage", q.get("level", "初级")),
        stage=q.get("stage", "初级"),
        chapter=q.get("chapter", ""),
        chapter_num=q.get("chapter_num", 1),
        test_cases=q.get("test_cases", []),
        starter_code=q.get("starter_code", ""),
        score=q.get("score", 5),
        source=q.get("source", "question_bank"),
    )

# ========== Badges (8 items) ==========
BADGES_DATA = [
    {"name": "初次登录", "description": "首次登录 PyGrow 平台", "icon_url": "", "condition_type": "login_first", "condition_value": 1},
    {"name": "测评先锋", "description": "完成首次能力测评", "icon_url": "", "condition_type": "assessment_complete", "condition_value": 1},
    {"name": "坚持学习者", "description": "连续学习 7 天", "icon_url": "", "condition_type": "streak_days", "condition_value": 7},
    {"name": "练习达人", "description": "累计答对 50 道练习题", "icon_url": "", "condition_type": "correct_count", "condition_value": 50},
    {"name": "课程毕业", "description": "完成第一门课程", "icon_url": "", "condition_type": "course_complete", "condition_value": 1},
    {"name": "积分先锋", "description": "累计获得 500 积分", "icon_url": "", "condition_type": "points_total", "condition_value": 500},
    {"name": "段位晋升", "description": "达到达标选手段位", "icon_url": "", "condition_type": "level_reach", "condition_value": 500},
    {"name": "满分答卷", "description": "单次测评获得满分", "icon_url": "", "condition_type": "assessment_perfect", "condition_value": 1},
    {"name": "项目优秀", "description": "项目批改获得 90 分以上", "icon_url": "", "condition_type": "project_excellent", "condition_value": 1},
]

# ========== Daily Tasks (5 items, with new EXP values) ==========
DAILY_TASKS_DATA = [
    {"title": "签到打卡", "description": "每日签到领取经验奖励", "task_type": "daily_checkin", "reward_exp": 5, "reward_points": 0},
    {"title": "观看课程视频", "description": "今天观看课程视频至少5分钟", "task_type": "watch_video", "reward_exp": 10, "reward_points": 0},
    {"title": "完成每日一练", "description": "今天完成每日5道练习题", "task_type": "do_practice", "reward_exp": 20, "reward_points": 0},
    {"title": "记录学习笔记", "description": "今天记录至少1条AI学习笔记", "task_type": "write_note", "reward_exp": 5, "reward_points": 0},
    {"title": "社区有效互动", "description": "在讨论区发帖或回复", "task_type": "community_interact", "reward_exp": 5, "reward_points": 0},
]

# ========== Load projects from JSON ==========
def _load_projects_from_json():
    json_paths = [
        Path(__file__).resolve().parent / "app" / "data" / "projects.json",
        Path(__file__).resolve().parent / "data" / "projects.json",
    ]
    for p in json_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    print("WARNING: projects.json not found, using empty project list.")
    return []


# ========== Community Seed Posts ==========
COMMUNITY_POSTS = [
    {"title": "Python 列表推导式怎么用？求大神指导", "content": "刚开始学 Python 列表推导式，看到 [x for x in range(10) if x%2==0] 这种写法感觉很酷，但不太理解执行顺序。请问哪位大神能详细解释一下列表推导式的工作原理？", "category": "问答专区", "tags": "列表,for循环,初级,代码求助"},
    {"title": "分享一个很实用的 Python 字符串处理技巧", "content": "最近在处理大量文本数据时发现，用 str.translate() 和 str.maketrans() 比 replace 循环快很多。我来分享一下具体用法和性能对比，希望对大家有帮助！", "category": "技术分享区", "tags": "字符串,经验分享,初级"},
    {"title": "推荐几个免费的 Python 视频课程资源", "content": "整理了几个免费的 Python 视频课程资源，包括 B 站上质量很高的教程，还有一些国外大学的公开课，适合不同阶段的学习者。", "category": "资源分享", "tags": "视频课程,图文教程,入门级,初级"},
    {"title": "学了三个月 Python，感觉啥也不会...", "content": "每天看视频跟着敲代码，感觉看的时候都懂，但让自己写就完全不知道从哪里下手。是不是不适合学编程啊？求各位过来人指点一下！", "category": "我要吐槽", "tags": "学习吐槽,入门级,初级"},
    {"title": "NameError: name 'xxx' is not defined 怎么解决？", "content": "运行代码的时候总是报 NameError，说变量没有定义。检查了好几遍变量名拼写也没问题，请问还可能是什么原因导致的？", "category": "问答专区", "tags": "NameError,变量未定义,变量,入门级,报错求助"},
    {"title": "PyTorch 入门经验分享：从零到跑通第一个模型", "content": "花了两周时间终于跑通了第一个图像分类模型，记录一下踩过的坑和学习路线，希望对想学深度学习的同学有帮助。", "category": "技术分享区", "tags": "数据分析,面向对象,经验分享,学习笔记,中级"},
    {"title": "收集的 Python 练习题大合集（带答案）分享", "content": "整理了 100 道 Python 练习题，涵盖基础语法到面向对象，每道题都有详细答案和解析。适合新手练习和面试准备。", "category": "资源分享", "tags": "练习题,代码模板,变量,函数,初级,中级"},
    {"title": "缩进错误搞得我心态炸了", "content": "复制了一段代码过来改了一下，结果满屏的 IndentationError，tab 和空格混用的问题真的要命。Python 这个强制缩进有时候真的很烦！", "category": "我要吐槽", "tags": "IndentationError,缩进问题,学习吐槽,入门级"},
    {"title": "while 循环怎么避免死循环？求最佳实践", "content": "写了个 while 循环来读取文件，结果忘了写退出条件，程序跑了一分钟还在转。大家平时怎么避免写死循环的？有什么好的习惯吗？", "category": "问答专区", "tags": "while循环,死循环,文件操作,初级,代码求助"},
    {"title": "分享一个我自己写的天气查询小工具", "content": "用 requests + tkinter 写了个桌面天气查询工具，输入城市名就能显示实时天气。代码开源在 GitHub 上，欢迎大家提建议！", "category": "技术分享区", "tags": "函数,模块,项目展示,中级"},
]

async def seed():
    async with async_session() as session:
        result = await session.execute(select(Course).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded, skipping.")
            return

        for cdata in COURSES_DATA:
            lessons_data = cdata.pop("lessons")
            course = Course(**cdata)
            session.add(course)
            await session.flush()

            for i, (chapter, title, duration, page) in enumerate(lessons_data):
                lesson = Lesson(
                    course_id=course.id,
                    chapter=chapter,
                    title=title,
                    duration=duration,
                    bilibili_page=page,
                    sort_order=i + 1,
                )
                session.add(lesson)

        # Seed questions from parsed JSON
        questions_data = _load_questions_from_json()
        if questions_data:
            for q in questions_data:
                session.add(_question_to_model(q))
            print(f"Seeded {len(questions_data)} questions from question bank.")
        else:
            print("No questions to seed.")

        # Seed badges
        for bdata in BADGES_DATA:
            session.add(Badge(**bdata))

        # Seed daily tasks
        for tdata in DAILY_TASKS_DATA:
            session.add(DailyTask(**tdata))

        # Seed projects from JSON
        projects_data = _load_projects_from_json()
        for pdata in projects_data:
            project = Project(
                project_id=pdata["project_id"],
                stage=pdata["stage"],
                chapter=pdata["chapter"],
                knowledge_tags=pdata.get("knowledge_tags", []),
                difficulty=pdata.get("difficulty", "medium"),
                project_title=pdata["project_title"],
                title=pdata["project_title"],
                task_description=pdata.get("task_description", ""),
                description=pdata.get("task_description", ""),
                requirements=pdata.get("requirements", []),
                submit_type="code",
                max_score=100,
                ai_review_enabled=1,
                reward_exp=pdata.get("reward_exp", 50),
                reward_points=pdata.get("reward_points", 30),
            )
            session.add(project)
        if projects_data:
            print(f"Seeded {len(projects_data)} projects.")

        # Ensure system user exists for seed posts
        from app.services.auth_service import hash_password
        sys_user = (await session.execute(select(User).where(User.id == 1))).scalar_one_or_none()
        if not sys_user:
            session.add(User(id=1, username="admin", password_hash=hash_password("admin123"), nickname="社区管理员", is_admin=1))

        # Seed community posts
        for pdata in COMMUNITY_POSTS:
            session.add(Post(user_id=1, **pdata))

        await session.commit()
        print("Database seeded successfully.")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(seed())
