# 导入必要的库
import os  # 处理文件和目录路径
import matplotlib.pyplot as plt  # 绘图核心库
import pandas as pd  # 处理表格数据
from datetime import datetime  # 生成时间戳，避免文件名重复

# --------------------------
# 全局配置（Web环境必须）
# --------------------------
# 强制使用非交互式后端，解决Web服务器无法显示图形界面的问题
plt.switch_backend('Agg')
# 解决中文显示乱码问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
# 解决负号显示为方块的问题
plt.rcParams['axes.unicode_minus'] = False

# 图表保存目录，自动创建（如果不存在）
CHART_DIR = "outputs/charts"
os.makedirs(CHART_DIR, exist_ok=True)

# --------------------------
# 核心函数：生成图表
# --------------------------
def generate_chart(
    df: pd.DataFrame,    # 输入的数据源（表格）
    chart_type: str,     # 图表类型：line/bar/scatter
    x_col: str,          # X轴列名
    y_col: str,          # Y轴列名
    title: str = None,   # 图表标题（可选）
    color: str = "#3498db",  # 图表颜色（默认蓝色）
    figsize_width: int = 10,  # 图片宽度（英寸）
    figsize_height: int = 6   # 图片高度（英寸）
):
    """
    生成基础可视化图表
    支持：折线图（趋势）、柱状图（对比）、散点图（相关性）
    返回：生成的图片URL路径
    """
    # 1. 参数校验：防止用户传入无效参数
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"列名不存在：{x_col} 或 {y_col}")
    
    valid_types = ["line", "bar", "scatter"]
    if chart_type not in valid_types:
        raise ValueError(f"不支持的图表类型：{chart_type}")
    
    # 2. 自动生成标题（如果用户没传）
    if not title:
        title = f"{x_col} vs {y_col}"
    
    # 3. 生成唯一文件名：时间戳命名，避免覆盖之前的图表
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_name = f"{chart_type}_{timestamp}.png"
    img_path = os.path.join(CHART_DIR, img_name)
    
    # 4. 创建画布和坐标系
    fig, ax = plt.subplots(figsize=(figsize_width, figsize_height))
    
    # 5. 根据类型绘制不同图表
    if chart_type == "scatter":
        ax.scatter(df[x_col], df[y_col], color=color, alpha=0.7, s=50)  # 散点图
    elif chart_type == "line":
        ax.plot(df[x_col], df[y_col], color=color, marker='o', linewidth=2)  # 折线图
    elif chart_type == "bar":
        ax.bar(df[x_col], df[y_col], color=color, alpha=0.8)  # 柱状图
    
    # 6. 图表基础配置
    ax.set_title(title, fontsize=14, pad=15)  # 设置标题
    ax.set_xlabel(x_col, fontsize=12)         # 设置X轴标签
    ax.set_ylabel(y_col, fontsize=12)         # 设置Y轴标签
    ax.grid(True, linestyle='--', alpha=0.3)  # 添加网格线
    
    # 优化X轴标签显示，防止重叠
    plt.xticks(rotation=30, ha='right')
    # 自动调整布局，防止标签被截断
    plt.tight_layout()
    
    # 7. 保存为PNG图片并释放资源
    plt.savefig(img_path, dpi=100, bbox_inches='tight')
    plt.close()  # 必须关闭，否则会内存泄漏
    
    # 返回图片URL路径，供前端显示
    return f"/outputs/charts/{img_name}"
