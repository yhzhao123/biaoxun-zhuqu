"""
Analytics Tools - TDD Cycle 33-36

将各种分析器封装为 deer-flow Tools
使用 LangChain 的 @tool 装饰器
"""

# 导出所有 Tool
from apps.analytics.tools.classify_tender import classify_tender, ClassifyTenderInput
from apps.analytics.tools.score_opportunity import score_opportunity, ScoreOpportunityInput
from apps.analytics.tools.analyze_trends import analyze_trends, AnalyzeTrendsInput
from apps.analytics.tools.aggregate_data import aggregate_data, AggregateDataInput

__all__ = [
    "classify_tender",
    "ClassifyTenderInput",
    "score_opportunity",
    "ScoreOpportunityInput",
    "analyze_trends",
    "AnalyzeTrendsInput",
    "aggregate_data",
    "AggregateDataInput",
]