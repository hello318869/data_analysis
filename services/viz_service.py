from __future__ import annotations

import os
from datetime import datetime

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from pandas.plotting import scatter_matrix

from config import OUTPUT_DIR


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

# Note: If Chinese characters appear as boxes (tofu), install Chinese fonts.
# On Ubuntu: sudo apt install fonts-wqy-microhei
# On Windows: SimHei and Microsoft YaHei are typically pre-installed


def _choose_chart_font() -> tuple[str | None, bool]:
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    for font_name in FONT_PRIORITY:
        if font_name in available_fonts:
            return font_name, font_name in CHINESE_FONT_NAMES
    return None, False


def _get_chart_rc_params() -> tuple[dict[str, str | bool | list[str]], bool]:
    """Return rc params dict for chart font configuration (thread-safe)."""
    font_name, use_chinese_text = _choose_chart_font()
    rc_params: dict[str, str | bool | list[str]] = {"axes.unicode_minus": False}
    if font_name:
        rc_params["font.sans-serif"] = [font_name]
    return rc_params, use_chinese_text


def _parse_figsize(figsize_str: str) -> tuple[int, int]:
    parts = figsize_str.split(",")
    try:
        w = int(parts[0].strip())
        h = int(parts[1].strip()) if len(parts) > 1 else w
    except (ValueError, IndexError):
        w, h = 8, 5
    return max(4, min(w, 20)), max(3, min(h, 16))


def _chart_text(use_chinese_text: bool, chinese: str, english: str) -> str:
    return chinese if use_chinese_text else english


def _require_column(df: pd.DataFrame, column: str, label: str) -> None:
    if column not in df.columns:
        raise ValueError(f"{label}列 '{column}' 不存在")


def _require_numeric_column(df: pd.DataFrame, column: str, label: str) -> None:
    _require_column(df, column, label)
    if not is_numeric_dtype(df[column]):
        raise ValueError(f"{label}列 '{column}' 不是数值类型，请选择数值列。")


def _save_figure(fig, chart_type: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{chart_type}_{timestamp}.png"
    file_path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(file_path, bbox_inches="tight")
    return f"/outputs/charts/{filename}"


def generate_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_col: str,
    y_col: str,
    title: str = "",
    color: str = "#2563eb",
    figsize: str = "8,5",
) -> str:
    supported_types = {
        "line",
        "bar",
        "scatter",
        "hist",
        "box",
        "heatmap",
        "scatter_matrix",
        "grouped_bar",
        "missing",
    }
    if chart_type not in supported_types:
        raise ValueError(f"不支持的图表类型: {chart_type}")

    # Get font rc_params without changing global Matplotlib settings.
    rc_params, use_chinese_text = _get_chart_rc_params()

    figsize_tuple = _parse_figsize(figsize)

    with plt.rc_context(rc_params):
        fig = None
        try:
            if chart_type in {"line", "bar", "scatter"}:
                _require_column(df, x_col, "X 轴")
                _require_numeric_column(df, y_col, "Y 轴")
                plot_df = df[[x_col, y_col]].dropna()
                if plot_df.empty:
                    raise ValueError("选择的列没有可用于绘图的数据。")

                x_data = plot_df[x_col]
                y_data = plot_df[y_col]
                x_plot = x_data if is_numeric_dtype(x_data) else x_data.astype(str)

                fig, ax = plt.subplots(figsize=figsize_tuple, dpi=120)
                if chart_type == "line":
                    default_title = f"{y_col} vs {x_col}"
                    ax.plot(x_plot, y_data, color=color, linewidth=1.5, marker="o", markersize=4)
                elif chart_type == "bar":
                    default_title = f"{y_col} by {x_col}"
                    ax.bar(x_plot, y_data, color=color, width=0.65)
                    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
                else:
                    default_title = f"{y_col} vs {x_col}"
                    ax.scatter(x_plot, y_data, color=color, alpha=0.75, edgecolors="white", linewidth=0.5)

                ax.set_title(title or default_title, fontsize=13)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.grid(True, linestyle="--", alpha=0.25)

            elif chart_type == "hist":
                hist_col = y_col if y_col in df.columns and is_numeric_dtype(df[y_col]) else x_col
                _require_numeric_column(df, hist_col, "直方图")
                values = df[hist_col].dropna()
                if values.empty:
                    raise ValueError("选择的数值列没有可用于绘图的数据。")

                fig, ax = plt.subplots(figsize=figsize_tuple, dpi=120)
                ax.hist(values, bins=min(20, max(5, int(np.sqrt(len(values))))), color=color, alpha=0.8, edgecolor="white")
                ax.set_title(title or _chart_text(use_chinese_text, f"{hist_col} 分布直方图", f"{hist_col} Histogram"), fontsize=13)
                ax.set_xlabel(hist_col)
                ax.set_ylabel(_chart_text(use_chinese_text, "频数", "Count"))
                ax.grid(True, axis="y", linestyle="--", alpha=0.25)

            elif chart_type == "box":
                _require_numeric_column(df, y_col, "Y 轴")
                _require_column(df, x_col, "X 轴")
                plot_df = df[[x_col, y_col]].dropna()
                if plot_df.empty:
                    raise ValueError("选择的列没有可用于绘图的数据。")

                fig, ax = plt.subplots(figsize=figsize_tuple, dpi=120)
                if x_col != y_col and not is_numeric_dtype(plot_df[x_col]):
                    grouped = []
                    labels = []
                    for label, group in plot_df.groupby(x_col, sort=False):
                        if len(grouped) >= 15:
                            break
                        grouped.append(group[y_col].values)
                        labels.append(str(label))
                    ax.boxplot(grouped, labels=labels, patch_artist=True)
                    ax.set_xlabel(x_col)
                    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
                else:
                    ax.boxplot(plot_df[y_col].values, labels=[y_col], patch_artist=True)
                    ax.set_xlabel(y_col)
                ax.set_title(title or _chart_text(use_chinese_text, f"{y_col} 箱线图", f"{y_col} Box Plot"), fontsize=13)
                ax.set_ylabel(y_col)
                ax.grid(True, axis="y", linestyle="--", alpha=0.25)

            elif chart_type == "grouped_bar":
                _require_column(df, x_col, "分类")
                _require_numeric_column(df, y_col, "Y 轴")
                plot_df = df[[x_col, y_col]].dropna()
                if plot_df.empty:
                    raise ValueError("选择的列没有可用于绘图的数据。")

                grouped = plot_df.groupby(x_col)[y_col].mean().sort_values(ascending=False).head(20)
                fig, ax = plt.subplots(figsize=figsize_tuple, dpi=120)
                ax.bar(grouped.index.astype(str), grouped.values, color=color, width=0.65)
                ax.set_title(title or _chart_text(use_chinese_text, f"{y_col} 按 {x_col} 分组均值", f"Average {y_col} by {x_col}"), fontsize=13)
                ax.set_xlabel(x_col)
                ax.set_ylabel(_chart_text(use_chinese_text, f"{y_col} 均值", f"Average {y_col}"))
                ax.grid(True, axis="y", linestyle="--", alpha=0.25)
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)

            elif chart_type == "heatmap":
                numeric_df = df.select_dtypes(include="number").dropna(how="all", axis=1)
                if numeric_df.shape[1] < 2:
                    raise ValueError("相关性热力图至少需要 2 个数值列。")
                numeric_df = numeric_df.iloc[:, :12]
                corr = numeric_df.corr()

                fig, ax = plt.subplots(figsize=figsize_tuple, dpi=120)
                image = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
                fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
                ax.set_xticks(range(len(corr.columns)))
                ax.set_yticks(range(len(corr.columns)))
                ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
                ax.set_yticklabels(corr.columns, fontsize=8)
                for row_idx in range(len(corr.columns)):
                    for col_idx in range(len(corr.columns)):
                        ax.text(col_idx, row_idx, f"{corr.iloc[row_idx, col_idx]:.2f}", ha="center", va="center", fontsize=7)
                ax.set_title(title or _chart_text(use_chinese_text, "相关性热力图", "Correlation Heatmap"), fontsize=13)

            elif chart_type == "scatter_matrix":
                numeric_df = df.select_dtypes(include="number").dropna()
                if numeric_df.shape[1] < 2:
                    raise ValueError("多字段散点矩阵至少需要 2 个数值列。")
                selected_cols = []
                for col in [x_col, y_col]:
                    if col in numeric_df.columns and col not in selected_cols:
                        selected_cols.append(col)
                for col in numeric_df.columns:
                    if col not in selected_cols:
                        selected_cols.append(col)
                    if len(selected_cols) >= 5:
                        break
                matrix_df = numeric_df[selected_cols].sample(n=min(len(numeric_df), 500), random_state=42)
                axes = scatter_matrix(matrix_df, figsize=figsize_tuple, diagonal="hist", color=color, alpha=0.65)
                fig = axes[0, 0].figure
                fig.suptitle(title or _chart_text(use_chinese_text, "多字段散点矩阵", "Scatter Matrix"), fontsize=13)

            elif chart_type == "missing":
                missing_counts = df.isna().sum().sort_values(ascending=False)
                missing_counts = missing_counts[missing_counts > 0]
                if missing_counts.empty:
                    missing_counts = pd.Series([0], index=[_chart_text(use_chinese_text, "无缺失值", "No Missing Values")])
                missing_counts = missing_counts.head(30)

                fig, ax = plt.subplots(figsize=figsize_tuple, dpi=120)
                ax.bar(missing_counts.index.astype(str), missing_counts.values, color=color, width=0.65)
                ax.set_title(title or _chart_text(use_chinese_text, "缺失值可视化", "Missing Values"), fontsize=13)
                ax.set_xlabel(_chart_text(use_chinese_text, "字段", "Column"))
                ax.set_ylabel(_chart_text(use_chinese_text, "缺失数量", "Missing Count"))
                ax.grid(True, axis="y", linestyle="--", alpha=0.25)
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)

            if fig is None:
                raise ValueError(f"不支持的图表类型: {chart_type}")

            fig.tight_layout()
            chart_path = _save_figure(fig, chart_type)
        finally:
            if fig is not None:
                plt.close(fig)

    return chart_path
