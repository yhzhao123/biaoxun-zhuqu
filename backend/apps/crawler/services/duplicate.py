"""
Duplicate detection service
数据去重服务

提供基于 URL + 标题的精确去重和基于内容相似度的模糊去重
"""

import re
import logging
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from datetime import datetime, timedelta

from django.db.models import Q

from apps.tenders.models import TenderNotice
from apps.crawler.models import CrawlTask


logger = logging.getLogger(__name__)


class DuplicateChecker:
    """
    重复数据检测器

    Features:
    - 精确去重：基于 URL + 来源网站
    - 精确去重：基于标题 + 来源网站
    - 模糊去重：基于内容相似度
    - 重复记录追踪
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize duplicate checker

        Args:
            similarity_threshold: 模糊去重相似度阈值 (0-1)
        """
        self.similarity_threshold = similarity_threshold
        # 内存中的重复记录缓存
        self._duplicate_cache: List[Dict[str, Any]] = []

    def is_duplicate(
        self,
        source_url: str,
        title: str,
        source_site: Optional[str] = None
    ) -> bool:
        """
        检查是否为重复数据（精确匹配）

        Args:
            source_url: 公告来源URL
            title: 公告标题
            source_site: 来源网站名称

        Returns:
            True if duplicate
        """
        # 1. 检查 URL 是否已存在
        url_exists = TenderNotice.objects.filter(
            source_url=source_url
        ).exists()

        if url_exists:
            logger.debug(f"Duplicate found by URL: {source_url}")
            return True

        # 2. 检查同一网站的相同标题
        if source_site:
            title_exists = TenderNotice.objects.filter(
                title=title,
                source_site=source_site
            ).exists()

            if title_exists:
                logger.debug(f"Duplicate found by title+site: {title}")
                return True

        return False

    def is_fuzzy_duplicate(
        self,
        title: str,
        source_site: Optional[str] = None
    ) -> bool:
        """
        模糊去重检测

        比较标题相似度，超过阈值认为是重复

        Args:
            title: 公告标题
            source_site: 来源网站（可选，限制在同一网站内比较）

        Returns:
            True if fuzzy duplicate
        """
        # 构建查询
        query = TenderNotice.objects.all()
        if source_site:
            query = query.filter(source_site=source_site)

        # 只检查最近 30 天的记录（性能优化）
        cutoff_date = datetime.now() - timedelta(days=30)
        query = query.filter(created_at__gte=cutoff_date)

        # 获取候选标题
        candidates = query.values('id', 'title').iterator()

        for candidate in candidates:
            similarity = self.calculate_similarity(title, candidate['title'])
            if similarity >= self.similarity_threshold:
                logger.debug(
                    f"Fuzzy duplicate found: '{title}' ~ "
                    f"'{candidate['title']}' (similarity: {similarity:.2f})"
                )
                return True

        return False

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        使用 SequenceMatcher 计算相似度，并针对中文优化

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度 (0-1)
        """
        if not text1 or not text2:
            return 0.0

        if text1 == text2:
            return 1.0

        # 预处理：去除空格和标点
        def preprocess(text: str) -> str:
            # 去除空白字符
            text = re.sub(r'\s+', '', text)
            # 去除常见标点
            text = re.sub(r'[，。！？、；：""''（）【】《》]', '', text)
            # 转换为小写（英文部分）
            return text.lower()

        clean1 = preprocess(text1)
        clean2 = preprocess(text2)

        if clean1 == clean2:
            return 1.0

        # 使用 SequenceMatcher 计算相似度
        similarity = SequenceMatcher(None, clean1, clean2).ratio()

        return similarity

    def filter_duplicates(
        self,
        items: List[Dict[str, Any]],
        source_site: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        从列表中过滤掉重复项

        Args:
            items: 待检查的列表
            source_site: 来源网站

        Returns:
            非重复项目列表
        """
        new_items = []

        for item in items:
            title = item.get('title', '')
            source_url = item.get('source_url', '')
            item_site = item.get('source_site', source_site)

            # 检查精确重复
            if self.is_duplicate(source_url, title, item_site):
                logger.info(f"Filtered exact duplicate: {title}")
                continue

            # 检查模糊重复
            if self.is_fuzzy_duplicate(title, item_site):
                logger.info(f"Filtered fuzzy duplicate: {title}")
                continue

            new_items.append(item)

        logger.info(f"Filter complete: {len(items)} -> {len(new_items)}")
        return new_items

    def record_duplicate(
        self,
        task_id: int,
        source_url: str,
        title: str,
        reason: str
    ) -> None:
        """
        记录重复数据

        Args:
            task_id: 爬虫任务ID
            source_url: 来源URL
            title: 标题
            reason: 重复原因
        """
        record = {
            'task_id': task_id,
            'source_url': source_url,
            'title': title,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
        }

        self._duplicate_cache.append(record)
        logger.debug(f"Recorded duplicate: {title} - {reason}")

    def get_duplicate_records(
        self,
        task_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取重复记录

        Args:
            task_id: 可选的任务ID过滤

        Returns:
            重复记录列表
        """
        if task_id:
            return [
                r for r in self._duplicate_cache
                if r['task_id'] == task_id
            ]
        return self._duplicate_cache.copy()

    def get_stats(
        self,
        task_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取去重统计信息

        Args:
            task_id: 可选的任务ID过滤

        Returns:
            统计信息字典
        """
        records = self.get_duplicate_records(task_id)

        return {
            'total_duplicates': len(records),
            'by_reason': self._group_by_reason(records),
        }

    def _group_by_reason(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """按原因分组统计"""
        groups: Dict[str, int] = {}
        for record in records:
            reason = record.get('reason', 'unknown')
            groups[reason] = groups.get(reason, 0) + 1
        return groups

    def mark_duplicate(
        self,
        tender_id: int,
        reason: str
    ) -> bool:
        """
        标记 TenderNotice 为重复

        Args:
            tender_id: TenderNotice ID
            reason: 重复原因

        Returns:
            True if marked successfully
        """
        try:
            tender = TenderNotice.objects.get(id=tender_id)
            # 使用 'closed' 状态表示重复/已关闭
            tender.status = 'closed'
            tender.save()

            logger.info(f"Marked tender {tender_id} as duplicate: {reason}")
            return True

        except TenderNotice.DoesNotExist:
            logger.error(f"TenderNotice not found: {tender_id}")
            return False

    def clear_cache(self) -> None:
        """清除重复记录缓存"""
        self._duplicate_cache.clear()
        logger.debug("Duplicate cache cleared")


# 全局实例（可选的单例模式）
_default_checker: Optional[DuplicateChecker] = None


def get_duplicate_checker(
    similarity_threshold: float = 0.85
) -> DuplicateChecker:
    """
    获取默认的 DuplicateChecker 实例

    Args:
        similarity_threshold: 相似度阈值

    Returns:
        DuplicateChecker instance
    """
    global _default_checker
    if _default_checker is None:
        _default_checker = DuplicateChecker(similarity_threshold)
    return _default_checker
