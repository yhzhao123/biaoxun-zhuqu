"""
Filter Service - Phase 6 Task 033
Multi-condition filtering implementation
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.db.models import Q, QuerySet
from django.core.paginator import Paginator

from ..models import TenderNotice


class QueryBuilder:
    """
    Builder for constructing complex filter queries.

    Supports:
    - Multi-condition filtering with AND logic between types
    - Array filtering with OR logic within types
    - Range filtering for dates and amounts
    - Dynamic query construction
    """

    def __init__(self):
        """Initialize query builder."""
        self.filters = Q()

    def build(self, filter_params: Dict) -> Q:
        """
        Build Q object from filter parameters.

        Args:
            filter_params: Dictionary of filter criteria

        Returns:
            Django Q object for filtering
        """
        q_objects = Q()

        # Region filters (OR within regions, AND with other types)
        if filter_params.get('regions'):
            region_q = self._build_region_filter(filter_params['regions'])
            if region_q:
                q_objects &= region_q

        if filter_params.get('region_name'):
            q_objects &= Q(region_name__icontains=filter_params['region_name'])

        # Industry filters (OR within industries, AND with other types)
        if filter_params.get('industries'):
            industry_q = self._build_industry_filter(filter_params['industries'])
            if industry_q:
                q_objects &= industry_q

        if filter_params.get('industry_name'):
            q_objects &= Q(industry_name__icontains=filter_params['industry_name'])

        # Budget range filters
        budget_q = self._build_budget_filter(filter_params)
        if budget_q:
            q_objects &= budget_q

        # Date range filters
        date_q = self._build_date_filter(filter_params)
        if date_q:
            q_objects &= date_q

        # Notice type filter
        if filter_params.get('notice_type'):
            q_objects &= Q(notice_type=filter_params['notice_type'])

        # Tenderer filter
        if filter_params.get('tenderer'):
            q_objects &= Q(tenderer__icontains=filter_params['tenderer'])

        # Project name filter
        if filter_params.get('project_name'):
            q_objects &= Q(project_name__icontains=filter_params['project_name'])

        return q_objects

    def _build_region_filter(self, regions: List[str]) -> Optional[Q]:
        """Build region filter with OR logic."""
        if not regions:
            return None

        region_q = Q()
        for region in regions:
            region_q |= Q(region_code=region)
            region_q |= Q(region_name__icontains=region)

        return region_q

    def _build_industry_filter(self, industries: List[str]) -> Optional[Q]:
        """Build industry filter with OR logic."""
        if not industries:
            return None

        industry_q = Q()
        for industry in industries:
            industry_q |= Q(industry_code=industry)
            industry_q |= Q(industry_name__icontains=industry)

        return industry_q

    def _build_budget_filter(self, filter_params: Dict) -> Optional[Q]:
        """Build budget range filter."""
        budget_q = Q()
        has_budget_filter = False

        if 'budgetMin' in filter_params:
            budget_q &= Q(budget_amount__gte=filter_params['budgetMin'])
            has_budget_filter = True

        if 'budgetMax' in filter_params:
            budget_q &= Q(budget_amount__lte=filter_params['budgetMax'])
            has_budget_filter = True

        return budget_q if has_budget_filter else None

    def _build_date_filter(self, filter_params: Dict) -> Optional[Q]:
        """Build date range filter."""
        date_q = Q()
        has_date_filter = False

        if filter_params.get('publishDateFrom'):
            date_from = self._parse_date(filter_params['publishDateFrom'])
            if date_from:
                date_q &= Q(publish_date__gte=date_from)
                has_date_filter = True

        if filter_params.get('publishDateTo'):
            date_to = self._parse_date(filter_params['publishDateTo'])
            if date_to:
                date_q &= Q(publish_date__lte=date_to)
                has_date_filter = True

        return date_q if has_date_filter else None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats."""
        if not date_str or not isinstance(date_str, str):
            raise ValueError(f"Invalid date format: {date_str}")

        formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S']

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Invalid date format: {date_str}")


class FilterService:
    """
    Service for filtering tender notices.

    Provides multi-condition filtering with:
    - Region/area filtering
    - Industry/category filtering
    - Budget amount range filtering
    - Publish date range filtering
    - Combined AND/OR logic
    """

    DEFAULT_PER_PAGE = 20

    def __init__(self):
        """Initialize filter service."""
        self.model = TenderNotice
        self.query_builder = QueryBuilder()

    def filter(
        self,
        filter_params: Dict,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
        order_by: str = '-publish_date'
    ) -> List[Dict]:
        """
        Filter tender notices by multiple criteria.

        Args:
            filter_params: Dictionary of filter criteria
            page: Page number (1-based)
            per_page: Items per page
            order_by: Ordering field(s)

        Returns:
            List of filtered result dictionaries
        """
        # Validate filters
        self.validate_filters(filter_params)

        # Build queryset
        queryset = self._build_filter_queryset(filter_params, order_by)

        # Paginate
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        # Convert to results
        return [self._notice_to_dict(notice) for notice in page_obj.object_list]

    def filter_with_meta(
        self,
        filter_params: Dict,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
        order_by: str = '-publish_date'
    ) -> Dict:
        """
        Filter with metadata (total count, pagination info).

        Args:
            filter_params: Dictionary of filter criteria
            page: Page number
            per_page: Items per page
            order_by: Ordering field(s)

        Returns:
            Dictionary with results, total, and pagination info
        """
        self.validate_filters(filter_params)

        queryset = self._build_filter_queryset(filter_params, order_by)
        total = queryset.count()

        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        results = [self._notice_to_dict(notice) for notice in page_obj.object_list]

        return {
            'results': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        }

    def _build_filter_queryset(self, filter_params: Dict, order_by: str) -> QuerySet:
        """Build filtered queryset."""
        queryset = self.model.objects.all()

        # Build and apply filter Q object
        q_filter = self.query_builder.build(filter_params)
        queryset = queryset.filter(q_filter)

        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset

    def validate_filters(self, filter_params: Dict) -> bool:
        """
        Validate filter parameters.

        Args:
            filter_params: Dictionary of filter criteria

        Returns:
            True if valid

        Raises:
            ValueError: If filters are invalid
        """
        # Validate budget range
        if 'budgetMin' in filter_params and 'budgetMax' in filter_params:
            try:
                budget_min = Decimal(str(filter_params['budgetMin']))
                budget_max = Decimal(str(filter_params['budgetMax']))
                if budget_min > budget_max:
                    raise ValueError("budgetMin cannot be greater than budgetMax")
            except InvalidOperation:
                raise ValueError("Invalid budget values")

        # Validate date range
        if filter_params.get('publishDateFrom') and filter_params.get('publishDateTo'):
            date_from = self.query_builder._parse_date(filter_params['publishDateFrom'])
            date_to = self.query_builder._parse_date(filter_params['publishDateTo'])
            if date_from and date_to and date_from > date_to:
                raise ValueError("publishDateFrom cannot be after publishDateTo")

        # Validate region codes (should be 6 digits or valid region names)
        if filter_params.get('regions'):
            for region in filter_params['regions']:
                if not isinstance(region, str):
                    raise ValueError(f"Region code must be string: {region}")
                stripped = region.strip()
                if not stripped:
                    raise ValueError("Region code cannot be empty")
                # Allow region codes (digits) or region names (Chinese characters)
                if stripped.isdigit():
                    if len(stripped) not in [2, 4, 6]:
                        raise ValueError(f"Invalid region code format: {region}")
                else:
                    # Must contain at least one Chinese character to be a valid region name
                    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in stripped)
                    if not has_chinese:
                        raise ValueError(f"Invalid region format: {region}")

        return True

    def _notice_to_dict(self, notice: TenderNotice) -> Dict:
        """Convert TenderNotice to dictionary."""
        return {
            'id': notice.id,
            'title': notice.title,
            'description': notice.description or '',
            'notice_type': notice.notice_type,
            'notice_type_display': notice.get_notice_type_display(),
            'region_code': notice.region_code,
            'region_name': notice.region_name,
            'industry_code': notice.industry_code,
            'industry_name': notice.industry_name,
            'budget_amount': float(notice.budget_amount) if notice.budget_amount else None,
            'publish_date': notice.publish_date.isoformat() if notice.publish_date else None,
            'deadline_date': notice.deadline_date.isoformat() if notice.deadline_date else None,
            'tenderer': notice.tenderer,
            'winner': notice.winner,
            'project_name': notice.project_name,
            'created_at': notice.created_at.isoformat() if notice.created_at else None,
            'updated_at': notice.updated_at.isoformat() if notice.updated_at else None,
        }

    def get_filter_options(self) -> Dict:
        """
        Get available filter options.

        Returns:
            Dictionary with available regions, industries, etc.
        """
        return {
            'regions': self._get_region_options(),
            'industries': self._get_industry_options(),
            'notice_types': [
                {'value': TenderNotice.TYPE_BIDDING, 'label': '招标公告'},
                {'value': TenderNotice.TYPE_WIN, 'label': '中标公告'},
            ]
        }

    def _get_region_options(self) -> List[Dict]:
        """Get available region options."""
        regions = self.model.objects.exclude(
            region_code__isnull=True
        ).values('region_code', 'region_name').distinct()

        return [
            {'code': r['region_code'], 'name': r['region_name']}
            for r in regions if r['region_code']
        ]

    def _get_industry_options(self) -> List[Dict]:
        """Get available industry options."""
        industries = self.model.objects.exclude(
            industry_code__isnull=True
        ).values('industry_code', 'industry_name').distinct()

        return [
            {'code': i['industry_code'], 'name': i['industry_name']}
            for i in industries if i['industry_code']
        ]

