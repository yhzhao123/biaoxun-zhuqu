"""
TenderAgent - 招标信息智能提取系统

基于 DeerFlow 框架重构的招标信息提取智能体系统
"""

__version__ = "2.0.0"

# V1 基础编排器
from .tender_orchestrator import TenderOrchestrator

# V2 增强编排器 (4智能体团队)
from .orchestrator_v2 import TenderOrchestratorV2, OrchestratorV2Config

# 4个智能体团队
from .workers.concurrency_agent import ConcurrencyControlAgent, ConcurrencyConfig
from .workers.retry_agent import RetryMechanismAgent, RetryConfig
from .workers.cache_agent import CacheAgent, CacheConfig
from .workers.field_optimizer import FieldOptimizationAgent, FieldOptimizationConfig

# Schema
from .schema import (
    TenderNoticeSchema,
    ExtractionStrategy,
    DetailResult,
    ValidationResult,
    Attachment
)

__all__ = [
    # V1
    'TenderOrchestrator',
    # V2
    'TenderOrchestratorV2',
    'OrchestratorV2Config',
    # 4智能体团队
    'ConcurrencyControlAgent',
    'ConcurrencyConfig',
    'RetryMechanismAgent',
    'RetryConfig',
    'CacheAgent',
    'CacheConfig',
    'FieldOptimizationAgent',
    'FieldOptimizationConfig',
    # Schema
    'TenderNoticeSchema',
    'ExtractionStrategy',
    'DetailResult',
    'ValidationResult',
    'Attachment',
]
