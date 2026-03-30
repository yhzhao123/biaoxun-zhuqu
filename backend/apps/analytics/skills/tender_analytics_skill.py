"""
Tender Analytics Skill 加载器

将 Analytics Tools 封装为 deer-flow Skill。
"""

from apps.analytics.tools import (
    aggregate_data,
    analyze_trends,
    classify_tender,
    score_opportunity,
)

SKILL_NAME = "tender-analytics"
SKILL_PATH = "skills/tender-analytics"


def load_skill() -> dict:
    """
    加载 Tender Analytics Skill

    Returns:
        Skill 配置字典，包含 name、tools、path 字段
    """
    return {
        "name": SKILL_NAME,
        "tools": [
            classify_tender,
            score_opportunity,
            analyze_trends,
            aggregate_data,
        ],
        "path": SKILL_PATH,
    }


__all__ = ["load_skill", "SKILL_NAME", "SKILL_PATH"]