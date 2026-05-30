"""自动化清洗规则引擎 — 预设模板 / JSON 持久化 / 规则校验 / 批量执行。

所有实现委托给 services.clean_service 单一数据源。
"""

from services.clean_service import (
    ColumnRule,
    RuleSet,
    PRESETS,
    validate_ruleset,
    apply_ruleset,
    save_ruleset,
    load_ruleset,
    delete_ruleset,
    list_saved_rules,
)

__all__ = [
    "ColumnRule",
    "RuleSet",
    "PRESETS",
    "validate_ruleset",
    "apply_ruleset",
    "save_ruleset",
    "load_ruleset",
    "delete_ruleset",
    "list_saved_rules",
]
