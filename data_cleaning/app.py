"""数据清洗模块 — FastAPI 应用入口。

接口（参见 api-contract.md 第三章）：
  GET  /clean              清洗前报告
  POST /clean/execute      按策略手动清洗
  POST /clean/auto         一键自动清洗
  GET  /clean/rules        列出所有规则集（预设 + 已保存）
  GET  /clean/rules/{name} 获取单个规则集详情
  POST /clean/rules/apply  按规则集执行清洗
  POST /clean/rules/save   保存自定义规则集
  DELETE /clean/rules/{name} 删除已保存规则集
"""

import io
import json
import os
from typing import Any
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from data_cleaning.service import analyze_missing, detect_outliers_iqr, execute_clean, auto_clean
from data_cleaning.config import (
    PRESETS,
    ColumnRule,
    RuleSet,
    list_saved_rules,
    load_ruleset,
    save_ruleset,
    delete_ruleset,
    validate_ruleset,
    apply_ruleset,
)

SECRET_KEY = "data-cleaning-secret-key-change-in-production"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _get_df(request: Request) -> pd.DataFrame | None:
    """从 session 读取 DataFrame（契约 �7）。"""
    df_json = request.session.get("df_json")
    if not df_json:
        return None
    return pd.read_json(io.StringIO(df_json), orient="split")


def _df_to_json(df: pd.DataFrame) -> str:
    """DataFrame 序列化为 JSON 字符串存入 session。"""
    return df.to_json(orient="split")


def _preview_rows(df: pd.DataFrame, n: int = 10) -> list[list[Any]]:
    """取前 n 行，NaN → None（JSON 安全）。"""
    preview = df.head(n).copy()
    for col in preview.columns:
        if pd.api.types.is_datetime64_any_dtype(preview[col]):
            preview[col] = preview[col].astype(str)
    return json.loads(preview.where(pd.notna(preview), None).to_json(orient="values"))


# ---------------------------------------------------------------------------
# 应用初始化
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期。"""
    yield


app = FastAPI(
    title="数据清洗模块",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# 首页 — 数据清洗页面
# ---------------------------------------------------------------------------

@app.get("/")
async def index():
    """GET / — 返回清洗功能页面。"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ---------------------------------------------------------------------------
# 数据载入（模拟数据管理模块）
# ---------------------------------------------------------------------------

@app.post("/data/upload")
async def upload_data(request: Request, file: UploadFile = File(...)):
    """POST /data/upload — 上传 CSV/Excel 文件并存入 session。"""
    if not file.filename:
        return JSONResponse(status_code=400, content={"detail": "请选择文件"})

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("csv", "xlsx", "xls"):
        return JSONResponse(status_code=400, content={"detail": "仅支持 CSV / Excel 文件"})

    content = await file.read()
    try:
        if ext == "csv":
            df = None
            for enc in ("utf-8", "utf-8-sig", "gbk"):
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                return JSONResponse(status_code=400, content={"detail": "编码识别失败"})
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": f"文件解析失败: {e}"})

    df = df.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    request.session["df_json"] = _df_to_json(df)
    request.session["filename"] = file.filename

    return {
        "message": f"文件 {file.filename} 上传成功",
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
    }


@app.post("/data/seed")
async def seed_data(request: Request):
    """POST /data/seed — 直接注入 DataFrame JSON 到 session（Demo 用）。"""
    body: dict[str, Any] = await request.json()
    request.session["df_json"] = body.get("df_json", "")
    request.session["filename"] = body.get("filename", "demo.csv")
    return {"message": "数据已注入 session", "filename": request.session["filename"]}


# ---------------------------------------------------------------------------
# 3.1 清洗前报告
# ---------------------------------------------------------------------------

@app.get("/clean")
async def clean_page(request: Request):
    """GET /clean — 展示缺失值报告、异常值报告（契约 �3.1）。"""
    df = _get_df(request)
    if df is None:
        return JSONResponse(
            status_code=400,
            content={"detail": "请先上传数据文件，确保 session 中存在 df_json"},
        )

    return {
        "missing_report": analyze_missing(df),
        "outlier_report": detect_outliers_iqr(df),
        "columns": list(df.columns),
        "rows": _preview_rows(df),
        "row_count": len(df),
        "column_count": len(df.columns),
    }


# ---------------------------------------------------------------------------
# 3.2 执行清洗
# ---------------------------------------------------------------------------

@app.post("/clean/execute")
async def clean_execute(request: Request):
    """POST /clean/execute — 按策略清洗指定列（契约 �3.2）。"""
    df = _get_df(request)
    if df is None:
        return JSONResponse(
            status_code=400,
            content={"detail": "请先上传数据文件，确保 session 中存在 df_json"},
        )

    body: dict[str, Any] = await request.json()
    strategy: str = body.get("strategy", "mean")
    columns: list[str] = body.get("columns", [])
    fill_value: Any = body.get("fill_value")

    if not columns:
        return JSONResponse(
            status_code=400,
            content={"detail": "请选择至少一列进行清洗"},
        )

    valid_strategies = {"mean", "median", "mode", "drop", "custom"}
    if strategy not in valid_strategies:
        return JSONResponse(
            status_code=400,
            content={"detail": f"无效策略 {strategy}，可选值: {', '.join(valid_strategies)}"},
        )

    if strategy == "custom" and fill_value is not None:
        try:
            fill_value = float(fill_value)
        except (ValueError, TypeError):
            pass

    df_cleaned, cleaned_count, messages = execute_clean(df, strategy, columns, fill_value)
    df_cleaned = df_cleaned.reset_index(drop=True)

    request.session["df_json"] = _df_to_json(df_cleaned)

    return {
        "message": "; ".join(messages) if messages else "清洗完成",
        "cleaned_count": cleaned_count,
        "missing_report": analyze_missing(df_cleaned),
        "outlier_report": detect_outliers_iqr(df_cleaned),
        "columns": list(df_cleaned.columns),
        "rows": _preview_rows(df_cleaned),
        "row_count": len(df_cleaned),
        "column_count": len(df_cleaned.columns),
    }


# ---------------------------------------------------------------------------
# 3.3 一键自动清洗
# ---------------------------------------------------------------------------

@app.post("/clean/auto")
async def clean_auto(request: Request):
    """POST /clean/auto — 一键自动清洗（契约 �3.3）。"""
    df = _get_df(request)
    if df is None:
        return JSONResponse(
            status_code=400,
            content={"detail": "请先上传数据文件，确保 session 中存在 df_json"},
        )

    df_cleaned, cleaned_count, messages = auto_clean(df)
    df_cleaned = df_cleaned.reset_index(drop=True)

    request.session["df_json"] = _df_to_json(df_cleaned)

    return {
        "message": "; ".join(messages) if messages else "自动清洗完成",
        "cleaned_count": cleaned_count,
        "missing_report": analyze_missing(df_cleaned),
        "outlier_report": detect_outliers_iqr(df_cleaned),
        "columns": list(df_cleaned.columns),
        "rows": _preview_rows(df_cleaned),
        "row_count": len(df_cleaned),
        "column_count": len(df_cleaned.columns),
    }


# ---------------------------------------------------------------------------
# 3.4 规则集管理
# ---------------------------------------------------------------------------

@app.get("/clean/rules")
async def list_rules():
    """GET /clean/rules — 列出所有可用规则集。"""
    saved = list_saved_rules()
    return {
        "presets": list(PRESETS.keys()),
        "saved": saved,
    }


@app.get("/clean/rules/{name}")
async def get_rule(name: str):
    """GET /clean/rules/{name} — 获取单个规则集详情。"""
    ruleset = load_ruleset(name)
    if ruleset is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"规则集 '{name}' 不存在"},
        )
    return ruleset.to_dict()


@app.post("/clean/rules/apply")
async def apply_rule(request: Request):
    """POST /clean/rules/apply — 按规则集执行清洗。"""
    df = _get_df(request)
    if df is None:
        return JSONResponse(
            status_code=400,
            content={"detail": "请先上传数据文件，确保 session 中存在 df_json"},
        )

    body: dict[str, Any] = await request.json()

    ruleset: RuleSet | None = None
    name: str | None = body.get("name")

    if name:
        ruleset = load_ruleset(name)
        if ruleset is None:
            return JSONResponse(
                status_code=404,
                content={"detail": f"规则集 '{name}' 不存在"},
            )
    elif "ruleset" in body:
        try:
            ruleset = RuleSet.from_dict(body["ruleset"])
            errors = validate_ruleset(ruleset)
            if errors:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "规则校验失败", "errors": errors},
                )
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"detail": f"规则集格式错误: {e}"},
            )
    else:
        return JSONResponse(
            status_code=400,
            content={"detail": "请提供 name（规则集名称）或 ruleset（内联规则定义）"},
        )

    df_cleaned, cleaned_count, messages = apply_ruleset(df, ruleset)
    df_cleaned = df_cleaned.reset_index(drop=True)

    request.session["df_json"] = _df_to_json(df_cleaned)

    return {
        "message": "; ".join(messages) if messages else "规则集清洗完成",
        "cleaned_count": cleaned_count,
        "missing_report": analyze_missing(df_cleaned),
        "outlier_report": detect_outliers_iqr(df_cleaned),
        "columns": list(df_cleaned.columns),
        "rows": _preview_rows(df_cleaned),
        "row_count": len(df_cleaned),
        "column_count": len(df_cleaned.columns),
    }


@app.post("/clean/rules/save")
async def save_rule(request: Request):
    """POST /clean/rules/save — 保存自定义规则集。"""
    body: dict[str, Any] = await request.json()
    try:
        ruleset = RuleSet.from_dict(body)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"detail": f"规则集格式错误: {e}"},
        )

    errors = validate_ruleset(ruleset)
    if errors:
        return JSONResponse(
            status_code=400,
            content={"detail": "规则校验失败", "errors": errors},
        )

    if ruleset.name in PRESETS:
        return JSONResponse(
            status_code=400,
            content={"detail": f"'{ruleset.name}' 是预设规则集名称，不可覆盖"},
        )

    path = save_ruleset(ruleset)
    return {
        "message": f"规则集 '{ruleset.name}' 已保存",
        "path": path,
    }


@app.delete("/clean/rules/{name}")
async def delete_rule(name: str):
    """DELETE /clean/rules/{name} — 删除已保存的规则集。"""
    if name in PRESETS:
        return JSONResponse(
            status_code=400,
            content={"detail": f"'{name}' 是预设规则集，不可删除"},
        )

    ok = delete_ruleset(name)
    if not ok:
        return JSONResponse(
            status_code=404,
            content={"detail": f"规则集 '{name}' 不存在"},
        )

    return {"message": f"规则集 '{name}' 已删除"}


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
