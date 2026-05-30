"""
算法分析路由：展示分析页面、运行回归分析、查看上次结果。
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from models import get_db
from models.analysis_record import AnalysisRecord
from schemas.analysis import AnalysisParams
from services.data_service import load_dataframe_from_session
from services.ml_service import compare_regression_models, run_linear_regression


router = APIRouter()
templates = None  # Will be set by main.py


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


def _predict_single(
    features: list[str],
    coefficients: dict[str, float],
    intercept: float,
    input_values: dict[str, float],
) -> float:
    """Compute prediction: intercept + sum(c_i * v_i)."""
    return intercept + sum(coefficients[f] * input_values[f] for f in features)


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
        df = load_dataframe_from_session(request)
        if df is None:
            raise ValueError("请先上传数据文件")
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
        df = load_dataframe_from_session(request)
        if df is None:
            raise ValueError("请先上传数据文件")
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    try:
        result = run_linear_regression(df, params.features, params.target)
        request.session["last_analysis"] = {
            "analysis_type": "regression",
            "features": result["features"],
            "target": result["target"],
            "coefficients": result["coefficients"],
            "intercept": result["intercept"],
            "r2_score": result["r2_score"],
            "mse": result["mse"],
            "mae": result["mae"],
            "train_size": result["train_size"],
            "test_size": result["test_size"],
            "scatter_chart_path": result["scatter_chart_path"],
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
        df = load_dataframe_from_session(request)
        if df is None:
            raise ValueError("请先上传数据文件")
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    try:
        result = run_linear_regression(df, params.features, params.target)
        compare_result = compare_regression_models(df, params.features, params.target)
        result.update(compare_result)
        request.session["last_analysis"] = {
            "analysis_type": "compare",
            "features": result["features"],
            "target": result["target"],
            "coefficients": result["coefficients"],
            "intercept": result["intercept"],
            "r2_score": result["r2_score"],
            "mse": result["mse"],
            "mae": result["mae"],
            "train_size": result["train_size"],
            "test_size": result["test_size"],
            "scatter_chart_path": result["scatter_chart_path"],
            "comparison": compare_result.get("comparison"),
            "best_algorithm": compare_result.get("best_algorithm"),
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


@router.post("/predict", response_class=HTMLResponse)
async def predict_single(request: Request):
    """手动预测：基于上次训练模型的系数和截距，对用户输入进行预测。"""
    try:
        df = load_dataframe_from_session(request)
        if df is None:
            raise ValueError("请先上传数据文件")
    except ValueError as exc:
        return _redirect_home_with_message(request, str(exc))

    last_analysis = request.session.get("last_analysis")
    if not last_analysis:
        return _redirect_home_with_message(request, "请先运行一次回归分析")

    features = last_analysis.get("features", [])
    target = last_analysis.get("target", "")
    coefficients = last_analysis.get("coefficients", {})
    intercept = last_analysis.get("intercept", 0.0)

    if not features or not target or not coefficients:
        return _redirect_home_with_message(request, "上次分析数据不完整，请重新运行回归分析")

    try:

        # Parse form input (one field per feature, using feature name as form key)
        form_data = await request.form()
        input_values: dict[str, float] = {}
        for feat in features:
            raw = form_data.get(feat)
            if raw is None:
                raise ValueError(f"缺少特征值：{feat}")
            try:
                input_values[feat] = float(raw)
            except (ValueError, TypeError):
                raise ValueError(f"特征 {feat} 的值不是有效数字")

        # Compute prediction using coefficients from session
        prediction = _predict_single(features, coefficients, intercept, input_values)

        context = _build_page_context(request, df, {
            **last_analysis,
            "prediction_input": input_values,
            "prediction_result": prediction,
        })
    except ValueError as exc:
        context = _build_page_context(request, df, {"error": str(exc)})
    except Exception as exc:
        context = _build_page_context(
            request, df, {"error": f"预测失败：{exc}"}
        )

    return templates.TemplateResponse(request, "analysis.html", context)


@router.get("/result", response_class=HTMLResponse)
async def last_analysis_result(request: Request):
    """查看 session 中保存的上一次算法分析结果。"""
    last_analysis = request.session.get("last_analysis")
    if not last_analysis:
        return RedirectResponse(url="/analysis", status_code=303)

    try:
        df = load_dataframe_from_session(request)
        if df is None:
            raise ValueError("请先上传数据文件")
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
