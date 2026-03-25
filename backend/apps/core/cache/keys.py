"""
缓存键名生成器模块

生成标准化的缓存键名
"""

import hashlib
import json
from typing import Any, Dict, Optional


def _generate_hash(data: Any) -> str:
    """生成数据的哈希值"""
    if data is None:
        return 'none'
    if isinstance(data, dict):
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    else:
        data_str = str(data)
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:8]


def tender_list(page: int, filters: Optional[Dict] = None) -> str:
    """
    生成招标列表缓存键

    Args:
        page: 页码
        filters: 过滤条件

    Returns:
        缓存键名
    """
    if filters is None:
        filters = {}
    filter_hash = _generate_hash(filters)
    return f'tenders:list:{page}:{filter_hash}'


def tender_detail(tender_id: int) -> str:
    """
    生成招标详情缓存键

    Args:
        tender_id: 招标ID

    Returns:
        缓存键名
    """
    return f'tender:{tender_id}:detail'


def tender_stats() -> str:
    """
    生成招标统计数据缓存键

    Returns:
        缓存键名
    """
    return 'tenders:stats'


def search_results(query: str) -> str:
    """
    生成搜索结果缓存键

    Args:
        query: 搜索关键词

    Returns:
        缓存键名
    """
    query_hash = _generate_hash(query)
    return f'search:{query_hash}'


def region_distribution() -> str:
    """
    生成地区分布缓存键

    Returns:
        缓存键名
    """
    return 'stats:regions'


def industry_distribution() -> str:
    """
    生成行业分布缓存键

    Returns:
        缓存键名
    """
    return 'stats:industries'


def user_preferences(user_id: int) -> str:
    """
    生成用户偏好缓存键

    Args:
        user_id: 用户ID

    Returns:
        缓存键名
    """
    return f'user:{user_id}:preferences'


def notification_list(user_id: int, page: int = 1) -> str:
    """
    生成通知列表缓存键

    Args:
        user_id: 用户ID
        page: 页码

    Returns:
        缓存键名
    """
    return f'notifications:{user_id}:page:{page}'


def dashboard_stats(user_id: int) -> str:
    """
    生成仪表盘统计数据缓存键

    Args:
        user_id: 用户ID

    Returns:
        缓存键名
    """
    return f'dashboard:{user_id}:stats'