"""
Cache Strategy Tests - TDD Cycle 20

测试多级缓存策略:
- L1: 内存缓存 (TTL 5分钟)
- L2: Redis 缓存 (TTL 1小时)
- L3: 数据库缓存 (TTL 24小时)
"""
import asyncio
import hashlib
import time
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


class TestCacheStrategy:
    """测试缓存策略"""

    def test_cache_key_format(self):
        """测试缓存 key 格式: tender:{source}:{url_hash}"""
        from apps.crawler.deer_flow.cache import TenderCache

        cache = TenderCache()

        source = "http://example.com/tenders"
        url = "http://example.com/tender/123"

        key = cache._make_cache_key(source, url)

        # Key 格式应该是 tender:{source}:{hash}
        assert key.startswith("tender:")
        assert source in key
        assert len(key) > len(source) + 10  # 应该包含 hash

    def test_memory_cache_l1(self):
        """测试 L1 内存缓存，TTL 5分钟"""
        from apps.crawler.deer_flow.cache import TenderCache, CacheLevel

        cache = TenderCache()

        source = "http://test.com"
        url = "http://test.com/item/1"
        data = {"title": "Test Tender", "amount": 100000}

        # 设置缓存
        cache.set(source, url, data, level=CacheLevel.L1_MEMORY)

        # 立即获取 - 应该命中
        result = cache.get(source, url, level=CacheLevel.L1_MEMORY)
        assert result == data

        # 验证 L1 缓存 ttl 是 5 分钟 (300 秒)
        assert cache._l1_cache_ttl == 300

    def test_redis_cache_l2(self):
        """测试 L2 Redis 缓存，TTL 1小时"""
        from apps.crawler.deer_flow.cache import TenderCache, CacheLevel

        # 创建缓存实例
        cache = TenderCache()

        # 验证 L2 缓存 ttl 是 1 小时 (3600 秒)
        assert cache._l2_cache_ttl == 3600

        # 如果 Redis 不可用，记录警告但不失败
        if cache._redis_client is None:
            # Redis 未连接，跳过功能测试
            self.skipTest("Redis not available")
            return

        source = "http://test.com"
        url = "http://test.com/item/2"
        data = {"title": "Test Tender 2", "amount": 200000}

        # 设置缓存
        cache.set(source, url, data, level=CacheLevel.L2_REDIS)

    def test_database_cache_l3(self):
        """测试 L3 数据库缓存，TTL 24小时"""
        from apps.crawler.deer_flow.cache import TenderCache, CacheLevel

        cache = TenderCache()

        # 验证 L3 缓存 ttl 是 24 小时 (86400 秒)
        assert cache._l3_cache_ttl == 86400

    def test_cache_miss_returns_none(self):
        """测试缓存未命中返回 None"""
        from apps.crawler.deer_flow.cache import TenderCache, CacheLevel

        cache = TenderCache()

        # 不存在的 key 应该返回 None
        result = cache.get("nonexistent", "http://test.com/item/999")
        assert result is None

    def test_cache_invalidation(self):
        """测试缓存失效"""
        from apps.crawler.deer_flow.cache import TenderCache, CacheLevel

        cache = TenderCache()

        source = "http://test.com"
        url = "http://test.com/item/3"
        data = {"title": "Test", "amount": 300000}

        # 设置缓存
        cache.set(source, url, data)

        # 验证数据存在
        assert cache.get(source, url) == data

        # 删除缓存
        cache.delete(source, url)

        # 验证数据已删除
        assert cache.get(source, url) is None

    @pytest.mark.asyncio
    async def test_multi_level_cache_fallback(self):
        """测试多级缓存降级策略"""
        from apps.crawler.deer_flow.cache import TenderCache, CacheLevel

        cache = TenderCache()

        source = "http://test.com"
        url = "http://test.com/item/4"
        data = {"title": "Multi-level Test", "amount": 400000}

        # L1 未命中
        l1_result = cache.get(source, url, level=CacheLevel.L1_MEMORY)
        assert l1_result is None

        # 写入 L1
        cache.set(source, url, data, level=CacheLevel.L1_MEMORY)

        # L1 命中
        l1_hit = cache.get(source, url, level=CacheLevel.L1_MEMORY)
        assert l1_hit == data

    def test_cache_hit_rate_tracking(self):
        """测试缓存命中率追踪"""
        from apps.crawler.deer_flow.cache import TenderCache

        cache = TenderCache()

        source = "http://test.com"
        url = "http://test.com/item/5"
        data = {"title": "Hit Rate Test", "amount": 500000}

        # 缓存未命中
        cache.get(source, url)

        # 缓存命中
        cache.set(source, url, data)
        cache.get(source, url)

        # 获取统计
        stats = cache.get_stats()

        # 验证统计信息
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats


class TestCacheKeyHashing:
    """测试缓存键哈希"""

    def test_url_hash_consistency(self):
        """测试相同 URL 产生相同哈希"""
        from apps.crawler.deer_flow.cache import TenderCache

        cache = TenderCache()

        url = "http://example.com/tender/123"

        hash1 = cache._hash_url(url)
        hash2 = cache._hash_url(url)

        assert hash1 == hash2

    def test_different_urls_different_hashes(self):
        """测试不同 URL 产生不同哈希"""
        from apps.crawler.deer_flow.cache import TenderCache

        cache = TenderCache()

        url1 = "http://example.com/tender/123"
        url2 = "http://example.com/tender/456"

        hash1 = cache._hash_url(url1)
        hash2 = cache._hash_url(url2)

        assert hash1 != hash2

    def test_hash_algorithm(self):
        """测试使用 MD5 哈希算法"""
        from apps.crawler.deer_flow.cache import TenderCache

        cache = TenderCache()

        test_url = "http://test.com/item"
        result = cache._hash_url(test_url)

        # MD5 产生 32 位十六进制字符串
        assert len(result) == 32
        assert result == hashlib.md5(test_url.encode()).hexdigest()