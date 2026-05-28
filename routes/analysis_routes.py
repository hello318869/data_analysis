"""
算法分析路由：展示分析页面、运行回归分析、查看上次结果。
"""
from __future__ import annotations

import json
from io import StringIO
from typing import Any

import pandas as pd
from fastapi import APIRouter, Request ,Form
from fastapi.responses import HTMLResponse, RedirectResponse

from models import get_db
from models.analysis_record import AnalysisRecord
from schemas.analysis import AnalysisParams
from services.ml_service import compare_regression_models, run_linear_regression


router = APIRouter()
templates = None  # Will be set by main.py


def _load_dataframe_from_session(request: Request) -> pd.DataFrame:
    """从 session["df_json"] 还原 DataFrame。"""
    df_json = request.session.get("df_json")
    if not df_json:
        raise ValueError("请先上传数据文件")

    if isinstance(df_json, str):
        try:
            parsed = json.loads(df_json)
        except json.JSONDecodeError:
            return pd.read_json(StringIO(df_json))
    else:
        parsed = df_json

    if isinstance(parsed, dict) and {"columns", "data"}.issubset(parsed):
        return pd.DataFrame(
            parsed["data"],
            columns=parsed["columns"],
            index=parsed.get("index"),
        )

    if isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
        return pd.DataFrame(parsed["data"])

    if isinstance(parsed, list):
        return pd.DataFrame(parsed)

    if isinstance(parsed, dict):
        return pd.DataFrame(parsed)

    raise ValueError("无法读取 session 中的数据，请重新上传数据文件")


def _get_filename(request: Request) -> str | None:
    """兼容不同数据上传模块可能使用的文件名 session key。"""
    return (
        request.session.get("filename")
        or request.session.get("current_filename")
        or request.session.get("uploaded_filename")
    )


def _build_page_context(
    request: Request,
    df: pd.DataFrame,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """组装 analysis.html 每次渲染都需要的基础变量。"""
    context = {
        "user": request.session.get("user"),
        "columns": df.columns.tolist(),
        "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
        "filename": _get_filename(request),
    }
    if extra:
        context.update(extra)
    return context


def _redirect_home_with_message(request: Request, message: str) -> RedirectResponse:
    """没有数据时返回首页，并把提示放入 session 供首页读取。"""
    request.session["flash_error"] = message
    return RedirectResponse(url="/", status_code=303)


def _format_regression_summary(result: dict[str, Any], model_name: str) -> str:
    """生成写入历史记录表的简短摘要。"""
    return (
        f"模型：{model_name}；"
        f"R²={result.get('r2_score', 0):.4f}，"
        f"MSE={result.get('mse', 0):.4f}，"
        f"MAE={result.get('mae', 0):.4f}"
    )


def _save_analysis_record(
    request: Request,
    analysis_type: str,
    params: AnalysisParams,
    result: dict[str, Any],
) -> None:
    """登录用户执行分析后，把本次结果写入 analysis_records 表。"""
    user = request.session.get("user")
    if not user:
        return

    chart_path = result.get("scatter_chart_path")
    model_name = result.get("best_algorithm") or "LinearRegression"
    summary = _format_regression_summary(result, model_name)

    if analysis_type == "compare" and result.get("best_algorithm"):
        summary = f"{summary}；最佳算法：{result['best_algorithm']}"

    try:
        with get_db() as db:
            record = AnalysisRecord(
                user_id=user["id"],
                dataset_id=request.session.get("current_dataset_id"),
                analysis_type=analysis_type,
                parameters={
                    "features": params.features,
                    "target": params.target,
                },
                result_summary=summary,
                chart_paths=[chart_path] if chart_path else [],
            )
            db.add(record)
            db.commit()
    except Exception as exc:
        # 历史记录是附加能力，数据库临时不可用时不应影响分析结果展示。
        print(f"保存分析记录失败：{exc}")
        return


@router.get("", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """展示算法分析页面。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    return templates.TemplateResponse(
        request,
        "analysis.html",
        _build_page_context(request, df),
    )


@router.post("/regression", response_class=HTMLResponse)
async def regression_analysis(request: Request, params: AnalysisParams):
    """运行线性回归分析，并返回 HTML 结果页。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    try:
        result = run_linear_regression(df, params.features, params.target)
        request.session["last_analysis"] = {
            "analysis_type": "regression",
            **result,
        }
        _save_analysis_record(request, "regression", params, result)
        context = _build_page_context(request, df, result)
    except ValueError as exc:
        context = _build_page_context(request, df, {"error": str(exc)})
    except Exception as exc:
        context = _build_page_context(
            request, df, {"error": f"算法分析失败：{exc}"}
        )

    return templates.TemplateResponse(request, "analysis.html", context)


@router.post("/compare", response_class=HTMLResponse)
async def compare_analysis(request: Request, params: AnalysisParams):
    """运行线性回归基础结果，并额外对比 LinearRegression/Ridge/Lasso。"""
    try:
        df = _load_dataframe_from_session(request)
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    try:
        result = run_linear_regression(df, params.features, params.target)
        compare_result = compare_regression_models(df, params.features, params.target)
        result.update(compare_result)
        request.session["last_analysis"] = {
            "analysis_type": "compare",
            **result,
        }
        _save_analysis_record(request, "compare", params, result)
        context = _build_page_context(request, df, result)
    except ValueError as exc:
        context = _build_page_context(request, df, {"error": str(exc)})
    except Exception as exc:
        context = _build_page_context(
            request, df, {"error": f"算法分析失败：{exc}"}
        )

    return templates.TemplateResponse(request, "analysis.html", context)


@router.get("/result", response_class=HTMLResponse)
async def last_analysis_result(request: Request):
    """查看 session 中保存的上一次算法分析结果。"""
    last_analysis = request.session.get("last_analysis")
    if not last_analysis:
        return RedirectResponse(url="/analysis", status_code=303)

    try:
        df = _load_dataframe_from_session(request)
        context = _build_page_context(request, df, last_analysis)
    except ValueError:
        context = {
            "user": request.session.get("user"),
            "columns": last_analysis.get("features", []),
            "numeric_columns": last_analysis.get("features", []),
            "filename": _get_filename(request),
            **last_analysis,
        }

    return templates.TemplateResponse(request, "analysis.html", context)
