"""
首页路由 - 系统入口页面
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models import get_db

router = APIRouter()
templates: Jinja2Templates = None  # Will be set by main.py


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 - 系统入口"""
    with get_db() as db:
        user = request.session.get("user")
        error = request.session.pop("flash_error", None)
        message = request.session.pop("flash_message", None)
        return templates.TemplateResponse(request, "index.html", {
            "user": user,
            "error": error,
            "message": message,
        })
