"""
Full-text Search Tests - Phase 6 Task 030
Tests for PostgreSQL full-text search functionality.
"""

import pytest
from datetime import datetime, timedelta
from django.test import TestCase
from apps.tenders.models import TenderNotice
from apps.tenders.repositories import TenderRepository
from apps.tenders.search.search_service import SearchService


class TestSearchServiceExists:
    """Test 1: SearchService class exists"""

    def test_search_service_class_exists(self):
        """SearchService class should exist"""
        from apps.tenders.search.search_service import SearchService
        assert SearchService is not None

    def test_search_service_has_search_method(self):
        """SearchService should have search method"""
        from apps.tenders.search.search_service import SearchService
        assert hasattr(SearchService, 'search')


class TestBasicSearch(TestCase):
    """Test 2: Basic full-text search"""

    def setUp(self):
        self.repo = TenderRepository()
        self.search_service = SearchService()

        # Create test data
        self.tender1 = self.repo.create({
            'title': '某市人民医院医疗设备采购项目',
            'description': '采购CT机、MRI等医疗设备',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        self.tender2 = self.repo.create({
            'title': '某市政府办公用品采购',
            'description': '采购电脑、打印机等办公设备',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        self.tender3 = self.repo.create({
            'title': '某县教育系统信息化建设项目',
            'description': '学校网络设备、服务器采购',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

    def test_search_by_title(self):
        """Should search by title keywords"""
        results = self.search_service.search(query='医院')

        assert len(results) == 1
        assert results[0]['title'] == '某市人民医院医疗设备采购项目'

    def test_search_by_description(self):
        """Should search by description keywords"""
        results = self.search_service.search(query='CT机')

        assert len(results) == 1
        assert 'CT机' in results[0]['description']

    def test_search_across_title_and_description(self):
        """Should search across both title and description"""
        results = self.search_service.search(query='设备')

        # Should match all three tenders
        assert len(results) == 3

    def test_search_no_results(self):
        """Should return empty list for no matches"""
        results = self.search_service.search(query='不存在的关键词')

        assert len(results) == 0


class TestRelevanceRanking(TestCase):
    """Test 3: Relevance-based ranking"""

    def setUp(self):
        self.repo = TenderRepository()
        self.search_service = SearchService()

        # Create tenders with varying relevance
        self.tender1 = self.repo.create({
            'title': '医疗设备采购项目',
            'description': '医疗设备采购',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        self.tender2 = self.repo.create({
            'title': '医疗设备',
            'description': '普通设备',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        self.tender3 = self.repo.create({
            'title': '其他项目',
            'description': '医疗设备相关',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

    def test_results_ordered_by_relevance(self):
        """Should order results by relevance score"""
        results = self.search_service.search(query='医疗设备')

        # Title match should rank higher than description match
        assert len(results) == 3
        assert results[0]['relevance_score'] >= results[1]['relevance_score']

    def test_relevance_score_included(self):
        """Should include relevance score in results"""
        results = self.search_service.search(query='设备')

        for result in results:
            assert 'relevance_score' in result
            assert 0 <= result['relevance_score'] <= 1


class TestSearchPagination(TestCase):
    """Test 4: Search result pagination"""

    def setUp(self):
        self.repo = TenderRepository()
        self.search_service = SearchService()

        # Create 25 tenders for pagination testing
        for i in range(25):
            self.repo.create({
                'title': f'采购项目-{i}',
                'description': f'项目描述-{i}',
                'publish_date': datetime.now(),
                'notice_type': TenderNotice.TYPE_BIDDING
            })

    def test_default_page_size(self):
        """Should use default page size of 20"""
        results = self.search_service.search(query='采购项目')

        assert len(results) <= 20

    def test_custom_page_size(self):
        """Should support custom page size"""
        results = self.search_service.search(query='采购项目', per_page=10)

        assert len(results) <= 10

    def test_pagination_with_page(self):
        """Should support page-based pagination"""
        page1 = self.search_service.search(query='采购项目', page=1, per_page=10)
        page2 = self.search_service.search(query='采购项目', page=2, per_page=10)

        assert len(page1) == 10
        assert len(page2) == 10
        # Different pages should have different results
        assert page1[0]['id'] != page2[0]['id']

    def test_total_count_included(self):
        """Should include total count in response"""
        response = self.search_service.search_with_meta(query='采购项目', per_page=10)

        assert 'results' in response
        assert 'total' in response
        assert response['total'] == 25


class TestChineseSearch(TestCase):
    """Test 5: Chinese text search support"""

    def setUp(self):
        self.repo = TenderRepository()
        self.search_service = SearchService()

        self.tender1 = self.repo.create({
            'title': '北京市政府采购项目',
            'description': '北京市各区设备采购',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        self.tender2 = self.repo.create({
            'title': '上海市医疗系统升级',
            'description': '上海医院信息化改造',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

    def test_search_chinese_characters(self):
        """Should support Chinese character search"""
        results = self.search_service.search(query='北京市')

        assert len(results) == 1
        assert '北京市' in results[0]['title']

    def test_search_chinese_phrases(self):
        """Should support Chinese phrase search"""
        results = self.search_service.search(query='医疗系统')

        assert len(results) == 1


class TestSearchPerformance(TestCase):
    """Test 6: Search performance (< 1s)"""

    def setUp(self):
        self.repo = TenderRepository()
        self.search_service = SearchService()

        # Create 1000 tenders for performance testing
        for i in range(1000):
            self.repo.create({
                'title': f'性能测试项目-{i} 包含关键词',
                'description': f'性能测试描述-{i}',
                'publish_date': datetime.now(),
                'notice_type': TenderNotice.TYPE_BIDDING
            })

    def test_search_performance_under_1s(self):
        """Search should complete in under 1 second"""
        import time

        start_time = time.time()
        results = self.search_service.search(query='关键词')
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"Search took {elapsed}s, should be under 1s"


class TestSearchFilters(TestCase):
    """Test 7: Search with filters"""

    def setUp(self):
        self.repo = TenderRepository()
        self.search_service = SearchService()

        # Create tenders with different attributes
        self.tender1 = self.repo.create({
            'title': '医院设备采购',
            'description': 'CT设备',
            'publish_date': datetime.now() - timedelta(days=10),
            'notice_type': TenderNotice.TYPE_BIDDING,
            'region_code': '110000',
            'industry_code': 'F06'
        })

        self.tender2 = self.repo.create({
            'title': '学校设备采购',
            'description': '电脑设备',
            'publish_date': datetime.now() - timedelta(days=5),
            'notice_type': TenderNotice.TYPE_WIN,
            'region_code': '310000',
            'industry_code': 'I65'
        })

    def test_search_with_notice_type_filter(self):
        """Should filter by notice type"""
        results = self.search_service.search(
            query='设备',
            filters={'notice_type': TenderNotice.TYPE_BIDDING}
        )

        assert len(results) == 1
        assert results[0]['notice_type'] == TenderNotice.TYPE_BIDDING

    def test_search_with_region_filter(self):
        """Should filter by region"""
        results = self.search_service.search(
            query='设备',
            filters={'region_code': '110000'}
        )

        assert len(results) == 1
        assert results[0]['region_code'] == '110000'

    def test_search_with_industry_filter(self):
        """Should filter by industry"""
        results = self.search_service.search(
            query='设备',
            filters={'industry_code': 'I65'}
        )

        assert len(results) == 1
        assert results[0]['industry_code'] == 'I65'


class TestEmptyAndEdgeCases(TestCase):
    """Test 8: Empty and edge cases"""

    def setUp(self):
        self.repo = TenderRepository()
        self.search_service = SearchService()

    def test_search_empty_query(self):
        """Should handle empty query gracefully"""
        results = self.search_service.search(query='')

        assert isinstance(results, list)

    def test_search_whitespace_only(self):
        """Should handle whitespace-only query"""
        results = self.search_service.search(query='   ')

        assert isinstance(results, list)

    def test_search_special_characters(self):
        """Should handle special characters"""
        results = self.search_service.search(query='!@#$%')

        assert isinstance(results, list)

    def test_search_none_query(self):
        """Should handle None query"""
        with pytest.raises(ValueError):
            self.search_service.search(query=None)


class TestSearchIndexExists(TestCase):
    """Test 9: Full-text search index exists"""

    def test_search_vector_field_exists(self):
        """TenderNotice should have search_vector field"""
        assert hasattr(TenderNotice, 'search_vector')

    def test_search_vector_is_tsvector(self):
        """search_vector should be tsvector type (PostgreSQL only)"""
        from django.db import connection
        if connection.vendor != 'postgresql':
            self.skipTest("PostgreSQL-only test")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'tenders_tendernotice'
                AND column_name = 'search_vector'
            """)
            result = cursor.fetchone()
            assert result is not None
            # PostgreSQL tsvector is reported as 'tsvector' or USER-DEFINED
            assert result[0] in ['tsvector', 'USER-DEFINED']

    def test_gin_index_exists(self):
        """GIN index should exist on search_vector (PostgreSQL only)"""
        from django.db import connection
        if connection.vendor != 'postgresql':
            self.skipTest("PostgreSQL-only test")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'tenders_tendernotice'
                AND indexdef LIKE '%search_vector%'
            """)
            result = cursor.fetchone()
            assert result is not None, "GIN index on search_vector should exist"

