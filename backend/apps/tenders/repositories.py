"""
招标公告仓库层 - Phase 2 Task 009
提供数据访问层抽象
"""
from typing import Optional, Tuple, Any, Dict
from django.db.models import QuerySet, Q
from django.core.paginator import Paginator
from .models import TenderNotice


class TenderRepository:
    """招标公告数据仓库"""

    def get_by_id(self, id: int) -> Optional[TenderNotice]:
        """
        根据ID获取招标公告

        Args:
            id: 招标公告ID

        Returns:
            TenderNotice对象或None
        """
        try:
            return TenderNotice.objects.get(id=id)
        except TenderNotice.DoesNotExist:
            return None

    def get_by_notice_id(self, notice_id: str) -> Optional[TenderNotice]:
        """
        根据公告编号获取招标公告

        Args:
            notice_id: 公告编号

        Returns:
            TenderNotice对象或None
        """
        try:
            return TenderNotice.objects.get(notice_id=notice_id)
        except TenderNotice.DoesNotExist:
            return None

    def find_duplicates(
        self,
        title: str,
        publish_date,
        tenderer: Optional[str] = None
    ) -> QuerySet:
        """
        根据标题和发布日期查找重复的招标公告

        Args:
            title: 公告标题
            publish_date: 发布日期
            tenderer: 招标人（可选）

        Returns:
            QuerySet of TenderNotice
        """
        queryset = TenderNotice.objects.filter(
            title=title,
            publish_date__date=publish_date.date() if publish_date else None
        )

        if tenderer:
            queryset = queryset.filter(tenderer=tenderer)

        return queryset

    def create_or_update(self, data: Dict[str, Any]) -> TenderNotice:
        """
        创建或更新招标公告

        Args:
            data: 招标公告数据字典

        Returns:
            TenderNotice对象
        """
        notice_id = data.get('notice_id')

        if not notice_id:
            raise ValueError("notice_id is required for create_or_update")

        # Use update_or_create for create or update
        tender, created = TenderNotice.objects.update_or_create(
            notice_id=notice_id,
            defaults=data
        )

        return tender

    def search(
        self,
        keywords: Optional[str] = None,
        region: Optional[str] = None,
        industry: Optional[str] = None,
        status: Optional[str] = None,
        date_range: Optional[Tuple] = None,
        page: int = 1,
        page_size: Optional[int] = None
    ) -> QuerySet:
        """
        多条件搜索招标公告

        Args:
            keywords: 关键词搜索
            region: 地区筛选
            industry: 行业筛选
            status: 状态筛选
            date_range: 日期范围 (start_date, end_date)
            page: 页码
            page_size: 每页数量 (如果为None则返回QuerySet)

        Returns:
            QuerySet or Paginator
        """
        queryset = TenderNotice.objects.all()

        # Keyword search
        if keywords:
            queryset = queryset.filter(
                Q(title__icontains=keywords) |
                Q(description__icontains=keywords) |
                Q(tenderer__icontains=keywords) |
                Q(ai_keywords__icontains=keywords)
            )

        # Region filter
        if region:
            queryset = queryset.filter(region=region)

        # Industry filter
        if industry:
            queryset = queryset.filter(industry=industry)

        # Status filter
        if status:
            queryset = queryset.filter(status=status)

        # Date range filter
        if date_range:
            start_date, end_date = date_range
            if start_date:
                queryset = queryset.filter(publish_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(publish_date__lte=end_date)

        # Return paginated results if page_size is specified
        if page_size is not None and page_size > 0:
            paginator = Paginator(queryset, page_size)
            try:
                return paginator.page(page)
            except:
                return paginator.page(1)

        return queryset

    def get_by_tenderer(
        self,
        tenderer: str,
        limit: Optional[int] = None
    ) -> QuerySet:
        """
        根据招标人查询招标公告

        Args:
            tenderer: 招标人名称
            limit: 返回数量限制

        Returns:
            QuerySet of TenderNotice
        """
        queryset = TenderNotice.objects.filter(
            tenderer__icontains=tenderer
        ).order_by('-publish_date', '-created_at')

        if limit:
            queryset = queryset[:limit]

        return queryset

    def get_active_tenders(self) -> QuerySet:
        """
        获取所有进行中的招标公告

        Returns:
            QuerySet of active TenderNotice
        """
        return TenderNotice.objects.filter(
            status=TenderNotice.STATUS_ACTIVE
        ).order_by('-publish_date')

    def get_tenders_by_batch(self, batch_id: str) -> QuerySet:
        """
        根据爬虫批次ID获取招标公告

        Args:
            batch_id: 爬虫批次ID

        Returns:
            QuerySet of TenderNotice
        """
        return TenderNotice.objects.filter(
            crawl_batch_id=batch_id
        ).order_by('-created_at')