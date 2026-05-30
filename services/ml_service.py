"""
算法分析模块的机器学习服务函数。

本文件只负责数据校验、模型训练、指标计算和图表生成。
路由层负责接收请求、读取 session、渲染模板，本文件不直接操作
FastAPI 的 request/session。
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from config import OUTPUT_DIR


TEST_SIZE = 0.2
RANDOM_STATE = 42
MIN_SAMPLE_SIZE = 5
# Note: If Chinese characters appear as boxes (tofu), install one of the fonts above.
# On Ubuntu: sudo apt install fonts-wqy-microhei
# On Windows: fonts are typically pre-installed
FONT_PRIORITY = [
    "SimHei",
    "Microsoft YaHei",
    "PingFang SC",
    "Heiti SC",
    "Noto Sans CJK SC",
    "WenQuanYi Micro Hei",
    "DejaVu Sans",
]
CHINESE_FONT_NAMES = set(FONT_PRIORITY[:-1])


def _to_python_number(value: Any) -> Any:
    """把 numpy 数值转换成普通 Python 数值，便于模板或 JSON 使用。"""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _choose_chart_font() -> tuple[str | None, bool]:
    """
    根据当前系统真实存在的字体选择图表字体。

    返回值：
    - font_name：找到的字体名；没有可用字体时为 None
    - use_chinese_text：是否可以安全使用中文图表文案
    """
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}

    for font_name in FONT_PRIORITY:
        if font_name in available_fonts:
            return font_name, font_name in CHINESE_FONT_NAMES

    return None, False


def _apply_chart_font() -> tuple[bool, dict]:
    """
    返回是否应该使用中文文案，以及对应的 rcParams 字典。

    不再直接修改全局 rcParams，调用方应使用 plt.rc_context()
    来应用这些设置，以避免并发或跨图表副作用。

    如果系统只有 DejaVu Sans 或没有中文字体，就让图表使用英文文案，
    避免 Matplotlib 在终端输出大量中文 glyph warning。
    """
    font_name, use_chinese_text = _choose_chart_font()
    rc_params: dict[str, Any] = {"axes.unicode_minus": False}
    if font_name:
        rc_params["font.sans-serif"] = [font_name]
    return use_chinese_text, rc_params


def validate_regression_columns(
    df: pd.DataFrame, features: list[str], target: str
) -> None:
    """
    校验回归分析所需的特征列和目标列。

    如果列不存在、列不是数值类型，或用户没有选择特征列，则抛出
    ValueError，交给路由层转换成页面错误提示。
    """
    if not features:
        raise ValueError("请至少选择 1 个特征列")

    if not target:
        raise ValueError("请选择目标列")

    if target not in df.columns:
        raise ValueError(f"目标列 {target} 不存在")

    missing_features = [feature for feature in features if feature not in df.columns]
    if missing_features:
        missing_text = "、".join(missing_features)
        raise ValueError(f"特征列 {missing_text} 不存在")

    if target in features:
        raise ValueError("目标列不能同时作为特征列")

    if not is_numeric_dtype(df[target]):
        raise ValueError(f"目标列 {target} 不是数值类型，无法用于回归")

    for feature in features:
        if not is_numeric_dtype(df[feature]):
            raise ValueError(f"特征列 {feature} 不是数值类型，无法用于回归")


def prepare_regression_data(
    df: pd.DataFrame, features: list[str], target: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    准备回归训练数据：只保留特征列和目标列，并删除这些列里的缺失值行。

    注意：不相关列的缺失值不会影响训练。例如用户选择
    ["sqft", "bedrooms"] -> "price" 时，age 列为空不会导致该行被删除。
    """
    validate_regression_columns(df, features, target)

    regression_columns = features + [target]
    clean_df = df.loc[:, regression_columns].dropna(subset=regression_columns).copy()

    if len(clean_df) < MIN_SAMPLE_SIZE:
        raise ValueError("清洗后可用于训练的数据不足 5 行，无法进行回归分析")

    x_data = clean_df[features]
    y_data = clean_df[target]
    return clean_df, x_data, y_data


def _split_regression_data(
    x_data: pd.DataFrame, y_data: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """按项目约定划分训练集和测试集：80/20，random_state=42。"""
    return train_test_split(
        x_data,
        y_data,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )


def _calculate_metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    """计算接口契约要求的三个评价指标。"""
    return {
        "r2_score": float(r2_score(actual, predicted)),
        "mse": float(mean_squared_error(actual, predicted)),
        "mae": float(mean_absolute_error(actual, predicted)),
    }


def _build_prediction_rows(
    x_test: pd.DataFrame, actual: pd.Series, predicted: np.ndarray
) -> list[dict[str, Any]]:
    """组装逐行预测结果，供 analysis.html 表格展示。"""
    rows: list[dict[str, Any]] = []

    for (_, feature_values), actual_value, predicted_value in zip(
        x_test.iterrows(), actual.to_numpy(), predicted
    ):
        row = {
            feature: _to_python_number(feature_values[feature])
            for feature in x_test.columns
        }
        row["actual"] = _to_python_number(actual_value)
        row["predicted"] = float(predicted_value)
        rows.append(row)

    return rows


def run_linear_regression(
    df: pd.DataFrame, features: list[str], target: str
) -> dict[str, Any]:
    """
    训练 LinearRegression，并返回指标、系数、预测明细和散点图路径。

    返回的字典可以由路由层直接传给 analysis.html。
    """
    _, x_data, y_data = prepare_regression_data(df, features, target)
    x_train, x_test, y_train, y_test = _split_regression_data(x_data, y_data)

    model = LinearRegression()
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)

    metrics = _calculate_metrics(y_test, predicted)
    scatter_chart_path = generate_regression_scatter_chart(
        y_test, predicted, OUTPUT_DIR
    )

    coefficients = {
        feature: float(coefficient)
        for feature, coefficient in zip(features, model.coef_)
    }

    return {
        **metrics,
        "coefficients": coefficients,
        "intercept": float(model.intercept_),
        "train_size": int(len(x_train)),
        "test_size": int(len(x_test)),
        "features": features,
        "target": target,
        "predictions": _build_prediction_rows(x_test, y_test, predicted),
        "scatter_chart_path": scatter_chart_path,
    }


def compare_regression_models(
    df: pd.DataFrame, features: list[str], target: str
) -> dict[str, Any]:
    """
    使用同一份训练集/测试集对比 LinearRegression、Ridge、Lasso。

    最优模型选择规则：
    1. 优先选择 r2_score 最大的模型；
    2. 如果 r2_score 相同，选择 mse 更小的模型。
    """
    _, x_data, y_data = prepare_regression_data(df, features, target)
    x_train, x_test, y_train, y_test = _split_regression_data(x_data, y_data)

    # Scale features for regularized models
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    models = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(),
        "Lasso": Lasso(max_iter=10000),
    }

    comparison: list[dict[str, Any]] = []
    for algorithm, model in models.items():
        if algorithm == "LinearRegression":
            model.fit(x_train, y_train)
            predicted = model.predict(x_test)
        else:
            model.fit(x_train_scaled, y_train)
            predicted = model.predict(x_test_scaled)
            if algorithm == "Lasso" and model.n_iter_ >= 10000:
                import warnings
                from sklearn.exceptions import ConvergenceWarning
                warnings.warn(
                    f"Lasso may not have fully converged (n_iter={model.n_iter_})",
                    ConvergenceWarning,
                )
        metrics = _calculate_metrics(y_test, predicted)
        comparison.append({
            "algorithm": algorithm,
            **metrics,
        })

    best = max(comparison, key=lambda item: (item["r2_score"], -item["mse"]))

    return {
        "comparison": comparison,
        "best_algorithm": best["algorithm"],
    }


def generate_regression_scatter_chart(
    actual: pd.Series | np.ndarray | list[float],
    predicted: pd.Series | np.ndarray | list[float],
    output_dir: str,
) -> str:
    """
    保存“预测值 vs 真实值”散点图，并返回模板可直接使用的路径。

    返回路径固定为：/outputs/charts/<filename>.png
    """
    os.makedirs(output_dir, exist_ok=True)

    use_chinese_text, rc_params = _apply_chart_font()
    if use_chinese_text:
        title = "预测值 vs 真实值"
        x_label = "真实值"
        y_label = "预测值"
        reference_label = "y=x 参考线"
    else:
        title = "Predicted vs Actual"
        x_label = "Actual Value"
        y_label = "Predicted Value"
        reference_label = "y=x Reference"

    actual_values = np.asarray(actual, dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"regression_scatter_{timestamp}.png"
    file_path = os.path.join(output_dir, filename)

    with plt.rc_context(rc_params):
        fig, ax = plt.subplots(figsize=(7, 5), dpi=120)
        try:
            ax.scatter(actual_values, predicted_values, alpha=0.75, color="#2563eb")

            min_value = float(min(actual_values.min(), predicted_values.min()))
            max_value = float(max(actual_values.max(), predicted_values.max()))
            if min_value == max_value:
                min_value -= 1.0
                max_value += 1.0

            ax.plot(
                [min_value, max_value],
                [min_value, max_value],
                linestyle="--",
                color="#dc2626",
                linewidth=1.5,
                label=reference_label,
            )
            ax.set_title(title)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.legend()
            ax.grid(True, linestyle="--", alpha=0.25)

            fig.tight_layout()
            fig.savefig(file_path, bbox_inches="tight")
        finally:
            plt.close(fig)

    return f"/outputs/charts/{filename}"
