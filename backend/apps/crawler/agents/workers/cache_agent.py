"""
智能缓存智能体

为爬虫系统提供智能缓存功能，避免重复爬取相同页面。
功能包括：
1. 内存LRU缓存（热点数据）
2. 磁盘缓存（HTML内容）
3. TTL缓存失效
4. 缓存统计
"""
import logging
import hashlib
import json
import os
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, Pattern

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """缓存配置

    Attributes:
        memory_cache_size: 内存缓存最大条目数（LRU缓存）
        disk_cache_dir: 磁盘缓存目录路径（绝对路径）
        default_ttl: 默认缓存过期时间（秒）
        max_disk_cache_size_mb: 磁盘缓存最大大小（MB）
    """
    memory_cache_size: int = 1000
    disk_cache_dir: str = field(default_factory=lambda: os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..', '..', '.cache', 'crawler'
    ))
    default_ttl: int = 3600  # 1 hour
    max_disk_cache_size_mb: int = 500


@dataclass
class CacheEntry:
    """缓存条目

    Attributes:
        content: 缓存内容
        timestamp: 缓存时间戳
        ttl: 过期时间（秒）
        source_id: 数据源ID
        source_version: 数据源版本（用于智能缓存键）
        access_count: 访问次数
    """
    content: Any
    timestamp: float
    ttl: int
    source_id: Optional[str] = None
    source_version: Optional[str] = None
    access_count: int = field(default=0)

    def is_expired(self) -> bool:
        """检查缓存是否已过期"""
        return time.time() - self.timestamp > self.ttl

    def touch(self) -> None:
        """更新访问计数"""
        self.access_count += 1


@dataclass
class CacheStats:
    """缓存统计信息

    Attributes:
        memory_hits: 内存缓存命中次数
        memory_misses: 内存缓存未命中次数
        disk_hits: 磁盘缓存命中次数
        disk_misses: 磁盘缓存未命中次数
        total_memory_entries: 当前内存缓存条目数
        total_disk_entries: 当前磁盘缓存条目数
        disk_cache_size_mb: 磁盘缓存大小（MB）
        memory_hit_rate: 内存缓存命中率
        overall_hit_rate: 总体命中率
    """
    memory_hits: int = 0
    memory_misses: int = 0
    disk_hits: int = 0
    disk_misses: int = 0
    total_memory_entries: int = 0
    total_disk_entries: int = 0
    disk_cache_size_mb: float = 0.0
    memory_hit_rate: float = 0.0
    overall_hit_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "memory_hits": self.memory_hits,
            "memory_misses": self.memory_misses,
            "disk_hits": self.disk_hits,
            "disk_misses": self.disk_misses,
            "total_memory_entries": self.total_memory_entries,
            "total_disk_entries": self.total_disk_entries,
            "disk_cache_size_mb": round(self.disk_cache_size_mb, 2),
            "memory_hit_rate": round(self.memory_hit_rate, 4),
            "overall_hit_rate": round(self.overall_hit_rate, 4),
        }


class CacheAgent:
    """智能缓存智能体

    提供双层缓存机制：
    1. 内存LRU缓存：存储热点数据，快速访问
    2. 磁盘缓存：存储HTML内容，持久化保存

    缓存键策略：
    - 使用URL哈希作为主键
    - 可选包含source_id和source_version形成智能缓存键
    - 支持按URL模式和数据源失效缓存
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """初始化缓存智能体

        Args:
            config: 缓存配置，使用默认配置如果未提供
        """
        self.config = config or CacheConfig()

        # 内存LRU缓存
        self._memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._memory_lock = Lock()

        # 缓存统计
        self._stats = CacheStats()
        self._stats_lock = Lock()

        # 磁盘缓存目录
        self._disk_cache_path = Path(self.config.disk_cache_dir)
        self._disk_cache_path.mkdir(parents=True, exist_ok=True)

        # 元数据文件路径
        self._metadata_path = self._disk_cache_path / "cache_metadata.json"
        self._disk_metadata: Dict[str, Dict[str, Any]] = {}

        # 加载磁盘缓存元数据
        self._load_metadata()

        logger.info(
            f"CacheAgent initialized: memory_size={self.config.memory_cache_size}, "
            f"disk_dir={self.config.disk_cache_dir}, default_ttl={self.config.default_ttl}s"
        )

    def _generate_cache_key(
        self, url: str, source_id: Optional[str] = None, source_version: Optional[str] = None
    ) -> str:
        """生成缓存键

        使用URL的SHA256哈希作为主键，可选包含source_id和source_version
        形成智能缓存键，支持按数据源版本失效。

        Args:
            url: 页面URL
            source_id: 数据源ID
            source_version: 数据源版本

        Returns:
            缓存键字符串
        """
        # 基础键：URL哈希
        key_parts = [url]

        # 智能缓存键：包含数据源信息
        if source_id:
            key_parts.append(f"sid:{source_id}")
        if source_version:
            key_parts.append(f"ver:{source_version}")

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode("utf-8")).hexdigest()

    def _get_disk_path(self, cache_key: str) -> Path:
        """获取磁盘缓存文件路径

        使用两级目录结构避免单个目录文件过多：
        - 第一级：哈希前2字符
        - 第二级：哈希后2字符
        - 文件名：完整哈希

        Args:
            cache_key: 缓存键

        Returns:
            磁盘文件路径
        """
        return self._disk_cache_path / cache_key[:2] / cache_key[2:4] / f"{cache_key}.cache"

    def _load_metadata(self) -> None:
        """加载磁盘缓存元数据"""
        if self._metadata_path.exists():
            try:
                with open(self._metadata_path, "r", encoding="utf-8") as f:
                    self._disk_metadata = json.load(f)
                logger.debug(f"Loaded {len(self._disk_metadata)} disk cache metadata entries")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                self._disk_metadata = {}

    def _save_metadata(self) -> None:
        """保存磁盘缓存元数据"""
        try:
            with open(self._metadata_path, "w", encoding="utf-8") as f:
                json.dump(self._disk_metadata, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def _update_stats(self, memory_hit: bool = False, memory_miss: bool = False,
                      disk_hit: bool = False, disk_miss: bool = False) -> None:
        """更新缓存统计

        Args:
            memory_hit: 内存缓存命中
            memory_miss: 内存缓存未命中
            disk_hit: 磁盘缓存命中
            disk_miss: 磁盘缓存未命中
        """
        with self._stats_lock:
            if memory_hit:
                self._stats.memory_hits += 1
            if memory_miss:
                self._stats.memory_misses += 1
            if disk_hit:
                self._stats.disk_hits += 1
            if disk_miss:
                self._stats.disk_misses += 1

            # 计算命中率
            memory_total = self._stats.memory_hits + self._stats.memory_misses
            if memory_total > 0:
                self._stats.memory_hit_rate = self._stats.memory_hits / memory_total

            overall_total = (self._stats.memory_hits + self._stats.disk_hits +
                           self._stats.memory_misses + self._stats.disk_misses)
            if overall_total > 0:
                self._stats.overall_hit_rate = (
                    (self._stats.memory_hits + self._stats.disk_hits) / overall_total
                )

    def _write_to_disk(self, cache_key: str, entry: CacheEntry) -> bool:
        """写入磁盘缓存

        Args:
            cache_key: 缓存键
            entry: 缓存条目

        Returns:
            是否写入成功
        """
        disk_path = self._get_disk_path(cache_key)

        try:
            # 创建目录
            disk_path.parent.mkdir(parents=True, exist_ok=True)

            # 序列化数据
            data = {
                "content": entry.content,
                "timestamp": entry.timestamp,
                "ttl": entry.ttl,
                "source_id": entry.source_id,
                "source_version": entry.source_version,
                "access_count": entry.access_count,
            }

            # 写入文件
            with open(disk_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            # 更新元数据
            self._disk_metadata[cache_key] = {
                "timestamp": entry.timestamp,
                "ttl": entry.ttl,
                "source_id": entry.source_id,
                "size": disk_path.stat().st_size if disk_path.exists() else 0,
            }
            self._save_metadata()

            return True
        except (IOError, TypeError) as e:
            logger.error(f"Failed to write disk cache for {cache_key}: {e}")
            return False

    def _read_from_disk(self, cache_key: str) -> Optional[CacheEntry]:
        """从磁盘读取缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存条目，如果不存在或已过期则返回None
        """
        disk_path = self._get_disk_path(cache_key)

        if not disk_path.exists():
            return None

        try:
            with open(disk_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            entry = CacheEntry(
                content=data["content"],
                timestamp=data["timestamp"],
                ttl=data["ttl"],
                source_id=data.get("source_id"),
                source_version=data.get("source_version"),
                access_count=data.get("access_count", 0),
            )

            # 检查是否过期
            if entry.is_expired():
                # 删除过期文件
                disk_path.unlink(missing_ok=True)
                if cache_key in self._disk_metadata:
                    del self._disk_metadata[cache_key]
                    self._save_metadata()
                return None

            return entry

        except (IOError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to read disk cache for {cache_key}: {e}")
            return None

    def _enforce_disk_cache_limit(self) -> None:
        """强制执行磁盘缓存大小限制

        当磁盘缓存超过限制时，删除最旧的缓存文件。
        """
        max_size_bytes = self.config.max_disk_cache_size_mb * 1024 * 1024

        # 计算当前磁盘缓存大小
        total_size = 0
        cache_files: List[Tuple[Path, float]] = []  # (path, mtime)

        for cache_file in self._disk_cache_path.rglob("*.cache"):
            try:
                stat = cache_file.stat()
                total_size += stat.st_size
                cache_files.append((cache_file, stat.st_mtime))
            except OSError:
                continue

        # 如果超过限制，删除最旧的文件
        if total_size > max_size_bytes:
            # 按修改时间排序（最旧的在前面）
            cache_files.sort(key=lambda x: x[1])

            for cache_file, _ in cache_files:
                try:
                    stat = cache_file.stat()
                    cache_key = cache_file.stem

                    cache_file.unlink()
                    if cache_key in self._disk_metadata:
                        del self._disk_metadata[cache_key]

                    total_size -= stat.st_size

                    if total_size <= max_size_bytes * 0.8:  # 删除到80%以下
                        break
                except OSError:
                    continue

            self._save_metadata()
            logger.info(f"Enforced disk cache limit: removed old entries, new size: {total_size / 1024 / 1024:.2f}MB")

    def get(
        self, url: str, source_id: Optional[str] = None
    ) -> Tuple[bool, Any]:
        """获取缓存内容

        首先检查内存LRU缓存，如果未命中则检查磁盘缓存。

        Args:
            url: 页面URL
            source_id: 数据源ID

        Returns:
            (缓存是否命中, 缓存内容或None)
        """
        cache_key = self._generate_cache_key(url, source_id)

        # 1. 检查内存缓存
        with self._memory_lock:
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]

                if not entry.is_expired():
                    # 移动到LRU末尾（最近使用）
                    self._memory_cache.move_to_end(cache_key)
                    entry.touch()

                    self._update_stats(memory_hit=True)
                    logger.debug(f"Memory cache hit: {url}")
                    return True, entry.content
                else:
                    # 删除过期条目
                    del self._memory_cache[cache_key]

        # 2. 检查磁盘缓存
        entry = self._read_from_disk(cache_key)
        if entry:
            # 提升热点数据到内存缓存
            with self._memory_lock:
                self._memory_cache[cache_key] = entry
                entry.touch()

                # 维护LRU大小
                while len(self._memory_cache) > self.config.memory_cache_size:
                    self._memory_cache.popitem(last=False)

            self._update_stats(memory_miss=True, disk_hit=True)
            logger.debug(f"Disk cache hit: {url}")
            return True, entry.content

        self._update_stats(memory_miss=True, disk_miss=True)
        logger.debug(f"Cache miss: {url}")
        return False, None

    def set(
        self,
        url: str,
        content: Any,
        ttl: Optional[int] = None,
        source_id: Optional[str] = None,
        source_version: Optional[str] = None,
    ) -> bool:
        """设置缓存内容

        同时更新内存缓存和磁盘缓存。

        Args:
            url: 页面URL
            content: 缓存内容
            ttl: 过期时间（秒），使用默认配置如果未提供
            source_id: 数据源ID
            source_version: 数据源版本

        Returns:
            是否设置成功
        """
        cache_key = self._generate_cache_key(url, source_id, source_version)
        ttl = ttl or self.config.default_ttl

        entry = CacheEntry(
            content=content,
            timestamp=time.time(),
            ttl=ttl,
            source_id=source_id,
            source_version=source_version,
            access_count=0,
        )

        # 1. 更新内存缓存
        with self._memory_lock:
            self._memory_cache[cache_key] = entry
            self._memory_cache.move_to_end(cache_key)

            # 维护LRU大小
            while len(self._memory_cache) > self.config.memory_cache_size:
                self._memory_cache.popitem(last=False)

        # 2. 更新磁盘缓存
        if not self._write_to_disk(cache_key, entry):
            logger.warning(f"Failed to write disk cache for {url}")

        # 3. 检查磁盘缓存限制
        self._enforce_disk_cache_limit()

        logger.debug(f"Cache set: {url} (ttl={ttl}s)")
        return True

    def invalidate(self, url_pattern: str) -> int:
        """失效匹配的缓存

        支持正则表达式模式匹配URL。

        Args:
            url_pattern: URL匹配模式（正则表达式）

        Returns:
            失效的缓存条目数
        """
        count = 0
        compiled_pattern: Optional[Pattern] = None

        try:
            compiled_pattern = re.compile(url_pattern)
        except re.error as e:
            logger.error(f"Invalid URL pattern: {url_pattern}, error: {e}")
            return 0

        # 1. 清理内存缓存
        with self._memory_lock:
            keys_to_remove = []
            for cache_key, entry in list(self._memory_cache.items()):
                # 对于内存缓存，我们需要遍历并检查（因为key是哈希值）
                # 这里使用一种启发式方法：检查source_id匹配
                if entry.source_id and compiled_pattern.search(entry.source_id):
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                del self._memory_cache[key]
                count += 1

        # 2. 清理磁盘缓存
        keys_to_remove = []
        for cache_key, metadata in list(self._disk_metadata.items()):
            # 检查source_id匹配
            if metadata.get("source_id") and compiled_pattern.search(metadata.get("source_id", "")):
                disk_path = self._get_disk_path(cache_key)
                disk_path.unlink(missing_ok=True)
                keys_to_remove.append(cache_key)
                count += 1

        for key in keys_to_remove:
            if key in self._disk_metadata:
                del self._disk_metadata[key]

        if keys_to_remove:
            self._save_metadata()

        logger.info(f"Invalidated {count} cache entries matching pattern: {url_pattern}")
        return count

    def invalidate_by_source(self, source_id: str) -> int:
        """按数据源ID失效缓存

        Args:
            source_id: 数据源ID

        Returns:
            失效的缓存条目数
        """
        count = 0

        # 1. 清理内存缓存
        with self._memory_lock:
            keys_to_remove = [
                key for key, entry in self._memory_cache.items()
                if entry.source_id == source_id
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]
                count += 1

        # 2. 清理磁盘缓存
        keys_to_remove = [
            key for key, metadata in self._disk_metadata.items()
            if metadata.get("source_id") == source_id
        ]
        for key in keys_to_remove:
            disk_path = self._get_disk_path(key)
            disk_path.unlink(missing_ok=True)
            del self._disk_metadata[key]
            count += 1

        if keys_to_remove:
            self._save_metadata()

        logger.info(f"Invalidated {count} cache entries for source: {source_id}")
        return count

    def get_stats(self) -> CacheStats:
        """获取缓存统计信息

        Returns:
            当前缓存统计信息
        """
        with self._stats_lock:
            stats = CacheStats(
                memory_hits=self._stats.memory_hits,
                memory_misses=self._stats.memory_misses,
                disk_hits=self._stats.disk_hits,
                disk_misses=self._stats.disk_misses,
                total_memory_entries=len(self._memory_cache),
                total_disk_entries=len(self._disk_metadata),
                disk_cache_size_mb=self._calculate_disk_size(),
                memory_hit_rate=self._stats.memory_hit_rate,
                overall_hit_rate=self._stats.overall_hit_rate,
            )
        return stats

    def _calculate_disk_size(self) -> float:
        """计算磁盘缓存大小（MB）

        Returns:
            磁盘缓存大小（MB）
        """
        total_size = 0
        for cache_file in self._disk_cache_path.rglob("*.cache"):
            try:
                total_size += cache_file.stat().st_size
            except OSError:
                continue
        return total_size / (1024 * 1024)

    def clear(self) -> bool:
        """清空所有缓存

        Returns:
            是否清空成功
        """
        # 1. 清空内存缓存
        with self._memory_lock:
            self._memory_cache.clear()

        # 2. 清空磁盘缓存
        try:
            for cache_file in self._disk_cache_path.rglob("*.cache"):
                cache_file.unlink(missing_ok=True)

            # 删除空目录
            for subdir in self._disk_cache_path.rglob("*/"):
                try:
                    subdir.rmdir()  # 只删除空目录
                except OSError:
                    pass

            self._disk_metadata.clear()
            self._save_metadata()

            # 重置统计
            with self._stats_lock:
                self._stats = CacheStats()

            logger.info("All caches cleared")
            return True
        except OSError as e:
            logger.error(f"Failed to clear disk cache: {e}")
            return False

    def cleanup_expired(self) -> int:
        """清理过期缓存

        Returns:
            清理的缓存条目数
        """
        count = 0
        current_time = time.time()

        # 1. 清理内存缓存
        with self._memory_lock:
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if current_time - entry.timestamp > entry.ttl
            ]
            for key in expired_keys:
                del self._memory_cache[key]
                count += 1

        # 2. 清理磁盘缓存
        expired_keys = [
            key for key, metadata in self._disk_metadata.items()
            if current_time - metadata["timestamp"] > metadata["ttl"]
        ]
        for key in expired_keys:
            disk_path = self._get_disk_path(key)
            disk_path.unlink(missing_ok=True)
            del self._disk_metadata[key]
            count += 1

        if expired_keys:
            self._save_metadata()

        logger.info(f"Cleaned up {count} expired cache entries")
        return count


# 全局缓存智能体实例
_cache_agent: Optional[CacheAgent] = None


def get_cache_agent(config: Optional[CacheConfig] = None) -> CacheAgent:
    """获取全局缓存智能体实例

    Args:
        config: 缓存配置，可选

    Returns:
        CacheAgent实例
    """
    global _cache_agent
    if _cache_agent is None:
        _cache_agent = CacheAgent(config)
    return _cache_agent
