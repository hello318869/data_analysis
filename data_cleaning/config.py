"""自动化清洗规则配置模块。

支持预设规则模板、JSON 持久化、规则校验、按规则集批量执行清洗。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any

import pandas as pd
import numpy as np


RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")


@dataclass
class ColumnRule:
    """单列的清洗规则。"""

    column: str
    missing_strategy: str = "median"  # mean / median / mode / drop / custom / skip
    fill_value: float | str | None = None
    outlier_method: str = "iqr"  # iqr / zscore / none
    outlier_action: str = "clip"  # clip / remove / none
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ColumnRule":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
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


# ---- 预设规则集 ----


def preset_numeric() -> RuleSet:
    """数值列默认规则：中位数填充 + IQR 截断。"""
    return RuleSet(
        name="numeric_default",
        description="数值列：中位数填充缺失值，IQR 截断异常值",
        rules=[
            ColumnRule(
                column="*",
                missing_strategy="median",
                outlier_method="iqr",
                outlier_action="clip",
            ),
        ],
    )


def preset_categorical() -> RuleSet:
    """分类列默认规则：众数填充，不处理异常值。"""
    return RuleSet(
        name="categorical_default",
        description="分类列：众数填充缺失值，不检测异常值",
        rules=[
            ColumnRule(
                column="*",
                missing_strategy="mode",
                outlier_method="none",
                outlier_action="none",
            ),
        ],
    )


def preset_full() -> RuleSet:
    """综合规则：数值中位数+截断，分类众数。"""
    return RuleSet(
        name="full_auto",
        description="全自动：数值列中位数+IQR截断，分类列众数填充",
        rules=[
            ColumnRule(
                column="*",
                missing_strategy="median",
                outlier_method="iqr",
                outlier_action="clip",
            ),
        ],
    )


PRESETS: dict[str, RuleSet] = {
    "numeric": preset_numeric(),
    "categorical": preset_categorical(),
    "full": preset_full(),
}


# ---- 规则持久化 ----


def _ensure_rules_dir() -> None:
    os.makedirs(RULES_DIR, exist_ok=True)


def list_saved_rules() -> list[str]:
    """列出本地已保存的规则集名称。"""
    _ensure_rules_dir()
    return [f[:-5] for f in os.listdir(RULES_DIR) if f.endswith(".json")]


def load_ruleset(name: str) -> RuleSet | None:
    """按名称加载规则集（先查 presets 再查本地 JSON）。"""
    if name in PRESETS:
        return PRESETS[name]

    path = os.path.join(RULES_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return None

    with open(path, encoding="utf-8") as f:
        return RuleSet.from_dict(json.load(f))


def save_ruleset(ruleset: RuleSet) -> str:
    """保存规则集到本地 JSON 文件。返回文件路径。"""
    _ensure_rules_dir()
    path = os.path.join(RULES_DIR, f"{ruleset.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ruleset.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def delete_ruleset(name: str) -> bool:
    """删除本地规则集。返回是否成功。"""
    path = os.path.join(RULES_DIR, f"{name}.json")
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def validate_ruleset(ruleset: RuleSet) -> list[str]:
    """校验规则集，返回错误信息列表（空列表表示合法）。"""
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


# ---- 规则执行引擎 ----


def _detect_outliers_zscore(series: pd.Series, threshold: float) -> pd.Series:
    """Z-Score 异常值检测，返回布尔 mask。"""
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(False, index=series.index)
    z = (series - mean).abs() / std
    return z > threshold


def apply_ruleset(df: pd.DataFrame, ruleset: RuleSet) -> tuple[pd.DataFrame, int, list[str]]:
    """按规则集清洗 DataFrame。返回 (清洗后DataFrame, 处理单元格数, 消息列表)。"""
    messages: list[str] = []
    total_cleaned = 0
    df_out = df.copy()

    numeric_cols = set(df_out.select_dtypes(include=[np.number]).columns)
    categorical_cols = set(df_out.columns) - numeric_cols

    for rule in ruleset.rules:
        # 解析 target columns
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
            # 缺失值处理
            col_missing = df_out[col].isna().sum()
            if col_missing > 0 and rule.missing_strategy != "skip":
                handled, msg = _apply_missing_strategy(df_out, col, rule)
                total_cleaned += handled
                if msg:
                    messages.append(msg)

            # 异常值处理
            if rule.outlier_method != "none" and rule.outlier_action != "none":
                handled, msg = _apply_outlier_action(df_out, col, rule)
                total_cleaned += handled
                if msg:
                    messages.append(msg)

    return df_out, total_cleaned, messages


def _apply_missing_strategy(df: pd.DataFrame, col: str, rule: ColumnRule) -> tuple[int, str]:
    col_missing = df[col].isna().sum()
    if col_missing == 0:
        return 0, ""

    if rule.missing_strategy == "drop":
        before = len(df)
        df.dropna(subset=[col], inplace=True)
        return col_missing, f"{col} 列（规则）：删除含缺失值的 {col_missing} 行"
    elif rule.missing_strategy == "mean":
        if not pd.api.types.is_numeric_dtype(df[col]):
            return 0, f"{col} 列（规则）：非数值类型，跳过均值填充"
        df[col] = df[col].fillna(df[col].mean())
        return col_missing, f"{col} 列（规则）：均值填充 {col_missing} 个缺失值"
    elif rule.missing_strategy == "median":
        if not pd.api.types.is_numeric_dtype(df[col]):
            return 0, f"{col} 列（规则）：非数值类型，跳过中位数填充"
        df[col] = df[col].fillna(df[col].median())
        return col_missing, f"{col} 列（规则）：中位数填充 {col_missing} 个缺失值"
    elif rule.missing_strategy == "mode":
        mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else ""
        df[col] = df[col].fillna(mode_val)
        return col_missing, f"{col} 列（规则）：众数填充 {col_missing} 个缺失值"
    elif rule.missing_strategy == "custom" and rule.fill_value is not None:
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

    outlier_count = outlier_mask.sum()

    if outlier_count == 0:
        return 0, ""

    if rule.outlier_action == "remove":
        df.drop(df.index[outlier_mask], inplace=True)
        return int(outlier_count), f"{col} 列（规则）：删除 {outlier_count} 个异常值"
    elif rule.outlier_action == "clip":
        df[col] = df[col].clip(
            lower=float(series.quantile(0.25) - rule.iqr_multiplier * (series.quantile(0.75) - series.quantile(0.25))),
            upper=float(series.quantile(0.75) + rule.iqr_multiplier * (series.quantile(0.75) - series.quantile(0.25))),
        )
        return int(outlier_count), f"{col} 列（规则）：IQR 截断 {outlier_count} 个异常值"

    return 0, ""
