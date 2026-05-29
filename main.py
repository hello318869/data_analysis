"""
交互式数据分析系统 - FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

from config import SECRET_KEY, BASE_DIR
from models import engine, Base
from routes import main_routes, auth_routes, history_routes
from routes import analysis_routes, clean_routes, data_routes, viz_routes

# Create all tables on startup
import sys

try:
    Base.metadata.create_all(bind=engine)
    print("数据库表初始化成功")
except SQLAlchemyError as exc:
    print(
        f"\n[ERROR] 数据库初始化失败：{exc}\n"
        "  请检查：\n"
        "  1. MySQL 服务是否已启动\n"
        "  2. config.py 中 DATABASE_URL 的用户名/密码/地址是否正确\n"
        "  3. 数据库 data_analysis_db 是否已创建\n"
        "  应用将继续启动，但涉及数据库的功能将不可用。\n",
        file=sys.stderr,
    )

app = FastAPI(title="交互式数据分析系统", version="1.0.0")

# Session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(main_routes.router)
app.include_router(analysis_routes.router, prefix="/analysis", tags=["算法分析"])
app.include_router(auth_routes.router, prefix="/auth", tags=["认证"])
app.include_router(history_routes.router, prefix="/history", tags=["历史记录"])
app.include_router(data_routes.router, prefix="/data", tags=["数据管理"])
app.include_router(clean_routes.router, tags=["数据清洗"])
app.include_router(viz_routes.router, tags=["可视化"])

# Share templates with route modules
main_routes.templates = templates
analysis_routes.templates = templates
auth_routes.templates = templates
history_routes.templates = templates
data_routes.templates = templates
clean_routes.templates = templates
viz_routes.templates = templates
