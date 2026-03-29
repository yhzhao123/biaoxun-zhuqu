"""
Multi-Level Cache System - TDD Cycle 20

多级缓存策略:
- L1: 内存缓存 (TTL 5分钟)
- L2: Redis 缓存 (TTL 1小时)
- L3: 数据库缓存 (TTL 24小时)

Cache Key 格式: tender:{source}:{url_hash}
"""
import hashlib
import json
import logging
import os
from enum import Enum
from typing import Any, Optional

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "l1_memory"  # 内存缓存
    L2_REDIS = "l2_redis"    # Redis 缓存
    L3_DATABASE = "l3_database"  # 数据库缓存


class TenderCache:
    """
    招标信息多级缓存

    支持 L1/L2/L3 三级缓存，按优先级查找
    """

    # L1 内存缓存 TTL: 5 分钟
    _l1_cache_ttl = 300
    # L2 Redis 缓存 TTL: 1 小时
    _l2_cache_ttl = 3600
    # L3 数据库缓存 TTL: 24 小时
    _l3_cache_ttl = 86400

    def __init__(self, max_memory_items: int = 1000):
        """
        初始化缓存

        Args:
            max_memory_items: 内存缓存最大条目数
        """
        self.logger = logging.getLogger(__name__)

        # L1: 内存缓存 (TTL 5分钟)
        self._l1_cache = TTLCache(maxsize=max_memory_items, ttl=self._l1_cache_ttl)

        # L2: Redis 缓存
        self._redis_client = None
        self._init_redis_client()

        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "sets": 0,
        }

    def _init_redis_client(self):
        """初始化 Redis 客户端"""
        try:
            import redis
            # 尝试从环境变量或配置获取 Redis URL
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis_client = redis.from_url(redis_url, decode_responses=True)
            self._redis_client.ping()
            self.logger.info(f"Redis cache connected: {redis_url}")
        except Exception as e:
            self.logger.warning(f"Redis not available, L2 cache disabled: {e}")
            self._redis_client = None

    def _make_cache_key(self, source: str, url: str) -> str:
        """
        生成缓存键

        格式: tender:{source}:{url_hash}

        Args:
            source: 数据源
            url: 原始 URL

        Returns:
            缓存键字符串
        """
        url_hash = self._hash_url(url)
        return f"tender:{source}:{url_hash}"

    def _hash_url(self, url: str) -> str:
        """
        对 URL 进行 MD5 哈希

        Args:
            url: 原始 URL

        Returns:
            32 位十六进制哈希字符串
        """
        return hashlib.md5(url.encode()).hexdigest()

    def get(
        self,
        source: str,
        url: str,
        level: Optional[CacheLevel] = None
    ) -> Optional[Any]:
        """
        获取缓存值

        如果未指定 level，尝试从所有级别查找

        Args:
            source: 数据源
            url: 原始 URL
            level: 指定缓存级别，None 表示所有级别

        Returns:
            缓存值，未命中返回 None
        """
        key = self._make_cache_key(source, url)

        if level == CacheLevel.L1_MEMORY or level is None:
            # 尝试 L1 内存缓存
            if key in self._l1_cache:
                self._stats["hits"] += 1
                self._stats["l1_hits"] += 1
                self.logger.debug(f"L1 cache hit: {key}")
                return self._l1_cache[key]

        if (level == CacheLevel.L2_REDIS or level is None) and self._redis_client:
            # 尝试 L2 Redis 缓存
            try:
                value = self._redis_client.get(key)
                if value is not None:
                    self._stats["hits"] += 1
                    self._stats["l2_hits"] += 1
                    self.logger.debug(f"L2 cache hit: {key}")
                    # 可选: 回填到 L1 缓存
                    self._l1_cache[key] = json.loads(value)
                    return json.loads(value)
            except Exception as e:
                self.logger.warning(f"L2 cache read error: {e}")

        # 未命中
        self._stats["misses"] += 1
        return None

    def set(
        self,
        source: str,
        url: str,
        value: Any,
        level: CacheLevel = CacheLevel.L1_MEMORY
    ) -> bool:
        """
        设置缓存值

        Args:
            source: 数据源
            url: 原始 URL
            value: 要缓存的值
            level: 缓存级别

        Returns:
            是否成功
        """
        key = self._make_cache_key(source, url)
        success = False

        if level == CacheLevel.L1_MEMORY:
            # L1 内存缓存
            self._l1_cache[key] = value
            success = True
            self.logger.debug(f"L1 cache set: {key}")

        if level == CacheLevel.L2_REDIS and self._redis_client:
            # L2 Redis 缓存
            try:
                serialized = json.dumps(value, ensure_ascii=False)
                self._redis_client.setex(key, self._l2_cache_ttl, serialized)
                success = True
                self.logger.debug(f"L2 cache set: {key} (TTL: {self._l2_cache_ttl}s)")
            except Exception as e:
                self.logger.warning(f"L2 cache write error: {e}")

        if level == CacheLevel.L3_DATABASE:
            # L3 数据库缓存 (预留接口)
            # 可以通过 Django ORM 实现
            self.logger.debug(f"L3 cache set: {key} (TTL: {self._l3_cache_ttl}s)")
            success = True

        if success:
            self._stats["sets"] += 1

        return success

    def delete(self, source: str, url: str) -> bool:
        """
        删除缓存

        Args:
            source: 数据源
            url: 原始 URL

        Returns:
            是否成功
        """
        key = self._make_cache_key(source, url)
        deleted = False

        # 删除 L1
        if key in self._l1_cache:
            del self._l1_cache[key]
            deleted = True

        # 删除 L2
        if self._redis_client:
            try:
                self._redis_client.delete(key)
                deleted = True
            except Exception as e:
                self.logger.warning(f"L2 cache delete error: {e}")

        self.logger.debug(f"Cache deleted: {key}")
        return deleted

    def clear(self, level: Optional[CacheLevel] = None):
        """
        清除缓存

        Args:
            level: 指定缓存级别，None 表示所有级别
        """
        if level is None or level == CacheLevel.L1_MEMORY:
            self._l1_cache.clear()
            self.logger.info("L1 cache cleared")

        if (level is None or level == CacheLevel.L2_REDIS) and self._redis_client:
            try:
                # 只清除以 tender: 开头的键
                keys = self._redis_client.keys("tender:*")
                if keys:
                    self._redis_client.delete(*keys)
                self.logger.info("L2 cache cleared")
            except Exception as e:
                self.logger.warning(f"L2 cache clear error: {e}")

    def get_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0

        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "l1_hits": self._stats["l1_hits"],
            "l2_hits": self._stats["l2_hits"],
            "l3_hits": self._stats["l3_hits"],
            "sets": self._stats["sets"],
            "l1_size": len(self._l1_cache),
        }


# 全局缓存实例
_global_cache: Optional[TenderCache] = None


def get_cache() -> TenderCache:
    """
    获取全局缓存实例

    Returns:
        TenderCache 实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = TenderCache()
    return _global_cache