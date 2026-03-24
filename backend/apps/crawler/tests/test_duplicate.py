"""
Duplicate detection service tests

Test DuplicateChecker functionality including:
- URL + title based exact deduplication
- Content similarity based fuzzy deduplication
- Integration with crawler workflow
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


class TestDuplicateCheckerExists:
    """Test 1: DuplicateChecker class exists"""

    def test_duplicate_checker_class_exists(self):
        """DuplicateChecker class should exist"""
        from apps.crawler.services.duplicate import DuplicateChecker
        assert DuplicateChecker is not None

    def test_duplicate_checker_singleton(self):
        """DuplicateChecker should be usable as singleton"""
        from apps.crawler.services.duplicate import DuplicateChecker

        checker1 = DuplicateChecker()
        checker2 = DuplicateChecker()
        # Both instances should work independently
        assert checker1 is not None
        assert checker2 is not None


class TestExactDuplicateDetection:
    """Test 2: URL + title based exact deduplication"""

    @pytest.mark.django_db
    def test_is_duplicate_by_url(self):
        """Should detect duplicate by exact URL match"""
        from apps.crawler.services.duplicate import DuplicateChecker
        from apps.tenders.models import TenderNotice

        # Create existing tender
        TenderNotice.objects.create(
            title="测试招标公告",
            notice_id="TEST-001",
            source_url="http://example.com/notice/123",
            source_site="测试网站"
        )

        checker = DuplicateChecker()
        is_dup = checker.is_duplicate(
            source_url="http://example.com/notice/123",
            title="另一个标题"  # 不同标题但相同URL
        )

        assert is_dup is True

    @pytest.mark.django_db
    def test_is_duplicate_by_title_and_site(self):
        """Should detect duplicate by title + source_site match"""
        from apps.crawler.services.duplicate import DuplicateChecker
        from apps.tenders.models import TenderNotice

        TenderNotice.objects.create(
            title="某单位信息化建设项目",
            notice_id="TEST-00X",
            source_url="http://example.com/notice/456",
            source_site="政府采购网"
        )

        checker = DuplicateChecker()
        is_dup = checker.is_duplicate(
            source_url="http://different-url.com/notice",  # 不同URL
            title="某单位信息化建设项目",
            source_site="政府采购网"
        )

        assert is_dup is True

    @pytest.mark.django_db
    def test_not_duplicate_different_site(self):
        """Same title from different sites should not be duplicate"""
        from apps.crawler.services.duplicate import DuplicateChecker
        from apps.tenders.models import TenderNotice

        TenderNotice.objects.create(
            title="某单位信息化建设项目",
            notice_id="TEST-00X",
            source_url="http://example.com/notice/1",
            source_site="政府采购网"
        )

        checker = DuplicateChecker()
        is_dup = checker.is_duplicate(
            source_url="http://other.com/notice/2",
            title="某单位信息化建设项目",
            source_site="其他采购网"  # 不同网站
        )

        assert is_dup is False


class TestFuzzyDuplicateDetection:
    """Test 3: Content similarity based fuzzy deduplication"""

    def test_similarity_same_content(self):
        """Identical content should have 100% similarity"""
        from apps.crawler.services.duplicate import DuplicateChecker

        checker = DuplicateChecker()
        similarity = checker.calculate_similarity(
            "某单位信息化建设项目招标公告",
            "某单位信息化建设项目招标公告"
        )

        assert similarity == 1.0

    def test_similarity_similar_content(self):
        """Similar content should have high similarity"""
        from apps.crawler.services.duplicate import DuplicateChecker

        checker = DuplicateChecker()
        similarity = checker.calculate_similarity(
            "某单位信息化建设项目招标公告",
            "某单位信息化建设项目采购公告"
        )

        assert similarity > 0.7  # 应该很相似
        assert similarity < 1.0  # 但不是完全相同

    def test_similarity_different_content(self):
        """Different content should have low similarity"""
        from apps.crawler.services.duplicate import DuplicateChecker

        checker = DuplicateChecker()
        similarity = checker.calculate_similarity(
            "某单位信息化建设项目招标公告",
            "某医院医疗设备采购项目中标公告"
        )

        assert similarity < 0.5  # 应该不相似

    @pytest.mark.django_db
    def test_is_fuzzy_duplicate(self):
        """Should detect fuzzy duplicate based on similarity threshold"""
        from apps.crawler.services.duplicate import DuplicateChecker
        from apps.tenders.models import TenderNotice

        # Create existing tender
        TenderNotice.objects.create(
            title="某单位信息化建设项目招标公告",
            notice_id="TEST-00X",
            source_url="http://example.com/notice/1",
            source_site="政府采购网"
        )

        checker = DuplicateChecker(similarity_threshold=0.85)

        # Very similar title should be detected as duplicate
        is_dup = checker.is_fuzzy_duplicate(
            title="某单位信息化建设项目采购公告",  # 招标 -> 采购
            source_site="政府采购网"
        )

        assert is_dup is True


class TestDuplicateRecordTracking:
    """Test 4: Duplicate record tracking"""

    @pytest.mark.django_db
    def test_record_duplicate(self):
        """Should record duplicate encounter"""
        from apps.crawler.services.duplicate import DuplicateChecker
        from apps.crawler.models import CrawlTask

        task = CrawlTask.objects.create(
            name="测试任务",
            source_url="http://example.com",
            source_site="测试网站"
        )

        checker = DuplicateChecker()
        checker.record_duplicate(
            task_id=task.id,
            source_url="http://example.com/notice/1",
            title="测试公告",
            reason="URL已存在"
        )

        # 应该创建重复记录
        duplicates = checker.get_duplicate_records(task_id=task.id)
        assert len(duplicates) == 1
        assert duplicates[0]['source_url'] == "http://example.com/notice/1"


class TestDuplicateStats:
    """Test 5: Duplicate statistics"""

    @pytest.mark.django_db
    def test_get_duplicate_stats(self):
        """Should return duplicate statistics"""
        from apps.crawler.services.duplicate import DuplicateChecker
        from apps.crawler.models import CrawlTask

        task = CrawlTask.objects.create(
            name="测试任务",
            source_url="http://example.com",
            source_site="测试网站"
        )

        checker = DuplicateChecker()

        # Record some duplicates
        checker.record_duplicate(task.id, "url1", "title1", "reason1")
        checker.record_duplicate(task.id, "url2", "title2", "reason2")

        stats = checker.get_stats(task_id=task.id)

        assert stats['total_duplicates'] == 2


class TestDuplicateCheckerIntegration:
    """Test 6: Integration with crawler workflow"""

    @pytest.mark.django_db
    def test_filter_duplicates_from_list(self):
        """Should filter duplicates from a list of items"""
        from apps.crawler.services.duplicate import DuplicateChecker
        from apps.tenders.models import TenderNotice

        # Create existing tender
        TenderNotice.objects.create(
            title="已存在的公告",
            notice_id="TEST-00X",
            source_url="http://example.com/existing",
            source_site="政府采购网"
        )

        checker = DuplicateChecker()

        items = [
            {
                'title': "已存在的公告",
                'source_url': "http://example.com/existing",
                'source_site': "政府采购网"
            },
            {
                'title': "新公告",
                'source_url': "http://example.com/new",
                'source_site': "政府采购网"
            },
        ]

        new_items = checker.filter_duplicates(items)

        assert len(new_items) == 1
        assert new_items[0]['title'] == "新公告"

    @pytest.mark.django_db
    def test_mark_as_duplicate(self):
        """Should be able to mark item as duplicate"""
        from apps.crawler.services.duplicate import DuplicateChecker
        from apps.tenders.models import TenderNotice

        checker = DuplicateChecker()

        tender = TenderNotice.objects.create(
            title="测试公告",
            notice_id="TEST-00X",
            source_url="http://example.com/test",
            source_site="测试网站"
        )

        # Mark as duplicate
        checker.mark_duplicate(tender.id, "与ID 123重复")

        # Refresh from db
        tender.refresh_from_db()
        assert tender.status == 'closed'
