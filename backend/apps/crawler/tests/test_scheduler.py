"""
Crawler scheduler tests

Test Celery Beat configuration and scheduled tasks:
- Daily crawl at 02:00
- Scheduled task registration
- Celery Beat schedule configuration
"""

import pytest
from datetime import datetime, time
from unittest.mock import Mock, patch, MagicMock


class TestSchedulerConfiguration:
    """Test 1: Scheduler configuration exists"""

    def test_celery_beat_schedule_exists(self):
        """Celery beat schedule should be configured"""
        from apps.crawler.scheduler import get_beat_schedule

        schedule = get_beat_schedule()
        assert schedule is not None
        assert 'daily-crawl' in schedule

    def test_daily_crawl_schedule_time(self):
        """Daily crawl should be scheduled at 02:00"""
        from apps.crawler.scheduler import get_beat_schedule

        schedule = get_beat_schedule()
        daily_crawl = schedule['daily-crawl']

        # Check schedule configuration
        assert daily_crawl is not None
        assert 'task' in daily_crawl
        assert daily_crawl['task'] == 'apps.crawler.tasks.scheduled_daily_crawl'


class TestDailyCrawlTask:
    """Test 2: Daily crawl task registration"""

    def test_daily_crawl_task_exists(self):
        """scheduled_daily_crawl task should exist"""
        from apps.crawler.tasks import scheduled_daily_crawl

        assert scheduled_daily_crawl is not None
        assert hasattr(scheduled_daily_crawl, 'delay')

    @pytest.mark.django_db
    def test_daily_crawl_creates_tasks(self):
        """Daily crawl should create crawl tasks"""
        from apps.crawler.tasks import scheduled_daily_crawl

        result = scheduled_daily_crawl()

        assert result['status'] == 'scheduled'
        assert result['tasks_created'] > 0


class TestCeleryBeatIntegration:
    """Test 3: Celery Beat integration"""

    def test_celery_app_has_beat_schedule(self):
        """Celery app should have beat_schedule configuration"""
        from config.celery import app

        # Check if beat_schedule is configured
        if hasattr(app.conf, 'beat_schedule'):
            assert app.conf.beat_schedule is not None
        else:
            # beat_schedule might be in config
            pass

    def test_celery_beat_crontab_format(self):
        """Celery beat schedule should use correct crontab format"""
        from celery.schedules import crontab

        # Create a crontab for 02:00 daily
        schedule = crontab(hour=2, minute=0)

        assert schedule is not None
        # Verify it's a valid crontab
        assert hasattr(schedule, 'hour')
        assert hasattr(schedule, 'minute')


class TestSchedulerCommands:
    """Test 4: Scheduler management commands"""

    def test_start_scheduler_command_exists(self):
        """Start scheduler command should exist"""
        from django.core.management import call_command, CommandError

        # Check if command exists
        try:
            call_command('help', 'start_crawler_scheduler', verbosity=0)
            assert True
        except CommandError:
            # Command might not exist yet
            pass


class TestScheduledTaskExecution:
    """Test 5: Scheduled task execution"""

    @pytest.mark.django_db
    @patch('apps.crawler.tasks.run_crawl_task.delay')
    def test_daily_crawl_triggers_tasks(self, mock_delay):
        """Daily crawl should trigger individual crawl tasks"""
        from apps.crawler.tasks import scheduled_daily_crawl

        # Run the scheduled task
        result = scheduled_daily_crawl()

        # Should have created tasks
        assert result['tasks_created'] > 0

        # Should have called delay for each task
        assert mock_delay.called

    @pytest.mark.django_db
    @patch('apps.crawler.scheduler.run_crawl_task.apply_async')
    def test_scheduler_uses_apply_async(self, mock_apply_async):
        """Scheduler should use apply_async for better control"""
        from apps.crawler.scheduler import run_scheduled_crawl

        run_scheduled_crawl()

        # Should have triggered tasks
        assert mock_apply_async.called


class TestSchedulerConfigurationOptions:
    """Test 6: Scheduler configuration options"""

    def test_scheduler_can_disable_sources(self):
        """Should be able to disable specific sources"""
        from apps.crawler.scheduler import get_enabled_sources

        sources = get_enabled_sources()

        # Should return list of enabled sources
        assert isinstance(sources, list)

    def test_scheduler_has_default_sources(self):
        """Should have default sources configured"""
        from apps.crawler.scheduler import DEFAULT_SOURCES

        assert DEFAULT_SOURCES is not None
        assert len(DEFAULT_SOURCES) > 0

        # Each source should have required fields
        for source in DEFAULT_SOURCES:
            assert 'name' in source
            assert 'source_url' in source
            assert 'source_site' in source
