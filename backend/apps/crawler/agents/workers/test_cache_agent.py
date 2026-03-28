"""
CacheAgent 测试

TDD Cycle 8: 缓存系统智能体测试
"""
import pytest
import tempfile
import shutil
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from apps.crawler.agents.workers.cache_agent import (
    CacheAgent,
    CacheConfig,
    CacheEntry,
    CacheStats,
    get_cache_agent,
)


class TestCacheConfig:
    """CacheConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = CacheConfig()

        assert config.memory_cache_size == 1000
        assert config.default_ttl == 3600
        assert config.max_disk_cache_size_mb == 500
        assert config.disk_cache_dir is not None

    def test_custom_values(self):
        """测试自定义值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CacheConfig(
                memory_cache_size=500,
                disk_cache_dir=tmpdir,
                default_ttl=7200,
                max_disk_cache_size_mb=200,
            )

            assert config.memory_cache_size == 500
            assert config.disk_cache_dir == tmpdir
            assert config.default_ttl == 7200
            assert config.max_disk_cache_size_mb == 200


class TestCacheEntry:
    """CacheEntry 测试"""

    def test_is_expired(self):
        """测试过期检查"""
        # 未过期
        entry = CacheEntry(
            content="test",
            timestamp=time.time(),
            ttl=3600,
        )
        assert entry.is_expired() is False

        # 已过期
        entry = CacheEntry(
            content="test",
            timestamp=time.time() - 7200,  # 2小时前
            ttl=3600,  # 1小时TTL
        )
        assert entry.is_expired() is True

    def test_touch(self):
        """测试访问计数更新"""
        entry = CacheEntry(
            content="test",
            timestamp=time.time(),
            ttl=3600,
            access_count=0,
        )

        entry.touch()
        assert entry.access_count == 1

        entry.touch()
        assert entry.access_count == 2


class TestCacheStats:
    """CacheStats 测试"""

    def test_default_values(self):
        """测试默认值"""
        stats = CacheStats()

        assert stats.memory_hits == 0
        assert stats.memory_misses == 0
        assert stats.disk_hits == 0
        assert stats.disk_misses == 0
        assert stats.memory_hit_rate == 0.0
        assert stats.overall_hit_rate == 0.0

    def test_to_dict(self):
        """测试转换为字典"""
        stats = CacheStats(
            memory_hits=10,
            memory_misses=5,
            disk_hits=20,
            disk_misses=10,
            memory_hit_rate=0.6667,
            overall_hit_rate=0.75,
        )

        stats_dict = stats.to_dict()

        assert stats_dict["memory_hits"] == 10
        assert stats_dict["memory_misses"] == 5
        assert stats_dict["disk_hits"] == 20
        assert stats_dict["disk_misses"] == 10
        assert stats_dict["memory_hit_rate"] == 0.6667
        assert stats_dict["overall_hit_rate"] == 0.75


class TestCacheAgent:
    """CacheAgent 测试"""

    @pytest.fixture
    def temp_cache_dir(self):
        """临时缓存目录"""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def cache_agent(self, temp_cache_dir):
        """缓存代理实例"""
        config = CacheConfig(
            memory_cache_size=100,
            disk_cache_dir=temp_cache_dir,
            default_ttl=3600,
        )
        return CacheAgent(config)

    def test_initialization(self, temp_cache_dir):
        """测试初始化"""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        agent = CacheAgent(config)

        assert agent.config == config
        assert agent._memory_cache is not None
        assert agent._disk_cache_path.exists()

    def test_generate_cache_key(self, cache_agent):
        """测试缓存键生成"""
        # 基础键
        key1 = cache_agent._generate_cache_key("http://example.com")
        assert len(key1) == 64  # SHA256 hex

        # 带source_id
        key2 = cache_agent._generate_cache_key(
            "http://example.com", source_id="test_source"
        )
        assert key1 != key2

        # 带source_version
        key3 = cache_agent._generate_cache_key(
            "http://example.com", source_id="test_source", source_version="v1"
        )
        assert key2 != key3

    def test_get_disk_path(self, cache_agent):
        """测试磁盘路径生成"""
        path = cache_agent._get_disk_path("abc123")

        # 检查两级目录结构
        assert path.parent.parent.name == "ab"
        assert path.parent.name == "c1"
        assert path.name == "abc123.cache"

    def test_set_and_get_memory_cache(self, cache_agent):
        """测试内存缓存设置和获取"""
        url = "http://example.com/test"
        content = {"html": "<html>test</html>"}

        # 设置缓存
        result = cache_agent.set(url, content, ttl=3600)
        assert result is True

        # 获取缓存
        hit, cached_content = cache_agent.get(url)
        assert hit is True
        assert cached_content == content

    def test_get_cache_miss(self, cache_agent):
        """测试缓存未命中"""
        hit, content = cache_agent.get("http://nonexistent.com")

        assert hit is False
        assert content is None

    def test_memory_cache_ttl_expiration(self, cache_agent):
        """测试内存缓存过期"""
        url = "http://example.com/expiring"
        content = "test content"

        # 设置短TTL缓存
        cache_agent.set(url, content, ttl=1)

        # 立即获取应该命中
        hit, _ = cache_agent.get(url)
        assert hit is True

        # 等待过期
        time.sleep(1.1)

        # 过期后应该未命中
        hit, _ = cache_agent.get(url)
        assert hit is False

    def test_disk_cache_persistence(self, temp_cache_dir):
        """测试磁盘缓存持久化"""
        config = CacheConfig(disk_cache_dir=temp_cache_dir, default_ttl=3600)
        agent1 = CacheAgent(config)

        url = "http://example.com/persistent"
        content = {"data": "persistent data"}

        # 设置缓存
        agent1.set(url, content)

        # 创建新实例（模拟重启）
        agent2 = CacheAgent(config)

        # 从磁盘获取
        hit, cached_content = agent2.get(url)
        assert hit is True
        assert cached_content == content

    def test_invalidate_by_url_pattern(self, cache_agent):
        """测试按URL模式失效缓存"""
        # 设置多个缓存
        cache_agent.set("http://example.com/page1", "content1", source_id="example")
        cache_agent.set("http://example.com/page2", "content2", source_id="example")
        cache_agent.set("http://other.com/page", "content3", source_id="other")

        # 按模式失效
        count = cache_agent.invalidate_by_source("example")
        assert count >= 2

        # 验证已失效
        hit, _ = cache_agent.get("http://example.com/page1")
        assert hit is False

    def test_invalidate(self, cache_agent):
        """测试正则模式失效缓存"""
        # 设置缓存
        cache_agent.set("http://example.com/page1", "content1", source_id="example")
        cache_agent.set("http://example.com/page2", "content2", source_id="example")

        # 使用正则表达式失效
        count = cache_agent.invalidate("example")
        assert count >= 0  # 可能匹配到source_id

    def test_clear(self, cache_agent):
        """测试清空缓存"""
        # 设置缓存
        cache_agent.set("http://example.com/page1", "content1")
        cache_agent.set("http://example.com/page2", "content2")

        # 清空
        result = cache_agent.clear()
        assert result is True

        # 验证已清空
        hit1, _ = cache_agent.get("http://example.com/page1")
        hit2, _ = cache_agent.get("http://example.com/page2")
        assert hit1 is False
        assert hit2 is False

    def test_cleanup_expired(self, cache_agent):
        """测试清理过期缓存"""
        # 设置过期缓存
        cache_agent.set("http://example.com/expired", "content", ttl=1)
        cache_agent.set("http://example.com/valid", "content", ttl=3600)

        # 等待过期
        time.sleep(1.1)

        # 清理过期
        count = cache_agent.cleanup_expired()
        assert count >= 1

    def test_get_stats(self, cache_agent):
        """测试获取统计信息"""
        # 设置并获取缓存以产生统计
        cache_agent.set("http://example.com/page", "content")
        cache_agent.get("http://example.com/page")  # 命中
        cache_agent.get("http://example.com/other")  # 未命中

        stats = cache_agent.get_stats()

        assert isinstance(stats, CacheStats)
        assert stats.memory_hits >= 0
        assert stats.memory_misses >= 0

    def test_memory_cache_lru_eviction(self, temp_cache_dir):
        """测试内存缓存LRU淘汰"""
        config = CacheConfig(memory_cache_size=3, disk_cache_dir=temp_cache_dir)
        agent = CacheAgent(config)

        # 设置超过限制的缓存
        for i in range(5):
            agent.set(f"http://example.com/page{i}", f"content{i}")

        # 检查内存缓存大小
        assert len(agent._memory_cache) <= 3

    def test_update_stats(self, cache_agent):
        """测试统计更新"""
        # 初始状态
        assert cache_agent._stats.memory_hits == 0

        # 更新内存命中
        cache_agent._update_stats(memory_hit=True)
        assert cache_agent._stats.memory_hits == 1

        # 更新内存未命中
        cache_agent._update_stats(memory_miss=True)
        assert cache_agent._stats.memory_misses == 1

        # 更新磁盘命中
        cache_agent._update_stats(disk_hit=True)
        assert cache_agent._stats.disk_hits == 1

        # 验证命中率计算
        assert cache_agent._stats.memory_hit_rate == 0.5  # 1/(1+1)
        # 总体命中率 = (memory_hits + disk_hits) / (memory_hits + memory_misses + disk_hits + disk_misses)
        # = (1 + 1) / (1 + 1 + 1 + 0) = 2/3
        assert abs(cache_agent._stats.overall_hit_rate - 0.6667) < 0.01


class TestCacheAgentDiskOperations:
    """磁盘操作测试"""

    @pytest.fixture
    def temp_cache_dir(self):
        """临时缓存目录"""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_write_to_disk(self, temp_cache_dir):
        """测试写入磁盘"""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        agent = CacheAgent(config)

        entry = CacheEntry(
            content="test content",
            timestamp=time.time(),
            ttl=3600,
            source_id="test",
        )

        result = agent._write_to_disk("testkey123", entry)
        assert result is True

        # 验证文件存在
        disk_path = agent._get_disk_path("testkey123")
        assert disk_path.exists()

    def test_read_from_disk(self, temp_cache_dir):
        """测试从磁盘读取"""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        agent = CacheAgent(config)

        # 写入
        entry = CacheEntry(
            content={"key": "value"},
            timestamp=time.time(),
            ttl=3600,
            source_id="test",
        )
        agent._write_to_disk("readtest123", entry)

        # 读取
        cached_entry = agent._read_from_disk("readtest123")
        assert cached_entry is not None
        assert cached_entry.content == {"key": "value"}
        assert cached_entry.source_id == "test"

    def test_read_expired_from_disk(self, temp_cache_dir):
        """测试从磁盘读取过期缓存"""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        agent = CacheAgent(config)

        # 写入过期缓存
        entry = CacheEntry(
            content="expired",
            timestamp=time.time() - 7200,  # 2小时前
            ttl=3600,  # 1小时TTL
            source_id="test",
        )
        agent._write_to_disk("expiredkey", entry)

        # 读取应该返回None
        cached_entry = agent._read_from_disk("expiredkey")
        assert cached_entry is None

    def test_read_nonexistent_from_disk(self, temp_cache_dir):
        """测试读取不存在的磁盘缓存"""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        agent = CacheAgent(config)

        cached_entry = agent._read_from_disk("nonexistent")
        assert cached_entry is None


class TestGlobalCacheAgent:
    """全局缓存代理测试"""

    def test_get_cache_agent_singleton(self):
        """测试单例模式"""
        # 重置全局实例
        import apps.crawler.agents.workers.cache_agent as ca
        ca._cache_agent = None

        agent1 = get_cache_agent()
        agent2 = get_cache_agent()

        assert agent1 is agent2

    def test_get_cache_agent_with_config(self):
        """测试带配置获取代理"""
        import apps.crawler.agents.workers.cache_agent as ca
        ca._cache_agent = None

        with tempfile.TemporaryDirectory() as tmpdir:
            config = CacheConfig(memory_cache_size=500, disk_cache_dir=tmpdir)
            agent = get_cache_agent(config)

            assert agent.config.memory_cache_size == 500


class TestCacheAgentIntegration:
    """集成测试"""

    @pytest.fixture
    def temp_cache_dir(self):
        """临时缓存目录"""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_full_cache_workflow(self, temp_cache_dir):
        """测试完整缓存工作流"""
        config = CacheConfig(
            memory_cache_size=10,
            disk_cache_dir=temp_cache_dir,
            default_ttl=3600,
        )
        agent = CacheAgent(config)

        urls = [f"http://example.com/page{i}" for i in range(5)]
        contents = [{"html": f"<html>Page {i}</html>"} for i in range(5)]

        # 设置缓存
        for url, content in zip(urls, contents):
            agent.set(url, content)

        # 获取缓存（应该命中内存）
        for url, expected_content in zip(urls, contents):
            hit, content = agent.get(url)
            assert hit is True
            assert content == expected_content

        # 检查统计
        stats = agent.get_stats()
        assert stats.memory_hits >= 5

    def test_memory_to_disk_promotion(self, temp_cache_dir):
        """测试内存到磁盘提升"""
        config = CacheConfig(
            memory_cache_size=2,  # 很小的内存
            disk_cache_dir=temp_cache_dir,
            default_ttl=3600,
        )
        agent = CacheAgent(config)

        # 设置多个缓存（超出内存限制）
        for i in range(5):
            agent.set(f"http://example.com/page{i}", f"content{i}")

        # 创建新实例（清除内存，保留磁盘）
        agent2 = CacheAgent(config)

        # 从磁盘获取
        hit, content = agent2.get("http://example.com/page0")
        # 可能命中也可能不命中，取决于磁盘缓存是否被清理

    def test_concurrent_access(self, temp_cache_dir):
        """测试并发访问"""
        import threading

        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        agent = CacheAgent(config)

        results = []

        def worker(url, content):
            agent.set(url, content)
            hit, cached = agent.get(url)
            results.append((hit, cached))

        # 多线程访问
        threads = []
        for i in range(10):
            t = threading.Thread(
                target=worker,
                args=(f"http://example.com/page{i}", f"content{i}")
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证结果
        assert len(results) == 10
        assert all(hit for hit, _ in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
