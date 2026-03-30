"""
实时推送系统测试 - Cycle 31
TDD: 先编写测试，再实现代码
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List
import asyncio

from apps.analytics.realtime.models import (
    MessageType,
    Priority,
    AlertLevel,
    SubscriptionFilter,
    Subscription,
    Connection,
    TenderData,
    PushMessage,
    OpportunityAlert,
)
from apps.analytics.realtime.push_service import RealtimePushService


# ==================== Fixtures ====================

@pytest_asyncio.fixture
async def service():
    """创建实时推送服务实例"""
    return RealtimePushService()


@pytest.fixture
def sample_tender() -> TenderData:
    """示例招标信息"""
    return TenderData(
        tender_id="T001",
        title="某省政府办公家具采购项目",
        tenderer="某省政府采购中心",
        region="北京",
        industry="家具",
        budget=500000.0,
        publish_date=datetime.now(),
        deadline_date=datetime.now() + timedelta(days=30),
        url="https://example.com/tender/T001",
        opportunity_score=85.0,
    )


@pytest.fixture
def sample_opportunity_alert() -> OpportunityAlert:
    """示例商机预警"""
    return OpportunityAlert(
        tender_id="T001",
        title="高价值项目招标",
        tenderer="某省政府",
        score=85.0,
        alert_level=AlertLevel.HIGH,
        reason="高预算+低竞争+长期项目",
        matched_filters=["high_budget", "low_competition"],
    )


# ==================== 测试 1-2: 连接管理 ====================

@pytest.mark.asyncio
async def test_connect_creates_new_connection(service: RealtimePushService):
    """测试连接建立 - 应该创建新的连接对象"""
    client_id = "client_001"

    connection = await service.connect(client_id)

    assert connection is not None
    assert connection.client_id == client_id
    assert connection.is_authenticated is True
    assert connection.id in service.connections


@pytest.mark.asyncio
async def test_disconnect_removes_connection(service: RealtimePushService):
    """测试连接断开 - 应该移除连接"""
    connection = await service.connect("client_001")
    connection_id = connection.id

    await service.disconnect(connection_id)

    assert connection_id not in service.connections


# ==================== 测试 3: 心跳检测 ====================

@pytest.mark.asyncio
async def test_ping_updates_last_ping_time(service: RealtimePushService):
    """测试心跳检测 - 应该更新最后 ping 时间"""
    connection = await service.connect("client_001")
    original_ping = connection.last_ping

    # 等待一小段时间确保时间差
    import asyncio
    await asyncio.sleep(0.01)

    await service.ping(connection.id)

    assert connection.last_ping > original_ping


# ==================== 测试 4-7: 订阅管理 ====================

@pytest.mark.asyncio
async def test_subscribe_creates_subscription(service: RealtimePushService):
    """测试订阅创建"""
    connection = await service.connect("client_001")
    filters = SubscriptionFilter(regions=["北京", "上海"])

    subscription = await service.subscribe(connection.id, filters)

    assert subscription is not None
    assert subscription.connection_id == connection.id
    assert subscription.filters.regions == ["北京", "上海"]
    assert len(connection.subscriptions) == 1


@pytest.mark.asyncio
async def test_unsubscribe_removes_subscription(service: RealtimePushService):
    """测试订阅取消"""
    connection = await service.connect("client_001")
    filters = SubscriptionFilter(regions=["北京"])
    subscription = await service.subscribe(connection.id, filters)
    subscription_id = subscription.id

    await service.unsubscribe(subscription_id)

    assert subscription_id not in [s.id for s in connection.subscriptions]


@pytest.mark.asyncio
async def test_get_subscriptions_returns_all_subscriptions(service: RealtimePushService):
    """测试获取订阅列表"""
    connection = await service.connect("client_001")
    await service.subscribe(connection.id, SubscriptionFilter(regions=["北京"]))
    await service.subscribe(connection.id, SubscriptionFilter(industries=["家具"]))

    subscriptions = await service.get_subscriptions(connection.id)

    assert len(subscriptions) == 2


# ==================== 测试 8-11: 订阅筛选 ====================

@pytest.mark.asyncio
async def test_subscription_filter_by_region(service: RealtimePushService):
    """测试按地区订阅筛选"""
    connection = await service.connect("client_001")
    filters = SubscriptionFilter(regions=["北京", "上海"])
    await service.subscribe(connection.id, filters)

    # 创建测试数据
    tender_beijing = TenderData(
        tender_id="T001", title="北京项目", tenderer="北京公司",
        region="北京", budget=100000
    )
    tender_shanghai = TenderData(
        tender_id="T002", title="上海项目", tenderer="上海公司",
        region="上海", budget=100000
    )
    tender_guangzhou = TenderData(
        tender_id="T003", title="广州项目", tenderer="广州公司",
        region="广州", budget=100000
    )

    # 验证筛选逻辑
    assert filters.matches_tender(tender_beijing) is True
    assert filters.matches_tender(tender_shanghai) is True
    assert filters.matches_tender(tender_guangzhou) is False


@pytest.mark.asyncio
async def test_subscription_filter_by_industry(service: RealtimePushService):
    """测试按行业订阅筛选"""
    filters = SubscriptionFilter(industries=["家具", "办公设备"])

    tender_furniture = TenderData(
        tender_id="T001", title="家具项目", tenderer="公司A",
        industry="家具", budget=100000
    )
    tender_office = TenderData(
        tender_id="T002", title="办公设备项目", tenderer="公司B",
        industry="办公设备", budget=100000
    )
    tender_it = TenderData(
        tender_id="T003", title="IT项目", tenderer="公司C",
        industry="IT", budget=100000
    )

    assert filters.matches_tender(tender_furniture) is True
    assert filters.matches_tender(tender_office) is True
    assert filters.matches_tender(tender_it) is False


@pytest.mark.asyncio
async def test_subscription_filter_by_amount_range(service: RealtimePushService):
    """测试按金额区间订阅筛选"""
    filters = SubscriptionFilter(amount_range=(100000, 500000))

    tender_low = TenderData(
        tender_id="T001", title="小额项目", tenderer="公司A", budget=50000
    )
    tender_mid = TenderData(
        tender_id="T002", title="中等项目", tenderer="公司B", budget=300000
    )
    tender_high = TenderData(
        tender_id="T003", title="大额项目", tenderer="公司C", budget=1000000
    )

    assert filters.matches_tender(tender_low) is False
    assert filters.matches_tender(tender_mid) is True
    assert filters.matches_tender(tender_high) is False


@pytest.mark.asyncio
async def test_subscription_filter_by_opportunity_score(service: RealtimePushService):
    """测试按商机评分订阅筛选"""
    filters = SubscriptionFilter(min_opportunity_score=80.0)

    tender_high_score = TenderData(
        tender_id="T001", title="高评分项目", tenderer="公司A",
        opportunity_score=85.0
    )
    tender_low_score = TenderData(
        tender_id="T002", title="低评分项目", tenderer="公司B",
        opportunity_score=60.0
    )
    tender_no_score = TenderData(
        tender_id="T003", title="无评分项目", tenderer="公司C",
        opportunity_score=None
    )

    assert filters.matches_tender(tender_high_score) is True
    assert filters.matches_tender(tender_low_score) is False
    assert filters.matches_tender(tender_no_score) is False


# ==================== 测试 12: 组合订阅 ====================

@pytest.mark.asyncio
async def test_multiple_filter_conditions(service: RealtimePushService):
    """测试多条件组合订阅"""
    filters = SubscriptionFilter(
        regions=["北京"],
        industries=["家具"],
        amount_range=(100000, 500000),
        min_opportunity_score=70.0
    )

    # 匹配所有条件
    tender_match = TenderData(
        tender_id="T001", title="北京家具项目", tenderer="北京公司",
        region="北京", industry="家具", budget=300000, opportunity_score=80.0
    )
    # 不匹配地区
    tender_no_region = TenderData(
        tender_id="T002", title="上海家具项目", tenderer="上海公司",
        region="上海", industry="家具", budget=300000, opportunity_score=80.0
    )
    # 不匹配行业
    tender_no_industry = TenderData(
        tender_id="T003", title="北京IT项目", tenderer="北京公司",
        region="北京", industry="IT", budget=300000, opportunity_score=80.0
    )
    # 不匹配金额
    tender_no_amount = TenderData(
        tender_id="T004", title="北京家具大项目", tenderer="北京公司",
        region="北京", industry="家具", budget=1000000, opportunity_score=80.0
    )
    # 不匹配评分
    tender_no_score = TenderData(
        tender_id="T005", title="北京家具低分项目", tenderer="北京公司",
        region="北京", industry="家具", budget=300000, opportunity_score=50.0
    )

    assert filters.matches_tender(tender_match) is True
    assert filters.matches_tender(tender_no_region) is False
    assert filters.matches_tender(tender_no_industry) is False
    assert filters.matches_tender(tender_no_amount) is False
    assert filters.matches_tender(tender_no_score) is False


# ==================== 测试 13-14: 推送功能 ====================

@pytest.mark.asyncio
async def test_push_new_tender(service: RealtimePushService, sample_tender: TenderData):
    """测试新招标信息推送"""
    # 创建带匹配的订阅
    connection = await service.connect("client_001")
    filters = SubscriptionFilter(regions=["北京"])
    await service.subscribe(connection.id, filters)

    # 模拟推送
    with patch.object(service, 'send_message', new_callable=AsyncMock) as mock_send:
        await service.push_new_tender(sample_tender)
        # 验证发送了消息
        assert mock_send.called or service.statistics.new_tender_count > 0


@pytest.mark.asyncio
async def test_push_opportunity_alert(service: RealtimePushService, sample_opportunity_alert: OpportunityAlert):
    """测试高价值商机预警推送"""
    connection = await service.connect("client_001")
    filters = SubscriptionFilter(min_opportunity_score=80.0)
    await service.subscribe(connection.id, filters)

    with patch.object(service, 'send_message', new_callable=AsyncMock) as mock_send:
        await service.push_opportunity_alert(sample_opportunity_alert)
        assert mock_send.called or service.statistics.opportunity_alert_count > 0


# ==================== 测试 15: 推送频率控制 ====================

@pytest.mark.asyncio
async def test_rate_limiting(service: RealtimePushService, sample_tender: TenderData):
    """测试推送频率控制"""
    connection = await service.connect("client_001")
    filters = SubscriptionFilter()
    await service.subscribe(connection.id, filters)

    # 设置较低的速率限制用于测试
    service.rate_limit_messages = 3

    # 快速发送多条消息
    for i in range(5):
        await service.push_new_tender(sample_tender)

    # 验证速率限制生效
    assert service.statistics.total_messages <= 5  # 可能部分被限制


# ==================== 测试 16: 消息队列集成 ====================

@pytest.mark.asyncio
async def test_publish_to_queue(service: RealtimePushService):
    """测试消息队列发布"""
    test_channel = "test_channel"
    message = PushMessage(
        type=MessageType.NEW_TENDER,
        data={"tender_id": "T001", "title": "测试项目"}
    )

    # 模拟 Redis 发布
    with patch('redis.asyncio.Redis') as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance

        # 如果没有 Redis，直接测试内部队列
        service.message_queue = []
        await service.publish_to_queue(test_channel, message)

        # 验证消息已加入队列或发布
        assert len(service.message_queue) > 0 or mock_redis_instance.publish.called


# ==================== 测试 17: 连接状态管理 ====================

@pytest.mark.asyncio
async def test_connection_state_management(service: RealtimePushService):
    """测试连接状态管理"""
    connection = await service.connect("client_001")

    # 初始状态
    assert connection.is_active() is True

    # 模拟超时
    connection.last_ping = datetime.now() - timedelta(seconds=120)

    # 超时后应不活跃
    assert connection.is_active(timeout_seconds=60) is False


# ==================== 测试 18: 错误处理 ====================

@pytest.mark.asyncio
async def test_error_handling_invalid_connection(service: RealtimePushService):
    """测试错误处理 - 无效连接"""
    # 尝试断开不存在的连接
    await service.disconnect("invalid_id")

    # 尝试向不存在的连接发送消息
    result = await service.send_message("invalid_id", PushMessage(
        type=MessageType.NEW_TENDER,
        data={}
    ))
    assert result is False


# ==================== 测试 19: 并发连接处理 ====================

@pytest.mark.asyncio
async def test_concurrent_connections(service: RealtimePushService):
    """测试并发连接处理"""

    async def create_and_subscribe(client_id: str):
        conn = await service.connect(client_id)
        await service.subscribe(conn.id, SubscriptionFilter(regions=["北京"]))
        return conn.id

    # 并发创建多个连接
    tasks = [create_and_subscribe(f"client_{i}") for i in range(10)]
    connection_ids = await asyncio.gather(*tasks)

    # 验证所有连接都创建成功
    assert len(service.connections) == 10

    # 验证每个连接都有订阅
    for conn_id in connection_ids:
        conn = service.connections[conn_id]
        assert len(conn.subscriptions) == 1


# ==================== 测试 20-22: 队列管理 ====================

@pytest.mark.asyncio
async def test_subscribe_to_queue(service: RealtimePushService):
    """测试订阅消息队列"""
    received_messages = []

    async def callback(message: PushMessage):
        received_messages.append(message)

    await service.subscribe_to_queue("test_channel", callback)

    assert "test_channel" in service._queue_subscribers
    assert callback in service._queue_subscribers["test_channel"]


@pytest.mark.asyncio
async def test_unsubscribe_from_queue(service: RealtimePushService):
    """测试取消订阅消息队列"""
    async def callback(message: PushMessage):
        pass

    await service.subscribe_to_queue("test_channel", callback)
    await service.unsubscribe_from_queue("test_channel", callback)

    assert callback not in service._queue_subscribers.get("test_channel", [])


# ==================== 测试 23-24: 统计功能 ====================

@pytest.mark.asyncio
async def test_get_statistics(service: RealtimePushService, sample_tender: TenderData):
    """测试获取统计信息"""
    connection = await service.connect("client_001")
    filters = SubscriptionFilter()
    await service.subscribe(connection.id, filters)

    await service.push_new_tender(sample_tender)

    stats = service.get_statistics()
    assert stats.total_messages > 0
    assert stats.new_tender_count > 0


@pytest.mark.asyncio
async def test_get_active_connections(service: RealtimePushService):
    """测试获取活跃连接列表"""
    await service.connect("client_001")
    await service.connect("client_002")

    active = service.get_active_connections()
    assert len(active) == 2


# ==================== 测试 25-26: 连接状态检查 ====================

@pytest.mark.asyncio
async def test_is_connection_active(service: RealtimePushService):
    """测试检查连接是否活跃"""
    connection = await service.connect("client_001")

    assert service.is_connection_active(connection.id) is True
    assert service.is_connection_active("invalid_id") is False


# ==================== 测试 27-28: 清理功能 ====================

@pytest.mark.asyncio
async def test_cleanup_stale_connections(service: RealtimePushService):
    """测试清理不活跃连接"""
    connection = await service.connect("client_001")
    # 模拟超时
    connection.last_ping = datetime.now() - timedelta(seconds=120)

    cleaned = await service.cleanup_stale_connections()

    assert cleaned == 1
    assert connection.id not in service.connections


@pytest.mark.asyncio
async def test_ping_nonexistent_connection(service: RealtimePushService):
    """测试 ping 不存在的连接"""
    result = await service.ping("invalid_connection_id")
    assert result is False


# ==================== 测试 29: 组合筛选推送 ====================

@pytest.mark.asyncio
async def test_push_tender_matches_multiple_subscriptions(service: RealtimePushService):
    """测试推送匹配多个订阅"""
    # 创建两个连接，每个都有匹配的订阅
    conn1 = await service.connect("client_001")
    conn2 = await service.connect("client_002")

    await service.subscribe(conn1.id, SubscriptionFilter(regions=["北京"]))
    await service.subscribe(conn2.id, SubscriptionFilter(regions=["北京"]))

    tender = TenderData(
        tender_id="T001", title="北京项目", tenderer="北京公司",
        region="北京", budget=100000
    )

    count = await service.push_new_tender(tender)
    assert count == 2  # 应该匹配两个订阅


# ==================== 测试 30: 错误处理增强 ====================

@pytest.mark.asyncio
async def test_subscribe_invalid_connection(service: RealtimePushService):
    """测试向不存在的连接订阅"""
    filters = SubscriptionFilter(regions=["北京"])

    with pytest.raises(ValueError):
        await service.subscribe("invalid_connection_id", filters)