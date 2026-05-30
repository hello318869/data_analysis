"""
用户认证路由 (注册 / 登录 / 登出)
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from models import get_db
from models.user import User
from schemas.user import UserLogin, UserRegister
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
    # Validate with Pydantic schema
    try:
        _ = UserLogin(username=username, password=password)
    except ValidationError as e:
        messages: list[str] = []
        for error in e.errors():
            messages.append(error.get("msg", "输入格式错误"))
        return templates.TemplateResponse(request, "login.html", {
            "error": "；".join(messages),
            "message": None
        }, status_code=400)
    
    try:
        with get_db() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user or not verify_password(password, user.password_hash):
                return templates.TemplateResponse(request, "login.html", {
                    "error": "用户名或密码错误",
                    "message": None
                }, status_code=400)
            request.session["user"] = {"id": user.id, "username": user.username}
            return RedirectResponse(url="/", status_code=303)
    except OperationalError:
        return templates.TemplateResponse(request, "login.html", {
            "error": "服务暂时不可用，请稍后重试",
            "message": None
        }, status_code=500)


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
    # Validate with Pydantic schema (replaces manual checks)
    try:
        _ = UserRegister(username=username, password=password, confirm_password=confirm_password)
    except ValidationError as e:
        messages: list[str] = []
        for error in e.errors():
            messages.append(error.get("msg", "输入格式错误"))
        return templates.TemplateResponse(request, "register.html", {
            "error": "；".join(messages)
        }, status_code=400)
    
    with get_db() as db:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return templates.TemplateResponse(request, "register.html", {
                "error": "用户名已存在"
            }, status_code=400)
        
        try:
            new_user = User(username=username, password_hash=hash_password(password))
            db.add(new_user)
            db.commit()
        except (IntegrityError, OperationalError) as e:
            db.rollback()
            error_msg = "用户名已存在" if isinstance(e, IntegrityError) else "服务暂时不可用，请稍后重试"
            return templates.TemplateResponse(request, "register.html", {
                "error": error_msg
            }, status_code=400)
        
        return RedirectResponse(url="/auth/login?registered=1", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    """登出"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
