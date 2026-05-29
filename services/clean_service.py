"""数据清洗业务逻辑 — 缺失值分析、异常值检测、策略清洗、规则引擎。

API 契约参见 api-contract.md 第三章。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any

import pandas as pd
import numpy as np


# ============================================================
# 缺失值分析
# ============================================================

def analyze_missing(df: pd.DataFrame) -> list[dict[str, Any]]:
    """分析缺失值，返回 missing_report 格式（契约 �3.1）。"""
    report = []
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if missing_count > 0:
            report.append({
                "column": col,
                "missing_count": missing_count,
                "missing_pct": round(missing_count / len(df) * 100, 2),
                "dtype": str(df[col].dtype),
            })
    return report


# ============================================================
# 异常值检测 (IQR)
# ============================================================

def detect_outliers_iqr(df: pd.DataFrame, multiplier: float = 1.5) -> list[dict[str, Any]]:
    """使用 IQR 方法检测数值列的异常值，返回 outlier_report 格式（契约 �3.1）。"""
    report = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 4:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = round(q1 - multiplier * iqr, 2)
        upper_bound = round(q3 + multiplier * iqr, 2)

        outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_indices = df.index[outlier_mask].tolist()

        if outlier_indices:
            report.append({
                "column": col,
                "outlier_count": len(outlier_indices),
                "outlier_indices": outlier_indices,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            })

    return report


# ============================================================
# 按策略清洗
# ============================================================

def execute_clean(
    df: pd.DataFrame,
    strategy: str,
    columns: list[str],
    fill_value: float | None = None,
) -> tuple[pd.DataFrame, int, list[str]]:
    """按策略清洗指定列（契约 �3.2）。

    Returns:
        (清洗后DataFrame, 处理的单元格数, 消息列表)
    """
    cleaned_count = 0
    messages: list[str] = []

    df_out = df.copy()
    valid_columns = [c for c in columns if c in df_out.columns]
    invalid_columns = set(columns) - set(valid_columns)

    for col in valid_columns:
        col_missing = df_out[col].isna().sum()
        if col_missing == 0:
            continue

        if strategy == "drop":
            before = len(df_out)
            df_out = df_out[df_out[col].notna()]
            removed = before - len(df_out)
            cleaned_count += col_missing
            messages.append(f"{col} 列：删除含缺失值的 {removed} 行")

        elif strategy == "mean":
            if not pd.api.types.is_numeric_dtype(df_out[col]):
                messages.append(f"{col} 列：非数值类型，跳过均值填充")
                continue
            fill = df_out[col].mean()
            if pd.isna(fill):
                messages.append(f"{col} 列：全为空值，无法计算均值，跳过")
                continue
            df_out[col] = df_out[col].fillna(fill)
            cleaned_count += col_missing
            messages.append(f"{col} 列：均值填充 {col_missing} 个缺失值（填充值: {fill:.2f}）")

        elif strategy == "median":
            if not pd.api.types.is_numeric_dtype(df_out[col]):
                messages.append(f"{col} 列：非数值类型，跳过中位数填充")
                continue
            fill = df_out[col].median()
            if pd.isna(fill):
                messages.append(f"{col} 列：全为空值，无法计算中位数，跳过")
                continue
            df_out[col] = df_out[col].fillna(fill)
            cleaned_count += col_missing
            messages.append(f"{col} 列：中位数填充 {col_missing} 个缺失值（填充值: {fill:.2f}）")

        elif strategy == "mode":
            mode_vals = df_out[col].mode()
            fill = mode_vals.iloc[0] if not mode_vals.empty else ""
            df_out[col] = df_out[col].fillna(fill)
            cleaned_count += col_missing
            messages.append(f"{col} 列：众数填充 {col_missing} 个缺失值（填充值: {fill}）")

        elif strategy == "custom":
            if fill_value is None:
                messages.append(f"{col} 列：custom 策略未提供 fill_value，跳过")
                continue
            df_out[col] = df_out[col].fillna(fill_value)
            cleaned_count += col_missing
            messages.append(f"{col} 列：自定义值填充 {col_missing} 个缺失值（填充值: {fill_value}）")

        else:
            messages.append(f"{col} 列：未知策略 {strategy}，跳过")

    for col in invalid_columns:
        messages.append(f"{col} 列：不存在于数据集中，跳过")

    return df_out, int(cleaned_count), messages


# ============================================================
# 一键自动清洗
# ============================================================

def auto_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, int, list[str]]:
    """一键自动清洗（契约 �3.3）。

    数值列 → 中位数填充，分类列 → 众数填充，异常值 → IQR 截断。
    """
    all_messages: list[str] = []
    total_cleaned = 0
    df_out = df.copy()

    for col in df_out.columns:
        col_missing = df_out[col].isna().sum()
        if col_missing == 0:
            continue

        if pd.api.types.is_numeric_dtype(df_out[col]):
            fill = df_out[col].median()
            if pd.isna(fill):
                continue
            df_out[col] = df_out[col].fillna(fill)
            all_messages.append(f"{col} 列：中位数填充 {col_missing} 个缺失值")
        else:
            mode_vals = df_out[col].mode()
            fill = mode_vals.iloc[0] if not mode_vals.empty else ""
            df_out[col] = df_out[col].fillna(fill)
            all_messages.append(f"{col} 列：众数填充 {col_missing} 个缺失值")
        total_cleaned += col_missing

    outlier_report = detect_outliers_iqr(df_out)
    for entry in outlier_report:
        col = entry["column"]
        lower = entry["lower_bound"]
        upper = entry["upper_bound"]
        df_out[col] = df_out[col].clip(lower=lower, upper=upper)
        all_messages.append(
            f"{col} 列：IQR 截断 {entry['outlier_count']} 个异常值（边界: [{lower}, {upper}]）"
        )

    return df_out, int(total_cleaned), all_messages


# ============================================================
# 规则引擎
# ============================================================

RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rules")


@dataclass
class ColumnRule:
    """单列的清洗规则。"""
    column: str
    missing_strategy: str = "median"
    fill_value: float | str | None = None
    outlier_method: str = "iqr"
    outlier_action: str = "clip"
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ColumnRule":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid_keys})


@dataclass
class RuleSet:
    """一组建清洗规则。"""
    name: str
    description: str = ""
    rules: list[ColumnRule] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RuleSet":
        rules = [ColumnRule.from_dict(r) for r in d.get("rules", [])]
        return cls(name=d["name"], description=d.get("description", ""), rules=rules)


def preset_numeric() -> RuleSet:
    return RuleSet(
        name="numeric_default",
        description="数值列：中位数填充缺失值，IQR 截断异常值",
        rules=[ColumnRule(column="*", missing_strategy="median", outlier_method="iqr", outlier_action="clip")],
    )


def preset_categorical() -> RuleSet:
    return RuleSet(
        name="categorical_default",
        description="分类列：众数填充缺失值",
        rules=[ColumnRule(column="*", missing_strategy="mode", outlier_method="none", outlier_action="none")],
    )


def preset_full() -> RuleSet:
    return RuleSet(
        name="full_auto",
        description="全自动：数值列中位数+IQR截断，分类列众数",
        rules=[ColumnRule(column="*", missing_strategy="median", outlier_method="iqr", outlier_action="clip")],
    )


PRESETS: dict[str, RuleSet] = {
    "numeric": preset_numeric(),
    "categorical": preset_categorical(),
    "full": preset_full(),
}


def _ensure_rules_dir() -> None:
    os.makedirs(RULES_DIR, exist_ok=True)


def list_saved_rules() -> list[str]:
    _ensure_rules_dir()
    return sorted(f[:-5] for f in os.listdir(RULES_DIR) if f.endswith(".json"))


def load_ruleset(name: str) -> RuleSet | None:
    if name in PRESETS:
        return PRESETS[name]
    path = os.path.join(RULES_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return RuleSet.from_dict(json.load(f))


def save_ruleset(ruleset: RuleSet) -> str:
    _ensure_rules_dir()
    path = os.path.join(RULES_DIR, f"{ruleset.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ruleset.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def delete_ruleset(name: str) -> bool:
    path = os.path.join(RULES_DIR, f"{name}.json")
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def validate_ruleset(ruleset: RuleSet) -> list[str]:
    errors: list[str] = []
    valid_strategies = {"mean", "median", "mode", "drop", "custom", "skip"}
    valid_outlier_methods = {"iqr", "zscore", "none"}
    valid_outlier_actions = {"clip", "remove", "none"}

    if not ruleset.name.strip():
        errors.append("规则集名称不能为空")

    for rule in ruleset.rules:
        prefix = f"[{rule.column}]"
        if rule.missing_strategy not in valid_strategies:
            errors.append(f"{prefix} 无效的缺失值策略: {rule.missing_strategy}")
        if rule.missing_strategy == "custom" and rule.fill_value is None:
            errors.append(f"{prefix} custom 策略必须提供 fill_value")
        if rule.outlier_method not in valid_outlier_methods:
            errors.append(f"{prefix} 无效的异常值检测方法: {rule.outlier_method}")
        if rule.outlier_action not in valid_outlier_actions:
            errors.append(f"{prefix} 无效的异常值处理动作: {rule.outlier_action}")
        if rule.iqr_multiplier <= 0:
            errors.append(f"{prefix} IQR 乘数必须大于 0")
        if rule.zscore_threshold <= 0:
            errors.append(f"{prefix} Z-Score 阈值必须大于 0")

    return errors


def _detect_outliers_zscore(series: pd.Series, threshold: float) -> pd.Series:
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(False, index=series.index)
    return (series - mean).abs() / std > threshold


def apply_ruleset(df: pd.DataFrame, ruleset: RuleSet) -> tuple[pd.DataFrame, int, list[str]]:
    messages: list[str] = []
    total_cleaned = 0
    df_out = df.copy()

    numeric_cols = set(df_out.select_dtypes(include=[np.number]).columns)
    categorical_cols = set(df_out.columns) - numeric_cols

    for rule in ruleset.rules:
        if rule.column == "*":
            if ruleset.name == "numeric_default":
                target_cols = list(numeric_cols)
            elif ruleset.name == "categorical_default":
                target_cols = list(categorical_cols)
            else:
                target_cols = list(df_out.columns)
        else:
            target_cols = [rule.column]

        target_cols = [c for c in target_cols if c in df_out.columns]

        for col in target_cols:
            col_missing = int(df_out[col].isna().sum())
            if col_missing > 0 and rule.missing_strategy != "skip":
                handled, msg = _apply_missing_strategy(df_out, col, rule)
                total_cleaned += handled
                if msg:
                    messages.append(msg)

            if rule.outlier_method != "none" and rule.outlier_action != "none":
                handled, msg = _apply_outlier_action(df_out, col, rule)
                total_cleaned += handled
                if msg:
                    messages.append(msg)

    return df_out, int(total_cleaned), messages


def _apply_missing_strategy(df: pd.DataFrame, col: str, rule: ColumnRule) -> tuple[int, str]:
    col_missing = int(df[col].isna().sum())
    if col_missing == 0:
        return 0, ""

    s = rule.missing_strategy

    if s == "drop":
        before = len(df)
        df.dropna(subset=[col], inplace=True)
        return col_missing, f"{col} 列（规则）：删除含缺失值的 {col_missing} 行"

    if s == "mean":
        if not pd.api.types.is_numeric_dtype(df[col]):
            return 0, f"{col} 列（规则）：非数值类型，跳过均值填充"
        df[col] = df[col].fillna(df[col].mean())
        return col_missing, f"{col} 列（规则）：均值填充 {col_missing} 个缺失值"

    if s == "median":
        if not pd.api.types.is_numeric_dtype(df[col]):
            return 0, f"{col} 列（规则）：非数值类型，跳过中位数填充"
        df[col] = df[col].fillna(df[col].median())
        return col_missing, f"{col} 列（规则）：中位数填充 {col_missing} 个缺失值"

    if s == "mode":
        mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else ""
        df[col] = df[col].fillna(mode_val)
        return col_missing, f"{col} 列（规则）：众数填充 {col_missing} 个缺失值"

    if s == "custom" and rule.fill_value is not None:
        df[col] = df[col].fillna(rule.fill_value)
        return col_missing, f"{col} 列（规则）：自定义值填充 {col_missing} 个缺失值"

    return 0, ""


def _apply_outlier_action(df: pd.DataFrame, col: str, rule: ColumnRule) -> tuple[int, str]:
    if not pd.api.types.is_numeric_dtype(df[col]):
        return 0, ""

    series = df[col].dropna()
    if len(series) < 4:
        return 0, ""

    if rule.outlier_method == "iqr":
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return 0, ""
        lower = q1 - rule.iqr_multiplier * iqr
        upper = q3 + rule.iqr_multiplier * iqr
        outlier_mask = (df[col] < lower) | (df[col] > upper)
    elif rule.outlier_method == "zscore":
        outlier_mask = _detect_outliers_zscore(series, rule.zscore_threshold)
        outlier_mask = outlier_mask.reindex(df.index, fill_value=False)
    else:
        return 0, ""

    outlier_count = int(outlier_mask.sum())
    if outlier_count == 0:
        return 0, ""

    if rule.outlier_action == "remove":
        df.drop(df.index[outlier_mask], inplace=True)
        return outlier_count, f"{col} 列（规则）：删除 {outlier_count} 个异常值"

    if rule.outlier_action == "clip":
        lower_val = float(q1 - rule.iqr_multiplier * (q3 - q1))
        upper_val = float(q3 + rule.iqr_multiplier * (q3 - q1))
        df[col] = df[col].clip(lower=lower_val, upper=upper_val)
        return outlier_count, f"{col} 列（规则）：IQR 截断 {outlier_count} 个异常值"

    return 0, ""
