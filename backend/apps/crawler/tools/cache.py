"""
多级缓存系统

提供 L1 内存缓存和 L2 Redis 缓存，支持：
- LRU 驱逐策略
- TTL 过期
- 缓存穿透/击穿/雪崩防护
- 缓存预热和刷新
"""
import asyncio
import time
import json
import hashlib
import logging
import random
from typing import Optional, Any, Dict, List, Callable, Awaitable, TypeVar, Generic, Protocol
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================
# 缓存统计
# ============================================================

@dataclass
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "hit_rate": self.hit_rate,
        }


# ============================================================
# L1 内存缓存
# ============================================================

class MemoryCache:
    """
    L1 内存缓存 - 基于 LRU 策略

    特性:
    - LRU 驱逐
    - TTL 过期
    - 线程安全
    - 统计追踪
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 300,
        enable_stats: bool = True,
    ):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 默认 TTL（秒）
            enable_stats: 是否启用统计
        """
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._expiry: Dict[str, float] = {}
        self._max_size = max_size
        self._default_ttl = ttl
        self._enable_stats = enable_stats
        self._lock = threading.RLock()

        self._stats = CacheStats()

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期返回 None
        """
        with self._lock:
            # 检查是否存在
            if key not in self._cache:
                if self._enable_stats:
                    self._stats.misses += 1
                return None

            # 检查是否过期
            expiry = self._expiry.get(key)
            if expiry and time.time() > expiry:
                # 已过期，删除
                del self._cache[key]
                del self._expiry[key]
                if self._enable_stats:
                    self._stats.misses += 1
                return None

            # 移到末尾（最近使用）
            self._cache.move_to_end(key)

            if self._enable_stats:
                self._stats.hits += 1

            return self._cache[key]

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），使用默认 TTL 如果为 None

        Returns:
            是否成功
        """
        with self._lock:
            # 检查是否需要驱逐
            if key not in self._cache and len(self._cache) >= self._max_size:
                # 驱逐最老的条目
                self._evict_lru()

            # 设置值
            self._cache[key] = value
            self._cache.move_to_end(key)

            # 设置过期时间
            ttl = ttl if ttl is not None else self._default_ttl
            if ttl > 0:
                self._expiry[key] = time.time() + ttl
            else:
                self._expiry.pop(key, None)

            if self._enable_stats:
                self._stats.sets += 1

            return True

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._expiry.pop(key, None)
                if self._enable_stats:
                    self._stats.deletes += 1
                return True
            return False

    async def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()

    def _evict_lru(self) -> None:
        """驱逐最少使用的条目"""
        if self._cache:
            key = next(iter(self._cache))
            del self._cache[key]
            self._expiry.pop(key, None)
            if self._enable_stats:
                self._stats.evictions += 1
            logger.debug(f"Evicted LRU key: {key}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.to_dict()

    @property
    def size(self) -> int:
        """获取当前缓存大小"""
        return len(self._cache)


# ============================================================
# L2 Redis 缓存
# ============================================================

class RedisCache:
    """
    L2 Redis 缓存

    特性:
    - 分布式支持
    - TTL 过期
    - 序列化支持
    """

    def __init__(
        self,
        prefix: str = "cache:",
        ttl: int = 300,
        redis_url: str = "redis://localhost:6379/0",
    ):
        """
        初始化 Redis 缓存

        Args:
            prefix: 键前缀
            ttl: 默认 TTL（秒）
            redis_url: Redis 连接 URL
        """
        self._prefix = prefix
        self._default_ttl = ttl
        self._redis_url = redis_url
        self.client = None
        self._stats = CacheStats()

        # 尝试导入 redis
        try:
            import redis.asyncio as redis
            self._redis = redis
        except ImportError:
            logger.warning("redis package not installed, using mock")
            self._redis = None

    async def _ensure_client(self):
        """确保 Redis 客户端已连接"""
        if self.client is None and self._redis:
            self.client = await self._redis.from_url(self._redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在返回 None
        """
        await self._ensure_client()

        if self.client is None:
            return None

        try:
            full_key = f"{self._prefix}{key}"
            value = await self.client.get(full_key)

            if value is None:
                self._stats.misses += 1
                return None

            self._stats.hits += 1
            return json.loads(value)

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._stats.misses += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒）

        Returns:
            是否成功
        """
        await self._ensure_client()

        if self.client is None:
            return False

        try:
            full_key = f"{self._prefix}{key}"
            serialized = json.dumps(value, ensure_ascii=False)

            ttl = ttl if ttl is not None else self._default_ttl

            if ttl > 0:
                await self.client.set(full_key, serialized, ex=ttl)
            else:
                await self.client.set(full_key, serialized)

            self._stats.sets += 1
            return True

        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        await self._ensure_client()

        if self.client is None:
            return False

        try:
            full_key = f"{self._prefix}{key}"
            result = await self.client.delete(full_key)
            self._stats.deletes += 1
            return result > 0

        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def clear(self) -> None:
        """清空缓存（删除所有带前缀的键）"""
        await self._ensure_client()

        if self.client is None:
            return

        try:
            pattern = f"{self._prefix}*"
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.client.delete(*keys)

        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.to_dict()


# ============================================================
# 多级缓存管理器
# ============================================================

class MultiLevelCache:
    """
    多级缓存管理器

    L1: 内存缓存（高频访问）
    L2: Redis 缓存（分布式）
    """

    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_ttl: int = 300,
        l2_prefix: str = "cache:",
        l2_ttl: int = 3600,
        l2_redis_url: str = "redis://localhost:6379/0",
    ):
        """
        初始化多级缓存

        Args:
            l1_max_size: L1 最大条目数
            l1_ttl: L1 默认 TTL（秒）
            l2_prefix: L2 键前缀
            l2_ttl: L2 默认 TTL（秒）
            l2_redis_url: Redis URL
        """
        self.l1_cache = MemoryCache(max_size=l1_max_size, ttl=l1_ttl)
        self.l2_cache = RedisCache(prefix=l2_prefix, ttl=l2_ttl, redis_url=l2_redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        优先从 L1 获取，未命中则从 L2 获取

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在返回 None
        """
        # L1 命中
        value = await self.l1_cache.get(key)
        if value is not None:
            return value

        # L2 命中
        value = await self.l2_cache.get(key)
        if value is not None:
            # 提升到 L1
            await self.l1_cache.set(key, value)
            return value

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值（同时写入 L1 和 L2）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒）

        Returns:
            是否成功
        """
        # 同时写入 L1 和 L2
        l1_success = await self.l1_cache.set(key, value, ttl)
        l2_success = await self.l2_cache.set(key, value, ttl)

        return l1_success

    async def delete(self, key: str) -> bool:
        """
        删除缓存（同时删除 L1 和 L2）

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        l1_success = await self.l1_cache.delete(key)
        l2_success = await self.l2_cache.delete(key)

        return l1_success or l2_success

    async def clear(self) -> None:
        """清空所有缓存"""
        await self.l1_cache.clear()
        await self.l2_cache.clear()


# ============================================================
# 缓存策略
# ============================================================

class CacheStrategy(Protocol):
    """缓存策略接口"""

    def get_ttl(self, key: str) -> int: ...


class TTLStrategy:
    """TTL 缓存策略"""

    def __init__(
        self,
        default_ttl: int = 60,
        max_ttl: int = 3600,
    ):
        self._default_ttl = default_ttl
        self._max_ttl = max_ttl

        # 不同类型数据的 TTL 配置
        self._ttl_rules = {
            "tender_list": 60,       # 列表缓存较短
            "tender_detail": 300,    # 详情缓存较长
            "llm_result": 1800,      # LLM 结果缓存更长
            "config": 3600,          # 配置缓存最长
        }

    def get_ttl(self, key: str) -> int:
        """根据键获取 TTL"""
        # 根据键名前缀匹配
        for prefix, ttl in self._ttl_rules.items():
            if key.startswith(prefix):
                return ttl

        return self._default_ttl


class AdaptiveTTLStrategy:
    """自适应 TTL 策略"""

    def __init__(self):
        self._access_counts: Dict[str, int] = {}
        self._last_access: Dict[str, float] = {}
        self._base_ttl = 60
        self._max_ttl = 3600

    def record_access(self, key: str) -> None:
        """记录访问"""
        self._access_counts[key] = self._access_counts.get(key, 0) + 1
        self._last_access[key] = time.time()

    def get_ttl(self, key: str) -> int:
        """根据访问模式计算 TTL"""
        access_count = self._access_counts.get(key, 0)

        # 访问次数越多，TTL 越长
        if access_count < 5:
            return self._base_ttl
        elif access_count < 20:
            return self._base_ttl * 5
        elif access_count < 50:
            return self._base_ttl * 10
        else:
            return self._max_ttl


# ============================================================
# 缓存防护
# ============================================================

class CacheWithProtection:
    """带防护的缓存"""

    def __init__(
        self,
        cache: Optional[MemoryCache] = None,
        null_cache_ttl: int = 60,
        lock_timeout: float = 10.0,
        jitter: bool = True,
    ):
        self._cache = cache or MemoryCache()
        self._null_cache_ttl = null_cache_ttl
        self._lock_timeout = lock_timeout
        self._jitter = jitter
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock_guard = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        value = await self._cache.get(key)

        # 处理空值标记
        if value == "null_marker":
            return None

        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """设置缓存"""
        # 空值处理
        if value is None:
            value = "null_marker"
            ttl = ttl or self._null_cache_ttl

        # 添加 jitter 防止雪崩
        if self._jitter and ttl:
            ttl = int(ttl * (0.9 + random.random() * 0.2))

        return await self._cache.set(key, value, ttl)

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        """
        获取或设置（带锁防止击穿）

        Args:
            key: 缓存键
            factory: 值工厂函数

        Returns:
            缓存值
        """
        # 尝试获取
        value = await self.get(key)
        if value is not None:
            return value

        # 获取或创建锁
        async with self._lock_guard:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            # 双重检查
            value = await self.get(key)
            if value is not None:
                return value

            # 执行工厂函数
            value = await factory()
            await self.set(key, value)

            return value

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return await self._cache.delete(key)

    async def clear(self) -> None:
        """清空缓存"""
        await self._cache.clear()
        self._locks.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return self._cache.get_stats()


# ============================================================
# 缓存预热和刷新
# ============================================================

class CacheWarmer:
    """缓存预热器"""

    def __init__(
        self,
        initial_data: Dict[str, Any],
        cache: Optional[MemoryCache] = None,
    ):
        self._data = initial_data
        self._cache = cache or MemoryCache()

    async def warmup(self) -> None:
        """预热缓存"""
        for key, value in self._data.items():
            await self._cache.set(key, value)

    @property
    def cache(self) -> MemoryCache:
        """获取缓存实例"""
        return self._cache


class CacheRefresher:
    """缓存刷新器"""

    def __init__(
        self,
        fetch_func: Callable[[], Awaitable[Any]],
        interval: float = 60.0,
        cache: Optional[MemoryCache] = None,
    ):
        self._fetch_func = fetch_func
        self._interval = interval
        self._cache = cache or MemoryCache()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """启动刷新"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """停止刷新"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        """运行刷新循环"""
        while self._running:
            try:
                data = await self._fetch_func()
                await self._cache.set("refreshed_data", data)
            except Exception as e:
                logger.error(f"Cache refresh error: {e}")

            await asyncio.sleep(self._interval)


# ============================================================
# 缓存键生成器
# ============================================================

class CacheKeyGenerator:
    """缓存键生成器"""

    @staticmethod
    def for_tender_list(source: str, page: int = 1) -> str:
        """招标列表缓存键"""
        return f"tender_list:{source}:{page}"

    @staticmethod
    def for_tender_detail(tender_id: str) -> str:
        """招标详情缓存键"""
        return f"tender_detail:{tender_id}"

    @staticmethod
    def for_llm_result(prompt_hash: str, model: str = "gpt-4") -> str:
        """LLM 结果缓存键"""
        return f"llm_result:{model}:{prompt_hash}"

    @staticmethod
    def for_config(key: str) -> str:
        """配置缓存键"""
        return f"config:{key}"


# ============================================================
# 缓存装饰器
# ============================================================

def generate_cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_str = ":".join(key_parts)

    # 如果键太长，使用 hash
    if len(key_str) > 200:
        return hashlib.md5(key_str.encode()).hexdigest()

    return key_str


def cached(
    ttl: int = 300,
    key_generator: Callable[..., str] = None,
):
    """
    缓存装饰器

    Args:
        ttl: TTL（秒）
        key_generator: 键生成函数
    """
    _cache = MemoryCache(max_size=1000, ttl=ttl)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = generate_cache_key(*args, **kwargs)

            # 尝试从缓存获取
            result = await _cache.get(cache_key)
            if result is not None:
                return result

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            await _cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# ============================================================
# 默认缓存实例
# ============================================================

# 全局默认缓存
_default_cache: Optional[MultiLevelCache] = None


def get_default_cache() -> MultiLevelCache:
    """获取默认缓存实例"""
    global _default_cache
    if _default_cache is None:
        _default_cache = MultiLevelCache(
            l1_max_size=1000,
            l1_ttl=300,
            l2_prefix="deer_flow:",
            l2_ttl=3600,
        )
    return _default_cache


def set_default_cache(cache: MultiLevelCache) -> None:
    """设置默认缓存实例"""
    global _default_cache
    _default_cache = cache