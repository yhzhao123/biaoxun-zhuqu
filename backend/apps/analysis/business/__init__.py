"""
Business Analysis Module - Phase 7 Tasks 036-041
Provides business intelligence, opportunity identification,
competitor analysis, and market trend analysis.
"""

from .opportunity_service import OpportunityService
from .competitor_service import CompetitorService
from .trend_service import TrendService
from .business_intelligence import BusinessIntelligence

__all__ = [
    'OpportunityService',
    'CompetitorService',
    'TrendService',
    'BusinessIntelligence',
]
