"""
用户认证路由 (注册 / 登录 / 登出)
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError

from models import get_db
from models.user import User
from services.auth_service import hash_password, verify_password

router = APIRouter()
templates: Jinja2Templates = None  # Will be set by main.py


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    registered = request.query_params.get("registered")
    message = "注册成功，请登录" if registered else None
    return templates.TemplateResponse(request, "login.html", {
        "error": None,
        "message": message
    })


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """处理登录请求"""
    with get_db() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return templates.TemplateResponse(request, "login.html", {
                "error": "用户名或密码错误",
                "message": None
            }, status_code=401)

        request.session["user"] = {"id": user.id, "username": user.username}
        return RedirectResponse(url="/", status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse(request, "register.html", {
        "error": None
    })


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """处理注册请求"""
    # Validate
    if password != confirm_password:
        return templates.TemplateResponse(request, "register.html", {
            "error": "两次输入的密码不一致"
        }, status_code=400)

    if len(username) < 3 or len(password) < 6:
        return templates.TemplateResponse(request, "register.html", {
            "error": "用户名至少3位，密码至少6位"
        }, status_code=400)

    with get_db() as db:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return templates.TemplateResponse(request, "register.html", {
                "error": "用户名已存在"
            }, status_code=400)

        try:
            new_user = User(
                username=username,
                password_hash=hash_password(password)
            )
            db.add(new_user)
            db.commit()
        except IntegrityError:
            db.rollback()
            return templates.TemplateResponse(request, "register.html", {
                "error": "用户名已存在"
            }, status_code=400)

        return RedirectResponse(url="/auth/login?registered=1", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    """登出"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
