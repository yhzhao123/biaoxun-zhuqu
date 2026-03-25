"""
缓存管理器模块

提供招标相关的缓存管理功能
"""

from typing import Any, Dict, List, Optional

from django.core.cache import cache

from .config import (
    DEFAULT_TTL,
    INDUSTRY_DISTRIBUTION_TTL,
    REGION_DISTRIBUTION_TTL,
    SEARCH_TTL,
    STATS_TTL,
    TENDER_DETAIL_TTL,
    TENDER_LIST_TTL,
)
from .keys import (
    industry_distribution,
    region_distribution,
    search_results,
    tender_detail,
    tender_list,
    tender_stats,
)


class TenderCacheManager:
    """
    招标缓存管理器

    提供招标列表、详情、统计等缓存操作
    """

    def __init__(self):
        """初始化缓存管理器"""
        self.default_ttl = DEFAULT_TTL

    def cache_tender_list(
        self,
        page: int,
        filters: Dict,
        data: List[Dict],
        ttl: int = TENDER_LIST_TTL
    ) -> bool:
        """
        缓存招标列表

        Args:
            page: 页码
            filters: 过滤条件
            data: 招标列表数据
            ttl: 缓存时间(秒)

        Returns:
            是否成功
        """
        key = tender_list(page, filters)
        return cache.set(key, data, ttl)

    def get_tender_list(
        self,
        page: int,
        filters: Dict,
    ) -> Optional[List[Dict]]:
        """
        获取招标列表缓存

        Args:
            page: 页码
            filters: 过滤条件

        Returns:
            缓存数据或None
        """
        key = tender_list(page, filters)
        return cache.get(key)

    def invalidate_tender_list(self, page: Optional[int] = None) -> bool:
        """
        清除招标列表缓存

        Args:
            page: 指定页码，为None时清除所有列表缓存

        Returns:
            是否成功
        """
        if page is not None:
            key = tender_list(page, {})
            return cache.delete(key)
        else:
            # 清除所有列表缓存(使用模式匹配)
            try:
                cache.delete_pattern('tenders:list:*')
                return True
            except AttributeError:
                return False

    def cache_tender_detail(
        self,
        tender_id: int,
        data: Dict,
        ttl: int = TENDER_DETAIL_TTL
    ) -> bool:
        """
        缓存招标详情

        Args:
            tender_id: 招标ID
            data: 招标详情数据
            ttl: 缓存时间(秒)

        Returns:
            是否成功
        """
        key = tender_detail(tender_id)
        return cache.set(key, data, ttl)

    def get_tender_detail(self, tender_id: int) -> Optional[Dict]:
        """
        获取招标详情缓存

        Args:
            tender_id: 招标ID

        Returns:
            缓存数据或None
        """
        key = tender_detail(tender_id)
        return cache.get(key)

    def invalidate_tender_detail(self, tender_id: int) -> bool:
        """
        清除招标详情缓存

        Args:
            tender_id: 招标ID

        Returns:
            是否成功
        """
        key = tender_detail(tender_id)
        return cache.delete(key)

    def cache_tender_stats(
        self,
        stats: Dict,
        ttl: int = STATS_TTL
    ) -> bool:
        """
        缓存招标统计数据

        Args:
            stats: 统计数据
            ttl: 缓存时间(秒)

        Returns:
            是否成功
        """
        key = tender_stats()
        return cache.set(key, stats, ttl)

    def get_tender_stats(self) -> Optional[Dict]:
        """
        获取招标统计数据缓存

        Returns:
            缓存数据或None
        """
        key = tender_stats()
        return cache.get(key)

    def invalidate_tender_stats(self) -> bool:
        """
        清除招标统计数据缓存

        Returns:
            是否成功
        """
        key = tender_stats()
        return cache.delete(key)

    def cache_search_results(
        self,
        query: str,
        results: List[Dict],
        ttl: int = SEARCH_TTL
    ) -> bool:
        """
        缓存搜索结果

        Args:
            query: 搜索关键词
            results: 搜索结果
            ttl: 缓存时间(秒)

        Returns:
            是否成功
        """
        key = search_results(query)
        return cache.set(key, results, ttl)

    def get_search_results(self, query: str) -> Optional[List[Dict]]:
        """
        获取搜索结果缓存

        Args:
            query: 搜索关键词

        Returns:
            缓存数据或None
        """
        key = search_results(query)
        return cache.get(key)

    def cache_region_distribution(
        self,
        data: Dict,
        ttl: int = REGION_DISTRIBUTION_TTL
    ) -> bool:
        """
        缓存地区分布数据

        Args:
            data: 地区分布数据
            ttl: 缓存时间(秒)

        Returns:
            是否成功
        """
        key = region_distribution()
        return cache.set(key, data, ttl)

    def get_region_distribution(self) -> Optional[Dict]:
        """
        获取地区分布缓存

        Returns:
            缓存数据或None
        """
        key = region_distribution()
        return cache.get(key)

    def cache_industry_distribution(
        self,
        data: Dict,
        ttl: int = INDUSTRY_DISTRIBUTION_TTL
    ) -> bool:
        """
        缓存行业分布数据

        Args:
            data: 行业分布数据
            ttl: 缓存时间(秒)

        Returns:
            是否成功
        """
        key = industry_distribution()
        return cache.set(key, data, ttl)

    def get_industry_distribution(self) -> Optional[Dict]:
        """
        获取行业分布缓存

        Returns:
            缓存数据或None
        """
        key = industry_distribution()
        return cache.get(key)

    def invalidate_all(self) -> bool:
        """
        清除所有招标相关缓存

        Returns:
            是否成功
        """
        try:
            cache.delete_pattern('tenders:*')
            cache.delete_pattern('search:*')
            cache.delete_pattern('stats:*')
            return True
        except AttributeError:
            return False


# 全局缓存管理器实例
_cache_manager = None


def get_cache_manager() -> TenderCacheManager:
    """
    获取全局缓存管理器实例

    Returns:
        TenderCacheManager实例
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = TenderCacheManager()
    return _cache_manager