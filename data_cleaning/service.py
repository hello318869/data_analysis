import pandas as pd
import numpy as np
from typing import Any


def analyze_missing(df: pd.DataFrame) -> list[dict[str, Any]]:
    """分析缺失值，返回 missing_report 格式。"""
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


def detect_outliers_iqr(df: pd.DataFrame, multiplier: float = 1.5) -> list[dict[str, Any]]:
    """使用 IQR 方法检测数值列的异常值，返回 outlier_report 格式。"""
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


def execute_clean(
    df: pd.DataFrame,
    strategy: str,
    columns: list[str],
    fill_value: float | None = None,
) -> tuple[pd.DataFrame, int, list[str]]:
    """按策略清洗指定列，返回 (清洗后DataFrame, 处理单元格数, 消息列表)。"""
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
            df_out[col] = df_out[col].fillna(fill)
            cleaned_count += col_missing
            messages.append(f"{col} 列：均值填充 {col_missing} 个缺失值（填充值: {fill:.2f}）")
        elif strategy == "median":
            if not pd.api.types.is_numeric_dtype(df_out[col]):
                messages.append(f"{col} 列：非数值类型，跳过中位数填充")
                continue
            fill = df_out[col].median()
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

    return df_out, cleaned_count, messages


def auto_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, int, list[str]]:
    """一键自动清洗：数值列中位数填充，分类列众数填充，异常值按 IQR 边界截断。"""
    all_messages: list[str] = []
    total_cleaned = 0

    df_out = df.copy()

    # 缺失值处理
    for col in df_out.columns:
        col_missing = df_out[col].isna().sum()
        if col_missing == 0:
            continue

        if pd.api.types.is_numeric_dtype(df_out[col]):
            fill = df_out[col].median()
            df_out[col] = df_out[col].fillna(fill)
            all_messages.append(f"{col} 列：中位数填充 {col_missing} 个缺失值")
        else:
            mode_vals = df_out[col].mode()
            fill = mode_vals.iloc[0] if not mode_vals.empty else ""
            df_out[col] = df_out[col].fillna(fill)
            all_messages.append(f"{col} 列：众数填充 {col_missing} 个缺失值")
        total_cleaned += col_missing

    # 异常值处理：IQR 截断
    outlier_report = detect_outliers_iqr(df_out)
    for entry in outlier_report:
        col = entry["column"]
        lower = entry["lower_bound"]
        upper = entry["upper_bound"]
        before = len(df_out)
        # 用边界值截断而非删除
        df_out[col] = df_out[col].clip(lower=lower, upper=upper)
        outlier_count = entry["outlier_count"]
        all_messages.append(f"{col} 列：IQR 截断 {outlier_count} 个异常值（边界: [{lower}, {upper}]）")

    return df_out, total_cleaned, all_messages
