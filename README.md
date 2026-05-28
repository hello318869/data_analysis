# 交互式数据分析系统

基于 FastAPI + Matplotlib + scikit-learn + MySQL 的 Web 交互式数据分析平台。

## 功能特性

- 📤 **数据上传**：支持 CSV / Excel 格式，自动编码检测
- 🧹 **数据清洗**：缺失值填充、异常值检测、归一化处理
- 📊 **可视化分析**：折线图、柱状图、散点图，参数可配置
- 🤖 **机器学习**：线性回归预测，支持 Ridge / Lasso 算法对比
- 👤 **用户系统**：注册、登录、历史记录管理

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI + Jinja2 (服务端渲染) |
| 数据处理 | Pandas + NumPy |
| 机器学习 | scikit-learn (LinearRegression / Ridge / Lasso) |
| 可视化 | Matplotlib (Agg 后端) |
| 数据库 | MySQL 8.0 + SQLAlchemy ORM |
| 认证 | bcrypt 密码哈希 + Session |
| 前端 | 原生 HTML/CSS/JS，响应式布局 |

## 项目结构

```
data-analysis-system/
├── main.py              # FastAPI 应用入口
├── config.py            # 数据库配置、路径常量
├── requirements.txt     # Python 依赖清单
├── models/              # SQLAlchemy ORM 模型
│   ├── user.py          # 用户表模型
│   └── analysis_record.py  # 数据集 & 分析记录模型
├── schemas/             # Pydantic 请求/响应校验
│   ├── user.py          # 注册/登录校验
│   └── analysis.py      # 分析参数校验
├── services/            # 业务逻辑层
│   └── auth_service.py  # 密码哈希与验证
├── routes/              # 路由控制器
│   ├── main_routes.py   # 首页
│   ├── auth_routes.py   # 注册/登录/登出
│   └── history_routes.py # 历史记录
├── templates/           # Jinja2 模板
│   ├── base.html        # 基础布局
│   ├── index.html       # 首页
│   ├── login.html       # 登录
│   ├── register.html    # 注册
│   ├── history.html     # 历史记录列表
│   └── history_detail.html # 详情
├── static/              # 静态文件 (CSS, JS, 上传文件)
├── outputs/charts/      # 生成的图表图片
├── data/                # 示例数据
│   └── sample_housing.csv  # 房价预测数据集
└── database/
    └── init.sql         # MySQL 建表脚本
```

## 示例数据

项目内置了 `data/sample_housing.csv` 示例数据集，包含 52 条房价记录，字段说明：

| 字段 | 含义 | 类型 | 取值范围 |
|------|------|------|----------|
| sqft | 房屋面积（平方英尺） | int | 500–4000 |
| bedrooms | 卧室数 | int | 1–6 |
| bathrooms | 浴室数 | float | 1.0–4.0 |
| age | 房龄（年） | int | 0–80 |
| price | 房价（美元） | int | 80000–800000 |

数据特点：
- 价格与面积大致呈线性关系，适合线性回归建模（R² 约 0.5–0.8）
- 包含 **4 处缺失值**：第 12 行缺少 bedrooms、第 25 行缺少 age、第 38 行缺少 price、第 45 行缺少 bathrooms，用于演示数据清洗模块的缺失值填充功能
- 包含 **2 处异常值**：第 48 行（200 sqft，$5,000,000）和第 49 行（5000 sqft，$1），用于演示异常值检测功能

## 快速开始

### 1. 环境要求

- Python 3.10+
- MySQL 8.0+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE data_analysis_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 导入建表脚本
mysql -u root -p data_analysis_db < database/init.sql
```

### 4. 配置数据库连接

编辑 `config.py`，修改 `DATABASE_URL` 中的用户名和密码：

```python
DATABASE_URL = "mysql+pymysql://root:你的密码@localhost:3306/data_analysis_db"
```

### 5. 启动应用

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000

### 6. 使用流程

1. 注册账号 → 登录
2. 上传 CSV/Excel 数据文件（或使用内置示例数据 `data/sample_housing.csv`）
3. 查看数据预览
4. 进行数据清洗（缺失值填充、异常值处理）
5. 生成可视化图表（折线图/柱状图/散点图）
6. 运行线性回归分析
7. 在历史记录中查看过往分析

## API 接口

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | / | 首页 |
| GET | /auth/login | 登录页面 |
| POST | /auth/login | 提交登录 |
| GET | /auth/register | 注册页面 |
| POST | /auth/register | 提交注册 |
| GET | /auth/logout | 登出 |
| GET | /history | 历史记录列表 |
| GET | /history/{id} | 查看详情 |
| POST | /history/{id}/delete | 删除记录 |

## 团队

本项目为 Python Web 开发课程小组项目。

## 许可证

仅供学习使用。
