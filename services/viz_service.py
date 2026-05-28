import os
import uuid

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from config import OUTPUT_DIR


plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_chart(df, chart_type, x_col, y_col, title="图表", color="#3498db"):
    img_name = f"{uuid.uuid4().hex}.png"
    img_path = os.path.join(OUTPUT_DIR, img_name)

    fig, ax = plt.subplots(figsize=(10, 5))

    if chart_type == "scatter":
        ax.scatter(df[x_col], df[y_col], color=color)
    elif chart_type == "line":
        ax.plot(df[x_col], df[y_col], color=color)
    elif chart_type == "bar":
        ax.bar(df[x_col], df[y_col], color=color)

    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()

    return f"/outputs/charts/{img_name}"
