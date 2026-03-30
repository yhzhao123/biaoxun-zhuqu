"""
Analytics Skills Package

包含 Tender Analytics Skill 的定义和加载器。
"""

from apps.analytics.skills.tender_analytics_skill import load_skill, SKILL_NAME, SKILL_PATH

__all__ = ["load_skill", "SKILL_NAME", "SKILL_PATH"]