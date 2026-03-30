"""
实时推送系统数据类型定义 - Cycle 31
定义 WebSocket 连接、订阅、消息等数据结构
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Tuple
from enum import Enum
from datetime import datetime
import uuid


class MessageType(Enum):
    """消息类型"""
    NEW_TENDER = "new_tender"
    OPPORTUNITY_ALERT = "opportunity_alert"
    SYSTEM_NOTIFICATION = "system_notification"
    HEARTBEAT = "heartbeat"


class Priority(Enum):
    """消息优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertLevel(Enum):
    """预警级别"""
    CRITICAL = "critical"     # 紧急
    HIGH = "high"             # 高
    MEDIUM = "medium"         # 中
    LOW = "low"               # 低


@dataclass
class SubscriptionFilter:
    """订阅筛选条件"""
    regions: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    amount_range: Optional[Tuple[float, float]] = None
    min_opportunity_score: Optional[float] = None

    def matches_tender(self, tender_data: "TenderData") -> bool:
        """检查招标信息是否匹配筛选条件"""
        # 地区匹配
        if self.regions:
            if not tender_data.region or tender_data.region not in self.regions:
                return False

        # 行业匹配
        if self.industries:
            if not tender_data.industry or tender_data.industry not in self.industries:
                return False

        # 金额区间匹配
        if self.amount_range and tender_data.budget is not None:
            min_amount, max_amount = self.amount_range
            if not (min_amount <= tender_data.budget <= max_amount):
                return False

        # 商机评分匹配
        if self.min_opportunity_score is not None:
            if tender_data.opportunity_score is None:
                return False
            if tender_data.opportunity_score < self.min_opportunity_score:
                return False

        return True


@dataclass
class Subscription:
    """订阅配置"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str = ""
    filters: SubscriptionFilter = field(default_factory=SubscriptionFilter)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Connection:
    """WebSocket 连接"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str = ""
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)
    subscriptions: List[Subscription] = field(default_factory=list)
    is_authenticated: bool = False

    def is_active(self, timeout_seconds: int = 60) -> bool:
        """检查连接是否活跃"""
        now = datetime.now()
        diff = (now - self.last_ping).total_seconds()
        return diff < timeout_seconds


@dataclass
class TenderData:
    """招标信息数据（用于推送）"""
    tender_id: str
    title: str
    tenderer: str
    region: Optional[str] = None
    industry: Optional[str] = None
    budget: Optional[float] = None
    publish_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None
    url: Optional[str] = None
    opportunity_score: Optional[float] = None


@dataclass
class PushMessage:
    """推送消息"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: Priority = Priority.MEDIUM
    connection_id: Optional[str] = None
    subscription_id: Optional[str] = None


@dataclass
class OpportunityAlert:
    """商机预警"""
    tender_id: str
    title: str
    tenderer: str
    score: float
    alert_level: AlertLevel
    reason: str
    matched_filters: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PushStatistics:
    """推送统计"""
    total_messages: int = 0
    new_tender_count: int = 0
    opportunity_alert_count: int = 0
    failed_count: int = 0
    last_push_time: Optional[datetime] = None