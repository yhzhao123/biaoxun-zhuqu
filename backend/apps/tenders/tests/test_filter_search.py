"""
Filter Search Tests - Phase 6 Task 032
Tests for multi-condition filtering functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from apps.tenders.models import TenderNotice
from apps.tenders.repositories import TenderRepository
from apps.tenders.search.filter_service import FilterService


class TestFilterServiceExists:
    """Test 1: FilterService class exists"""

    def test_filter_service_class_exists(self):
        """FilterService class should exist"""
        from apps.tenders.search.filter_service import FilterService
        assert FilterService is not None

    def test_filter_service_has_filter_method(self):
        """FilterService should have filter method"""
        from apps.tenders.search.filter_service import FilterService
        assert hasattr(FilterService, 'filter')


class TestRegionFilter(TestCase):
    """Test 2: Region/area filtering"""

    def setUp(self):
        self.repo = TenderRepository()
        self.filter_service = FilterService()

        # Create tenders with different regions
        self.tender1 = self.repo.create({
            'title': '北京市项目',
            'region_code': '110000',
            'region_name': '北京市',
            'publish_date': datetime.now()
        })

        self.tender2 = self.repo.create({
            'title': '上海市项目',
            'region_code': '310000',
            'region_name': '上海市',
            'publish_date': datetime.now()
        })

        self.tender3 = self.repo.create({
            'title': '广东省项目',
            'region_code': '440000',
            'region_name': '广东省',
            'publish_date': datetime.now()
        })

    def test_filter_by_single_region(self):
        """Should filter by single region"""
        results = self.filter_service.filter({'regions': ['110000']})

        assert len(results) == 1
        assert results[0]['region_code'] == '110000'

    def test_filter_by_multiple_regions(self):
        """Should filter by multiple regions (OR logic)"""
        results = self.filter_service.filter({'regions': ['110000', '310000']})

        assert len(results) == 2
        region_codes = [r['region_code'] for r in results]
        assert '110000' in region_codes
        assert '310000' in region_codes

    def test_filter_by_region_name(self):
        """Should filter by region name"""
        results = self.filter_service.filter({'region_name': '北京市'})

        assert len(results) == 1
        assert results[0]['region_name'] == '北京市'

    def test_filter_nonexistent_region(self):
        """Should return empty for non-existent region"""
        results = self.filter_service.filter({'regions': ['999999']})

        assert len(results) == 0


class TestIndustryFilter(TestCase):
    """Test 3: Industry/category filtering"""

    def setUp(self):
        self.repo = TenderRepository()
        self.filter_service = FilterService()

        # Create tenders with different industries
        self.tender1 = self.repo.create({
            'title': '医疗设备采购',
            'industry_code': 'F06',
            'industry_name': '医疗健康',
            'publish_date': datetime.now()
        })

        self.tender2 = self.repo.create({
            'title': '软件系统开发',
            'industry_code': 'I65',
            'industry_name': '信息技术',
            'publish_date': datetime.now()
        })

        self.tender3 = self.repo.create({
            'title': '建筑工程项目',
            'industry_code': 'E47',
            'industry_name': '建筑工程',
            'publish_date': datetime.now()
        })

    def test_filter_by_single_industry(self):
        """Should filter by single industry"""
        results = self.filter_service.filter({'industries': ['F06']})

        assert len(results) == 1
        assert results[0]['industry_code'] == 'F06'

    def test_filter_by_multiple_industries(self):
        """Should filter by multiple industries (OR logic)"""
        results = self.filter_service.filter({'industries': ['F06', 'I65']})

        assert len(results) == 2
        industry_codes = [r['industry_code'] for r in results]
        assert 'F06' in industry_codes
        assert 'I65' in industry_codes

    def test_filter_by_industry_name(self):
        """Should filter by industry name"""
        results = self.filter_service.filter({'industry_name': '医疗健康'})

        assert len(results) == 1
        assert results[0]['industry_name'] == '医疗健康'


class TestBudgetFilter(TestCase):
    """Test 4: Budget amount filtering"""

    def setUp(self):
        self.repo = TenderRepository()
        self.filter_service = FilterService()

        # Create tenders with different budgets
        self.tender1 = self.repo.create({
            'title': '小额项目',
            'budget_amount': Decimal('50000.00'),
            'publish_date': datetime.now()
        })

        self.tender2 = self.repo.create({
            'title': '中额项目',
            'budget_amount': Decimal('500000.00'),
            'publish_date': datetime.now()
        })

        self.tender3 = self.repo.create({
            'title': '大额项目',
            'budget_amount': Decimal('5000000.00'),
            'publish_date': datetime.now()
        })

    def test_filter_by_budget_min(self):
        """Should filter by minimum budget"""
        results = self.filter_service.filter({'budgetMin': 100000})

        assert len(results) == 2
        for r in results:
            assert r['budget_amount'] >= 100000

    def test_filter_by_budget_max(self):
        """Should filter by maximum budget"""
        results = self.filter_service.filter({'budgetMax': 1000000})

        assert len(results) == 2
        for r in results:
            assert r['budget_amount'] <= 1000000

    def test_filter_by_budget_range(self):
        """Should filter by budget range"""
        results = self.filter_service.filter({
            'budgetMin': 100000,
            'budgetMax': 1000000
        })

        assert len(results) == 1
        assert results[0]['budget_amount'] == Decimal('500000.00')

    def test_filter_by_budget_min_only_no_results(self):
        """Should return empty when min budget exceeds all"""
        results = self.filter_service.filter({'budgetMin': 10000000})

        assert len(results) == 0


class TestDateFilter(TestCase):
    """Test 5: Publish date filtering"""

    def setUp(self):
        self.repo = TenderRepository()
        self.filter_service = FilterService()

        today = datetime.now()

        # Create tenders with different dates
        self.tender1 = self.repo.create({
            'title': '一月前项目',
            'publish_date': today - timedelta(days=30)
        })

        self.tender2 = self.repo.create({
            'title': '一周前项目',
            'publish_date': today - timedelta(days=7)
        })

        self.tender3 = self.repo.create({
            'title': '今日项目',
            'publish_date': today
        })

    def test_filter_by_date_from(self):
        """Should filter by publish date from"""
        date_from = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        results = self.filter_service.filter({'publishDateFrom': date_from})

        assert len(results) == 2

    def test_filter_by_date_to(self):
        """Should filter by publish date to"""
        date_to = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        results = self.filter_service.filter({'publishDateTo': date_to})

        assert len(results) == 1
        assert results[0]['title'] == '一月前项目'

    def test_filter_by_date_range(self):
        """Should filter by date range"""
        date_from = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        date_to = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')

        results = self.filter_service.filter({
            'publishDateFrom': date_from,
            'publishDateTo': date_to
        })

        assert len(results) == 1
        assert results[0]['title'] == '一周前项目'

    def test_filter_by_invalid_date_format(self):
        """Should handle invalid date format"""
        with pytest.raises(ValueError):
            self.filter_service.filter({'publishDateFrom': 'invalid-date'})


class TestNoticeTypeFilter(TestCase):
    """Test 6: Notice type filtering"""

    def setUp(self):
        self.repo = TenderRepository()
        self.filter_service = FilterService()

        self.tender1 = self.repo.create({
            'title': '招标公告',
            'notice_type': TenderNotice.TYPE_BIDDING,
            'publish_date': datetime.now()
        })

        self.tender2 = self.repo.create({
            'title': '中标公告',
            'notice_type': TenderNotice.TYPE_WIN,
            'publish_date': datetime.now()
        })

    def test_filter_by_bidding_notice(self):
        """Should filter by bidding notice type"""
        results = self.filter_service.filter({
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        assert len(results) == 1
        assert results[0]['notice_type'] == TenderNotice.TYPE_BIDDING

    def test_filter_by_win_notice(self):
        """Should filter by win notice type"""
        results = self.filter_service.filter({
            'notice_type': TenderNotice.TYPE_WIN
        })

        assert len(results) == 1
        assert results[0]['notice_type'] == TenderNotice.TYPE_WIN


class TestCombinedFilters(TestCase):
    """Test 7: Combined multi-condition filtering"""

    def setUp(self):
        self.repo = TenderRepository()
        self.filter_service = FilterService()

        # Create tenders with various attributes
        self.tender1 = self.repo.create({
            'title': '北京市医院设备采购',
            'region_code': '110000',
            'industry_code': 'F06',
            'budget_amount': Decimal('1000000.00'),
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        self.tender2 = self.repo.create({
            'title': '北京市软件系统开发',
            'region_code': '110000',
            'industry_code': 'I65',
            'budget_amount': Decimal('500000.00'),
            'publish_date': datetime.now() - timedelta(days=5),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        self.tender3 = self.repo.create({
            'title': '上海市医院设备采购',
            'region_code': '310000',
            'industry_code': 'F06',
            'budget_amount': Decimal('2000000.00'),
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_WIN
        })

    def test_filter_by_region_and_industry(self):
        """Should filter by region AND industry"""
        results = self.filter_service.filter({
            'regions': ['110000'],
            'industries': ['F06']
        })

        assert len(results) == 1
        assert results[0]['title'] == '北京市医院设备采购'

    def test_filter_by_region_and_budget(self):
        """Should filter by region AND budget range"""
        results = self.filter_service.filter({
            'regions': ['110000'],
            'budgetMin': 600000
        })

        assert len(results) == 1
        assert results[0]['title'] == '北京市医院设备采购'

    def test_filter_by_all_conditions(self):
        """Should filter by multiple conditions combined"""
        results = self.filter_service.filter({
            'regions': ['110000', '310000'],
            'industries': ['F06', 'I65'],
            'budgetMin': 500000,
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        assert len(results) == 2

    def test_filter_with_no_matches(self):
        """Should return empty when no matches"""
        results = self.filter_service.filter({
            'regions': ['110000'],
            'industries': ['F06'],
            'budgetMin': 5000000
        })

        assert len(results) == 0


class TestQueryBuilder(TestCase):
    """Test 8: QueryBuilder functionality"""

    def test_query_builder_exists(self):
        """QueryBuilder class should exist"""
        from apps.tenders.search.filter_service import QueryBuilder
        assert QueryBuilder is not None

    def test_query_builder_builds_query(self):
        """QueryBuilder should build Django Q object"""
        from apps.tenders.search.filter_service import QueryBuilder
        from django.db.models import Q

        builder = QueryBuilder()
        query = builder.build({
            'regions': ['110000'],
            'industries': ['F06']
        })

        # Should return a Q object
        assert isinstance(query, Q)
        assert query is not None


class TestFilterValidation(TestCase):
    """Test 9: Filter parameter validation"""

    def setUp(self):
        self.filter_service = FilterService()

    def test_validate_budget_range(self):
        """Should validate budget range (min <= max)"""
        with pytest.raises(ValueError):
            self.filter_service.validate_filters({
                'budgetMin': 1000000,
                'budgetMax': 500000
            })

    def test_validate_date_range(self):
        """Should validate date range (from <= to)"""
        with pytest.raises(ValueError):
            self.filter_service.validate_filters({
                'publishDateFrom': '2024-12-01',
                'publishDateTo': '2024-01-01'
            })

    def test_validate_region_codes(self):
        """Should validate region code format"""
        with pytest.raises(ValueError):
            self.filter_service.validate_filters({
                'regions': ['invalid']
            })


class TestFilterPagination(TestCase):
    """Test 10: Filter result pagination"""

    def setUp(self):
        self.repo = TenderRepository()
        self.filter_service = FilterService()

        # Create 25 tenders
        for i in range(25):
            self.repo.create({
                'title': f'项目-{i}',
                'region_code': '110000',
                'publish_date': datetime.now()
            })

    def test_filter_with_pagination(self):
        """Should support pagination in filter results"""
        results = self.filter_service.filter(
            {'regions': ['110000']},
            page=1,
            per_page=10
        )

        assert len(results) == 10

    def test_filter_pagination_page_2(self):
        """Should return correct page"""
        page1 = self.filter_service.filter(
            {'regions': ['110000']},
            page=1,
            per_page=10
        )
        page2 = self.filter_service.filter(
            {'regions': ['110000']},
            page=2,
            per_page=10
        )

        assert len(page1) == 10
        assert len(page2) == 10
        assert page1[0]['id'] != page2[0]['id']

    def test_filter_with_total_count(self):
        """Should return total count"""
        response = self.filter_service.filter_with_meta(
            {'regions': ['110000']},
            per_page=10
        )

        assert 'results' in response
        assert 'total' in response
        assert response['total'] == 25


class TestEmptyAndEdgeCases(TestCase):
    """Test 11: Empty and edge cases"""

    def setUp(self):
        self.filter_service = FilterService()

    def test_filter_empty_filters(self):
        """Should return all results when no filters"""
        results = self.filter_service.filter({})

        # Should not raise error
        assert isinstance(results, list)

    def test_filter_none_values(self):
        """Should handle None values in filters"""
        results = self.filter_service.filter({
            'regions': None,
            'industries': None
        })

        assert isinstance(results, list)

    def test_filter_empty_arrays(self):
        """Should handle empty arrays in filters"""
        results = self.filter_service.filter({
            'regions': [],
            'industries': []
        })

        assert isinstance(results, list)

