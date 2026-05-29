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


def _choose_chart_font() -> tuple[str | None, bool]:
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    for font_name in FONT_PRIORITY:
        if font_name in available_fonts:
            return font_name, font_name in CHINESE_FONT_NAMES
    return None, False


def _apply_chart_font() -> bool:
    font_name, use_chinese_text = _choose_chart_font()
    if font_name:
        plt.rcParams["font.sans-serif"] = [font_name]
    plt.rcParams["axes.unicode_minus"] = False
    return use_chinese_text


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
    use_chinese_text = _apply_chart_font()

    if not title:
        title = f"{y_col} vs {x_col}" if use_chinese_text else f"{y_col} vs {x_col}"

    figsize_tuple = _parse_figsize(figsize)
    fig, ax = plt.subplots(figsize=figsize_tuple, dpi=120)

    try:
        if chart_type == "line":
            ax.plot(x_data, y_data, color=color, linewidth=1.5, marker="o", markersize=4)
        elif chart_type == "bar":
            ax.bar(x_data.astype(str), y_data, color=color, width=0.65)
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
        elif chart_type == "scatter":
            ax.scatter(x_data, y_data, color=color, alpha=0.75, edgecolors="white", linewidth=0.5)
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
