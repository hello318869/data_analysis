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
from routes import analysis_routes, data_routes

# Create all tables on startup
try:
    Base.metadata.create_all(bind=engine)
except SQLAlchemyError as exc:
    print(f"数据库初始化失败，应用将继续启动：{exc}")

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

# Share templates with route modules
main_routes.templates = templates
analysis_routes.templates = templates
auth_routes.templates = templates
history_routes.templates = templates
data_routes.templates = templates
