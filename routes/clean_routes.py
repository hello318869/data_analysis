"""
数据清洗路由：清洗报告、手动清洗、自动清洗、规则集管理。
"""
from __future__ import annotations

import json
from io import StringIO
from typing import Any

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.clean_service import (
    analyze_missing, detect_outliers_iqr, execute_clean, auto_clean,
    PRESETS, RuleSet, ColumnRule,
    list_saved_rules, load_ruleset, save_ruleset, delete_ruleset,
    validate_ruleset, apply_ruleset,
)


router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def _parse_body(request: Request) -> dict[str, Any]:
    """JSON 和 form 数据兼容解析。"""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    form = await request.form()
    return {k: v for k, v in form.items()}


def _load_dataframe_from_session(request: Request) -> pd.DataFrame:
    """从 session["df_json"] 还原 DataFrame。"""
    df_json = request.session.get("df_json")
    if not df_json:
        raise ValueError("请先上传数据文件")

    if isinstance(df_json, str):
        try:
            parsed = json.loads(df_json)
        except json.JSONDecodeError:
            return pd.read_json(StringIO(df_json), orient="split")
    else:
        parsed = df_json

    if isinstance(parsed, dict) and {"columns", "data"}.issubset(parsed):
        return pd.DataFrame(parsed["data"], columns=parsed["columns"], index=parsed.get("index"))

    if isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
        return pd.DataFrame(parsed["data"])

    if isinstance(parsed, list):
        return pd.DataFrame(parsed)

    if isinstance(parsed, dict):
        return pd.DataFrame(parsed)

    raise ValueError("无法读取 session 中的数据，请重新上传数据文件")


def _get_filename(request: Request) -> str | None:
    return (
        request.session.get("filename")
        or request.session.get("current_filename")
        or request.session.get("uploaded_filename")
    )


def _redirect_home_with_message(request: Request, message: str) -> RedirectResponse:
    request.session["flash_error"] = message
    return RedirectResponse(url="/", status_code=303)


def _clean_preview_rows(df: pd.DataFrame, n: int = 10) -> list[list[Any]]:
    """取前 n 行，NaN → None（模板渲染安全）。"""
    preview = df.head(n).copy()
    for col in preview.columns:
        if pd.api.types.is_datetime64_any_dtype(preview[col]):
            preview[col] = preview[col].astype(str)
    return preview.where(pd.notna(preview), None).values.tolist()


def _clean_page_context(request: Request, df: pd.DataFrame, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """组装 clean.html 模板变量。"""
    ctx = {
        "request": request,
        "user": request.session.get("user"),
        "filename": _get_filename(request),
        "missing_report": analyze_missing(df),
        "outlier_report": detect_outliers_iqr(df),
        "columns": list(df.columns),
        "rows": _clean_preview_rows(df),
        "row_count": len(df),
        "column_count": len(df.columns),
        "presets": list(PRESETS.keys()),
        "saved_rules": list_saved_rules(),
    }
    if extra:
        ctx.update(extra)
    return ctx


# ====================== 数据清洗页面 ======================

@router.get("/clean", response_class=HTMLResponse)
async def clean_page(request: Request):
    """GET /analysis/clean — 清洗前报告页面。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    return templates.TemplateResponse(request, "clean.html", _clean_page_context(request, df))


@router.post("/clean/execute", response_class=HTMLResponse)
async def clean_execute(request: Request):
    """POST /analysis/clean/execute — 按策略清洗指定列。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    body: dict[str, Any] = await request.json()
    strategy: str = body.get("strategy", "mean")
    columns: list[str] = body.get("columns", [])
    fill_value: Any = body.get("fill_value")

    if not columns:
        return templates.TemplateResponse(
            request, "clean.html",
            _clean_page_context(request, df, {"error": "请选择至少一列进行清洗"})
        )

    valid_strategies = {"mean", "median", "mode", "drop", "custom"}
    if strategy not in valid_strategies:
        return templates.TemplateResponse(
            request, "clean.html",
            _clean_page_context(request, df, {"error": f"无效策略 {strategy}"})
        )

    if strategy == "custom" and fill_value is not None:
        try:
            fill_value = float(fill_value)
        except (ValueError, TypeError):
            pass

    df_cleaned, cleaned_count, messages = execute_clean(df, strategy, columns, fill_value)
    df_cleaned = df_cleaned.reset_index(drop=True)

    request.session["df_json"] = df_cleaned.to_json(orient="split")

    return templates.TemplateResponse(
        request, "clean.html",
        _clean_page_context(request, df_cleaned, {
            "message": "; ".join(messages) if messages else "清洗完成",
            "cleaned_count": cleaned_count,
        })
    )


@router.post("/clean/auto", response_class=HTMLResponse)
async def clean_auto(request: Request):
    """POST /analysis/clean/auto — 一键自动清洗。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    df_cleaned, cleaned_count, messages = auto_clean(df)
    df_cleaned = df_cleaned.reset_index(drop=True)

    request.session["df_json"] = df_cleaned.to_json(orient="split")

    return templates.TemplateResponse(
        request, "clean.html",
        _clean_page_context(request, df_cleaned, {
            "message": "; ".join(messages) if messages else "自动清洗完成",
            "cleaned_count": cleaned_count,
        })
    )


@router.get("/clean/rules", response_class=HTMLResponse)
async def clean_rules_list(request: Request):
    """GET /analysis/clean/rules — 规则集列表页面。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    return templates.TemplateResponse(
        request, "clean.html",
        _clean_page_context(request, df, {"show_rules_tab": True})
    )


@router.post("/clean/rules/apply", response_class=HTMLResponse)
async def clean_rules_apply(request: Request):
    """POST /analysis/clean/rules/apply — 按规则集执行清洗。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    body: dict[str, Any] = await _parse_body(request)
    name: str | None = body.get("name")
    ruleset: RuleSet | None = None

    if name:
        ruleset = load_ruleset(name)
        if ruleset is None:
            return templates.TemplateResponse(
                request, "clean.html",
                _clean_page_context(request, df, {"error": f"规则集 '{name}' 不存在"})
            )
    elif "ruleset" in body:
        try:
            ruleset = RuleSet.from_dict(body["ruleset"])
            errors = validate_ruleset(ruleset)
            if errors:
                return templates.TemplateResponse(
                    request, "clean.html",
                    _clean_page_context(request, df, {"error": "规则校验失败: " + "; ".join(errors)})
                )
        except Exception as e:
            return templates.TemplateResponse(
                request, "clean.html",
                _clean_page_context(request, df, {"error": f"规则集格式错误: {e}"})
            )
    else:
        return templates.TemplateResponse(
            request, "clean.html",
            _clean_page_context(request, df, {"error": "请提供 name 或 ruleset"})
        )

    df_cleaned, cleaned_count, messages = apply_ruleset(df, ruleset)
    df_cleaned = df_cleaned.reset_index(drop=True)

    request.session["df_json"] = df_cleaned.to_json(orient="split")

    return templates.TemplateResponse(
        request, "clean.html",
        _clean_page_context(request, df_cleaned, {
            "message": "; ".join(messages) if messages else "规则集清洗完成",
            "cleaned_count": cleaned_count,
        })
    )


@router.post("/clean/rules/save", response_class=HTMLResponse)
async def clean_rules_save(request: Request):
    """POST /analysis/clean/rules/save — 保存自定义规则集。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    body: dict[str, Any] = await _parse_body(request)
    try:
        ruleset = RuleSet.from_dict(body)
    except Exception as e:
        return templates.TemplateResponse(
            request, "clean.html",
            _clean_page_context(request, df, {"error": f"规则集格式错误: {e}"})
        )

    errors = validate_ruleset(ruleset)
    if errors:
        return templates.TemplateResponse(
            request, "clean.html",
            _clean_page_context(request, df, {"error": "规则校验失败: " + "; ".join(errors)})
        )

    if ruleset.name in PRESETS:
        return templates.TemplateResponse(
            request, "clean.html",
            _clean_page_context(request, df, {"error": f"'{ruleset.name}' 是预设规则集，不可覆盖"})
        )

    save_ruleset(ruleset)
    return templates.TemplateResponse(
        request, "clean.html",
        _clean_page_context(request, df, {
            "message": f"规则集 '{ruleset.name}' 已保存",
            "saved_rules": list_saved_rules(),
        })
    )


@router.post("/clean/rules/delete", response_class=HTMLResponse)
async def clean_rules_delete(request: Request):
    """POST /analysis/clean/rules/delete — 删除已保存的规则集。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    body: dict[str, Any] = await _parse_body(request)
    name: str = body.get("name", "")

    if name in PRESETS:
        return templates.TemplateResponse(
            request, "clean.html",
            _clean_page_context(request, df, {"error": f"'{name}' 是预设规则集，不可删除"})
        )

    ok = delete_ruleset(name)
    return templates.TemplateResponse(
        request, "clean.html",
        _clean_page_context(request, df, {
            "message": f"规则集 '{name}' 已删除" if ok else f"规则集 '{name}' 不存在",
            "saved_rules": list_saved_rules(),
        })
    )
