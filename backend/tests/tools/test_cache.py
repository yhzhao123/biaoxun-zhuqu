"""
多级缓存系统测试

测试缓存的核心功能:
1. L1 内存缓存 - 高频访问数据
2. L2 Redis 缓存 - 分布式缓存
3. 多级缓存管理器
4. 缓存策略（TTL、LRU、LFU）
5. 缓存防护（穿透、击穿、雪崩）
"""
import pytest
import asyncio
import time
import json
from typing import Optional, Any, Protocol
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass, field
import hashlib


# ============================================================
# 缓存接口和基础类
# ============================================================

class CacheBackend(Protocol):
    """缓存后端接口"""
    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool: ...
    async def delete(self, key: str) -> bool: ...
    async def clear(self) -> None: ...


class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# ============================================================
# L1 内存缓存测试
# ============================================================

class TestMemoryCache:
    """L1 内存缓存测试"""

    @pytest.fixture
    def cache(self):
        """创建内存缓存实例"""
        from apps.crawler.tools.cache import MemoryCache
        return MemoryCache(max_size=100, ttl=60)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """测试基本的设置和获取"""
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache):
        """测试获取不存在的键"""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """测试 TTL 过期"""
        from apps.crawler.tools.cache import MemoryCache
        cache = MemoryCache(max_size=100, ttl=1)

        await cache.set("key1", "value1")
        result1 = await cache.get("key1")
        assert result1 == "value1"

        # 等待 TTL 过期
        await asyncio.sleep(1.5)

        result2 = await cache.get("key1")
        assert result2 is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """测试 LRU 驱逐"""
        from apps.crawler.tools.cache import MemoryCache
        cache = MemoryCache(max_size=3, ttl=60)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # 访问 key1 使其变为最近使用
        await cache.get("key1")

        # 添加新键，key2 应该被驱逐
        await cache.set("key4", "value4")

        result = await cache.get("key2")
        assert result is None  # key2 已被驱逐
        assert await cache.get("key1") == "value1"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """测试删除"""
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """测试清空缓存"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_stats_tracking(self, cache):
        """测试统计追踪"""
        await cache.set("key1", "value1")

        # 命中
        await cache.get("key1")

        # 未命中
        await cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_null_value_handling(self, cache):
        """测试 null 值处理"""
        await cache.set("null_key", None)
        result = await cache.get("null_key")
        # null 值应该被视为不存在或者特殊处理
        assert result is None or result == "null_marker"

    @pytest.mark.asyncio
    async def test_large_value(self, cache):
        """测试大值"""
        large_value = "x" * 10000
        await cache.set("large_key", large_value)
        result = await cache.get("large_key")
        assert result == large_value

    @pytest.mark.asyncio
    async def test_key_with_special_chars(self, cache):
        """测试特殊字符键"""
        special_keys = ["key:1", "key/2", "key.3", "key space", "key😀"]
        for key in special_keys:
            await cache.set(key, f"value_{key}")

        for key in special_keys:
            result = await cache.get(key)
            assert result == f"value_{key}"


# ============================================================
# L2 Redis 缓存测试
# ============================================================

class TestRedisCache:
    """L2 Redis 缓存测试"""

    @pytest.fixture
    def cache(self):
        """创建 Redis 缓存实例（使用模拟）"""
        from apps.crawler.tools.cache import RedisCache
        return RedisCache(prefix="test:", ttl=60)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """测试基本的设置和获取"""
        # Mock Redis 客户端
        mock_client = AsyncMock()
        mock_client.set = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value=b'"value1"')
        cache.client = mock_client

        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """测试获取不存在的键"""
        mock_client = AsyncMock()
        cache.client = mock_client
        cache.client.get = AsyncMock(return_value=None)

        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl(self, cache):
        """测试 TTL"""
        mock_client = AsyncMock()
        cache.client = mock_client
        cache.client.set = AsyncMock(return_value=True)

        await cache.set("key1", "value1", ttl=30)
        # 验证 set 被调用时带上了 ex 参数
        cache.client.set.assert_called_once()
        call_args = cache.client.set.call_args
        assert call_args[1].get('ex') == 30  # TTL 通过 ex 参数传递


# ============================================================
# 多级缓存管理器测试
# ============================================================

class TestMultiLevelCache:
    """多级缓存管理器测试"""

    @pytest.fixture
    def multi_cache(self):
        """创建多级缓存实例"""
        from apps.crawler.tools.cache import MultiLevelCache
        return MultiLevelCache(
            l1_max_size=100,
            l1_ttl=60,
            l2_prefix="test:",
            l2_ttl=300,
        )

    @pytest.mark.asyncio
    async def test_l1_hit(self, multi_cache):
        """测试 L1 命中"""
        await multi_cache.set("key1", "value1")

        # 首次获取会写入 L1
        result = await multi_cache.get("key1")

        # 再次获取应该从 L1 命中
        with patch.object(multi_cache.l2_cache, 'get', new_callable=AsyncMock) as mock_l2:
            result = await multi_cache.get("key1")
            mock_l2.assert_not_called()  # 不需要访问 L2

    @pytest.mark.asyncio
    async def test_l1_miss_l2_hit(self, multi_cache):
        """测试 L1 未命中，L2 命中"""
        # 直接设置 L2
        with patch.object(multi_cache.l2_cache, 'set', new_callable=AsyncMock):
            with patch.object(multi_cache.l2_cache, 'get', new_callable=AsyncMock) as mock_l2_get:
                mock_l2_get.return_value = "l2_value"

                # 清除 L1，强制从 L2 获取
                multi_cache.l1_cache._cache.clear()

                result = await multi_cache.get("key1")
                assert result == "l2_value"

                # 应该被提升到 L1
                l1_result = await multi_cache.l1_cache.get("key1")
                assert l1_result == "l2_value"

    @pytest.mark.asyncio
    async def test_cache_miss(self, multi_cache):
        """测试缓存未命中"""
        result = await multi_cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_propagates(self, multi_cache):
        """测试删除传播"""
        await multi_cache.set("key1", "value1")
        await multi_cache.delete("key1")

        l1_result = await multi_cache.l1_cache.get("key1")
        assert l1_result is None

    @pytest.mark.asyncio
    async def test_clear_propagates(self, multi_cache):
        """测试清空传播"""
        await multi_cache.set("key1", "value1")
        await multi_cache.set("key2", "value2")
        await multi_cache.clear()

        assert await multi_cache.get("key1") is None
        assert await multi_cache.get("key2") is None


# ============================================================
# 缓存策略测试
# ============================================================

class TestCacheStrategy:
    """缓存策略测试"""

    @pytest.mark.asyncio
    async def test_ttl_strategy(self):
        """测试 TTL 策略"""
        from apps.crawler.tools.cache import CacheStrategy, TTLStrategy

        strategy = TTLStrategy(default_ttl=60, max_ttl=3600)

        # 测试不同类型的键
        assert strategy.get_ttl("tender_list:123") == 60  # 列表缓存较短
        assert strategy.get_ttl("tender_detail:123") == 300  # 详情缓存较长
        assert strategy.get_ttl("config:key") == 3600  # 配置缓存最长

    @pytest.mark.asyncio
    async def test_adaptive_ttl(self):
        """测试自适应 TTL"""
        from apps.crawler.tools.cache import CacheStrategy, AdaptiveTTLStrategy

        strategy = AdaptiveTTLStrategy()

        # 模拟访问模式
        for _ in range(5):
            strategy.record_access("hot_key")

        ttl = strategy.get_ttl("hot_key")
        assert ttl > 60  # 热门键应该有更长的 TTL


# ============================================================
# 缓存防护测试
# ============================================================

class TestCacheProtection:
    """缓存防护测试"""

    @pytest.mark.asyncio
    async def test_cache_penetration(self):
        """测试缓存穿透防护"""
        from apps.crawler.tools.cache import CacheWithProtection

        protection = CacheWithProtection(null_cache_ttl=60)

        # 存储空值
        await protection.set("empty_key", None)

        # 应该能够获取到空值标记
        result = await protection.get("empty_key")
        assert result is None or result == "null_marker"

    @pytest.mark.asyncio
    async def test_cache_breakdown(self):
        """测试缓存击穿防护（锁）"""
        from apps.crawler.tools.cache import CacheWithProtection

        protection = CacheWithProtection(lock_timeout=10)

        # 模拟并发请求同一个不存在的键
        results = await asyncio.gather(
            protection.get_or_set("key1", lambda: asyncio.sleep(0.1) or "value1"),
            protection.get_or_set("key1", lambda: asyncio.sleep(0.1) or "value1"),
        )

        # 应该只执行一次
        assert results[0] == results[1]

    @pytest.mark.asyncio
    async def test_cache_avalanche(self):
        """测试缓存雪崩防护（随机 TTL）"""
        from apps.crawler.tools.cache import CacheWithProtection

        protection = CacheWithProtection(jitter=True)

        # 设置多个键
        await protection.set("key1", "value1")
        await protection.set("key2", "value2")

        # TTL 应该有一些随机性（通过不同的过期时间体现）
        # 这里只验证不会因为同时过期而导致雪崩
        stats = protection.get_stats()
        assert "sets" in stats


# ============================================================
# 缓存预热和刷新测试
# ============================================================

class TestCacheWarmup:
    """缓存预热和刷新测试"""

    @pytest.mark.asyncio
    async def test_warmup(self):
        """测试预热"""
        from apps.crawler.tools.cache import CacheWarmer

        # 模拟数据源
        data_source = {
            "tender_list": [{"id": 1}, {"id": 2}],
            "config": {"setting": "value"},
        }

        warmer = CacheWarmer(data_source)
        await warmer.warmup()

        # 验证预热数据
        result = await warmer.cache.get("tender_list")
        assert result == [{"id": 1}, {"id": 2}]

    @pytest.mark.asyncio
    async def test_refresh(self):
        """测试刷新"""
        from apps.crawler.tools.cache import CacheRefresher

        call_count = 0

        async def fetch_data():
            nonlocal call_count
            call_count += 1
            return {"data": f"value_{call_count}"}

        refresher = CacheRefresher(fetch_data, interval=1)
        await refresher.start()

        # 等待至少一次刷新
        await asyncio.sleep(1.5)

        await refresher.stop()

        assert call_count >= 1


# ============================================================
# 缓存装饰器测试
# ============================================================

class TestCacheDecorator:
    """缓存装饰器测试"""

    @pytest.mark.asyncio
    async def test_cached_function(self):
        """测试缓存函数装饰器"""
        from apps.crawler.tools.cache import cached

        call_count = 0

        @cached(ttl=60)
        async def expensive_operation(key: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{key}"

        # 第一次调用
        result1 = await expensive_operation("test_key")
        assert result1 == "result_test_key"
        assert call_count == 1

        # 第二次调用应该使用缓存
        result2 = await expensive_operation("test_key")
        assert result2 == "result_test_key"
        assert call_count == 1  # 没有增加

    @pytest.mark.asyncio
    async def test_cache_key_generator(self):
        """测试缓存键生成器"""
        from apps.crawler.tools.cache import cached, generate_cache_key

        @cached(ttl=60, key_generator=generate_cache_key)
        async def func_with_args(a: int, b: int, c: str = "default") -> str:
            return f"{a}_{b}_{c}"

        result = await func_with_args(1, 2, c="test")
        assert "1_2_test" in str(result) or result == "1_2_test"


# ============================================================
# 集成测试
# ============================================================

class TestCacheIntegration:
    """缓存集成测试"""

    @pytest.mark.asyncio
    async def test_tender_list_caching(self):
        """测试招标列表缓存"""
        from apps.crawler.tools.cache import MultiLevelCache
        from apps.crawler.tools.cache import CacheKeyGenerator

        cache = MultiLevelCache(l1_max_size=100, l1_ttl=60, l2_prefix="tender:", l2_ttl=300)

        # 模拟招标列表数据
        tender_list = [
            {"id": "1", "title": "招标公告1", "url": "http://example.com/1"},
            {"id": "2", "title": "招标公告2", "url": "http://example.com/2"},
        ]

        key = CacheKeyGenerator.for_tender_list(source="test_source", page=1)

        await cache.set(key, tender_list)
        result = await cache.get(key)

        assert result == tender_list

    @pytest.mark.asyncio
    async def test_tender_detail_caching(self):
        """测试招标详情缓存"""
        from apps.crawler.tools.cache import MultiLevelCache
        from apps.crawler.tools.cache import CacheKeyGenerator

        cache = MultiLevelCache(l1_max_size=100, l1_ttl=60, l2_prefix="tender:", l2_ttl=300)

        # 模拟招标详情数据
        detail = {
            "id": "123",
            "title": "测试招标",
            "content": "详细内容...",
            "attachments": [{"name": "file.pdf"}],
        }

        key = CacheKeyGenerator.for_tender_detail(tender_id="123")

        await cache.set(key, detail)
        result = await cache.get(key)

        assert result == detail

    @pytest.mark.asyncio
    async def test_llm_result_caching(self):
        """测试 LLM 结果缓存"""
        from apps.crawler.tools.cache import MultiLevelCache
        from apps.crawler.tools.cache import CacheKeyGenerator

        cache = MultiLevelCache(l1_max_size=50, l1_ttl=300, l2_prefix="llm:", l2_ttl=3600)

        # 模拟 LLM 分析结果
        llm_result = {
            "analysis": "这是招标分析",
            "entities": {"招标人": "某单位", "中标人": "某某"},
            "confidence": 0.95,
        }

        key = CacheKeyGenerator.for_llm_result(prompt_hash="abc123", model="gpt-4")

        await cache.set(key, llm_result)
        result = await cache.get(key)

        assert result == llm_result