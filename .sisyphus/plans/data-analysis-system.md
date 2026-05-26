# 交互式数据分析系统 — 完整思路框架

## TL;DR

> **一句话概述**：基于 FastAPI + Matplotlib + scikit-learn + MySQL 构建一个 Web 交互式数据分析系统，覆盖「上传→清洗→分析→可视化→展示」完整流水线，含线性回归预测、用户系统和算法对比等扩展功能。
>
> **交付物**：
> - 可运行的 FastAPI Web 应用（源码 + 配置）
> - MySQL 数据库 schema 文件
> - 小组分工明确的任务清单
> - 每人一份成果展示文档（系统设计 + 模块说明 + 代码片段 + 截图 + 收获反思）
>
> **技术栈**：FastAPI | Jinja2 | Matplotlib | scikit-learn | Pandas | MySQL | Python 3.10+
> **项目周期**：2-4 周 | **团队规模**：5-6 人 | **难度等级**：适合 Python 初学者入门 Web 开发

---

## 一、项目概述

### 1.1 核心目标

构建一个可通过浏览器访问的数据分析 Web 系统，用户能够：
1. **上传** CSV/Excel 数据文件（或使用内置模拟数据）
2. **清洗** 数据（自动检测缺失值/异常值并提供处理选项）
3. **分析** 数据（使用线性回归进行预测建模）
4. **可视化** 展示结果（≥3 种图表以图片形式嵌入页面）
5. **管理** 分析历史记录（登录后查看过往分析）

### 1.2 技术栈总览

```
┌─────────────────────────────────────────────────┐
│                   前端层                          │
│         Jinja2 模板 + HTML/CSS + 原生 JS          │
│              (服务端渲染，无需前端框架)               │
├─────────────────────────────────────────────────┤
│                   Web 层                          │
│     FastAPI (路由 + API + 依赖注入 + 中间件)         │
│     Pydantic (数据校验 + 请求/响应模型)               │
├─────────────────────────────────────────────────┤
│                  业务逻辑层                         │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │ 数据管理  │ 数据清洗  │ 可视化    │ 算法分析  │  │
│  │ (上传/   │ (缺失值/ │ (图表生成) │ (回归预测) │  │
│  │  读取/   │  异常值/ │           │          │  │
│  │  导出)   │  归一化) │           │          │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
├─────────────────────────────────────────────────┤
│                  数据处理层                        │
│       Pandas (DataFrame 操作 + 统计分析)            │
│       scikit-learn (LinearRegression)              │
│       Matplotlib (图表渲染)                         │
├─────────────────────────────────────────────────┤
│                  数据存储层                         │
│      MySQL (用户 + 历史记录 + 已清洗数据集)           │
│      文件系统 (上传的原始文件 + 生成的图片)             │
└─────────────────────────────────────────────────┘
```

### 1.3 数据流设计

```
用户上传文件 ──→ 文件系统暂存 ──→ Pandas 加载为 DataFrame
                                        │
                    ┌───────────────────┤
                    ▼                   ▼
              数据预览展示         数据清洗处理
              (前10行表格)    (缺失值填充/异常值剔除)
                                        │
                    ┌───────────────────┤
                    ▼                   ▼
              可视化图表生成        线性回归分析
           (折线/柱状/散点图)    (训练 → 预测 → 评估)
                    │                   │
                    ▼                   ▼
              Matplotlib 渲染为 PNG 图片
                    │
                    ▼
            Jinja2 模板嵌入图片 → 返回 HTML 页面
                    │
                    ▼
           (登录用户: 结果存入 MySQL 历史记录)
```

### 1.4 目录结构

```
data-analysis-system/
├── main.py                  # FastAPI 应用入口
├── config.py                # 数据库连接、上传路径等配置
├── requirements.txt         # Python 依赖清单
├── models/                  # 数据库模型（SQLAlchemy ORM）
│   ├── __init__.py
│   ├── user.py              # 用户表模型
│   └── analysis_record.py   # 分析记录表模型
├── schemas/                 # Pydantic 请求/响应模型
│   ├── __init__.py
│   ├── user.py              # 用户注册/登录 schema
│   └── analysis.py          # 分析请求/响应 schema
├── routes/                  # 路由（视图函数）
│   ├── __init__.py
│   ├── main_routes.py       # 首页、关于等
│   ├── auth_routes.py       # 注册、登录、登出
│   ├── data_routes.py       # 上传、预览、删除
│   ├── analysis_routes.py   # 数据清洗、可视化、算法分析
│   └── history_routes.py    # 历史记录查看
├── services/                # 业务逻辑层
│   ├── __init__.py
│   ├── data_service.py      # 文件处理、数据加载
│   ├── clean_service.py     # 清洗逻辑（缺失值/异常值/归一化）
│   ├── viz_service.py       # 图表生成（折线/柱状/散点）
│   ├── ml_service.py        # 线性回归 + 算法对比
│   └── auth_service.py      # 用户认证逻辑
├── templates/               # Jinja2 模板
│   ├── base.html            # 基础布局模板
│   ├── index.html           # 首页（上传入口）
│   ├── login.html           # 登录页
│   ├── register.html        # 注册页
│   ├── upload.html          # 数据上传页
│   ├── preview.html         # 数据预览页
│   ├── clean.html           # 数据清洗页
│   ├── visualize.html       # 可视化展示页
│   ├── analysis.html        # 算法分析页
│   └── history.html         # 历史记录页
├── static/                  # 静态文件
│   ├── css/
│   │   └── style.css        # 全局样式
│   ├── js/
│   │   └── main.js          # 前端交互增强
│   └── uploads/            # 用户上传的原始文件
├── outputs/                 # 生成的图表图片
│   └── charts/
├── data/                    # 内置模拟数据集
│   └── sample_housing.csv   # 示例房价数据
├── database/
│   └── init.sql             # MySQL 建表 SQL
├── tests/                   # 手动测试脚本（可选）
│   └── test_api.py
└── docs/                    # 个人成果文档
    ├── 张三_成果展示.md
    ├── 李四_成果展示.md
    └── ...
```

---

## 二、功能模块设计

### 2.1 模块总览与评分对位

| 模块 | 基础功能 (70分) | 扩展功能 (加分) | 评分占比 |
|------|----------------|-----------------|---------|
| 数据管理 | CSV/Excel 上传、预览、删除 | MySQL 持久化存储 | 30分 |
| 数据清洗 | 缺失值填充 + 异常值剔除 | 自动清洗策略（智能推荐） | |
| 可视化 | 折线图、柱状图、散点图 (≥3种) | 参数可调（标题/颜色/尺寸） | 10分 |
| 算法分析 | 线性回归预测（训练→预测→评估） | 多种算法对比 (岭回归/Lasso) | 20分 |
| Web 服务 | 响应式布局，全流程串联 | 用户登录 + 历史记录 | 10分 |

### 2.2 模块一：数据管理

**用户故事**：用户可以上传一个 CSV/Excel 文件，系统自动读取并展示数据预览。

**技术要点**：
- FastAPI `UploadFile` 接收文件 → 保存到 `static/uploads/`
- Pandas `read_csv()` / `read_excel()` 加载为 DataFrame
- 返回前 10 行数据到 Jinja2 模板渲染为 HTML 表格
- 错误处理：文件格式校验、编码检测（UTF-8/GBK 自动判断）

**关键 API**：
```
POST /data/upload    → 上传文件，返回数据预览页
GET  /data/preview   → 查看当前加载的数据
POST /data/delete    → 清除当前数据
```

**扩展功能**：
- 上传的数据集自动存入 MySQL 的 `datasets` 表（含字段名元数据）
- 内置模拟数据集：`data/sample_housing.csv`（房价预测场景）

---

### 2.3 模块二：数据清洗

**用户故事**：系统自动检测数据中的缺失值和异常值，用户选择处理策略后一键清洗。

**技术要点**：
- **缺失值检测**：`df.isnull().sum()` 统计各列缺失数量
- **处理策略**（提供下拉选择）：
  - 数值列：均值填充 / 中位数填充 / 删除行
  - 分类列：众数填充 / 删除行
- **异常值检测**：IQR 法（Q1 - 1.5×IQR, Q3 + 1.5×IQR）
- **归一化**：MinMaxScaler（可选，用于回归算法预处理）

**关键 API**：
```
GET  /clean           → 展示缺失值/异常值统计报告
POST /clean/execute   → 执行清洗（传入策略参数），返回清洗后数据预览
```

**扩展功能**：
- 自动清洗策略：一键"智能清洗"（数值列用中位数，分类列用众数，异常值用 IQR 剔除）
- 清洗前后对比展示（并排表格）

---

### 2.4 模块三：可视化

**用户故事**：用户选择 X/Y 轴列名，系统动态生成图表并以图片形式展示在页面上。

**技术要点**：
- 使用 Matplotlib 后端设为 `Agg`（非交互式，适合 Web 环境）
- 图表生成流程：用户选列 → 后端用 Matplotlib 绑图 → `savefig()` 保存为 PNG → 图片路径传给模板
- **三种基础图表**：
  | 图表类型 | 适用场景 | Matplotlib 函数 |
  |---------|---------|-----------------|
  | 折线图 | 趋势变化 | `plt.plot()` |
  | 柱状图 | 分类对比 | `plt.bar()` |
  | 散点图 | 相关性分析 | `plt.scatter()` |
- 图表配置项（可调参数）：标题、X/Y 轴标签、颜色主题、图片尺寸

**关键 API**：
```
POST /visualize/generate → 接收列选择 + 图表类型 → 生成图片 → 返回展示页
GET  /visualize/show     → 展示已生成的所有图表
```

**关于"交互性"的说明**（应对评分标准）：
- 虽然图表为静态 PNG，但通过**参数可调整**（用户可通过表单重新选择列/图表类型/颜色等参数生成新图）来实现"交互式体验"
- 在成果文档中强调：参数驱动的图表重新生成是一种服务端交互，符合"用户可操作图表以获得不同视角"的要求

---

### 2.5 模块四：算法分析（线性回归预测）

**用户故事**：用户选择特征列（X）和目标列（Y），系统训练线性回归模型并展示预测结果和模型评估指标。

**技术要点**：
- 使用 `sklearn.linear_model.LinearRegression`
- 工作流程：
  1. 用户选择特征列（可多选）和目标列
  2. 系统按 80/20 划分训练集/测试集
  3. 训练模型 → 在测试集上预测 → 计算评估指标
  4. 展示结果：回归系数表、R² 分数、MSE、预测值 vs 真实值对比表

**关键 API**：
```
POST /analysis/regression → 接收特征列 + 目标列 → 训练 → 返回评估结果页
GET  /analysis/result     → 查看上次分析结果
```

**扩展功能（算法对比）**：
- 同时运行 3 种回归算法进行对比：
  | 算法 | scikit-learn 类 | 特点 |
  |------|----------------|------|
  | 线性回归 | `LinearRegression` | 基准模型 |
  | 岭回归 | `Ridge` | L2 正则化，防过拟合 |
  | Lasso 回归 | `Lasso` | L1 正则化，特征选择 |
- 对比表格展示各算法的 R²、MSE、MAE，帮助用户选择最佳模型
- 可视化：用散点图画出"预测值 vs 真实值"对比

---

### 2.6 模块五：Web 服务

**用户故事**：所有功能通过统一的 Web 界面串联起来，操作流畅，界面美观。

**技术要点**：
- FastAPI + Jinja2 模板实现服务端渲染
- 响应式 CSS（使用 Flexbox/Grid，手机/电脑均可访问）
- 导航栏串联所有功能页面
- 文件上传进度提示（原生 JS 实现）
- 错误页面（404/500）友好提示

**扩展功能（用户系统）**：
- **注册**：用户名 + 密码（bcrypt 哈希存储到 MySQL）
- **登录**：Session 机制（FastAPI 的 `starlette.middleware.sessions`）
- **历史记录**：用户登录后，每次分析结果（图表路径、模型参数、评估指标）存入 MySQL
- **个人中心**：查看历史分析记录列表，支持回看和删除

---

### 2.7 模块六：数据库设计

**表结构**：

```sql
-- 用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据集元数据表（扩展）
CREATE TABLE datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    columns_info JSON,           -- 列名和类型元数据
    row_count INT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 分析记录表（扩展）
CREATE TABLE analysis_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    dataset_id INT,
    analysis_type VARCHAR(50),   -- 'regression' / 'visualization'
    parameters JSON,             -- 用户选择的参数
    result_summary TEXT,         -- R²、MSE 等指标
    chart_paths JSON,            -- 生成的图表文件路径列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);
```

---

## 三、团队角色分工（5-6人方案）

### 3.1 角色定义

> 原则：**一人一模块核心负责 + 全员代码互审**。初学者建议按"强带弱"配对。

```
┌─────────────────────────────────────────────────────┐
│                    项目经理（1人）                      │
│   统筹进度、Git 管理、文档整合、成果展示 PPT/答辩          │
│   兼任：数据库设计 + 用户认证模块                         │
├─────────────────────────────────────────────────────┤
│  后端开发 A（1人）        后端开发 B（1人）               │
│  数据管理模块             数据清洗模块                    │
│  + 数据预览 API           + 清洗策略服务                  │
│  + 文件上传处理           + 异常值检测                    │
├─────────────────────────────────────────────────────┤
│  算法工程师（1人）        前端工程师（1人）               │
│  线性回归模块             所有 Jinja2 模板                │
│  + 算法对比（扩展）        + HTML/CSS 布局                │
│  + 模型评估指标           + 前端 JS 交互增强              │
├─────────────────────────────────────────────────────┤
│  可视化工程师（1人）      [可选项：全栈支持（1人）]         │
│  Matplotlib 图表生成      协助薄弱模块                    │
│  + 图表配置参数化          + 集成测试                      │
│  + 图片渲染优化             + Bug 修复                     │
└─────────────────────────────────────────────────────┘
```

### 3.2 各角色学习重点

| 角色 | 必学内容 | 推荐资源 |
|------|---------|---------|
| **项目经理** | Git 基础操作、FastAPI 项目结构、MySQL 建表 | FastAPI 官方教程、MySQL 基础 CRUD |
| **后端 A（数据管理）** | FastAPI UploadFile、Pandas read_csv/read_excel、文件处理 | Pandas 10分钟入门 |
| **后端 B（数据清洗）** | Pandas 缺失值/异常值处理、numpy 统计函数 | Pandas 官方文档 - 处理缺失数据 |
| **算法工程师** | scikit-learn LinearRegression/Ridge/Lasso、train_test_split、评估指标 | scikit-learn 官方线性模型文档 |
| **可视化工程师** | Matplotlib pyplot、subplots、savefig、中文显示配置 | Matplotlib 官方教程 |
| **前端工程师** | Jinja2 模板语法、HTML5 表单、CSS Flexbox/Grid、fetch API | MDN HTML/CSS 教程 |

### 3.3 协作流程

```
Week 1:         各自学习 → 搭建环境 → 定接口契约
Week 2:         并行开发模块 → 每日 10 分钟站会同步
Week 3:         联调集成 → 测试 → Bug 修复
Week 4:         文档撰写 → 录屏/截图 → 答辩准备

工具：
  - Git + GitHub/Gitee 管理代码
  - 飞书/微信群 日常沟通
  - 腾讯文档 共享接口文档和进度
```

### 3.4 Git 工作流（简化版）

```
main 分支（稳定版本）
  ├── feat/data-management    （后端 A）
  ├── feat/data-cleaning      （后端 B）
  ├── feat/ml-analysis        （算法工程师）
  ├── feat/visualization       （可视化工程师）
  └── feat/frontend-templates  （前端工程师）

流程：
  1. 从 main 新建 feature 分支
  2. 在自己的分支上开发 + 测试
  3. 完成后发起 Pull Request
  4. 项目经理 Code Review 后合并到 main
```

---

## 四、开发阶段计划（4周拆解）

### Week 1：环境搭建 + 学习 + 基础骨架

| 任务 | 负责人 | 产出 |
|------|--------|------|
| Python 3.10+ 环境安装 + pip 依赖 | 全员 | `requirements.txt` |
| MySQL 安装配置 + 建表 | 项目经理 | `database/init.sql` |
| FastAPI 项目骨架搭建 | 项目经理 | `main.py` + 目录结构 |
| Jinja2 `base.html` 布局模板 | 前端 | 导航栏 + 响应式框架 |
| 数据管理模块开发 | 后端 A | 文件上传 API + 预览页 |
| Pandas 学习 + 示例数据准备 | 全员 | `data/sample_housing.csv` |
| 接口契约文档（API 定义 + 请求/响应格式） | 项目经理 | 共享文档 |

### Week 2：核心功能并行开发

| 任务 | 负责人 | 产出 |
|------|--------|------|
| 数据清洗模块开发 | 后端 B | 缺失值/异常值检测 + 清洗执行 API |
| 可视化模块开发 | 可视化工程师 | 折线图/柱状图/散点图生成 + 参数表单 |
| 线性回归模块开发 | 算法工程师 | 训练/预测/评估 API + 结果展示页 |
| 前端页面完善（upload/clean/visualize/analysis） | 前端 | 4 个核心页面 |
| 用户注册/登录功能 | 项目经理 | auth 路由 + `users` 表 CRUD |

### Week 3：扩展功能 + 联调集成

| 任务 | 负责人 | 产出 |
|------|--------|------|
| 算法对比（Ridge + Lasso） | 算法工程师 | 对比结果表 |
| 历史记录存储 + 回看 | 项目经理 + 前端 | `analysis_records` 表 + history 页 |
| 自动清洗策略 | 后端 B | 一键智能清洗按钮 |
| 全流程联调（上传→清洗→可视化→分析） | 全员 | 端到端流程无 Bug |
| 错误处理 + 404/500 页面 | 前端 | 友好错误提示 |

### Week 4：测试 + 文档 + 优化

| 任务 | 负责人 | 产出 |
|------|--------|------|
| 整体功能测试（各种数据+各种场景） | 全员 | 测试问题清单 → 修复 |
| 个人成果文档撰写 | 每人 | 每人一份 `.md` 文档 |
| 系统运行截图 + 录屏 | 前端 | 答辩展示素材 |
| 代码清理 + 注释补充 | 全员 | 整洁代码 |
| MySQL 集成完善 | 后端 A | 所有数据持久化 |
| 答辩 PPT 制作 | 项目经理 | 汇报材料 |

---

## 五、API 接口清单

### 5.1 数据管理

| 方法 | 路径 | 功能 | 请求 | 响应 |
|------|------|------|------|------|
| `GET` | `/` | 首页 | - | `index.html` |
| `POST` | `/data/upload` | 上传文件 | `FormData(file)` | `preview.html` |
| `GET` | `/data/preview` | 数据预览 | - | `preview.html` (含前10行表格) |
| `POST` | `/data/delete` | 清除数据 | - | 重定向到首页 |

### 5.2 数据清洗

| 方法 | 路径 | 功能 | 请求体 | 响应 |
|------|------|------|------|------|
| `GET` | `/clean` | 清洗前报告 | - | 缺失值统计 + 异常值报告 |
| `POST` | `/clean/execute` | 执行清洗 | `{strategy: "mean", columns: ["price"], ...}` | 清洗后数据预览 |
| `POST` | `/clean/auto` | 一键自动清洗（扩展） | - | 自动清洗结果 |

### 5.3 可视化

| 方法 | 路径 | 功能 | 请求体 | 响应 |
|------|------|------|------|------|
| `POST` | `/viz/generate` | 生成图表 | `{chart_type, x_col, y_col, title, ...}` | `visualize.html` (含图片) |
| `GET` | `/viz/show` | 查看已生成图表 | - | 所有图表展示 |

### 5.4 算法分析

| 方法 | 路径 | 功能 | 请求体 | 响应 |
|------|------|------|------|------|
| `POST` | `/analysis/regression` | 线性回归分析 | `{features: ["sqft","bedrooms"], target: "price"}` | 评估结果 + 图表 |
| `POST` | `/analysis/compare` | 多算法对比（扩展） | 同上 | 对比表 + 推荐最佳算法 |
| `GET` | `/analysis/result` | 查看上次结果 | - | 结果页 |

### 5.5 用户认证（扩展）

| 方法 | 路径 | 功能 | 请求体 | 响应 |
|------|------|------|------|------|
| `GET` | `/auth/login` | 登录页 | - | `login.html` |
| `POST` | `/auth/login` | 提交登录 | `{username, password}` | 重定向到首页 |
| `GET` | `/auth/register` | 注册页 | - | `register.html` |
| `POST` | `/auth/register` | 提交注册 | `{username, password, confirm}` | 重定向到登录页 |
| `GET` | `/auth/logout` | 登出 | - | 重定向到首页 |

### 5.6 历史记录（扩展）

| 方法 | 路径 | 功能 | 响应 |
|------|------|------|------|
| `GET` | `/history` | 历史分析记录列表 | `history.html` |
| `GET` | `/history/{id}` | 查看某次分析详情 | 分析详情页 |
| `POST` | `/history/{id}/delete` | 删除记录 | 重定向 |

---

## 六、关键技术难点与解决方案

### 6.1 FastAPI + Jinja2 模板渲染

```python
# main.py 核心结构示例
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="交互式数据分析系统")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

### 6.2 Matplotlib 中文乱码问题

```python
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows 中文字体
plt.rcParams['axes.unicode_minus'] = False     # 解决负号显示问题
```

### 6.3 MySQL 连接（初学者友好方式）

```python
# 使用 SQLAlchemy ORM 而非原生 SQL
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/data_analysis"
engine = create_engine(DATABASE_URL)

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
```

### 6.4 文件上传大小限制

```python
from fastapi import FastAPI

app = FastAPI()

# 在路由中限制文件大小
@app.post("/data/upload")
async def upload(file: UploadFile = File(..., max_size=10_000_000)):  # 10MB
    ...
```

---

## 七、评分对照检查清单

> 对照实验文档评分标准，确保不丢分。

### 基础功能 (70分)

- [ ] **数据上传** (30分)：CSV/Excel 均可上传，显示数据预览
- [ ] **数据清洗** (30分)：缺失值填充 + 异常值剔除功能可用
- [ ] **机器学习** (20分)：线性回归算法正确实现（训练 + 预测 + R²/MSE 指标）
- [ ] **页面交互** (10分)：页面布局合理，图表可"通过参数调整重新生成"
- [ ] **文档规范** (10分)：格式规范、内容充实

### 加分扩展 (30分)

- [ ] **数据库集成** (MySQL 持久化存储用户和分析记录)
- [ ] **算法对比** (线性回归 + 岭回归 + Lasso 三种算法对比)
- [ ] **自动清洗** (一键智能清洗策略)
- [ ] **用户系统** (注册/登录/历史记录)
- [ ] **丰富可视化** (图表配置参数化，颜色/标题/尺寸可调)

### 文档要求检查清单

每人文档需覆盖：
- [ ] 系统整体设计（架构图 + 技术栈说明）
- [ ] 系统功能模块划分（模块图 + 职责说明）
- [ ] **自己负责的模块**详细说明（核心！）
- [ ] 实现思路（流程图 + 关键代码片段）
- [ ] 系统运行截图（至少 5 张，覆盖全流程）
- [ ] 遇到的问题及解决方法（至少 3 个问题）
- [ ] 收获与改进建议

---

## 八、推荐学习路径

| 阶段 | 内容 | 预计时间 | 关键资源 |
|------|------|---------|---------|
| 1 | FastAPI 入门（路由、模板、表单） | 2天 | [FastAPI 官方教程](https://fastapi.tiangolo.com/zh/tutorial/) |
| 2 | Jinja2 模板语法 | 1天 | [Jinja2 文档](https://jinja.palletsprojects.com/) |
| 3 | Pandas 数据处理 | 2天 | [Pandas 10分钟入门](https://pandas.pydata.org/docs/user_guide/10min.html) |
| 4 | Matplotlib 绑图 | 1天 | [Matplotlib 官方教程](https://matplotlib.org/stable/tutorials/) |
| 5 | scikit-learn 线性回归 | 1天 | [scikit-learn LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html) |
| 6 | MySQL + SQLAlchemy | 2天 | [SQLAlchemy ORM 教程](https://docs.sqlalchemy.org/en/20/orm/) |
| 7 | Git 基础 | 1天 | [Git 简明指南](https://rogerdudler.github.io/git-guide/index.zh.html) |

> **总计学习时间**：约 10 天。建议 Week 1 集中学习，Week 2-3 边做边学。

---

## 九、风险预案

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| MySQL 安装配置困难 | 高 | 中 | 准备 SQLite 降级方案（改动极小） |
| FastAPI 异步概念难理解 | 中 | 中 | 简单路由用同步函数 `def`，不强制 async |
| Matplotlib 中文乱码 | 高 | 低 | 提前配置好字体，写入项目 wiki |
| 团队成员进度不齐 | 中 | 高 | 每日站会同步，第 3 周初做一次进度排查 |
| scikit-learn 安装问题 | 低 | 中 | `requirements.txt` 固定版本号，用 `pip install -r` 统一安装 |
| 时间不够完成所有扩展 | 中 | 中 | 扩展按优先级做：算法对比 > 用户系统 > 数据库 > 自动清洗 |

---

## 十、后续行动建议

1. **立即行动**：项目经理召集全员会议，分配角色，建立 Git 仓库
2. **Week 1 重点**：环境统一 + `requirements.txt` + 骨架代码跑通
3. **接口契约先行**：所有人开始写代码前，先定好 API 的请求/响应格式
4. **个人文档边做边写**：不要最后一天赶文档，每完成一个模块就记录
5. **常回头看评分表**：确保每个评分点都有对应功能

---

## 十一、模块验收标准（逐模块可验证）

> 每完成一个模块，对照以下验收标准自行验证，确保功能可用后再进入下一模块。

### 11.1 数据管理模块

- [ ] **验收 1：文件上传**
  - 操作：打开 `http://localhost:8000/`，选择一个 `.csv` 文件点击上传
  - 预期：页面跳转到预览页，表格显示数据前 10 行
  - 失败标志：白页/报错/表格为空/乱码
  
- [ ] **验收 2：Excel 文件兼容**
  - 操作：上传一个 `.xlsx` 文件
  - 预期：同 CSV，正确显示数据
  
- [ ] **验收 3：编码兼容**
  - 操作：分别上传 UTF-8 和 GBK 编码的 CSV 文件
  - 预期：两种编码均正常显示，无乱码
  
- [ ] **验收 4：内置数据切换**
  - 操作：访问内置模拟数据入口，加载 `sample_housing.csv`
  - 预期：与上传文件效果相同，显示数据预览

### 11.2 数据清洗模块

- [ ] **验收 5：缺失值检测**
  - 操作：上传一个含空值的数据集，点击"数据清洗"
  - 预期：页面显示各列缺失值数量和比例统计
  
- [ ] **验收 6：均值填充**
  - 操作：选择数值列 → 策略选"均值填充" → 执行清洗
  - 预期：该列缺失值被列均值替换，清洗后数据预览中该列无空值
  
- [ ] **验收 7：异常值剔除**
  - 操作：对含极端值的数据列 → 策略选"IQR 异常值剔除" → 执行
  - 预期：极端值所在行被移除，行数减少
  
- [ ] **验收 8：一键自动清洗（扩展）**
  - 操作：点击"智能清洗"按钮
  - 预期：无需手动选择策略，系统自动完成清洗并报告处理了哪些列

### 11.3 可视化模块

- [ ] **验收 9：折线图生成**
  - 操作：选择 X 列 + Y 列 → 图表类型选"折线图" → 生成
  - 预期：页面出现一张折线图 PNG，X/Y 轴标签正确，标题可读
  
- [ ] **验收 10：柱状图生成**
  - 操作：选择分类列(X) + 数值列(Y) → 图表类型选"柱状图" → 生成
  - 预期：柱状图正确显示，柱子高度对应数值
  
- [ ] **验收 11：散点图生成**
  - 操作：选择两个数值列 → 图表类型选"散点图" → 生成
  - 预期：散点图显示数据点分布，可见相关性趋势
  
- [ ] **验收 12：图表参数调整**
  - 操作：修改标题文字 + 切换颜色主题 → 重新生成
  - 预期：新图表反映参数修改（标题改变、颜色改变）
  
- [ ] **验收 13：中文显示**
  - 操作：在图表中使用中文列名和标题
  - 预期：中文正常显示，无方块乱码

### 11.4 算法分析模块

- [ ] **验收 14：线性回归训练**
  - 操作：选择特征列(≥1个) + 目标列 → 点击"训练模型"
  - 预期：页面显示回归系数表、R² 分数(>0)、MSE 数值
  
- [ ] **验收 15：预测功能**
  - 操作：输入新样本的特征值 → 点击"预测"
  - 预期：返回预测结果数值，无报错
  
- [ ] **验收 16：算法对比（扩展）**
  - 操作：点击"算法对比"，勾选线性回归 + 岭回归 + Lasso
  - 预期：三种算法的 R²、MSE、MAE 并列展示在对比表格中
  
- [ ] **验收 17：边界情况**
  - 操作：选择与目标列无相关性的特征列 → 训练
  - 预期：不崩溃，显示较低的 R² 值（如 ≈0），提示"该特征与目标变量相关性较弱"

### 11.5 Web 服务与用户系统

- [ ] **验收 18：全流程串联**
  - 操作：从首页上传 → 预览 → 清洗 → 生成图表 → 回归分析，走完整流程
  - 预期：每一步都能正常跳转，数据在页面间正确传递
  
- [ ] **验收 19：用户注册**
  - 操作：填写用户名 + 密码 + 确认密码 → 注册
  - 预期：注册成功，跳转到登录页；重复用户名提示"用户名已存在"
  
- [ ] **验收 20：用户登录**
  - 操作：用已注册账号登录
  - 预期：登录成功，导航栏显示用户名；输错密码提示"密码错误"
  
- [ ] **验收 21：历史记录（扩展）**
  - 操作：登录后完成一次完整分析 → 访问"历史记录"页
  - 预期：看到刚才的分析记录，点击可查看详情（参数+图表+指标）
  
- [ ] **验收 22：404 友好处理**
  - 操作：访问 `http://localhost:8000/nonexistent`
  - 预期：显示友好的 404 页面（非浏览器默认白页）

### 11.6 数据库

- [ ] **验收 23：MySQL 连接**
  - 操作：启动应用，确认无数据库连接错误
  - 预期：控制台无 `Connection refused` 或 `Access denied` 错误
  
- [ ] **验收 24：数据持久化**
  - 操作：注册一个用户 → 重启应用 → 用该账号登录
  - 预期：登录成功（说明用户数据已持久化到 MySQL）

---

> 📌 **框架版本**: v1.1  
> 📌 **生成日期**: 2026-05-25  
> 📌 **适用团队**: Python 初学者为主，5-6 人组，2-4 周开发周期
