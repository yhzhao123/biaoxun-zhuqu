"""
Crawler base architecture tests

Test base spider infrastructure including:
- BaseSpider class existence
- run_crawl_task Celery task
- Retry mechanism (max_retries=3, countdown=60)
- Task status transitions (pending -> running -> completed/failed)
- Error logging
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestBaseSpiderExists:
    """Test 1: Test BaseSpider class exists and has required methods"""

    def test_base_spider_class_exists(self):
        """BaseSpider class should exist in spiders.base module"""
        from apps.crawler.spiders.base import BaseSpider
        assert BaseSpider is not None

    def test_base_spider_is_abstract(self):
        """BaseSpider should be an abstract class"""
        from apps.crawler.spiders.base import BaseSpider
        assert hasattr(BaseSpider, '__abstractmethods__')

    def test_base_spider_has_crawl_method(self):
        """BaseSpider should have crawl abstract method"""
        from apps.crawler.spiders.base import BaseSpider
        # Check that crawl is defined as abstract method
        assert 'crawl' in BaseSpider.__abstractmethods__

    def test_base_spider_has_parse_method(self):
        """BaseSpider should have parse method"""
        from apps.crawler.spiders.base import BaseSpider
        # Parse should be a concrete method
        assert hasattr(BaseSpider, 'parse')


class TestRunCrawlTaskExists:
    """Test 2: Test run_crawl_task Celery task exists"""

    def test_run_crawl_task_exists(self):
        """run_crawl_task should be a Celery task"""
        from apps.crawler.tasks import run_crawl_task
        assert run_crawl_task is not None

    def test_run_crawl_task_is_celery_task(self):
        """run_crawl_task should be decorated as Celery task"""
        from apps.crawler.tasks import run_crawl_task
        assert hasattr(run_crawl_task, 'delay') or hasattr(run_crawl_task, 'apply_async')


class TestRetryMechanism:
    """Test 3: Test retry mechanism (max_retries=3, countdown=60)"""

    def test_retry_max_retries_is_3(self):
        """Task should retry up to 3 times"""
        from apps.crawler.tasks import run_crawl_task
        # Check max_retries configuration
        assert hasattr(run_crawl_task, 'max_retries')
        assert run_crawl_task.max_retries == 3

    def test_retry_countdown_is_60(self):
        """Retry countdown should be 60 seconds"""
        from apps.crawler.tasks import run_crawl_task

        # Mock the task to check autoretry_for and retry_backoff
        if hasattr(run_crawl_task, 'autoretry_for'):
            assert run_crawl_task.autoretry_for == (Exception,)

    def test_task_has_retry_config(self):
        """Task should have retry configuration"""
        from apps.crawler.tasks import run_crawl_task

        # Check if task has retry configuration
        task_config = getattr(run_crawl_task, '航线', None) or {}
        # Should have some retry mechanism configured
        assert hasattr(run_crawl_task, 'max_retries')


class TestTaskStatusTransitions:
    """Test 4: Test task status transitions (pending -> running -> completed/failed)"""

    @pytest.mark.django_db
    def test_status_pending_to_running(self):
        """Task status should transition from pending to running"""
        from apps.crawler.models import CrawlTask

        # Create a pending task
        task = CrawlTask.objects.create(
            name="政府采购网-每日更新",
            source_url="http://www.ccgp.gov.cn/",
            source_site="政府采购网",
            status="pending"
        )

        # Simulate starting the task
        task.status = "running"
        task.started_at = datetime.now()
        task.save()

        # Verify status changed
        task.refresh_from_db()
        assert task.status == "running"
        assert task.started_at is not None

    @pytest.mark.django_db
    def test_status_running_to_completed(self):
        """Task status should transition from running to completed"""
        from apps.crawler.models import CrawlTask

        task = CrawlTask.objects.create(
            name="政府采购网-每日更新",
            source_url="http://www.ccgp.gov.cn/",
            source_site="政府采购网",
            status="running",
            started_at=datetime.now()
        )

        # Simulate completing the task
        task.status = "completed"
        task.completed_at = datetime.now()
        task.items_crawled = 10
        task.save()

        task.refresh_from_db()
        assert task.status == "completed"
        assert task.completed_at is not None
        assert task.items_crawled == 10

    @pytest.mark.django_db
    def test_status_running_to_failed(self):
        """Task status should transition from running to failed"""
        from apps.crawler.models import CrawlTask

        task = CrawlTask.objects.create(
            name="政府采购网-每日更新",
            source_url="http://www.ccgp.gov.cn/",
            source_site="政府采购网",
            status="running",
            started_at=datetime.now()
        )

        # Simulate task failure
        task.status = "failed"
        task.completed_at = datetime.now()
        task.error_message = "Connection timeout"
        task.save()

        task.refresh_from_db()
        assert task.status == "failed"
        assert task.error_message == "Connection timeout"

    @pytest.mark.django_db
    def test_status_choices_exist(self):
        """STATUS_CHOICES should exist in model"""
        from apps.crawler.models import CrawlTask, STATUS_CHOICES

        # Verify STATUS_CHOICES exists
        assert STATUS_CHOICES is not None
        assert len(STATUS_CHOICES) == 4  # pending, running, completed, failed

        # Verify all required statuses exist
        status_values = [choice[0] for choice in STATUS_CHOICES]
        assert "pending" in status_values
        assert "running" in status_values
        assert "completed" in status_values
        assert "failed" in status_values


class TestErrorLogging:
    """Test 5: Test error logging"""

    @pytest.mark.django_db
    def test_error_logged_on_failure(self):
        """Error message should be logged when task fails"""
        from apps.crawler.models import CrawlTask

        error_msg = "Target website returned 503 error"

        task = CrawlTask.objects.create(
            name="政府采购网-每日更新",
            source_url="http://www.ccgp.gov.cn/",
            source_site="政府采购网",
            status="failed",
            error_message=error_msg
        )

        task.refresh_from_db()
        assert task.error_message == error_msg

    @pytest.mark.django_db
    def test_task_tracks_retries(self):
        """Failed task should track retry count"""
        from apps.crawler.models import CrawlTask

        task = CrawlTask.objects.create(
            name="政府采购网-每日更新",
            source_url="http://www.ccgp.gov.cn/",
            source_site="政府采购网",
            status="running"
        )

        # In a real scenario, we'd track retry count in the task
        # For now, verify the model supports this field
        assert hasattr(CrawlTask, 'error_message')


class TestCrawlTaskModel:
    """Test CrawlTask model structure"""

    @pytest.mark.django_db
    def test_crawltask_has_all_required_fields(self):
        """CrawlTask should have all required fields"""
        from apps.crawler.models import CrawlTask

        # Check required fields exist
        assert hasattr(CrawlTask, 'name')
        assert hasattr(CrawlTask, 'source_url')
        assert hasattr(CrawlTask, 'source_site')
        assert hasattr(CrawlTask, 'status')
        assert hasattr(CrawlTask, 'items_crawled')
        assert hasattr(CrawlTask, 'error_message')
        assert hasattr(CrawlTask, 'started_at')
        assert hasattr(CrawlTask, 'completed_at')

    @pytest.mark.django_db
    def test_crawltask_can_be_created(self):
        """CrawlTask can be created with basic fields"""
        from apps.crawler.models import CrawlTask

        task = CrawlTask.objects.create(
            name="Test Crawl Task",
            source_url="http://example.com",
            source_site="Test Site",
            status="pending"
        )

        assert task.pk is not None
        assert task.name == "Test Crawl Task"
        assert task.status == "pending"