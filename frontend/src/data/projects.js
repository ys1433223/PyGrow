// Project challenge data — organized by level, chapter, and project
// Extracted from Chapter Resources/ Project folders

const projects = {
  初级: [
    // Chapter 1: 认识Python
    {
      id: 101,
      chapter: 1,
      chapterName: '认识Python',
      title: 'Python综合基础项目',
      summary: '搭建Python开发环境，编写第一个Python程序',
      description: '本综合基础项目覆盖Python基础概念、开发环境搭建、编码规范等知识。要求掌握Python发展历史、特性、应用领域，实践原始Python解释器、IDLE、Anaconda3、PyCharm等开发工具，按PEP8规范编写包含个人信息输出的代码，完成环境安装与功能开发。',
      knowledgePoints: ['Python概述', '开发环境搭建', 'PEP8编码规范'],
      difficulty: 'easy',
      estimatedTime: '2小时',
      tasks: [
        '安装Python解释器和IDE（PyCharm或VS Code）',
        '创建项目并配置Python环境',
        '编写个人信息输出程序',
        '遵循PEP8规范格式化代码',
        '编写项目文档和总结'
      ]
    },
    // Chapter 2: 编码规范与注释
    {
      id: 201,
      chapter: 2,
      chapterName: '编码规范与注释',
      title: '班级成绩管理系统',
      summary: '综合运用变量、数据类型、运算符，构建成绩管理系统',
      description: '以班级成绩管理为业务场景，涵盖代码书写规范、标识符命名、输入输出、变量与表达式、运算符与表达式等全章知识点。要求严格遵循Python命名规范，使用input()接收学生信息和各科成绩，通过类型转换统一数据格式，运用算术运算符计算总分与平均分，结合比较运算符和逻辑运算符判断及格情况。',
      knowledgePoints: ['编码规范', '输入输出', '变量与表达式', '运算符', '类型转换'],
      difficulty: 'medium',
      estimatedTime: '3小时',
      tasks: [
        '设计学生信息数据结构',
        '实现成绩录入与存储',
        '计算总分、平均分',
        '判断及格情况并输出等级',
        '添加中文注释和代码文档'
      ]
    },
    // Chapter 3: 数据类型与序列结构
    {
      id: 301,
      chapter: 3,
      chapterName: '数据类型与序列结构',
      title: '字符串统计（数字和字母个数统计）',
      summary: '字符串方法综合练习：统计字符类型',
      description: '围绕字符串全部知识点设计，包含字符串定义、索引与切片、常用方法、字符类型判断等。要求用户输入一段混合大小写字母、数字、符号、空格的字符串，运用isalpha()、isdigit()等方法判断字符类型，统计大写字母、小写字母、全部字母、数字的数量，自动排除符号和空格。',
      knowledgePoints: ['字符串定义', '字符串索引与切片', '字符串方法', '字符类型判断'],
      difficulty: 'easy',
      estimatedTime: '1.5小时',
      tasks: [
        '接收用户输入的混合字符串',
        '使用字符串方法判断字符类型',
        '分别统计字母、数字、符号数量',
        '格式化输出统计结果',
        '添加异常处理'
      ]
    },
    {
      id: 302,
      chapter: 3,
      chapterName: '数据类型与序列结构',
      title: '菜单管理系统（元组应用）',
      summary: '运用元组不可变特性实现固定菜单管理',
      description: '基于元组和列表基础知识，包含序列分类、元组不可变性、元组创建与元素访问、遍历、切片等知识点。利用元组固定不可修改、安全性高的特点存储餐厅菜单，使用元组创建包含菜品名称的固定菜单，通过索引取值、循环遍历、切片提取菜单数据，结合字符串格式化排版输出。',
      knowledgePoints: ['序列分类', '元组不可变性', '元组创建与访问', '列表基础'],
      difficulty: 'easy',
      estimatedTime: '1.5小时',
      tasks: [
        '使用元组定义固定菜单项',
        '实现菜单索引查询功能',
        '遍历元组展示全部菜品',
        '使用切片提取分类菜单',
        '格式化输出菜单列表'
      ]
    },
    {
      id: 303,
      chapter: 3,
      chapterName: '数据类型与序列结构',
      title: '学生成绩信息库（列表综合实战）',
      summary: '使用列表实现成绩的增删改查',
      description: '基于Python容器类型中列表的全部知识点，包括列表通用操作、增删改查、集合去重、嵌套列表等。使用列表存储多名学生的成绩记录，每条记录包含学生姓名和各科分数，通过索引、切片、追加、删除、修改等操作完成成绩信息的增删改查，使用集合自动去重，结合字符串格式化展示全部学生成绩。',
      knowledgePoints: ['列表操作', '列表增删改查', '集合去重', '嵌套列表', '字符串格式化'],
      difficulty: 'medium',
      estimatedTime: '3小时',
      tasks: [
        '设计学生成绩列表数据结构',
        '实现成绩的添加、删除、修改功能',
        '实现按姓名或成绩查询功能',
        '使用集合去重防止重复记录',
        '格式化输出成绩报表'
      ]
    },
    {
      id: 304,
      chapter: 3,
      chapterName: '数据类型与序列结构',
      title: '字典学生成绩管理（字典实战）',
      summary: '使用字典键值对管理成绩数据',
      description: '围绕字典知识点展开，以学生成绩管理为业务场景，涵盖字典键值对创建、取值、键值修改、嵌套字典、字典方法等。以学生姓名为唯一键，对应各科成绩列表为值，构建成绩字典，实现单学生成绩修改、多学生成绩查询、删除学生记录、计算全班总分和单科平均分，使用字符串格式化打印报表。',
      knowledgePoints: ['字典创建', '键值对操作', '字典方法', '嵌套字典', '字典遍历'],
      difficulty: 'medium',
      estimatedTime: '2.5小时',
      tasks: [
        '构建学生成绩字典（姓名→成绩列表）',
        '实现成绩修改和查询功能',
        '计算全班总分和单科平均分',
        '删除学生记录',
        '格式化输出成绩汇总表'
      ]
    },
    {
      id: 305,
      chapter: 3,
      chapterName: '数据类型与序列结构',
      title: '成绩排名系统（列表+字典综合实战）',
      summary: '综合运用所有序列结构实现成绩排名',
      description: '融合字符串、列表、元组、字典、集合全部序列结构知识点，以班级成绩管理为背景。使用字典存储全班学生姓名和成绩数据，将字典值转换为列表实现排序，元组固定科目表头，集合排除重复总分，字符串格式化排版排名表，支持按总分从高到低自动排序，显示名次、姓名、总分、平均分。',
      knowledgePoints: ['列表排序', '字典与列表转换', '元组固定表头', '集合去重', '字符串排版'],
      difficulty: 'hard',
      estimatedTime: '4小时',
      tasks: [
        '设计综合数据结构（字典+列表+元组）',
        '实现按总分自动排名',
        '处理同分并列情况',
        '格式化输出排名表',
        '添加科目表头和数据验证'
      ]
    },
    // Chapter 4: 运算符与表达式
    {
      id: 401,
      chapter: 4,
      chapterName: '运算符与表达式',
      title: '成绩等级判断',
      summary: '使用条件分支实现成绩等级判定',
      description: '围绕条件判断与分支结构知识点设计，包括比较表达式、单/双/多分支结构、分支嵌套。根据学生成绩分数进行等级判定，通过多分支if-elif-else划分优秀、良好、中等、及格、不及格五个等级，同时嵌套分支处理优秀和不及格的细分情况，规范化使用代码注释，结合字符串格式化输出判定结果。',
      knowledgePoints: ['比较表达式', 'if-elif-else', '分支嵌套', '逻辑运算'],
      difficulty: 'easy',
      estimatedTime: '1.5小时',
      tasks: [
        '接收用户输入的成绩分数',
        '使用多分支结构划分等级',
        '嵌套分支处理细分情况',
        '格式化输出等级结果',
        '添加输入验证和异常处理'
      ]
    },
    {
      id: 402,
      chapter: 4,
      chapterName: '运算符与表达式',
      title: '不同进制转换器',
      summary: '使用循环和分支实现进制转换',
      description: '涵盖while循环、for循环、break/continue控制语句、列表推导式等知识点。设定转换范围上下限，分别使用for循环实现正向遍历转换、while循环实现条件控制转换，中途通过break终止、continue跳过无效值，使用列表推导式筛选合法数据，对比不同循环写法的差异。',
      knowledgePoints: ['while循环', 'for循环', 'break/continue', '列表推导式'],
      difficulty: 'medium',
      estimatedTime: '2小时',
      tasks: [
        '实现十进制到二进制的转换',
        '使用for循环批量转换数据',
        '使用while循环条件控制',
        '对比两种循环的效率差异',
        '添加输入合法性检查'
      ]
    },
    {
      id: 403,
      chapter: 4,
      chapterName: '运算符与表达式',
      title: '猜数字游戏',
      summary: '综合运用循环和异常处理实现经典游戏',
      description: '综合循环结构和异常处理知识点，包含随机数生成、循环接收用户输入、try-except捕获非法输入异常、分支判断猜测偏差（偏大/偏小/猜对）、猜对后break退出循环。全面融合循环控制逻辑、分支判断、异常处理语法，掌握输入数据校验的基本实践方式。',
      knowledgePoints: ['随机数生成', 'while循环', 'try-except', 'break语句', '分支判断'],
      difficulty: 'easy',
      estimatedTime: '1.5小时',
      tasks: [
        '生成1-100的随机数',
        '循环接收用户猜测',
        '处理非数字输入异常',
        '提示偏大或偏小',
        '统计猜测次数'
      ]
    },
    {
      id: 404,
      chapter: 4,
      chapterName: '运算符与表达式',
      title: '停车场自动收费系统（综合实战）',
      summary: '大型综合实战：融合分支、循环、异常处理',
      description: '综合实战项目，融合比较表达式、多分支嵌套、while循环、break/continue、异常处理等全部第四章知识点。用户输入车辆入场时间，通过异常处理拦截非法输入，使用多分支嵌套判断车型（小型/中型/大型），按停留时长和收费标准分级计费，while循环支持多辆车连续计费，continue跳过无效时长输入，break退出计费程序。',
      knowledgePoints: ['分支嵌套', 'while循环', '异常处理', 'break/continue', '表达式计算'],
      difficulty: 'hard',
      estimatedTime: '4小时',
      tasks: [
        '设计车型分类和收费标准',
        '实现停车时长计算',
        '多分支判断计费规则',
        '支持多辆车连续计费',
        '生成收费单据'
      ]
    },
    // Chapter 5: 函数基础
    {
      id: 501,
      chapter: 5,
      chapterName: '函数基础',
      title: '查询城市所在省份',
      summary: '函数定义、参数传递和内置函数综合练习',
      description: '围绕函数定义与调用、位置参数、默认参数、关键字参数、可变参数及常用内置函数（enumerate、zip等）综合设计。使用字典存储省份与对应城市映射数据，自定义查询函数实现城市→省份查询，设计默认参数设置查询提示语、关键字参数限定查询方式、可变参数支持多城市批量查询，结合enumerate、zip处理省份城市编号。',
      knowledgePoints: ['函数定义', '参数类型', '默认参数', '关键字参数', '内置函数'],
      difficulty: 'medium',
      estimatedTime: '2.5小时',
      tasks: [
        '构建省份-城市映射字典',
        '实现单城市查询函数',
        '支持多城市批量查询',
        '使用enumerate和zip辅助处理',
        '添加未匹配城市的提示'
      ]
    },
    {
      id: 502,
      chapter: 5,
      chapterName: '函数基础',
      title: '斐波那契数列生成器',
      summary: '使用yield实现生成器函数',
      description: '聚焦生成器知识点，综合练习yield关键字和lambda匿名函数。要求使用yield关键字自定义生成器函数实现斐波那契数列值的生成，设置默认参数控制生成长度，同时使用lambda匿名函数辅助数值计算，通过循环遍历获取生成器数据，对比普通return函数和yield生成器在内存占用和执行逻辑上的差异。',
      knowledgePoints: ['生成器函数', 'yield关键字', 'lambda匿名函数', '内存优化'],
      difficulty: 'medium',
      estimatedTime: '2小时',
      tasks: [
        '使用yield定义斐波那契生成器',
        '设置参数控制生成长度',
        '使用lambda辅助数值计算',
        '对比生成器与普通函数的差异',
        '分析内存占用优势'
      ]
    },
    {
      id: 503,
      chapter: 5,
      chapterName: '函数基础',
      title: '打印星号图案',
      summary: '函数封装、局部变量与全局变量实践',
      description: '结合函数封装、全局变量与局部变量知识点。将打印三角形、正方形的逻辑封装为独立函数，函数内部使用局部变量存储每一行的星号值，同时使用全局变量控制图案的总行数。对比全局变量与局部变量的访问、修改规则，通过循环调用函数生成不同大小图案，理解变量作用域。',
      knowledgePoints: ['函数封装', '全局变量', '局部变量', '变量作用域', '循环'],
      difficulty: 'easy',
      estimatedTime: '1.5小时',
      tasks: [
        '封装打印三角形函数',
        '封装打印正方形函数',
        '使用全局变量控制图案大小',
        '理解变量作用域差异',
        '支持自定义图案字符'
      ]
    },
    {
      id: 504,
      chapter: 5,
      chapterName: '函数基础',
      title: '彩色螺旋图（综合大实战）',
      summary: '综合运用函数全部知识绘制彩色螺旋图案',
      description: '融合本章全部函数知识点，包含函数定义与调用、多种参数类型、嵌套函数、递归函数、全局/局部变量等。将绘图相关功能封装为多个函数，使用turtle库绘制彩色螺旋图案，通过参数控制图形尺寸、默认参数预设颜色、关键字参数控制旋转角度、可变参数接收多颜色值，使用嵌套函数组织绘图逻辑，递归函数生成螺旋层数。',
      knowledgePoints: ['函数嵌套', '递归函数', 'turtle绘图', '参数综合运用', '函数装饰器基础'],
      difficulty: 'hard',
      estimatedTime: '4小时',
      tasks: [
        '安装并导入turtle绘图库',
        '封装多个绘图函数',
        '实现递归螺旋算法',
        '支持自定义颜色和形状',
        '生成完整的彩色螺旋图'
      ]
    },
    // Chapter 6: 正则表达式
    {
      id: 601,
      chapter: 6,
      chapterName: '正则表达式',
      title: '手机号验证',
      summary: '使用正则表达式验证手机号码格式',
      description: '围绕正则表达式语法、匹配元字符、限定符、re模块match/search/findall方法设计。要求编写规范的正则表达式匹配手机号格式（1开头11位数字），对比match从字符串开始匹配与search全文搜索的差异，使用findall批量提取文本中的全部手机号，封装为验证函数，对合法/不合法号码分别给出提示。',
      knowledgePoints: ['正则表达式语法', '元字符', 're.match', 're.search', 're.findall'],
      difficulty: 'medium',
      estimatedTime: '2小时',
      tasks: [
        '编写手机号正则表达式',
        '实现手机号格式验证函数',
        '对比match和search的区别',
        '批量提取文本中的手机号',
        '添加详细的错误提示'
      ]
    },
    {
      id: 602,
      chapter: 6,
      chapterName: '正则表达式',
      title: '用户注册验证系统（综合实战）',
      summary: '综合运用正则表达式实现注册信息校验',
      description: '综合运用正则表达式全部语法和re模块全部常用方法，模拟网站注册校验场景。设计多个正则表达式分别校验用户名（字母开头、含数字）、密码（长度和字符类型）、邮箱格式，使用search判断是否包含违规字符，match验证格式合法性，findall提取用户名中的字母和数字计数，分支判断输出每个字段的校验结果。',
      knowledgePoints: ['正则表达式综合', 're模块全部方法', '字符串校验', '分支判断'],
      difficulty: 'hard',
      estimatedTime: '3小时',
      tasks: [
        '编写用户名格式正则（字母开头+数字）',
        '编写密码强度正则',
        '编写邮箱格式正则',
        '逐字段输出校验结果',
        '汇总所有校验结果'
      ]
    },
    // Chapter 7: 面向对象编程
    {
      id: 701,
      chapter: 7,
      chapterName: '面向对象编程',
      title: '商品信息管理',
      summary: '使用类和对象管理商品信息',
      description: '围绕类的构造方法、公有属性、私有属性、魔法方法等知识点设计。定义商品类，在构造方法__init__中定义商品名称、单价、库存等实例属性，将商品成本价设为私有属性、折扣计算逻辑封装为私有方法，重写__str__魔法方法实现商品信息格式化输出，实例化多个商品对象并调用方法展示信息。',
      knowledgePoints: ['类定义', '__init__构造方法', '实例属性', '私有属性', '__str__魔法方法'],
      difficulty: 'medium',
      estimatedTime: '2.5小时',
      tasks: [
        '定义商品类（Product）',
        '使用__init__初始化属性',
        '封装私有属性和私有方法',
        '重写__str__格式化输出',
        '创建多个商品实例并展示'
      ]
    },
    {
      id: 702,
      chapter: 7,
      chapterName: '面向对象编程',
      title: '英雄游戏对战（综合实战）',
      summary: '综合运用继承、多态、方法重写实现游戏对战',
      description: '融合全章面向对象知识，定义英雄基类，通过单继承、多重继承派生战士、法师、刺客等子类，重写父类攻击方法实现不同职业的攻击行为，使用私有方法封装角色伤害计算逻辑，使用__init__和__repr__魔法方法完成对象初始化和信息展示，实例化英雄对象进行对战，调用继承和重写的方法实现攻击、受伤和胜负判定。',
      knowledgePoints: ['继承', '多重继承', '方法重写', '多态', '私有成员', '魔法方法'],
      difficulty: 'hard',
      estimatedTime: '4小时',
      tasks: [
        '设计英雄基类（Hero）',
        '派生战士、法师、刺客子类',
        '重写攻击方法实现不同行为',
        '封装伤害计算逻辑',
        '实现完整对战流程和胜负判定'
      ]
    },
    // Chapter 8: 文件与目录操作
    {
      id: 801,
      chapter: 8,
      chapterName: '文件与目录操作',
      title: 'Excel表格创建',
      summary: '使用文件操作创建和读写数据文件',
      description: '围绕文件操作基本方法（打开、读取、写入、关闭）和字节流读写逻辑展开。使用原生文件操作创建表格数据文件，实现Excel表格数据的读取、字段提取、数据修改和保存，练习不同打开模式（r/w/a/r+/w+）的应用场景，掌握文件指针、资源自动释放等文件操作要点。',
      knowledgePoints: ['文件打开模式', '文件读写', 'with语句', '字节流', '文件指针'],
      difficulty: 'medium',
      estimatedTime: '2小时',
      tasks: [
        '使用不同模式打开文件',
        '读取表格数据并解析字段',
        '修改数据并保存',
        '使用with语句自动管理资源',
        '对比文本与二进制模式差异'
      ]
    },
    {
      id: 802,
      chapter: 8,
      chapterName: '文件与目录操作',
      title: '作业统计系统',
      summary: '综合运用文件和目录操作实现作业管理',
      description: '综合CSV/JSON文件读写、os/shutil/pathlib目录管理模块知识。自动遍历指定班级作业文件夹，识别CSV和JSON格式作业文件，提取学生姓名和作业完成状态，使用os获取文件路径，shutil迁移未提交作业文件，pathlib统一处理路径，创建统计结果文件，将未完成作业的学生信息写入CSV文档。',
      knowledgePoints: ['CSV读写', 'JSON读写', 'os模块', 'shutil模块', 'pathlib'],
      difficulty: 'hard',
      estimatedTime: '3.5小时',
      tasks: [
        '遍历作业文件夹',
        '识别CSV和JSON格式文件',
        '提取作业完成状态',
        '统计未提交名单',
        '生成统计报告文件'
      ]
    },
    {
      id: 803,
      chapter: 8,
      chapterName: '文件与目录操作',
      title: '数据提取与转换（综合实战）',
      summary: '多格式文件数据提取、清洗与格式转换',
      description: '融合本章全部文件和目录操作知识点，支持遍历多层目录、读取文本/CSV/JSON/Excel等多种文件。使用原生文件语法读取文本数据，通过csv/json标准库解析结构化数据，使用os/pathlib/shutil进行路径拼接、文件查找、移动归档等操作。实现从不同格式文件中提取学生成绩和人员信息，统一清洗数据后批量转换为CSV和JSON文件。',
      knowledgePoints: ['多格式文件读写', 'os/pathlib/shutil', '数据清洗', '格式转换', '批量处理'],
      difficulty: 'hard',
      estimatedTime: '4小时',
      tasks: [
        '遍历多层目录结构',
        '读取多种格式文件',
        '统一清洗提取的数据',
        '批量转换为CSV和JSON',
        '自动归档处理后的文件'
      ]
    },
    // Chapter 9: 网页基础HTML/CSS
    {
      id: 901,
      chapter: 9,
      chapterName: '网页基础HTML/CSS',
      title: '移动App原型图设计',
      summary: '使用Axure RP设计移动App页面原型',
      description: '基于本章页面结构搭建、UI设计规范、AxureRP交互设计全部知识点。遵循UI设计基本原则和统一视觉规范，使用AxureRP设计移动学习App全部页面原型。先构建页面结构，创建项目画布、设置屏幕尺寸，使用矩形、文本、图片、按钮等基础元件搭建页面框架，包含底部导航栏及四个主页面，规范统一字体、颜色、间距、按钮尺寸等UI样式。',
      knowledgePoints: ['UI设计规范', 'AxureRP使用', '页面结构', '交互设计', '原型设计'],
      difficulty: 'medium',
      estimatedTime: '3小时',
      tasks: [
        '设计App整体信息架构',
        '创建底部导航栏框架',
        '设计4个主要页面原型',
        '添加页面交互效果',
        '导出交互原型演示'
      ]
    },
    // Chapter 10: 爬虫基础
    {
      id: 1001,
      chapter: 10,
      chapterName: '爬虫基础',
      title: '登录页面HTML实现',
      summary: '使用HTML+CSS构建登录页面',
      description: '围绕HTML5标签与属性、CSS3选择器与样式、盒模型与布局定位等基础知识。使用语义化标签构建登录页面结构，包含输入框、按钮、图片等元素，精准使用CSS选择器匹配页面元素，设置字体、颜色、间距、阴影等样式美化界面，使用标准盒模型控制页面元素大小、排版和定位。',
      knowledgePoints: ['HTML5标签', 'CSS3选择器', '盒模型', '布局定位', '样式美化'],
      difficulty: 'easy',
      estimatedTime: '2小时',
      tasks: [
        '使用HTML5语义标签搭建结构',
        '设计登录表单（用户名+密码）',
        'CSS美化表单和按钮样式',
        '实现响应式布局',
        '添加表单验证提示'
      ]
    },
    {
      id: 1002,
      chapter: 10,
      chapterName: '爬虫基础',
      title: '学生成绩可视化大屏（综合实战）',
      summary: 'HTML+CSS+ECharts数据可视化综合项目',
      description: '融合HTML结构搭建、CSS高级样式、CSS3 2D变换与动画、ECharts数据可视化全章知识点。使用HTML搭建成绩展示页面框架，通过CSS进行页面布局、卡片样式和动画效果，使用transform/transition/animation实现按钮悬停和数据卡片交互动效，引入ECharts图表库，读取学生各科成绩数据，绘制柱状图和折线图展示各科分数分布。',
      knowledgePoints: ['HTML页面结构', 'CSS高级样式', 'CSS3动画', 'ECharts可视化', '数据图'],
      difficulty: 'hard',
      estimatedTime: '4小时',
      tasks: [
        '搭建成绩展示页面HTML结构',
        '使用CSS Grid/Flexbox布局',
        '添加CSS3过渡和动画效果',
        '引入ECharts绘制柱状图',
        '绘制折线图展示成绩趋势'
      ]
    },
    // Chapter 11: 爬虫进阶
    {
      id: 1101,
      chapter: 11,
      chapterName: '爬虫进阶',
      title: '爬取网上书店教材信息',
      summary: '使用requests+XPath爬取网页数据',
      description: '涵盖请求方法设计、requests/urllib网页请求库、开发者工具分析页面结构、XPath语法节点定位等知识点。先使用浏览器开发者工具分析目标网页HTML结构和教材名称、作者、价格等关键信息对应的节点路径，使用requests携带请求头向目标网页发起请求获取源码，使用XPath语法定位并批量提取教材信息。',
      knowledgePoints: ['requests库', 'HTTP请求头', 'XPath语法', '开发者工具', '数据提取'],
      difficulty: 'medium',
      estimatedTime: '3小时',
      tasks: [
        '使用开发者工具分析页面结构',
        '编写XPath提取规则',
        '使用requests发送HTTP请求',
        '批量提取教材信息',
        '规范输出提取的数据'
      ]
    },
    {
      id: 1102,
      chapter: 11,
      chapterName: '爬虫进阶',
      title: '爬取网络小说数据',
      summary: '使用BeautifulSoup4解析HTML并爬取小说',
      description: '围绕网页获取、页面结构分析和BeautifulSoup4解析展开。使用requests获取小说章节列表页源码，通过开发者工具分析页面结构和章节链接的DOM节点特征，使用BeautifulSoup4构建文档对象、进行节点查找和筛选，提取章节标题和阅读链接，循环进入各章节页面抓取正文内容并保存到本地文件。',
      knowledgePoints: ['BeautifulSoup4', 'DOM解析', '节点筛选', '多页爬取', '数据保存'],
      difficulty: 'medium',
      estimatedTime: '3小时',
      tasks: [
        '分析小说网站页面结构',
        '使用BS4解析章节列表',
        '循环爬取各章节正文',
        '保存小说到本地文件',
        '添加爬取进度和异常处理'
      ]
    },
    {
      id: 1103,
      chapter: 11,
      chapterName: '爬虫进阶',
      title: '批量图片资源下载（综合实战）',
      summary: '综合运用多种解析方式批量下载图片',
      description: '融合本章全部网页抓取和页面解析知识点。综合使用urllib和requests两种库分别设置请求头和超时等参数获取图片网页源码，使用开发者工具分析图片标签结构，灵活选择XPath和BeautifulSoup4两种解析方式定位图片链接，批量提取全部图片链接后循环下载图片资源写入本地文件，自动创建分类文件夹存储。',
      knowledgePoints: ['urllib/requests', 'XPath/BS4对比', '图片下载', '批量处理', '文件管理'],
      difficulty: 'hard',
      estimatedTime: '4小时',
      tasks: [
        '分析图片网站页面结构',
        '使用XPath或BS4提取图片链接',
        '批量下载图片到本地',
        '自动创建分类文件夹',
        '添加下载进度显示'
      ]
    },
    // Chapter 12: 数据存储
    {
      id: 1201,
      chapter: 12,
      chapterName: '数据存储',
      title: '编程网站排行榜',
      summary: '多格式数据存储与网页展示综合项目',
      description: '融合本章多格式文件存储、JSON数据解析和网页展示全部知识点。爬取或手动收集编程网站排名数据，分别用TXT、CSV、JSON三种格式存储，练习文本文件读写、CSV行列结构存储、JSON序列化存储的不同实现方式。读取JSON文件解析嵌套数据，使用HTML搭建展示页面，配合CSS美化样式，将排行榜数据渲染为网页。',
      knowledgePoints: ['TXT/CSV/JSON存储', 'JSON解析', 'HTML展示', 'CSS美化', '数据可视化'],
      difficulty: 'medium',
      estimatedTime: '3小时',
      tasks: [
        '收集编程网站排名数据',
        '分别用TXT、CSV、JSON存储',
        '解析JSON嵌套数据',
        '搭建HTML展示页面',
        'CSS美化排行榜样式'
      ]
    }
  ],

  中级: [
    // Chapter 1: 数据库基础
    {
      id: 2001,
      chapter: 1,
      chapterName: '数据库基础',
      title: '使用MySQLdb实现学生信息管理',
      summary: 'MySQL数据库+Python连接实现完整CRUD',
      description: '覆盖关系型数据库核心概念、MySQL安装配置、Navicat可视化管理、字段类型与约束、数据库与数据表增删改查、高级逻辑查询、Python对接MySQL全章知识点。使用MySQL创建学生数据库和信息表，设置字段类型和约束，通过SQL实现数据操作，安装MySQLdb模块编写Python代码连接数据库，封装学生信息增删改查全套功能。',
      knowledgePoints: ['MySQL安装配置', 'SQL语句', '字段类型与约束', 'MySQLdb模块', 'CRUD操作'],
      difficulty: 'medium',
      estimatedTime: '4小时',
      tasks: [
        '安装配置MySQL数据库',
        '创建学生信息数据库和表',
        '编写SQL增删改查语句',
        '使用Python连接MySQL',
        '封装完整的CRUD功能模块'
      ]
    },
    // Chapter 2: 非关系型数据库
    {
      id: 2002,
      chapter: 2,
      chapterName: '非关系型数据库',
      title: '使用pymongo实现学生信息管理',
      summary: 'MongoDB文档数据库+Python操作',
      description: '覆盖非关系型数据库核心概念、MongoDB安装配置、Navicat可视化管理、数据库/集合/文档增删改查、pymongo模块对接等知识点。搭建MongoDB环境，创建学生数据库和信息集合（文档型），通过pymongo编写Python代码连接数据库，封装功能函数实现学生信息录入、按班级查询、更新成绩、删除毕业学生记录、统计班级人数等业务逻辑。',
      knowledgePoints: ['MongoDB安装', '文档数据库', '集合操作', 'pymongo', 'CRUD'],
      difficulty: 'medium',
      estimatedTime: '3.5小时',
      tasks: [
        '安装配置MongoDB',
        '创建数据库和文档集合',
        '使用pymongo连接MongoDB',
        '实现学生信息CRUD操作',
        '对比MySQL与MongoDB差异'
      ]
    },
    {
      id: 2003,
      chapter: 2,
      chapterName: '非关系型数据库',
      title: '使用Redis实现用户注册与登录',
      summary: 'Redis内存数据库+Python实现用户系统',
      description: '覆盖Redis数据库安装、五种核心数据结构（String/Hash/List/Set/Sorted Set）、Redis命令行操作、Python redis客户端等知识点。使用Hash结构存储用户账号、密码、昵称等属性信息，String记录登录状态，Set存储已注册用户集合。实现注册查重、账号密码匹配登录、登录状态保存、注销等完整流程。',
      knowledgePoints: ['Redis安装', '五种数据结构', 'redis-py', 'Hash存储', '用户系统'],
      difficulty: 'medium',
      estimatedTime: '3.5小时',
      tasks: [
        '安装配置Redis',
        '使用Hash存储用户信息',
        '使用Set实现注册查重',
        '使用String管理登录状态',
        '实现完整的注册登录流程'
      ]
    },
    // Chapter 3: Django框架
    {
      id: 2004,
      chapter: 3,
      chapterName: 'Django框架',
      title: '自定义中间件实现访问日志',
      summary: 'Django中间件机制与自定义中间件开发',
      description: '围绕Django中间件知识点设计，熟悉Django自带中间件执行机制、中间件执行顺序和生命周期，编写自定义中间件并完成注册激活流程。针对前后端分离常见问题，封装跨域访问中间件，在项目settings文件中完成中间件注册，使前端页面发起的请求通过中间件验证生效，掌握中间件执行流程和自定义配置方法。',
      knowledgePoints: ['Django中间件', '中间件执行顺序', '自定义中间件', 'CORS跨域', 'settings配置'],
      difficulty: 'medium',
      estimatedTime: '3小时',
      tasks: [
        '理解Django中间件执行流程',
        '编写自定义中间件类',
        '在settings中注册中间件',
        '实现访问日志记录功能',
        '测试中间件执行效果'
      ]
    },
    {
      id: 2005,
      chapter: 3,
      chapterName: 'Django框架',
      title: '学生信息管理系统（Django综合大项目）',
      summary: '使用Django全栈框架构建完整Web管理系统',
      description: '融合Django全套核心知识点，包括框架安装与项目创建、MTV分层架构、ORM模型映射与数据库增删改查、模型继承、GET/POST请求处理、视图函数与响应、路由分发与反向解析、Admin后台管理、自定义中间件、Cookie/Session登录状态存储、RESTful接口规范。从零搭建学生课程成绩管理系统，使用ORM创建学生、课程、成绩数据表，通过路由分发编写视图函数处理业务逻辑，使用Session实现管理员登录状态校验，Template模板渲染前端页面，Admin快速维护后台数据，遵循RESTful规范编写API接口。',
      knowledgePoints: ['Django MTV架构', 'ORM模型', '路由分发', '视图函数', 'Session', 'Admin', 'RESTful API'],
      difficulty: 'hard',
      estimatedTime: '8小时',
      tasks: [
        '创建Django项目和APP',
        '设计ORM模型（学生/课程/成绩）',
        '编写视图和路由',
        '使用Session实现登录',
        '开发RESTful API接口',
        '使用Admin管理后台数据'
      ]
    },
    // Chapter 4: Selenium自动化
    {
      id: 2006,
      chapter: 4,
      chapterName: 'Selenium自动化',
      title: '使用Selenium抓取电商网站商品数据',
      summary: 'Selenium浏览器自动化+多线程高效爬取',
      description: '覆盖Selenium环境搭建、浏览器驱动配置、页面元素定位（id/xpath/css选择器）、页面交互操作、多线程并行处理等知识点。搭建Selenium自动化环境并配置浏览器驱动，使用多种定位方式定位商品页面元素，模拟用户浏览行为（滚动翻页、输入关键词、点击搜索等），提取商品名称、价格、图片链接等数据。引入多线程模块编写多线程任务，开启多线程并行爬取多页商品数据。',
      knowledgePoints: ['Selenium', '元素定位', '页面交互', '多线程', '数据爬取'],
      difficulty: 'hard',
      estimatedTime: '5小时',
      tasks: [
        '安装配置Selenium和浏览器驱动',
        '使用多种方式定位页面元素',
        '模拟用户浏览和搜索行为',
        '提取商品数据',
        '实现多线程并行爬取'
      ]
    },
    // Chapter 5: 爬虫原理与实战
    {
      id: 2007,
      chapter: 5,
      chapterName: '爬虫原理与实战',
      title: '使用Scrapy爬取电影票信息',
      summary: 'Scrapy框架全流程开发电影票数据爬虫',
      description: '覆盖Scrapy框架全部知识点，包括底层原理、框架架构、环境安装、项目创建流程。新建Scrapy爬虫项目，编写Spider定义爬取逻辑，使用XPath和CSS选择器解析页面，提取电影票编码、名称、票价、评分等数据。自定义Item规范封装爬取字段，编写Item Pipeline分别实现数据写入本地CSV文件和同步到MySQL数据库的持久化方案。配置中间件添加请求头和延时策略反反爬。',
      knowledgePoints: ['Scrapy框架', 'Spider', 'XPath/CSS', 'Item Pipeline', '数据持久化', '中间件'],
      difficulty: 'hard',
      estimatedTime: '5小时',
      tasks: [
        '安装Scrapy并创建项目',
        '编写Spider爬虫逻辑',
        '使用XPath/CSS提取数据',
        '自定义Item封装字段',
        '编写Pipeline存储到CSV和MySQL'
      ]
    },
    // Chapter 6: 分布式爬虫
    {
      id: 2008,
      chapter: 6,
      chapterName: '分布式爬虫',
      title: '分布式爬取电商网站图书数据',
      summary: 'Scrapy-Redis分布式爬虫实战',
      description: '覆盖分布式爬虫原理、Scrapy-redis框架架构与安装、分布式爬虫项目搭建、Redis共享队列、去重机制与断点续爬等知识点。搭建Scrapy-redis分布式环境并配置Redis服务器，创建分布式爬虫项目，继承RedisSpider实现共享请求队列，修改settings文件配置Redis连接地址、去重类和调度器。使用XPath/CSS提取图书名称、作者、价格等数据，通过Redis实现多节点并行爬取和请求指纹去重，通过Pipeline将数据批量写入MySQL。',
      knowledgePoints: ['Scrapy-redis', 'Redis共享队列', '分布式爬取', '去重机制', '断点续爬'],
      difficulty: 'hard',
      estimatedTime: '6小时',
      tasks: [
        '搭建Redis和Scrapy-redis环境',
        '创建分布式爬虫项目',
        '配置Redis共享请求队列',
        '实现多节点并行爬取',
        '实现去重和断点续爬'
      ]
    }
  ],

  高级: [
    // Chapter 1: NumPy科学计算库
    {
      id: 3001,
      chapter: 1,
      chapterName: 'NumPy科学计算库',
      title: '学生成绩数据计算与分析',
      summary: '使用NumPy进行大规模数组运算和统计分析',
      description: '覆盖NumPy安装配置、数组创建与属性、索引与切片、数学运算、通用函数、字符串函数等全章知识点。以班级多科考试成绩为业务场景，使用NumPy创建二维数组存储多名学生的多学科分数，通过数组索引和切片灵活提取学生成绩、全班成绩、单字段分片。使用算术运算和通用函数实现总分、平均分、最高分、最低分等统计指标计算，使用字符串函数处理学生姓名和班级信息。',
      knowledgePoints: ['NumPy数组', '索引切片', '数学运算', '通用函数', '统计分析'],
      difficulty: 'medium',
      estimatedTime: '4小时',
      tasks: [
        '安装NumPy并创建成绩数组',
        '使用切片提取不同维度数据',
        '计算各类统计指标',
        '使用通用函数批量处理',
        '对比NumPy与传统循环的效率'
      ]
    },
    // Chapter 2: Pandas数据操作
    {
      id: 3002,
      chapter: 2,
      chapterName: 'Pandas数据操作',
      title: '班级学生成绩数据分析系统',
      summary: '使用Pandas进行数据读取、处理和分析',
      description: '覆盖Pandas安装、Series一维序列操作、DataFrame二维表格操作、文件读写、数据筛选与排序、聚合统计等全章知识点。以全班学生多科成绩为分析对象，使用Series分别构建学生姓名和各科分数一维序列，将多个Series组装为DataFrame。实现CSV文件读写、字段增删、行列筛选、按条件查询学生记录。按总分或单科分数排序，对全班总分自动排名并处理同分情况。',
      knowledgePoints: ['Pandas安装', 'Series', 'DataFrame', '文件读写', '数据筛选', '排序排名'],
      difficulty: 'medium',
      estimatedTime: '4小时',
      tasks: [
        '使用Series和DataFrame构建成绩表',
        '实现CSV文件读写',
        '按条件筛选学生记录',
        '自动排名并处理并列',
        '生成数据分析报告'
      ]
    },
    // Chapter 3: 数据处理与清洗
    {
      id: 3003,
      chapter: 3,
      chapterName: '数据处理与清洗',
      title: '多班级考试成绩数据清洗处理平台',
      summary: '完整的数据预处理、清洗、聚合和合并流程',
      description: '覆盖数据清洗全流程：缺失值处理、重复值删除、异常值过滤、数据类型转换、数据分组聚合、数据透视与位移、多表合并等。以多班级多科目考试成绩数据集为对象，执行完整数据预处理：检测并处理缺失值、删除重复学生记录、过滤异常分数、统一班级文本格式。使用分组聚合按班级和科目计算平均分、最高分、及格率等指标，使用数据透视和位移实现分科排名和成绩波动对比，使用多表合并整合学生信息与成绩数据。',
      knowledgePoints: ['缺失值处理', '重复值删除', '异常值过滤', '分组聚合', '数据透视', '多表合并'],
      difficulty: 'hard',
      estimatedTime: '5小时',
      tasks: [
        '检测并处理缺失值',
        '删除重复和异常记录',
        '按班级和科目分组聚合',
        '使用数据透视分析排名',
        '合并多表数据源'
      ]
    },
    // Chapter 4: 数据可视化
    {
      id: 3004,
      chapter: 4,
      chapterName: '数据可视化',
      title: '班级成绩综合可视化大屏',
      summary: '使用Matplotlib和Seaborn创建专业数据图表',
      description: '覆盖数据可视化核心概念、Matplotlib基础图表绘制、Seaborn统计图表、可视化布局与配色等全章知识点。基于前面清洗完成的学生成绩数据集，使用Matplotlib绘制柱状图展示各科平均分、饼图展示各科不及格与优秀人数占比、散点图分析两科成绩相关性。使用Seaborn绘制箱线图查看各科分数离散程度、热力图展示科目间相关性、分组柱状图对比男女学生成绩差异。',
      knowledgePoints: ['Matplotlib', '柱状图/饼图/散点图', 'Seaborn', '箱线图/热力图', '图表美化'],
      difficulty: 'medium',
      estimatedTime: '4小时',
      tasks: [
        '使用Matplotlib绘制基础图表',
        '绘制散点图分析成绩相关性',
        '使用Seaborn绘制箱线图',
        '绘制热力图展示科目关联',
        '美化图表并导出可视化报告'
      ]
    },
    // Chapter 5: 数据分析
    {
      id: 3005,
      chapter: 5,
      chapterName: '数据分析',
      title: '学科成绩综合数据分析系统',
      summary: '描述统计、相关性分析、分布分析、多维度对比',
      description: '覆盖数据分析完整流程：描述性统计（均值/中位数/标准差/方差）、协方差与相关性分析、直方图分布分析、多维度对比分析。以全校多班级多科学生成绩数据集为对象，计算各科描述统计指标，通过协方差和相关性分析评估不同科目间的同步变化程度。绘制直方图展示各科成绩分布形态（集中/偏态/分化），从性别、班级、年级等多维度对比分析成绩差异。',
      knowledgePoints: ['描述统计', '协方差', '相关性分析', '分布分析', '多维度对比'],
      difficulty: 'hard',
      estimatedTime: '5小时',
      tasks: [
        '计算各科描述统计指标',
        '分析科目间协方差和相关性',
        '绘制成绩分布直方图',
        '多维度对比分析（性别/班级）',
        '撰写数据分析报告'
      ]
    },
    // Chapter 6: 机器学习
    {
      id: 3006,
      chapter: 6,
      chapterName: '机器学习',
      title: '学生成绩智能建模与学习评估平台',
      summary: '使用Scikit-Learn实现回归、分类和聚类建模',
      description: '覆盖机器学习核心概念、Scikit-Learn库安装配置、回归建模、分类建模、聚类建模等全章知识点。回归建模：以数学成绩为自变量、其他科目为因变量构建线性回归模型；分类建模：以各科分数区间为特征、学生等级为标签训练逻辑回归分类模型；聚类建模：提取多科成绩特征使用K-Means无监督算法自动将学生分为不同学习水平群体。对比监督学习与无监督学习的应用场景。',
      knowledgePoints: ['Scikit-Learn', '线性回归', '逻辑回归', 'K-Means聚类', '模型评估'],
      difficulty: 'hard',
      estimatedTime: '6小时',
      tasks: [
        '构建线性回归模型预测成绩',
        '训练逻辑回归分类模型',
        '使用K-Means聚类学生群体',
        '评估各模型准确率和效果',
        '对比不同算法的适用场景'
      ]
    },
    // Chapter 7: 深度学习
    {
      id: 3007,
      chapter: 7,
      chapterName: '深度学习',
      title: '基于Keras的学生成绩等级预测神经网络模型',
      summary: '使用TensorFlow/Keras构建全连接神经网络',
      description: '覆盖人工神经网络原理、Keras深度学习框架搭建与训练等知识点。理解神经网络基本结构（神经元/激活函数/反向传播/训练流程），安装配置TensorFlow和Keras。以学生多科成绩为输入特征、成绩等级（优秀/良好/中等/及格）为分类标签，构建全连接神经网络（输入层→隐藏层→输出层），配置激活函数、损失函数和优化器，划分训练集和验证集进行模型训练，评估准确率并与传统机器学习模型对比。',
      knowledgePoints: ['神经网络原理', 'TensorFlow/Keras', '全连接网络', '激活函数', '模型训练'],
      difficulty: 'hard',
      estimatedTime: '6小时',
      tasks: [
        '安装TensorFlow和Keras',
        '构建全连接神经网络',
        '数据预处理和标准化',
        '训练模型并绘制训练曲线',
        '评估并对比传统ML模型'
      ]
    },
    // Chapter 8: 推荐算法
    {
      id: 3008,
      chapter: 8,
      chapterName: '推荐算法',
      title: '图书个性化推荐系统',
      summary: '实现基于协同过滤的图书推荐算法',
      description: '覆盖协同过滤核心原理、基于用户的协同过滤、基于物品的协同过滤等知识点。以用户图书评分数据集为基础，实现两种推荐策略：基于用户的协同过滤——通过余弦相似度计算用户兴趣相似度，找到与目标用户偏好相近的邻居用户，提取邻居用户高评分但目标用户未读的书籍作为推荐；基于物品的协同过滤——计算图书间相似度，根据用户已读高评分书籍匹配同类图书进行推荐。封装两种推荐算法函数，支持输入用户ID一键获得推荐书单。',
      knowledgePoints: ['协同过滤', '用户相似度', '物品相似度', '余弦相似度', '推荐系统'],
      difficulty: 'hard',
      estimatedTime: '5小时',
      tasks: [
        '构建用户-图书评分矩阵',
        '实现基于用户的协同过滤',
        '实现基于物品的协同过滤',
        '对比两种推荐策略效果',
        '封装为一键推荐函数'
      ]
    }
  ]
}

export default projects
