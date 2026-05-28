"""数据清洗模块。

提供三种清洗入口：
  - 手动清洗：选择策略 (mean/median/mode/drop/custom) + 指定列
  - 一键自动清洗：数值列中位数 + 分类列众数 + IQR 异常值截断
  - 规则集清洗：加载预设/自定义规则集批量执行

Blueprint: clean_bp
  - GET  /clean                 清洗前报告
  - POST /clean/execute         执行清洗
  - POST /clean/auto            一键自动清洗
  - GET  /clean/rules           列出规则集
  - POST /clean/rules/save      保存规则集
  - POST /clean/rules/apply/<n> 应用规则集
  - POST /clean/rules/delete/<n> 删除规则集
"""

from .routes import clean_bp, init_rules_dir
from .service import analyze_missing, detect_outliers_iqr, execute_clean, auto_clean
from .config import (
    RuleSet,
    ColumnRule,
    preset_numeric,
    preset_categorical,
    preset_full,
    list_saved_rules,
    load_ruleset,
    save_ruleset,
    delete_ruleset,
    validate_ruleset,
    apply_ruleset,
)
