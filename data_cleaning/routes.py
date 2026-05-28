"""数据清洗模块路由 — Flask Blueprint。

接口：
  GET  /clean           清洗前报告（missing_report, outlier_report）
  POST /clean/execute   按策略手动清洗
  POST /clean/auto      一键自动清洗
"""

from flask import Blueprint, request, session, render_template, redirect, url_for

from .service import analyze_missing, detect_outliers_iqr, execute_clean, auto_clean
from .config import list_saved_rules, load_ruleset, save_ruleset, delete_ruleset, validate_ruleset, apply_ruleset, RuleSet, ColumnRule

import pandas as pd
import json
import os

clean_bp = Blueprint("clean", __name__)


def _get_df():
    """从 session 读取 DataFrame，失败返回 None。"""
    df_json = session.get("df_json")
    if df_json is None:
        return None
    return pd.read_json(df_json, orient="split")


def _get_user():
    return session.get("user")


def _render_clean(df, extra: dict | None = None):
    """渲染 clean.html 公共参数。"""
    missing_report = analyze_missing(df)
    outlier_report = detect_outliers_iqr(df)
    template_data = {
        "request": request,
        "user": _get_user(),
        "missing_report": missing_report,
        "outlier_report": outlier_report,
        "columns": list(df.columns),
    }
    if extra:
        template_data.update(extra)
    return render_template("clean.html", **template_data)


# ---- 3.1 清洗前报告 ----


@clean_bp.route("/clean")
def clean_report():
    df = _get_df()
    if df is None:
        return redirect(url_for("index", error="请先上传数据文件"))

    saved_rules = list_saved_rules()
    return _render_clean(df, extra={"saved_rules": saved_rules})


# ---- 3.2 执行清洗 ----


@clean_bp.route("/clean/execute", methods=["POST"])
def clean_execute():
    df = _get_df()
    if df is None:
        return redirect(url_for("index", error="请先上传数据文件"))

    data = request.get_json(silent=True) or {}
    strategy = data.get("strategy", "mean")
    columns = data.get("columns", [])
    fill_value = data.get("fill_value")

    if not columns:
        return _render_clean(df, extra={"error": "请选择至少一列进行清洗"})

    df_cleaned, cleaned_count, messages = execute_clean(df, strategy, columns, fill_value)

    # 更新 session
    session["df_json"] = df_cleaned.to_json(orient="split")

    return _render_clean(
        df_cleaned,
        extra={
            "message": "; ".join(messages),
            "cleaned_count": cleaned_count,
            "rows": _preview_rows(df_cleaned),
        },
    )


# ---- 3.3 一键自动清洗 ----


@clean_bp.route("/clean/auto", methods=["POST"])
def clean_auto():
    df = _get_df()
    if df is None:
        return redirect(url_for("index", error="请先上传数据文件"))

    df_cleaned, cleaned_count, messages = auto_clean(df)

    session["df_json"] = df_cleaned.to_json(orient="split")

    return _render_clean(
        df_cleaned,
        extra={
            "message": "; ".join(messages),
            "cleaned_count": cleaned_count,
            "rows": _preview_rows(df_cleaned),
        },
    )


# ---- 扩展：规则集管理 API ----


@clean_bp.route("/clean/rules")
def rules_list():
    """列出所有已保存规则集（含预设）。"""
    df = _get_df()
    if df is None:
        return redirect(url_for("index", error="请先上传数据文件"))

    presets = [{"name": name, "description": rs.description, "source": "preset"} for name, rs in [("numeric", None), ("categorical", None), ("full", None)]]
    # Actually read the real presets
    from .config import PRESETS

    presets = [{"name": name, "description": rs.description, "source": "preset"} for name, rs in PRESETS.items()]
    saved = [{"name": n, "source": "saved"} for n in list_saved_rules()]

    return _render_clean(df, extra={"rulesets": presets + saved})


@clean_bp.route("/clean/rules/save", methods=["POST"])
def rules_save():
    """保存自定义规则集。"""
    df = _get_df()
    if df is None:
        return redirect(url_for("index", error="请先上传数据文件"))

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    description = data.get("description", "")
    rules_data = data.get("rules", [])

    if not name:
        return _render_clean(df, extra={"error": "规则集名称不能为空"})

    rules = [ColumnRule.from_dict(r) for r in rules_data]
    ruleset = RuleSet(name=name, description=description, rules=rules)

    errors = validate_ruleset(ruleset)
    if errors:
        return _render_clean(df, extra={"error": "规则校验失败: " + "; ".join(errors)})

    save_ruleset(ruleset)
    return _render_clean(df, extra={"message": f"规则集 '{name}' 已保存"})


@clean_bp.route("/clean/rules/apply/<name>", methods=["POST"])
def rules_apply(name: str):
    """按规则集名称执行清洗。"""
    df = _get_df()
    if df is None:
        return redirect(url_for("index", error="请先上传数据文件"))

    ruleset = load_ruleset(name)
    if ruleset is None:
        return _render_clean(df, extra={"error": f"规则集 '{name}' 不存在"})

    df_cleaned, cleaned_count, messages = apply_ruleset(df, ruleset)

    session["df_json"] = df_cleaned.to_json(orient="split")

    return _render_clean(
        df_cleaned,
        extra={
            "message": f"[规则集: {name}] " + "; ".join(messages),
            "cleaned_count": cleaned_count,
            "rows": _preview_rows(df_cleaned),
        },
    )


@clean_bp.route("/clean/rules/delete/<name>", methods=["POST"])
def rules_delete(name: str):
    """删除本地规则集。"""
    df = _get_df()
    if df is None:
        return redirect(url_for("index", error="请先上传数据文件"))

    if delete_ruleset(name):
        return _render_clean(df, extra={"message": f"规则集 '{name}' 已删除"})
    return _render_clean(df, extra={"error": f"规则集 '{name}' 不存在或为预设规则，无法删除"})


# ---- helpers ----


def _preview_rows(df: pd.DataFrame, n: int = 10) -> list[list]:
    """取前 n 行转为 list[list]，NaN 替换为 None。"""
    return df.head(n).where(pd.notna(df.head(n)), None).values.tolist()


def init_rules_dir() -> None:
    """确保规则持久化目录存在。"""
    from .config import _ensure_rules_dir
    _ensure_rules_dir()
