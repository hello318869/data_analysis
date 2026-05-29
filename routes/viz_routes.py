"""Visualization routes."""
from __future__ import annotations

import math
from typing import Any

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from services.data_service import load_dataframe_from_session


router = APIRouter()
templates = None


def _format_value(value: Any) -> str:
    if pd.isna(value):
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _build_numeric_cards(df: pd.DataFrame) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    numeric_df = df.select_dtypes(include="number")

    for column in numeric_df.columns:
        series = numeric_df[column].dropna()
        if series.empty:
            continue

        cards.append(
            {
                "column": column,
                "mean": _format_value(series.mean()),
                "min": _format_value(series.min()),
                "max": _format_value(series.max()),
                "missing": int(df[column].isna().sum()),
            }
        )

    return cards


def _build_distribution(df: pd.DataFrame) -> dict[str, Any] | None:
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return None

    column = numeric_df.columns[0]
    series = numeric_df[column].dropna()
    if series.empty:
        return None

    counts = series.value_counts(bins=min(8, max(1, math.ceil(len(series) ** 0.5))))
    max_count = int(counts.max()) if not counts.empty else 1

    bars = []
    for interval, count in counts.sort_index().items():
        bars.append(
            {
                "label": f"{interval.left:.1f} - {interval.right:.1f}",
                "count": int(count),
                "percent": int((int(count) / max_count) * 100) if max_count else 0,
            }
        )

    return {"column": column, "bars": bars}


@router.get("/viz", response_class=HTMLResponse)
async def visualization_page(request: Request):
    df = load_dataframe_from_session(request)
    if df is None:
        request.session["flash_error"] = "请先上传数据文件"
        return RedirectResponse(url="/data/upload", status_code=303)

    context = {
        "user": request.session.get("user"),
        "filename": request.session.get("filename", "unknown"),
        "row_count": len(df),
        "column_count": len(df.columns),
        "numeric_cards": _build_numeric_cards(df),
        "distribution": _build_distribution(df),
        "columns": df.columns.tolist(),
    }
    return templates.TemplateResponse(request, "viz.html", context)
