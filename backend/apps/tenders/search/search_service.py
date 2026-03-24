"""
Search Service - Phase 6 Task 031
Full-text search implementation using PostgreSQL tsvector/tsquery
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.db import connection
from django.db.models import Q, F
from django.core.paginator import Paginator

# Try to import PostgreSQL-specific features
try:
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from ..models import TenderNotice


class SearchService:
    """
    Full-text search service for tender notices.

    Uses PostgreSQL full-text search with:
    - tsvector columns for pre-processed search vectors
    - GIN indexes for fast lookups
    - ts_rank_cd() for relevance scoring
    - Support for Chinese text via zhparser or simple parser
    """

    DEFAULT_PER_PAGE = 20

    def __init__(self):
        """Initialize search service."""
        self.model = TenderNotice

    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
        highlight: bool = False
    ) -> List[Dict]:
        """
        Search tender notices by full-text query.

        Args:
            query: Search query string
            filters: Optional filter criteria
            page: Page number (1-based)
            per_page: Items per page
            highlight: Whether to include highlighted results

        Returns:
            List of search result dictionaries
        """
        if query is None:
            raise ValueError("Query cannot be None")

        if not query.strip():
            return []

        # Build base queryset
        queryset = self._build_search_queryset(query)

        # Apply filters if provided
        if filters:
            queryset = self._apply_filters(queryset, filters)

        # Paginate
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        # Convert to results
        results = []
        for notice in page_obj.object_list:
            result = self._notice_to_dict(notice)

            # Add relevance score if available
            if hasattr(notice, 'rank'):
                result['relevance_score'] = float(notice.rank)
            else:
                result['relevance_score'] = 1.0

            # Add highlighting if requested
            if highlight:
                result.update(self._add_highlighting(result, query))

            results.append(result)

        return results

    def search_with_meta(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
        highlight: bool = False
    ) -> Dict:
        """
        Search with metadata (total count, pagination info).

        Args:
            query: Search query string
            filters: Optional filter criteria
            page: Page number
            per_page: Items per page
            highlight: Whether to include highlighted results

        Returns:
            Dictionary with results, total, and pagination info
        """
        queryset = self._build_search_queryset(query)

        if filters:
            queryset = self._apply_filters(queryset, filters)

        total = queryset.count()

        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        results = []
        for notice in page_obj.object_list:
            result = self._notice_to_dict(notice)

            if hasattr(notice, 'rank'):
                result['relevance_score'] = float(notice.rank)
            else:
                result['relevance_score'] = 1.0

            if highlight:
                result.update(self._add_highlighting(result, query))

            results.append(result)

        return {
            'results': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        }

    def _build_search_queryset(self, query: str):
        """
        Build queryset with full-text search.

        Uses PostgreSQL tsvector/tsquery for efficient full-text search.
        Falls back to simple OR-based search if tsvector is not available.
        """
        # Normalize query for PostgreSQL
        search_query = self._normalize_query(query)

        # Try to use PostgreSQL full-text search
        if POSTGRES_AVAILABLE and connection.vendor == 'postgresql':
            try:
                # Use SearchVector for combined title + description search
                search_vector = (
                    SearchVector('title', weight='A') +
                    SearchVector('description', weight='B')
                )

                query_obj = SearchQuery(search_query)

                queryset = self.model.objects.annotate(
                    search=search_vector
                ).filter(
                    search=query_obj
                ).annotate(
                    rank=SearchRank(search_vector, query_obj)
                ).order_by('-rank', '-publish_date')

                return queryset
            except Exception:
                pass  # Fall through to fallback

        # Fallback to simple OR-based search
        return self._fallback_search(query)

    def _fallback_search(self, query: str):
        """
        Fallback search using Django ORM Q objects.

        Splits query into terms and searches across title and description.
        """
        terms = query.split()

        q_objects = Q()
        for term in terms:
            q_objects |= Q(title__icontains=term)
            q_objects |= Q(description__icontains=term)

        return self.model.objects.filter(q_objects).order_by('-publish_date')

    def _normalize_query(self, query: str) -> str:
        """
        Normalize search query for PostgreSQL.

        - Removes extra whitespace
        - Handles special characters
        - Prepares for tsquery
        """
        # Remove extra whitespace
        query = ' '.join(query.split())

        # Escape special PostgreSQL tsquery characters
        special_chars = ['&', '|', '!', '(', ')', '@', '#', '$', '%', '^', '*']
        for char in special_chars:
            query = query.replace(char, ' ')

        return query.strip()

    def _apply_filters(self, queryset, filters: Dict) -> Any:
        """Apply additional filters to queryset."""
        if 'notice_type' in filters:
            queryset = queryset.filter(notice_type=filters['notice_type'])

        if 'region_code' in filters:
            queryset = queryset.filter(region_code=filters['region_code'])

        if 'region_codes' in filters:
            queryset = queryset.filter(region_code__in=filters['region_codes'])

        if 'industry_code' in filters:
            queryset = queryset.filter(industry_code=filters['industry_code'])

        if 'industry_codes' in filters:
            queryset = queryset.filter(industry_code__in=filters['industry_codes'])

        if 'budget_min' in filters:
            queryset = queryset.filter(budget_amount__gte=filters['budget_min'])

        if 'budget_max' in filters:
            queryset = queryset.filter(budget_amount__lte=filters['budget_max'])

        if 'publish_date_from' in filters:
            queryset = queryset.filter(publish_date__gte=filters['publish_date_from'])

        if 'publish_date_to' in filters:
            queryset = queryset.filter(publish_date__lte=filters['publish_date_to'])

        return queryset

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
            'created_at': notice.created_at.isoformat() if notice.created_at else None,
            'updated_at': notice.updated_at.isoformat() if notice.updated_at else None,
        }

    def _add_highlighting(self, result: Dict, query: str) -> Dict:
        """Add highlighted versions of title and description."""
        from .highlight_service import HighlightService, SnippetService

        highlight_service = HighlightService()
        snippet_service = SnippetService()

        keywords = query.split()

        highlighted = {}

        # Highlight title
        highlighted['highlighted_title'] = highlight_service.highlight(
            result['title'],
            keywords
        )

        # Generate snippet with highlighting for description
        if result['description']:
            snippet = snippet_service.generate(result['description'], keywords)
            highlighted['snippet'] = highlight_service.highlight(snippet, keywords)
            highlighted['highlighted_description'] = highlight_service.highlight(
                result['description'],
                keywords
            )
        else:
            highlighted['snippet'] = ''
            highlighted['highlighted_description'] = ''

        return highlighted

    def update_search_vector(self, notice_id: int):
        """
        Update search vector for a specific notice.

        This should be called when a notice is created or updated.
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tenders_tendernotice
                SET search_vector = (
                    setweight(to_tsvector('simple', COALESCE(title, '')), 'A') ||
                    setweight(to_tsvector('simple', COALESCE(description, '')), 'B')
                )
                WHERE id = %s
            """, [notice_id])

    def bulk_update_search_vectors(self):
        """Update search vectors for all notices."""
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tenders_tendernotice
                SET search_vector = (
                    setweight(to_tsvector('simple', COALESCE(title, '')), 'A') ||
                    setweight(to_tsvector('simple', COALESCE(description, '')), 'B')
                )
                WHERE search_vector IS NULL
            """)

