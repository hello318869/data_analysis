# 项目经理完整行动手册 — 交互式数据分析系统

> **对应计划文件**：`data-analysis-system.md`
> **适用角色**：项目经理（PM）
> **项目周期**：4 周 | **团队**：5-6 人 | **难度**：Python 初学者入门级

---

## 一、PM 职责总览

项目经理在本项目中承担**两条线**：

| 线 | 职责 | 时间占比 |
|----|------|---------|
| **管理线** | 进度统筹、Git 管理、接口契约、站会、Review、文档整合、答辩准备 | ~50% |
| **技术线** | 数据库设计（MySQL 建表 + ORM 模型）、用户认证模块（注册/登录/登出）、历史记录功能（扩展） | ~50% |

---

## 二、前置准备（项目启动前 1-2 天）

### 2.1 工具注册

- [ ] 注册/登录 [GitHub](https://github.com) 或 [Gitee](https://gitee.com)
- [ ] 安装 [Git](https://git-scm.com/) + 配置用户名和邮箱
- [ ] 安装 [Python 3.10+](https://www.python.org/downloads/)
- [ ] 安装 [MySQL 8.0+](https://dev.mysql.com/downloads/mysql/)
- [ ] 安装 [VS Code](https://code.visualstudio.com/)（推荐，团队统一编辑器）
- [ ] 注册腾讯文档 / 飞书文档（用于共享接口契约和进度看板）

### 2.2 知识储备（提前 3 天自学）

| 内容 | 预计时间 | 资源 |
|------|---------|------|
| Git 基础：clone / commit / push / pull / branch / merge | 2 小时 | [Git 简明指南](https://rogerdudler.github.io/git-guide/index.zh.html) |
| FastAPI 项目结构 + 路由基础 | 2 小时 | [FastAPI 官方教程](https://fastapi.tiangolo.com/zh/tutorial/) 前 5 章 |
| SQLAlchemy ORM 基础（定义模型 + CRUD） | 2 小时 | [SQLAlchemy 1.4 教程](https://docs.sqlalchemy.org/en/14/orm/tutorial.html) |
| MySQL 建库建表基本语法 | 1 小时 | [MySQL CREATE TABLE 文档](https://dev.mysql.com/doc/refman/8.0/en/create-table.html) |
| bcrypt 密码哈希原理 | 30 分钟 | 知道 `hashpw` / `checkpw` 两个函数即可 |

---

## 三、Week 1：环境搭建 + 骨架 + 接口契约（第 1-7 天）

---

### Day 1：团队启动

| 序号 | 动作 | 具体操作 | 产出物 |
|------|------|---------|--------|
| 1 | 建群 | 创建微信群/飞书群，拉入全部 5-6 人。群公告写：项目名「交互式数据分析系统」、时间线「4 周」、Git 仓库地址 | 群聊就绪 |
| 2 | 发计划 | 将 `data-analysis-system.md` 文件发到群里，要求每人通读全篇，标记自己看不懂的地方 | 全员对齐 |
| 3 | 建仓库 | 在 GitHub/Gitee 创建新仓库 `data-analysis-system`，勾选 `Add a README file`，设置 `main` 分支保护规则：`Require a pull request before merging` + `Require approvals (1)` | 仓库就绪 |
| 4 | 拉人 | 在仓库 Settings → Collaborators 中，输入每人 GitHub 用户名/Gitee 账号，发送邀请 | 权限分配 |
| 5 | 通讯录 | 新建腾讯文档「团队成员信息表」，表头：`姓名 | GitHub 账号 | 角色 | 微信/手机 | 技术基础自评 (1-5)`，发群里要求填写 | 通讯录 |

**Day 1 检查清单**：
```
□ 群建好了，所有人都在
□ 仓库建好了，main 分支保护已开
□ 邀请已发送，每人能 clone 到本地
□ 文档已发，每人已读
□ 通讯录表格已建，等待填写
```

---

### Day 2：角色分工确认会（30 分钟）

| 序号 | 动作 | 具体操作 | 产出物 |
|------|------|---------|--------|
| 1 | 开会 | 腾讯会议/微信群语音，30 分钟 | — |
| 2 | 摸底 | 每人 2 分钟自我介绍：用过 Python 吗？写过网页吗？Git 熟悉吗？自己想做什么模块？ | 能力画像 |
| 3 | 定角色 | 参考文档第三章的 6 个角色模板，结合摸底结果分配。原则：最弱的人搭配你（PM）或最强的人 | 角色定板 |

**角色分配模板**（直接复制到群里填空）：
```
项目经理（1人）：__________  → 数据库 + 用户认证 + 整体统筹
后端 A - 数据管理（1人）：__________  → 文件上传 + 数据预览
后端 B - 数据清洗（1人）：__________  → 缺失值/异常值 + 自动清洗
算法工程师（1人）：__________  → 线性回归 + 算法对比
可视化工程师（1人）：__________  → Matplotlib 图表 + 参数化
前端工程师（1人）：__________  → 全部 Jinja2 模板 + CSS + JS
[可选] 全栈支持（1人）：__________  → 协助薄弱模块 + 集成测试
```

| 4 | 定站会制度 | 定下每日站会时间（建议每晚 21:00，微信/飞书文字站会，3 句话即可）。通知：从明天正式开始 | 制度建立 |

---

### Day 3：环境核查

| 序号 | 动作 | 具体操作 | 产出物 |
|------|------|---------|--------|
| 1 | 发 checklist | 群发环境验证清单（见下方） | — |
| 2 | 收截图 | 要求每人截图私发你验证 | 环境确认 |
| 3 | 帮扶 | 对没配好的同学，开腾讯会议屏幕共享远程帮忙 | 全员就绪 |
| 4 | 首次推送 | 在本地仓库写一个最小 `main.py`（只有 `print("hello")` 的 FastAPI 骨架），commit + push 到 main | 首次提交 |

**环境验证清单**（复制发群里）：
```
请在终端依次运行以下命令，截图发到群里：

① python --version          → 应显示 3.10 或更高
② pip install fastapi uvicorn pandas matplotlib scikit-learn sqlalchemy pymysql bcrypt jinja2 python-multipart openpyxl
③ pip list | findstr fastapi   → 确认已安装
④ python -c "import pandas; import sklearn; import matplotlib; print('OK')"   → 输出 OK
⑤ mysql --version            → 应显示 8.0 或更高
```

---

### Day 4：接口契约制定 ⭐（最关键的一天）

这是整个项目联调成败的决定性步骤。**契约不写死 = Week 3 联调地狱。**

| 序号 | 动作 | 具体操作 | 产出物 |
|------|------|---------|--------|
| 1 | 建在线文档 | 新建腾讯文档/飞书文档，标题「API 接口契约 - 交互式数据分析系统」 | 文档就位 |
| 2 | 移植接口清单 | 把 `data-analysis-system.md` 第五章的 16 个接口表格全部搬过去 | — |
| 3 | 补充请求示例 | 给每个 POST 接口补充「请求体 JSON 示例」，例如： | 契约详表 |

```json
// POST /clean/execute 请求体示例
{
  "strategy": "mean",
  "columns": ["price", "sqft"],
  "fill_value": null
}
```

```json
// POST /analysis/regression 请求体示例
{
  "features": ["sqft", "bedrooms", "bathrooms"],
  "target": "price"
}
```

```json
// POST /viz/generate 请求体示例
{
  "chart_type": "scatter",
  "x_col": "sqft",
  "y_col": "price",
  "title": "房价与面积关系图",
  "color": "blue"
}
```

| 4 | 补充响应示例 | 给每个接口补充「响应 JSON 示例 / 返回的模板变量」，示例： | — |

```json
// POST /analysis/regression 响应（传给模板的变量）
{
  "r2_score": 0.78,
  "mse": 125000.5,
  "coefficients": {"sqft": 150.2, "bedrooms": 25000.0},
  "intercept": 50000.0,
  "predictions": [
    {"actual": 300000, "predicted": 310500, "sqft": 1800, "bedrooms": 3},
    {"actual": 450000, "predicted": 438200, "sqft": 2200, "bedrooms": 4}
  ],
  "chart_path": "/outputs/charts/regression_scatter_20240526_143022.png"
}
```

| 5 | 定命名规范 | 在文档最前面加一段「命名规范」： | 规范文档 |
| | | - Python 变量/函数：`snake_case` | |
| | | - 数据库表名/列名：`snake_case`，表名复数（`users`, `datasets`） | |
| | | - JSON key：`snake_case` | |
| | | - HTML 表单 name 属性：`snake_case` | |
| | | - 模板变量：`snake_case` | |
| | | - 路由路径：`/noun/verb`，小写，连字符分隔（如 `/data/upload`） | |

| 6 | 发文档 | 把文档链接发群里，要求每人 24h 内看完并对自己的模块标注「✅ 我负责提供 / 🔗 我需要调用 / ❓ 有疑问」 | 依存确认 |

---

### Day 5：代码仓库初始化

| 序号 | 动作 | 具体操作 | 产出物 |
|------|------|---------|--------|
| 1 | 建目录结构 | 在本地仓库按文档第一章 1.4 的目录树创建全部文件夹 | 骨架 |
| 2 | 创空白文件 | 每个 `__init__.py` 都创建（空文件即可），每个 `.py` 文件都创建（写一行 `# TODO: xxx`） | 文件骨架 |
| 3 | 写 `.gitignore` | 内容如下： | gitignore |

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
venv/
.env

# Uploads & outputs
static/uploads/*
outputs/charts/*
!static/uploads/.gitkeep
!outputs/charts/.gitkeep

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

| 4 | 写 README | 根目录 `README.md`，内容： | README |

```markdown
# 交互式数据分析系统

基于 FastAPI + Matplotlib + scikit-learn + MySQL 的 Web 数据分析平台。

## 技术栈

- **后端**：FastAPI + Jinja2
- **数据处理**：Pandas + scikit-learn
- **可视化**：Matplotlib
- **数据库**：MySQL + SQLAlchemy

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
mysql -u root -p < database/init.sql

# 3. 启动应用
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 项目结构

```
data-analysis-system/
├── main.py          # FastAPI 入口
├── models/          # ORM 模型
├── routes/          # 路由
├── services/        # 业务逻辑
├── templates/       # Jinja2 模板
├── static/          # 静态文件
└── database/        # SQL 建表脚本
```
```

| 5 | commit + push | `git add .` → `git commit -m "init: project skeleton with directory structure"` → `git push origin main` | 骨架 commit |

---

### Day 6-7：PM 自己的开发任务（MySQL + 用户认证）

这是你作为 PM 的技术交付物。**你的代码必须先跑通，给团队做榜样。**

#### 6.1 MySQL 数据库初始化

- [ ] 启动 MySQL 服务，用 root 登录
- [ ] 创建数据库：`CREATE DATABASE data_analysis_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
- [ ] 创建数据库用户（可选，生产级做法）：`CREATE USER 'da_user'@'localhost' IDENTIFIED BY 'your_password'; GRANT ALL ON data_analysis_db.* TO 'da_user'@'localhost';`
- [ ] 编写 `database/init.sql`，包含三张表的建表语句（直接从文档 2.7 节抄）
- [ ] 执行：`mysql -u root -p data_analysis_db < database/init.sql`
- [ ] 验证：`SHOW TABLES;` → 看到 `users`, `datasets`, `analysis_records`

#### 6.2 配置文件 `config.py`

```python
# config.py
import os

# 数据库连接
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:your_password@localhost:3306/data_analysis_db"
)

# 文件路径
UPLOAD_DIR = "static/uploads"
OUTPUT_DIR = "outputs/charts"
SAMPLE_DATA = "data/sample_housing.csv"

# 会话密钥（生产环境应从环境变量读取）
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-2024")

# 上传限制（MB）
MAX_UPLOAD_SIZE_MB = 10
```

#### 6.3 ORM 模型

- [ ] `models/__init__.py`：导入 `Base`、`User`、`Dataset`、`AnalysisRecord`
- [ ] `models/user.py`：定义 User 模型（id, username, password_hash, created_at）
- [ ] `models/analysis_record.py`：定义 Dataset 模型 + AnalysisRecord 模型
- [ ] 在 `main.py` 中初始化 SQLAlchemy engine 和 session

#### 6.4 认证服务 `services/auth_service.py`

实现两个核心函数：
- `hash_password(plain: str) -> str`：用 bcrypt 哈希
- `verify_password(plain: str, hashed: str) -> bool`：验证密码

#### 6.5 认证路由 `routes/auth_routes.py`

- [ ] `GET /auth/login` → 返回登录页面
- [ ] `POST /auth/login` → 验证用户名密码 → 写入 session → 重定向首页
- [ ] `GET /auth/register` → 返回注册页面
- [ ] `POST /auth/register` → 校验两次密码一致 → bcrypt 哈希存库 → 重定向登录页
- [ ] `GET /auth/logout` → 清除 session → 重定向首页

#### 6.6 登录/注册模板

- [ ] `templates/login.html`：用户名输入框 + 密码输入框 + 提交按钮 + 错误提示区域
- [ ] `templates/register.html`：用户名 + 密码 + 确认密码 + 提交按钮 + 错误提示区域

#### 6.7 自测

- [ ] 启动 `uvicorn main:app --reload`
- [ ] 浏览器打开 `http://localhost:8000/auth/register`
- [ ] 注册一个新用户 → 检查 MySQL `users` 表是否有记录，密码是否为哈希
- [ ] 用注册的账号登录 → 检查是否跳转到首页
- [ ] 登出 → 检查 session 是否清除

**Day 7 收尾检查**：
```
□ MySQL 数据库正常运行，三张表已创建
□ config.py 就绪，DATABASE_URL 能连上
□ 注册页能打开，能成功注册用户
□ 登录页能打开，能成功登录并跳转
□ 登出功能正常
□ 所有改动已 commit + push 到 main 分支
```

---

## 四、Week 2：并行开发 + 进度管理（第 8-14 天）

---

### 每日例行动作（Day 8-14 每天做）

| 时间 | 动作 | 耗时 |
|------|------|------|
| 09:00 | 查看邮箱/GitHub notifications，处理新的 PR | 5 min |
| 21:00 | 主持站会：每人回答「今天做了什么 / 卡在哪里 / 明天做什么」 | 10 min |
| 会后 | 更新进度看板表（共享文档） | 5 min |
| 随时 | 有新 PR → 24h 内完成 Review | 15-30 min/个 |

### 进度看板模板

在腾讯文档中创建表格，表头如下：

| 模块 | 负责人 | 状态 | 本周目标 | 实际进度 | 卡点/备注 |
|------|--------|------|---------|---------|----------|
| 数据管理 | 后端 A | 🟡 进行中 | 文件上传 API 完成 | 50% | — |
| 数据清洗 | 后端 B | 🟢 已完成 | 清洗页面联调 | 100% | — |
| 可视化 | 可视化 | 🔴 卡住 | 散点图生成 | 20% | 中文乱码待解决 |
| 算法分析 | 算法 | ⚪ 未开始 | 回归 API | 0% | 等数据管理完成 |
| 前端模板 | 前端 | 🟡 进行中 | 4 个页面 | 40% | — |
| 用户认证 | PM | 🟢 已完成 | 登录注册联调 | 100% | — |

---

### Day 8-9：分支创建 + 并行开发启动

| 序号 | 动作 | 具体操作 |
|------|------|---------|
| 1 | 创建 feature 分支 | 在 GitHub 上创建 5 个分支（或让组员自己从 main checkout 创建）： |
| | | `feat/data-management` |
| | | `feat/data-cleaning` |
| | | `feat/ml-analysis` |
| | | `feat/visualization` |
| | | `feat/frontend-templates` |
| 2 | 指定分支 | 私信告知每人对应的分支名 |
| 3 | 确认 checkout | 让每人截图 `git branch` 确认自己在正确的分支上 |
| 4 | 前后端对齐 | 单独找前端同学开 5 分钟小会：告诉他你的认证模块传给模板的变量名是什么（`request`, `error_msg`, `user`），让他做页面时预留这些变量的展示位置 |

### 各角色 Week 2 目标（你作为 PM 需要知道）

| 成员 | Week 2 必须完成 | 检查方式 |
|------|----------------|---------|
| 后端 A | `POST /data/upload` + `GET /data/preview` 能跑通，上传 CSV 后能看到前 10 行表格 | 浏览器操作 |
| 后端 B | `GET /clean` 展示缺失值报告 + `POST /clean/execute` 执行清洗返回结果 | Postman 调接口 |
| 算法 | `POST /analysis/regression` 能训练模型并返回 R² + MSE + 预测值 | Postman 调接口 |
| 可视化 | `POST /viz/generate` 能生成至少一种图表（折线图）并保存为 PNG | 检查 outputs/charts/ 目录 |
| 前端 | `base.html` 布局模板 + `upload.html` + `clean.html` 页面骨架完成 | 浏览器看页面 |

---

### Day 10-12：Code Review + 质量把控

**收到 PR 后的 Review 流程（标准化操作）**：

```
Step 1: 打开 PR 页面，看标题和描述——有没有写清楚改了什么？
        ↓ 不合格 → 评论 "请补充 PR 描述"
        ↓ 合格 ↓

Step 2: 在本地拉取该分支，跑一遍
        git fetch origin
        git checkout feat/xxx
        uvicorn main:app --reload
        ↓ 启动报错 → Request Changes，附上错误日志
        ↓ 能启动 ↓

Step 3: 对着接口契约文档，用浏览器/Postman 调一遍他写的 API
        ↓ 返回格式不符合契约 → Request Changes
        ↓ 符合 ↓

Step 4: 看代码本身，检查 Review 清单（见下方）
        ↓ 有问题 → Comment 具体哪一行 + 建议怎么改
        ↓ 没问题 ↓

Step 5: Approve → Merge → Delete branch → 通知组员 "已合并，请 pull 最新 main"
```

**Review 检查清单**（逐条过）：

```
□ 变量命名清晰吗？（不要出现 a, b, x, temp, data1 这种名字）
□ 有没有 import 了但没用到的包？
□ 有没有 print() 调试代码残留？
□ 有没有硬编码的绝对路径（如 C:/Users/xxx/...）？
□ 文件编码有没有问题？（中文注释是否正常显示）
□ 上传文件有没有做格式校验？（只允许 .csv, .xlsx）
□ 数据库操作有没有 try/except 包裹？
□ 密码有没有明文存储或明文传输？
□ 函数有没有超过 50 行？（超过就建议拆分）
□ 有没有注释解释"为什么这样做"而不是"做了什么"？
```

---

### Day 13-14：中段检查

| 序号 | 动作 | 具体操作 |
|------|------|---------|
| 1 | 拉全量代码 | `git pull origin main`，确保拿到所有人提交的最新代码 |
| 2 | 启动验证 | `uvicorn main:app --reload`，看能不能启动不报错 |
| 3 | 接口逐个测 | 对着契约文档，用 Postman/Browser 逐个调： |
| | | ✓ `GET /` 能返回首页 |
| | | ✓ `POST /data/upload` 上传 CSV 返回预览 |
| | | ✓ `GET /clean` 返回缺失值报告 |
| | | ✓ `POST /clean/execute` 执行清洗返回数据 |
| | | ✓ `POST /viz/generate` 生成图表 |
| | | ✓ `POST /analysis/regression` 返回评估结果 |
| | | ✓ `GET /auth/login` 返回登录页 |
| | | ✓ `POST /auth/register` 注册成功 |
| 4 | 建 Issue | 把跑不通的接口记录为 GitHub Issue，格式： | 
| | | 标题：`[Bug] /clean/execute 返回 500 错误` |
| | | 内容：复现步骤 + 请求体 + 错误截图 |
| | | 指派给对应负责人 + 标签 `bug` |

---

## 五、Week 3：扩展功能 + 联调集成（第 15-21 天）

---

### Day 15-16：联调准备

| 序号 | 动作 | 具体操作 | 产出物 |
|------|------|---------|--------|
| 1 | 统一基线 | 确保所有人的 feature 分支已 merge 到 main，没人还在分支上开发新功能（Week 3 起全部在 main 上协作） | 统一基线 |
| 2 | 全流程走查 | 拉最新 main，自己从头到尾完整走一遍：上传 → 预览 → 清洗 → 生成图表 → 回归分析。记录中途每一步的数据是怎么传递的 | 走查笔记 |
| 3 | 写联调手册 | 新建腾讯文档「联调操作手册」，内容： | 联调手册 |

**联调操作手册模板**：
```
## 联调流程（按顺序操作）

### Step 1: 上传数据
1. 打开 http://localhost:8000/
2. 点击「选择文件」，选择 test.csv
3. 点击「上传」
4. 预期结果：跳转到 /data/preview，看到前 10 行表格
5. 数据存储位置：session['df'] (JSON 格式)

### Step 2: 数据清洗
1. 点击导航栏「数据清洗」
2. 预期结果：看到缺失值统计表（每列缺失数 + 占比）
3. 选择策略：数值列 → 均值填充，点击「执行清洗」
4. 预期结果：跳回预览页，缺失值变为填充值
5. 传递给下一步：session['df_clean'] (JSON 格式)

### Step 3: 图表生成
1. 点击导航栏「可视化」
2. 选择 X 轴列：sqft，Y 轴列：price
3. 选择图表类型：散点图
4. 点击「生成图表」
5. 预期结果：页面出现散点图 PNG 图片
6. 图片保存路径：outputs/charts/scatter_<timestamp>.png

### Step 4: 回归分析
1. 点击导航栏「算法分析」
2. 选择特征列：sqft, bedrooms
3. 选择目标列：price
4. 点击「开始分析」
5. 预期结果：看到 R² 分数、MSE、回归系数表、预测值 vs 真实值对比
```

| 4 | 发手册 | 把联调手册发到群里，要求每人对着自己的模块检查：A 的输出是否符合 B 的输入预期 | 对齐确认 |

---

### Day 17-19：集中联调（建议周末约 2 小时线上集中对）

| 序号 | 动作 | 具体操作 |
|------|------|---------|
| 1 | 开会 | 腾讯会议，所有人到齐，PM 共享屏幕 |
| 2 | 按序走 | 严格按照联调手册 Step 1→2→3→4 顺序操作，每到一个环节暂停 |
| 3 | 逐环确认 | "后端 A，你的数据预览 API 返回了 10 行数据，前端你拿到了吗？" → 前端确认能渲染 |
| 4 | 当场修 | 小问题（字段名不对、少传了参数）：当场改，改完再跑一遍。大问题：开 Issue |
| 5 | 整理 Bug 清单 | 联调结束后 30 分钟内，整理完整的 Bug 清单发群里： |

**Bug 清单模板**：
```
| 编号 | 优先级 | 模块 | 描述 | 复现步骤 | 负责人 | 状态 |
|------|--------|------|------|---------|--------|------|
| B01 | P0 阻断 | 可视化 | 散点图中文乱码 | 选中文列名生成图表 | 可视化 | 待修复 |
| B02 | P1 异常 | 数据管理 | 上传 xlsx 报错 | 上传 test.xlsx | 后端 A | 待修复 |
| B03 | P2 体验 | 前端 | 导航栏手机端布局错乱 | 手机打开首页 | 前端 | 待修复 |

优先级定义：
  P0 = 阻断核心流程，不修无法演示
  P1 = 功能异常，影响使用但不阻断
  P2 = 体验问题，可延后
```

---

### Day 20-21：Bug 清零 + 扩展功能自开发

#### Bug 清零流程

- [ ] 按 P0 → P1 → P2 顺序逐一修复
- [ ] 每修一个 → 开 PR → PM Review → Merge
- [ ] 修完后 PM 亲自复测一遍确认关闭
- [ ] 全部 P0/P1 Bug 关闭后，打 Git Tag：`git tag v1.0-beta` → `git push origin v1.0-beta`

#### PM 自己的扩展开发：历史记录功能

这是你 Week 3 的技术开发任务：

- [ ] `models/dataset.py`：定义 Dataset ORM 模型（如果 Week 1 没写的话）
- [ ] 在 `data_routes.py` 的上传逻辑中，增加「登录用户上传成功后，写入一条 Dataset 记录到 MySQL」
- [ ] 在 `analysis_routes.py` 的分析逻辑中，增加「分析完成后，写入一条 AnalysisRecord 到 MySQL」
- [ ] 在 `viz_routes.py` 的图表生成逻辑中，增加「生成完成后更新 chart_paths 到对应 AnalysisRecord」
- [ ] `routes/history_routes.py`：
  - `GET /history`：查询当前登录用户的所有分析记录，按时间倒序
  - `GET /history/{record_id}`：查看某次分析的详细信息（图表、参数、评估指标）
  - `POST /history/{record_id}/delete`：删除记录
- [ ] `templates/history.html`：表格展示（日期、分析类型、数据集名、操作按钮），点击可查看详情
- [ ] 跟前端同学确认：导航栏加上「历史记录」链接（仅登录后显示）
- [ ] 自测：上传 → 清洗 → 分析 → 打开 `/history` 确认记录存在 → 点「查看详情」确认数据完整 → 点「删除」确认能删

---

## 六、Week 4：收尾 + 文档 + 答辩（第 22-28 天）

---

### Day 22：文档模板制定 + 下发

| 序号 | 动作 | 具体操作 | 产出物 |
|------|------|---------|--------|
| 1 | 写模板 | 创建 `docs/成果展示模板.md` 并 push 到仓库 | 模板就绪 |
| 2 | 发通知 | 群发通知：每人写一份成果文档，截止时间 **Day 26 晚上 22:00**，按模板格式写 | 截止线 |
| 3 | 定格式 | 明确要求：Markdown 格式，图片用相对路径 `![描述](../outputs/charts/xxx.png)`，代码块用 ` ```python ` | 格式规范 |
| 4 | 供素材 | 让前端同学把系统截图上传到仓库的 `docs/screenshots/` 目录，方便大家引用 | 公共素材 |

**个人成果文档模板**（`docs/成果展示模板.md`）：
```markdown
# 成果展示 — [姓名] — [角色：如 算法工程师]

## 一、系统概述（100-200 字）

> 本项目是一个基于 FastAPI 的交互式数据分析系统，支持数据上传、清洗、可视化和线性回归预测。
> [插入一张系统架构图]

---

## 二、我负责的模块（500 字）

### 2.1 模块功能描述
[用 1-2 段话描述你的模块做什么]

### 2.2 技术选型
- 使用了 [库名]，因为 [原因]
- 未使用 [替代方案]，因为 [原因]

### 2.3 实现思路
[描述你的核心逻辑流程，可以画流程图或列步骤]

---

## 三、核心代码展示（3-5 段）

> 每段代码附上注释，解释关键逻辑。

```python
# 示例：线性回归训练核心代码
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

# 1. 准备特征和目标
X = df[features]  # features 来自用户选择
y = df[target]

# 2. 划分训练集/测试集 (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3. 训练模型
model = LinearRegression()
model.fit(X_train, y_train)

# 4. 预测与评估
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)    # 越接近 1 越好
mse = mean_squared_error(y_test, y_pred)  # 越小越好
```

---

## 四、运行截图（至少 3 张）

### 4.1 [功能页名称]
![截图描述](../docs/screenshots/xxx.png)
*图注：xxx*

---

## 五、遇到的困难与解决方案（至少 2 个）

### 5.1 困难 1：[标题]
- **现象**：[描述]
- **原因分析**：[分析]
- **解决方案**：[怎么解决的]
- **学到什么**：[反思]

---

## 六、收获与反思（300 字以上）

[自由发挥，谈谈通过这个项目学到了什么、团队协作的体会、未来改进方向]
```

---

### Day 23-25：测试收尾

| 序号 | 动作 | 具体操作 |
|------|------|---------|
| 1 | 组织全员测试 | 群发消息：每人准备 3 个不同质量的 CSV 测试文件，互相交换测试 |
| 2 | 测试场景覆盖 | 确保覆盖以下场景： |

**测试场景清单**：
```
□ 标准 CSV (UTF-8 编码，英文列名)
□ CSV with 中文列名 (UTF-8)
□ CSV with GBK 编码
□ CSV 含缺失值 (空单元格)
□ CSV 含异常值 (价格 = 999999999)
□ Excel .xlsx 格式
□ 空文件 (0 字节)
□ 只有表头没有数据的 CSV
□ 超过 5000 行的 CSV
□ 包含非数值列的 CSV 用于回归分析
□ 注册时两次密码不一致
□ 登录时输入错误密码
□ 未登录访问 /history
□ 未上传数据直接点「数据清洗」
□ 未清洗数据直接点「可视化」
```

| 3 | 关闭最后 Issue | 测试中发现的 Bug → 开 Issue → 修复 → 关闭 |
| 4 | 打 release tag | 最后一个 Bug 关闭后：`git tag v1.0-release` → `git push origin v1.0-release` |

---

### Day 26：文档收集 + PPT 素材准备

| 序号 | 动作 | 具体操作 |
|------|------|---------|
| 1 | 收文档 | 截止时间到，检查群内谁还没交 → 私聊催 |
| 2 | 格式审查 | 逐份打开检查： |
| | | □ 章节结构是否完整（6 个大标题都在吗） |
| | | □ 截图是否清晰、能否正常加载 |
| | | □ 代码块是否有语法着色 |
| | | □ 字数是否达标（收获反思 300 字以上） |
| | | □ 图片路径是否正确（`../docs/screenshots/xxx.png`） |
| 3 | 退回修改 | 不合格的打回，标注哪里要改，给到 Day 27 中午前 |
| 4 | 收素材 | 收集前端同学的截图包和录屏文件 |
| 5 | 截图清单 | 确认以下页面截图都有： |

**答辩截图清单**：
```
□ 系统首页（含导航栏）
□ 数据上传页（含文件选择器）
□ 数据预览页（含前 10 行表格）
□ 数据清洗页（含缺失值统计报告）
□ 清洗后对比图（清洗前 vs 清洗后）
□ 可视化页面（含 3 种图表：折线/柱状/散点）
□ 算法分析页（含 R²/MSE/回归系数/预测对比表）
□ 算法对比页（含 3 种算法指标对比表）
□ 历史记录页（含多条记录列表）
□ 登录/注册页
```

---

### Day 27：PPT 制作

**PPT 结构（10-12 页）**：

| 页码 | 标题 | 内容要点 |
|------|------|---------|
| 1 | 封面 | 项目名「交互式数据分析系统」+ 团队成员姓名 + 日期 |
| 2 | 目录 | 1. 项目背景 2. 系统设计 3. 功能演示 4. 扩展亮点 5. 技术难点 6. 团队协作 7. 总结 |
| 3 | 项目背景与目标 | 一句话：让非技术人员通过浏览器完成数据分析全流程。核心目标 5 条（文档 1.1 节） |
| 4 | 系统架构 | 放文档中的五层架构图（1.2 节的 ASCII 图，或者画一个更美观的版本） |
| 5 | 技术栈一览 | 后端 FastAPI + 数据处理 Pandas/sklearn + 可视化 Matplotlib + 数据库 MySQL + 前端 Jinja2 |
| 6 | 核心功能演示 | 四宫格截图：上传→清洗→可视化→分析。每张图配一句话说明 |
| 7 | 算法分析详情 | 放回归分析的 R²/MSE 数值 + 预测 vs 真实值散点图 + 算法对比表 |
| 8 | 扩展功能亮点 | 三宫格截图：用户注册登录 + 历史记录列表 + 算法对比（Ridge/Lasso） |
| 9 | 团队分工与协作 | 放文档 3.1 节的分工图 + Git 分支工作流 + 站会制度 |
| 10 | 关键难点与解决方案 | 3 个问题：Matplotlib 中文乱码、session 数据传递、联调接口对齐（每人提供一个难点供你汇总） |
| 11 | 项目总结与收获 | 一句话总结 + 3 个关键收获（技术、协作、工程规范） |
| 12 | 致谢 & Q&A | 感谢观看 + "欢迎提问" |

**PPT 制作 Tips**：
- 用统一模板（建议用学校/课程统一模板）
- 每页文字不超过 5 行，多用图说话
- 代码片段截图用 VS Code 带语法高亮的截屏
- 图表元素标注关键数值（R²=0.78 用红色大字标出）

---

### Day 28：答辩演练

| 序号 | 动作 | 具体操作 |
|------|------|---------|
| 1 | 发 PPT | 把 PPT 导出 PDF 发群里，让所有人提前看 |
| 2 | 分配发言 | 给每人分配 1-2 分钟发言时间： |

**发言分配模板**：
```
总时长：12 分钟（10 分钟讲 + 2 分钟 Q&A）

0:00-2:00  PM 主讲：项目背景 + 系统架构 + 技术栈          (2 min)
2:00-3:00  后端 A：数据管理模块演示                        (1 min)
3:00-4:00  后端 B：数据清洗模块演示                        (1 min)
4:00-5:30  可视化：图表生成演示 + 参数化                    (1.5 min)
5:30-7:00  算法：回归分析 + 算法对比演示                    (1.5 min)
7:00-8:00  前端：页面设计亮点                              (1 min)
8:00-9:30  PM 主讲：扩展功能 + 团队协作 + 难点 + 总结       (1.5 min)
9:30-10:00 PM 收尾：致谢                                   (0.5 min)
剩下 2 分钟预留给 Q&A
```

| 3 | 模拟答辩 | 开腾讯会议，完整走一遍： |
| | | - PM 共享屏幕翻 PPT |
| | | - 每人按分配时间讲自己部分 |
| | | - 严格控制时间（超时打断） |
| | | - 其他人当观众，记下来哪里讲得不清楚 |
| 4 | 预演提问 | 模拟老师可能的提问，让每个人准备好回答： |

**预演提问清单**：
```
□ 为什么选择 FastAPI 而不是 Flask/Django？
□ 为什么用服务端渲染（Jinja2）而不是前后端分离（Vue/React）？
□ 线性回归的适用条件是什么？你的数据满足吗？
□ 数据库为什么设计这三张表？表之间的关系是什么？
□ 有没有做单元测试？为什么没有？
□ 如果数据量很大（10 万行），系统会不会崩？怎么优化？
□ 图表为什么是静态 PNG 而不是 ECharts 动态图？
□ 多人同时上传文件会不会冲突？怎么解决的？
□ 密码怎么存储的？安全吗？
□ 每个人的具体贡献比例是多少？
```

| 5 | 最终检查 | 答辩前一天晚上： |
| | | □ PPT 在答辩电脑上能正常打开吗？（字体不乱？） |
| | | □ 系统在答辩电脑上能跑起来吗？`uvicorn main:app` 试一下 |
| | | □ 截图的 PNG 都内嵌到 PPT 里了吗？（不要用链接） |
| | | □ 仓库 README 更新了吗？（含项目截图 + 启动说明） |
| | | □ 所有人的成果文档都交齐了吗？ |
| | | □ 录屏文件能播放吗？ |

---

## 七、贯穿始终的 PM 日常动作

| 频率 | 动作 | 工具/方法 | 耗时 |
|------|------|----------|------|
| **每日** | 站会主持（3 句话：做了啥 / 卡在哪 / 明天做啥） | 微信群文字 | 10 min |
| **每日** | 查看 GitHub notifications，处理新 PR | GitHub 网页 | 5 min |
| **每日** | 更新进度看板 | 腾讯文档表格 | 5 min |
| **每 2 天** | 检查分支差距 `git log main..feat/xxx --oneline` | 终端 | 5 min |
| **每周末** | 写周报（3 句话）发群里 | 群消息 | 10 min |
| **每次 Review** | 按清单逐条审查代码 | GitHub PR Review | 15-30 min |
| **发现问题** | 开 Issue，指派 + 贴标签 | GitHub Issues | 5 min |

---

## 八、PM 最容易踩的 5 个坑及应对

| 序号 | 坑 | 表现 | 应对 |
|------|-----|------|------|
| 1 | **有人进度严重落后** | 3 天没 push，站会说"还在学" | 不要等。立刻私聊：具体卡在哪里？环境没配好→远程帮配；不会写→安排结对编程；态度问题→明确告知会影响全组成绩 |
| 2 | **分支长期不合并导致大冲突** | feature 分支偏离 main 2 周以上 | 强制规定：feature 分支存活不超过 5 天。到时间没完成也要提 PR，合并能跑的部分，剩下的开新分支继续 |
| 3 | **接口对接不上** | 联调时 A 说"我以为你传的是 JSON"，B 说"我以为你传的是 FormData" | 根源在 Week 1 的接口契约没写死。补救：立刻拉会，当场打开 Postman，双方确认请求体和响应体的每个字段名和类型 |
| 4 | **有人不交文档** | 截止日过了，文档还是空白 | Deadline 前 3 天开始每天群内公布进度（"张三✅已交、李四⏳写了30%、王五❌还没开始"），公开进度的心理压力比私聊有效 10 倍 |
| 5 | **答辩前一天系统崩了** | 代码改了个"小优化"结果全挂了 | ① Week 3 打的 `v1.0-beta` Tag 就是保险，出问题 `git checkout v1.0-beta` 一秒回滚。② 答辩当天禁止任何人动代码 |

---

## 九、PM 自己的开发任务汇总

别光管别人，你自己的代码任务也需要按时交付。

| Week | 任务 | 涉及文件 |
|------|------|---------|
| W1 | MySQL 建库建表 | `database/init.sql` |
| W1 | 数据库配置 | `config.py` |
| W1 | ORM 模型（User, Dataset, AnalysisRecord） | `models/user.py`, `models/analysis_record.py` |
| W1 | 密码哈希工具 | `services/auth_service.py` |
| W1 | 注册/登录/登出路由 | `routes/auth_routes.py` |
| W1 | 登录/注册模板 | `templates/login.html`, `templates/register.html` |
| W3 | 上传时保存 Dataset 记录 | `routes/data_routes.py`（修改） |
| W3 | 分析/可视化后保存 AnalysisRecord | `routes/analysis_routes.py`, `routes/viz_routes.py`（修改） |
| W3 | 历史记录路由 + 模板 | `routes/history_routes.py`, `templates/history.html` |
| W4 | README 更新 + PPT 制作 | `README.md`, PPT 文件 |
| W4 | 个人成果文档 | `docs/PM姓名_成果展示.md` |

---

## 十、关键里程碑总表

| 时间 | 里程碑 | 标志 |
|------|--------|------|
| Day 2 | 团队启动完成 | 角色分配定板 + 仓库就绪 + 站会制度建立 |
| Day 4 | 接口契约定板 | 16 个 API 的请求/响应 JSON 示例全部写完 |
| Day 7 | Week 1 完成 | PM 自己的用户认证模块能跑通（注册→登录→登出） |
| Day 14 | Week 2 完成 | 5 个模块的 MVP 全部能独立跑通（各调各的 API） |
| Day 19 | 联调完成 | 全流程「上传→清洗→可视化→分析→历史记录」无阻断 |
| Day 21 | v1.0-beta | 所有 P0/P1 Bug 关闭 + Git Tag |
| Day 25 | v1.0-release | 全部测试通过 + Git Tag |
| Day 26 | 文档收齐 | 6 份成果文档全部合格 |
| Day 27 | PPT 定稿 | PPT 制作完成 + 群里 review 通过 |
| Day 28 | 答辩演练完成 | 模拟答辩走完 + 预演提问有答案 |

---

## 附录 A：每日站会模板（直接复制发群）

```
📅 Day X 站会 (日期)

🔥 昨日完成：
- PM：完成了 init.sql 建表，users 表创建成功
- 后端A：文件上传 API 写了一半，卡在文件编码检测
- ...

🧱 今日计划：
- PM：写 auth_service.py 密码哈希逻辑
- 后端A：解决编码检测问题，完成上传 API
- ...

⚠️ 卡点/求助：
- 后端A：GBK 编码的 CSV 读出来乱码，求帮助
```

## 附录 B：Git 常用命令速查（发给团队）

```bash
# 克隆仓库
git clone https://github.com/xxx/data-analysis-system.git

# 创建自己的 feature 分支
git checkout -b feat/your-module

# 日常开发后提交
git add .
git commit -m "feat: 完成了文件上传 API"
git push origin feat/your-module

# 拉取 main 最新代码（每天开始工作前执行）
git checkout main
git pull origin main
git checkout feat/your-module
git merge main   # 把 main 的最新代码合并到自己的分支

# 如果 merge 有冲突，解决冲突后：
git add .
git commit -m "merge: 解决与 main 的冲突"
```

---

> 📁 **文件位置**：`.sisyphus/plans/pm-action-plan.md`
> 📅 **最后更新**：2026-05-26
> 👤 **适用对象**：交互式数据分析系统 — 项目经理
