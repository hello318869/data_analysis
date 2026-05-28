"""
历史记录路由 (查看 / 删除过往分析记录)
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from models import get_db
from models.analysis_record import AnalysisRecord

router = APIRouter()
templates = None  # Will be set by main.py


@router.get("", response_class=HTMLResponse)
async def list_history(request: Request):
    """查看历史分析记录列表"""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    with get_db() as db:
        records = db.query(AnalysisRecord).filter(
            AnalysisRecord.user_id == user["id"]
        ).order_by(AnalysisRecord.created_at.desc()).all()

        return templates.TemplateResponse(request, "history.html", {
            "user": user,
            "records": records
        })


@router.get("/{record_id}", response_class=HTMLResponse)
async def view_record(request: Request, record_id: int):
    """查看某次分析的详细信息"""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    with get_db() as db:
        record = db.query(AnalysisRecord).filter(
            AnalysisRecord.id == record_id,
            AnalysisRecord.user_id == user["id"]
        ).first()

        if not record:
            return templates.TemplateResponse(request, "history.html", {
                "user": user,
                "records": [],
                "error": "记录不存在或无权访问"
            })

        return templates.TemplateResponse(request, "history_detail.html", {
            "user": user,
            "record": record
        })


@router.post("/{record_id}/delete")
async def delete_record(request: Request, record_id: int):
    """删除某次分析记录"""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    with get_db() as db:
        record = db.query(AnalysisRecord).filter(
            AnalysisRecord.id == record_id,
            AnalysisRecord.user_id == user["id"]
        ).first()

        if record:
            db.delete(record)
            db.commit()

        return RedirectResponse(url="/history", status_code=303)
