"""
Test TenderRepository - Phase 2 Task 008
TDD: RED state - tests should fail until repository is implemented
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestTenderRepository(TestCase):
    """Test TenderRepository CRUD operations."""

    def setUp(self):
        """Set up test data."""
        from apps.tenders.models import TenderNotice
        from apps.tenders.repositories import TenderRepository

        self.repository = TenderRepository()
        self.TenderNotice = TenderNotice

        # Create test data
        now = timezone.now()
        self.tender1 = self.TenderNotice.objects.create(
            notice_id='TEST-001',
            title='政府采购招标公告',
            description='某省政府采购项目',
            tenderer='某省政府采购中心',
            budget=1000000.00,
            currency='CNY',
            publish_date=now,
            deadline_date=now + timedelta(days=30),
            region='北京',
            industry='IT服务',
            source_url='https://www.ccgp.gov.cn/',
            source_site='中国政府采购网',
            status='active'
        )

        self.tender2 = self.TenderNotice.objects.create(
            notice_id='TEST-002',
            title='医疗器械采购招标',
            description='医院设备采购',
            tenderer='某市第一医院',
            budget=500000.00,
            currency='CNY',
            publish_date=now - timedelta(days=5),
            deadline_date=now + timedelta(days=25),
            region='上海',
            industry='医疗健康',
            source_url='https://www.ccgp.gov.cn/',
            source_site='中国政府采购网',
            status='pending'
        )

        self.tender3 = self.TenderNotice.objects.create(
            notice_id='TEST-003',
            title='工程建设招标公告',
            description='基建工程项目',
            tenderer='某建筑公司',
            budget=2000000.00,
            currency='CNY',
            publish_date=now - timedelta(days=10),
            deadline_date=now + timedelta(days=20),
            region='北京',
            industry='工程建设',
            source_url='https://www.ccgp.gov.cn/',
            source_site='中国政府采购网',
            status='active'
        )

    def test_get_by_id_exists(self):
        """Test get_by_id returns tender when exists."""
        result = self.repository.get_by_id(self.tender1.id)
        assert result is not None
        assert result.notice_id == 'TEST-001'
        assert result.title == '政府采购招标公告'

    def test_get_by_id_not_exists(self):
        """Test get_by_id returns None when not exists."""
        result = self.repository.get_by_id(99999)
        assert result is None

    def test_get_by_notice_id_exists(self):
        """Test get_by_notice_id returns tender when exists."""
        result = self.repository.get_by_notice_id('TEST-001')
        assert result is not None
        assert result.id == self.tender1.id
        assert result.tenderer == '某省政府采购中心'

    def test_get_by_notice_id_not_exists(self):
        """Test get_by_notice_id returns None when not exists."""
        result = self.repository.get_by_notice_id('NON-EXIST-001')
        assert result is None

    def test_find_duplicates_by_title_and_date(self):
        """Test find_duplicates finds duplicate by title and publish_date."""
        # Create a tender with same title and similar date
        duplicate = self.TenderNotice.objects.create(
            notice_id='TEST-001-DUP',
            title='政府采购招标公告',  # Same title
            tenderer='另一个招标人',
            publish_date=self.tender1.publish_date  # Same date
        )

        # Should find duplicates
        duplicates = self.repository.find_duplicates(
            title='政府采购招标公告',
            publish_date=self.tender1.publish_date,
            tenderer='某省政府采购中心'
        )

        # Should return at least the original tender
        assert duplicates.count() >= 1

    def test_find_duplicates_no_match(self):
        """Test find_duplicates returns empty when no duplicates."""
        duplicates = self.repository.find_duplicates(
            title='完全不存在的标题',
            publish_date=timezone.now(),
            tenderer='不存在的招标人'
        )

        assert duplicates.count() == 0

    def test_create_or_update_create(self):
        """Test create_or_update creates new tender when not exists."""
        initial_count = self.TenderNotice.objects.count()

        result = self.repository.create_or_update({
            'notice_id': 'NEW-TENDER-001',
            'title': '新招标公告',
            'tenderer': '新招标人',
            'budget': 300000.00,
        })

        assert result is not None
        assert result.notice_id == 'NEW-TENDER-001'
        assert self.TenderNotice.objects.count() == initial_count + 1

    def test_create_or_update_update(self):
        """Test create_or_update updates existing tender."""
        result = self.repository.create_or_update({
            'notice_id': 'TEST-001',
            'title': '更新后的标题',
            'budget': 2000000.00,  # Updated budget
        })

        assert result is not None
        assert result.notice_id == 'TEST-001'
        assert result.title == '更新后的标题'
        assert float(result.budget) == 2000000.00

        # Should not create new record
        assert self.TenderNotice.objects.count() == 3

    def test_search_by_keywords(self):
        """Test search by keywords."""
        results = self.repository.search(keywords='政府采购')
        assert results.count() >= 1
        assert any('政府采购' in t.title for t in results)

    def test_search_by_region(self):
        """Test search by region."""
        results = self.repository.search(region='北京')
        assert results.count() >= 2  # tender1 and tender3

    def test_search_by_industry(self):
        """Test search by industry."""
        results = self.repository.search(industry='IT服务')
        assert results.count() >= 1
        assert results[0].industry == 'IT服务'

    def test_search_by_date_range(self):
        """Test search by date range."""
        now = timezone.now()
        start_date = now - timedelta(days=7)
        end_date = now

        results = self.repository.search(
            date_range=(start_date, end_date)
        )

        # Should find tender1 (today) and tender2 (5 days ago)
        assert results.count() >= 2

    def test_search_pagination(self):
        """Test search with pagination."""
        # Create more tenders for pagination test
        for i in range(25):
            self.TenderNotice.objects.create(
                notice_id=f'PAGINATION-{i:03d}',
                title=f'分页测试标题{i}',
                tenderer='分页测试招标人',
            )

        # Test first page
        page1 = self.repository.search(page=1, page_size=10)
        assert page1.number == 1
        assert page1.paginator.num_pages >= 3

        # Test second page
        page2 = self.repository.search(page=2, page_size=10)
        assert page2.number == 2

    def test_get_by_tenderer(self):
        """Test get_by_tenderer returns tenders for specific tenderer."""
        results = self.repository.get_by_tenderer('某省政府采购中心')
        assert results.count() >= 1
        assert all(t.tenderer == '某省政府采购中心' for t in results)

    def test_get_by_tenderer_with_limit(self):
        """Test get_by_tenderer with limit parameter."""
        # Create multiple tenders for same tenderer
        for i in range(5):
            self.TenderNotice.objects.create(
                notice_id=f'SAME-TENDERER-{i:03d}',
                title=f'相同招标人标题{i}',
                tenderer='测试招标人',
            )

        results = self.repository.get_by_tenderer('测试招标人', limit=3)
        assert results.count() == 3

    def test_search_combined_filters(self):
        """Test search with multiple filters combined."""
        results = self.repository.search(
            keywords='招标',
            region='北京',
            industry='IT服务',
        )

        # Should find tender1 matching all criteria
        assert any(t.notice_id == 'TEST-001' for t in results)

    def test_search_empty_results(self):
        """Test search returns empty QuerySet for no matches."""
        results = self.repository.search(
            keywords='完全不存在的关键词xyz',
        )
        assert results.count() == 0