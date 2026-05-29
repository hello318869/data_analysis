from __future__ import annotations

import os
from datetime import datetime

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd

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


def generate_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_col: str,
    y_col: str,
    title: str = "",
    color: str = "#2563eb",
    figsize: str = "8,5",
) -> str:
    if x_col not in df.columns:
        raise ValueError(f"列 '{x_col}' 不存在")
    if y_col not in df.columns:
        raise ValueError(f"列 '{y_col}' 不存在")

    x_data = df[x_col]
    y_data = df[y_col]

    # Validate y column is numeric
    from pandas.api.types import is_numeric_dtype
    if not is_numeric_dtype(y_data):
        raise ValueError(f"列 '{y_col}' 不是数值类型，无法用于图表绘制。请选择一个数值列作为 Y 轴。")

    # Get font rc_params (thread-safe, no global rcParams modification)
    rc_params, use_chinese_text = _get_chart_rc_params()

    if not title:
        title = f"{y_col} vs {x_col}" if use_chinese_text else f"{y_col} vs {x_col}"

    figsize_tuple = _parse_figsize(figsize)

    # Determine x data type for proper display
    if is_numeric_dtype(x_data):
        x_plot = x_data
    else:
        x_plot = x_data.astype(str)

    with plt.rc_context(rc_params):
        fig, ax = plt.subplots(figsize=figsize_tuple, dpi=120)

        try:
            if chart_type == "line":
                ax.plot(x_plot, y_data, color=color, linewidth=1.5, marker="o", markersize=4)
            elif chart_type == "bar":
                ax.bar(x_plot, y_data, color=color, width=0.65)
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
            elif chart_type == "scatter":
                ax.scatter(x_plot, y_data, color=color, alpha=0.75, edgecolors="white", linewidth=0.5)
            else:
                raise ValueError(f"不支持的图表类型: {chart_type}")

            ax.set_title(title, fontsize=13)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.grid(True, linestyle="--", alpha=0.25)

            fig.tight_layout()

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{chart_type}_{timestamp}.png"
            file_path = os.path.join(OUTPUT_DIR, filename)
            fig.savefig(file_path, bbox_inches="tight")
        finally:
            plt.close(fig)

    return f"/outputs/charts/{filename}"
