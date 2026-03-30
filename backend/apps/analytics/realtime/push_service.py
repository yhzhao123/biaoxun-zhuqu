"""
实时推送服务 - Cycle 31
实现 WebSocket 连接管理、订阅管理、消息推送功能
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any

from .models import (
    MessageType,
    Priority,
    AlertLevel,
    SubscriptionFilter,
    Subscription,
    Connection,
    TenderData,
    PushMessage,
    OpportunityAlert,
    PushStatistics,
)

logger = logging.getLogger(__name__)


class RealtimePushService:
    """实时推送服务"""

    def __init__(self):
        """初始化推送服务"""
        self.connections: Dict[str, Connection] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.statistics = PushStatistics()
        self.message_queue: List[PushMessage] = []
        self.rate_limit_messages = 100  # 每秒最大消息数
        self.last_message_time: Dict[str, datetime] = {}
        self._queue_subscribers: Dict[str, List[Callable]] = {}

    # ==================== 连接管理 ====================

    async def connect(self, client_id: str) -> Connection:
        """建立新的 WebSocket 连接"""
        connection = Connection(
            id=str(uuid.uuid4()),
            client_id=client_id,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
            subscriptions=[],
            is_authenticated=True,
        )
        self.connections[connection.id] = connection
        logger.info(f"New connection established: {connection.id} for client {client_id}")
        return connection

    async def disconnect(self, connection_id: str) -> None:
        """断开 WebSocket 连接"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            # 移除所有订阅
            for sub in connection.subscriptions:
                if sub.id in self.subscriptions:
                    del self.subscriptions[sub.id]
            # 移除连接
            del self.connections[connection_id]
            logger.info(f"Connection disconnected: {connection_id}")

    async def ping(self, connection_id: str) -> bool:
        """心跳检测"""
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.last_ping = datetime.now()
        return True

    def is_connection_active(self, connection_id: str) -> bool:
        """检查连接是否活跃"""
        if connection_id not in self.connections:
            return False
        return self.connections[connection_id].is_active(timeout_seconds=60)

    # ==================== 订阅管理 ====================

    async def subscribe(
        self, connection_id: str, filters: SubscriptionFilter
    ) -> Subscription:
        """创建订阅"""
        if connection_id not in self.connections:
            raise ValueError(f"Connection {connection_id} not found")

        subscription = Subscription(
            id=str(uuid.uuid4()),
            connection_id=connection_id,
            filters=filters,
            created_at=datetime.now(),
        )

        self.subscriptions[subscription.id] = subscription
        self.connections[connection_id].subscriptions.append(subscription)
        logger.info(f"New subscription created: {subscription.id} for connection {connection_id}")
        return subscription

    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]
        connection_id = subscription.connection_id

        # 从连接中移除
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.subscriptions = [
                s for s in connection.subscriptions if s.id != subscription_id
            ]

        # 从订阅字典中移除
        del self.subscriptions[subscription_id]
        logger.info(f"Subscription removed: {subscription_id}")
        return True

    async def get_subscriptions(self, connection_id: str) -> List[Subscription]:
        """获取连接的所有订阅"""
        if connection_id not in self.connections:
            return []
        return self.connections[connection_id].subscriptions

    # ==================== 消息推送 ====================

    async def push_new_tender(self, tender: TenderData) -> int:
        """推送新招标信息"""
        # 检查速率限制
        if not self._check_rate_limit(tender.tender_id):
            logger.warning(f"Rate limit exceeded for tender {tender.tender_id}")
            return 0

        # 找到匹配的订阅
        matched_count = 0
        for subscription in self.subscriptions.values():
            if subscription.filters.matches_tender(tender):
                message = PushMessage(
                    type=MessageType.NEW_TENDER,
                    data={
                        "tender_id": tender.tender_id,
                        "title": tender.title,
                        "tenderer": tender.tenderer,
                        "region": tender.region,
                        "industry": tender.industry,
                        "budget": tender.budget,
                        "publish_date": tender.publish_date.isoformat() if tender.publish_date else None,
                        "deadline_date": tender.deadline_date.isoformat() if tender.deadline_date else None,
                        "url": tender.url,
                        "opportunity_score": tender.opportunity_score,
                    },
                    priority=Priority.MEDIUM,
                    connection_id=subscription.connection_id,
                    subscription_id=subscription.id,
                )

                await self.send_message(subscription.connection_id, message)
                matched_count += 1

        # 更新统计
        self.statistics.new_tender_count += 1
        self.statistics.total_messages += matched_count
        self.statistics.last_push_time = datetime.now()

        return matched_count

    async def push_opportunity_alert(self, alert: OpportunityAlert) -> int:
        """推送商机预警"""
        # 检查速率限制
        if not self._check_rate_limit(f"alert_{alert.tender_id}"):
            logger.warning(f"Rate limit exceeded for alert {alert.tender_id}")
            return 0

        # 商机预警推送给所有相关订阅
        matched_count = 0
        for subscription in self.subscriptions.values():
            # 检查是否匹配商机评分要求
            if (
                subscription.filters.min_opportunity_score is not None
                and alert.score >= subscription.filters.min_opportunity_score
            ):
                message = PushMessage(
                    type=MessageType.OPPORTUNITY_ALERT,
                    data={
                        "tender_id": alert.tender_id,
                        "title": alert.title,
                        "tenderer": alert.tenderer,
                        "score": alert.score,
                        "alert_level": alert.alert_level.value,
                        "reason": alert.reason,
                        "matched_filters": alert.matched_filters,
                    },
                    priority=Priority.HIGH,
                    connection_id=subscription.connection_id,
                    subscription_id=subscription.id,
                )

                await self.send_message(subscription.connection_id, message)
                matched_count += 1

        # 更新统计
        self.statistics.opportunity_alert_count += 1
        self.statistics.total_messages += matched_count
        self.statistics.last_push_time = datetime.now()

        return matched_count

    async def send_message(self, connection_id: str, message: PushMessage) -> bool:
        """发送消息到指定连接"""
        if connection_id not in self.connections:
            self.statistics.failed_count += 1
            return False

        connection = self.connections[connection_id]
        if not connection.is_active():
            self.statistics.failed_count += 1
            return False

        # 模拟发送消息（实际实现中会通过 WebSocket 发送）
        logger.debug(
            f"Sending message to {connection_id}: type={message.type.value}, "
            f"priority={message.priority.value}"
        )

        # 这里可以集成实际的 WebSocket 发送逻辑
        # 例如: await self.ws_manager.send(connection_id, message)

        return True

    def _check_rate_limit(self, key: str) -> bool:
        """检查速率限制"""
        now = datetime.now()

        # 清理过期的记录
        self.last_message_time = {
            k: v for k, v in self.last_message_time.items()
            if (now - v).total_seconds() < 1.0
        }

        # 检查是否超过限制
        if len(self.last_message_time) >= self.rate_limit_messages:
            return False

        self.last_message_time[key] = now
        return True

    # ==================== 消息队列集成 ====================

    async def publish_to_queue(self, channel: str, message: PushMessage) -> bool:
        """发布消息到队列"""
        try:
            # 添加到内部队列
            self.message_queue.append(message)

            # 如果有订阅者，通知他们
            if channel in self._queue_subscribers:
                for callback in self._queue_subscribers[channel]:
                    await callback(message)

            logger.debug(f"Message published to channel {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to queue: {e}")
            return False

    async def subscribe_to_queue(self, channel: str, callback: Callable) -> None:
        """订阅消息队列"""
        if channel not in self._queue_subscribers:
            self._queue_subscribers[channel] = []
        self._queue_subscribers[channel].append(callback)
        logger.info(f"Callback subscribed to channel {channel}")

    async def unsubscribe_from_queue(self, channel: str, callback: Callable) -> None:
        """取消订阅消息队列"""
        if channel in self._queue_subscribers:
            self._queue_subscribers[channel] = [
                cb for cb in self._queue_subscribers[channel] if cb != callback
            ]

    # ==================== 统计和管理 ====================

    def get_statistics(self) -> PushStatistics:
        """获取推送统计信息"""
        return self.statistics

    def get_active_connections(self) -> List[Connection]:
        """获取活跃连接列表"""
        return [
            conn for conn in self.connections.values() if conn.is_active()
        ]

    async def cleanup_stale_connections(self) -> int:
        """清理不活跃的连接"""
        stale_connections = [
            conn_id for conn_id, conn in self.connections.items()
            if not conn.is_active(timeout_seconds=60)
        ]

        for conn_id in stale_connections:
            await self.disconnect(conn_id)

        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")

        return len(stale_connections)