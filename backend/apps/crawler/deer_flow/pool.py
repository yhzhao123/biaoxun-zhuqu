"""
Connection Pool Manager - TDD Cycle 20

连接池管理:
- 控制最大连接数
- Keep-alive 管理
- 连接获取和释放
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from weakref import WeakSet

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """连接对象"""
    id: str
    active: bool = False
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)


class ConnectionPool:
    """
    连接池管理器

    管理 HTTP 连接，支持:
    - 最大连接数限制
    - Keep-alive 连接复用
    - 连接获取和释放
    """

    def __init__(
        self,
        max_connections: int = 10,
        max_keepalive: int = 20,
        acquire_timeout: float = 30.0
    ):
        """
        初始化连接池

        Args:
            max_connections: 最大连接数
            max_keepalive: 最大 keepalive 连接数
            acquire_timeout: 获取连接超时时间（秒）
        """
        self.logger = logging.getLogger(__name__)

        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.acquire_timeout = acquire_timeout

        # 活跃连接计数
        self._active_count = 0

        # Keep-alive 连接池
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_keepalive)

        # 所有连接跟踪（用于清理）
        self._all_connections: WeakSet[Connection] = WeakSet()

        # 统计信息
        self._stats = {
            "acquired": 0,
            "released": 0,
            "created": 0,
            "closed": 0,
        }

        self.logger.info(
            f"ConnectionPool initialized: max={max_connections}, "
            f"keepalive={max_keepalive}"
        )

    async def acquire(self) -> Connection:
        """
        从池中获取一个连接

        Returns:
            Connection 对象

        Raises:
            TimeoutError: 获取连接超时
        """
        # 尝试从池中获取现有连接
        try:
            conn = self._pool.get_nowait()
            if conn and conn.active:
                self._active_count += 1
                self._stats["acquired"] += 1
                self.logger.debug(f"Reused connection from pool: {conn.id}")
                return conn
        except asyncio.QueueEmpty:
            pass

        # 如果池为空且未达到最大连接数，创建新连接
        if self._active_count < self.max_connections:
            conn = Connection(
                id=f"conn_{self._stats['created']}",
                active=True
            )
            self._all_connections.add(conn)
            self._active_count += 1
            self._stats["created"] += 1
            self._stats["acquired"] += 1
            self.logger.debug(f"Created new connection: {conn.id}")
            return conn

        # 等待可用连接
        try:
            conn = await asyncio.wait_for(
                self._pool.get(),
                timeout=self.acquire_timeout
            )
            conn.active = True
            self._active_count += 1
            self._stats["acquired"] += 1
            self.logger.debug(f"Waited for connection: {conn.id}")
            return conn
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Failed to acquire connection within {self.acquire_timeout}s"
            )

    async def release(self, conn: Connection) -> None:
        """
        释放连接回池中

        Args:
            conn: 要释放的 Connection 对象
        """
        if not conn:
            return

        conn.active = False
        self._active_count = max(0, self._active_count - 1)

        # 如果池未满，放回池中
        if self._pool.qsize() < self.max_keepalive:
            try:
                self._pool.put_nowait(conn)
                self._stats["released"] += 1
                self.logger.debug(f"Released connection to pool: {conn.id}")
            except asyncio.QueueFull:
                # 池已满，关闭连接
                await self._close_connection(conn)
        else:
            # 池已满，关闭连接
            await self._close_connection(conn)

    async def _close_connection(self, conn: Connection) -> None:
        """
        关闭连接

        Args:
            conn: 要关闭的 Connection 对象
        """
        conn.active = False
        self._stats["closed"] += 1
        self.logger.debug(f"Closed connection: {conn.id}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取连接池统计信息

        Returns:
            统计信息字典
        """
        return {
            "active": self._active_count,
            "available": self._pool.qsize(),
            "max_connections": self.max_connections,
            "max_keepalive": self.max_keepalive,
            **self._stats
        }

    async def close_all(self) -> None:
        """关闭所有连接"""
        # 清空池
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except asyncio.QueueEmpty:
                break

        self._active_count = 0
        self.logger.info("All connections closed")


# 全局连接池实例
_global_pool: Optional[ConnectionPool] = None


def get_connection_pool() -> ConnectionPool:
    """
    获取全局连接池实例

    Returns:
        ConnectionPool 实例
    """
    global _global_pool
    if _global_pool is None:
        _global_pool = ConnectionPool(max_connections=10, max_keepalive=20)
    return _global_pool