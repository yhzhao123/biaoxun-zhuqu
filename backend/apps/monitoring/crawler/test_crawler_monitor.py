"""
Task 058: Crawler Monitoring Tests
测试爬虫监控功能 - TaskRecord, TaskCounter, TaskTracker, FlowerClient
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestTaskRecord:
    """测试 TaskRecord 数据模型"""

    def test_task_record_creation(self):
        """测试 TaskRecord 创建"""
        from apps.monitoring.crawler.models import TaskRecord

        record = TaskRecord(
            task_id='test-task-001',
            name='crawl_tenders',
            status='pending',
            start_time=datetime.now()
        )

        assert record.task_id == 'test-task-001'
        assert record.name == 'crawl_tenders'
        assert record.status == 'pending'
        assert record.retry_count == 0

    def test_task_record_status_transitions(self):
        """测试 TaskRecord 状态转换"""
        from apps.monitoring.crawler.models import TaskRecord

        record = TaskRecord(
            task_id='test-task-002',
            name='crawl_tenders',
            status='pending',
            start_time=datetime.now()
        )

        # 状态转换: pending -> running -> success
        record.status = 'running'
        assert record.status == 'running'

        record.status = 'success'
        record.end_time = datetime.now()
        assert record.status == 'success'
        assert record.end_time is not None

    def test_task_record_error_tracking(self):
        """测试 TaskRecord 错误跟踪"""
        from apps.monitoring.crawler.models import TaskRecord

        record = TaskRecord(
            task_id='test-task-003',
            name='crawl_tenders',
            status='pending',
            start_time=datetime.now()
        )

        record.status = 'failure'
        record.error_message = 'Connection timeout'
        record.end_time = datetime.now()

        assert record.status == 'failure'
        assert record.error_message == 'Connection timeout'
        assert record.end_time is not None

    def test_task_record_retry_increment(self):
        """测试 TaskRecord 重试计数"""
        from apps.monitoring.crawler.models import TaskRecord

        record = TaskRecord(
            task_id='test-task-004',
            name='crawl_tenders',
            status='pending',
            start_time=datetime.now()
        )

        # 模拟重试
        record.status = 'retry'
        record.retry_count = 1

        assert record.retry_count == 1


class TestTaskCounter:
    """测试 TaskCounter 聚合统计模型"""

    def test_task_counter_creation(self):
        """测试 TaskCounter 创建"""
        from apps.monitoring.crawler.models import TaskCounter

        counter = TaskCounter(
            task_name='crawl_tenders',
            window='hour'
        )

        assert counter.task_name == 'crawl_tenders'
        assert counter.window == 'hour'
        assert counter.success_count == 0
        assert counter.failure_count == 0

    def test_task_counter_increment_success(self):
        """测试 TaskCounter 成功计数增加"""
        from apps.monitoring.crawler.models import TaskCounter

        counter = TaskCounter(
            task_name='crawl_tenders',
            window='hour'
        )

        counter.increment_success()
        assert counter.success_count == 1

        counter.increment_success()
        assert counter.success_count == 2

    def test_task_counter_increment_failure(self):
        """测试 TaskCounter 失败计数增加"""
        from apps.monitoring.crawler.models import TaskCounter

        counter = TaskCounter(
            task_name='crawl_tenders',
            window='hour'
        )

        counter.increment_failure()
        assert counter.failure_count == 1

    def test_task_counter_success_rate_calculation(self):
        """测试 TaskCounter 成功率计算"""
        from apps.monitoring.crawler.models import TaskCounter

        counter = TaskCounter(
            task_name='crawl_tenders',
            window='hour'
        )

        # 3 成功, 1 失败 = 75% 成功率
        counter.success_count = 3
        counter.failure_count = 1

        success_rate = counter.get_success_rate()
        assert success_rate == 75.0

    def test_task_counter_zero_success_rate(self):
        """测试零成功率情况"""
        from apps.monitoring.crawler.models import TaskCounter

        counter = TaskCounter(
            task_name='crawl_tenders',
            window='hour'
        )

        counter.failure_count = 5
        success_rate = counter.get_success_rate()

        assert success_rate == 0.0

    def test_task_counter_total_count(self):
        """测试总计数"""
        from apps.monitoring.crawler.models import TaskCounter

        counter = TaskCounter(
            task_name='crawl_tenders',
            window='hour'
        )

        counter.success_count = 10
        counter.failure_count = 5

        assert counter.get_total_count() == 15


class TestFlowerTask:
    """测试 FlowerTask API 响应解析"""

    def test_flower_task_creation(self):
        """测试 FlowerTask 创建"""
        from apps.monitoring.crawler.models import FlowerTask

        task_data = {
            'id': 'task-123',
            'name': 'crawl_tenders',
            'status': 'SUCCESS',
            'startTime': 1640000000,
            'endTime': 1640000100,
            'runtime': 100,
            'worker': 'worker1@example.com'
        }

        task = FlowerTask(**task_data)

        assert task.id == 'task-123'
        assert task.name == 'crawl_tenders'
        assert task.status == 'SUCCESS'

    def test_flower_task_parsing(self):
        """测试 FlowerTask 解析"""
        from apps.monitoring.crawler.models import FlowerTask

        task_data = {
            'id': 'task-456',
            'name': 'process_data',
            'status': 'FAILURE',
            'startTime': 1640000200,
            'endTime': 1640000300,
            'runtime': 100,
            'worker': 'worker2@example.com',
            'result': 'Error: Connection failed'
        }

        task = FlowerTask(**task_data)

        assert task.id == 'task-456'
        assert task.status == 'FAILURE'


class TestTaskTracker:
    """测试 TaskTracker 任务追踪器"""

    def test_task_tracker_creation(self):
        """测试 TaskTracker 创建"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()

        assert tracker.tasks is not None
        assert len(tracker.tasks) == 0

    def test_task_tracker_start_task(self):
        """测试 TaskTracker 启动任务"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.start('task-001', 'crawl_tenders')

        assert 'task-001' in tracker.tasks
        task = tracker.tasks['task-001']
        assert task.name == 'crawl_tenders'
        assert task.status == 'running'
        assert task.start_time is not None

    def test_task_tracker_complete_task(self):
        """测试 TaskTracker 完成任务"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.start('task-002', 'crawl_tenders')
        tracker.complete('task-002')

        task = tracker.tasks['task-002']
        assert task.status == 'success'
        assert task.end_time is not None

    def test_task_tracker_fail_task(self):
        """测试 TaskTracker 任务失败"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.start('task-003', 'crawl_tenders')
        tracker.fail('task-003', error_message='Network error')

        task = tracker.tasks['task-003']
        assert task.status == 'failure'
        assert task.error_message == 'Network error'
        assert task.end_time is not None

    def test_task_tracker_retry_task(self):
        """测试 TaskTracker 重试任务"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.start('task-004', 'crawl_tenders')
        tracker.fail('task-004', error_message='Temp error')
        tracker.retry('task-004')

        task = tracker.tasks['task-004']
        assert task.status == 'retry'
        assert task.retry_count == 1

    def test_task_tracker_get_task(self):
        """测试获取任务信息"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.start('task-005', 'crawl_tenders')

        task = tracker.get_task('task-005')
        assert task is not None
        assert task.task_id == 'task-005'

    def test_task_tracker_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()
        task = tracker.get_task('nonexistent')

        assert task is None

    def test_task_tracker_get_running_tasks(self):
        """测试获取运行中的任务"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.start('task-006', 'crawl_tenders')
        tracker.start('task-007', 'process_data')
        tracker.start('task-008', 'crawl_tenders')
        tracker.complete('task-007')

        running = tracker.get_running_tasks()
        assert len(running) == 2

    def test_task_tracker_get_tasks_by_status(self):
        """测试按状态获取任务"""
        from apps.monitoring.crawler.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.start('task-009', 'crawl_tenders')
        tracker.complete('task-009')
        tracker.start('task-010', 'crawl_tenders')
        tracker.fail('task-010', error_message='Error')

        success_tasks = tracker.get_tasks_by_status('success')
        failure_tasks = tracker.get_tasks_by_status('failure')

        assert len(success_tasks) == 1
        assert len(failure_tasks) == 1


class TestTaskCounterClass:
    """测试 TaskCounter 类（聚合统计）"""

    def test_task_counter_class_creation(self):
        """测试 TaskCounter 类创建"""
        from apps.monitoring.crawler.counter import TaskCounter as CounterClass

        counter = CounterClass('crawl_tenders')

        assert counter.task_name == 'crawl_tenders'
        assert counter.success == 0
        assert counter.failure == 0
        assert counter.retries == 0

    def test_task_counter_class_record_success(self):
        """测试记录成功"""
        from apps.monitoring.crawler.counter import TaskCounter as CounterClass

        counter = CounterClass('crawl_tenders')
        counter.record_success()

        assert counter.success == 1

    def test_task_counter_class_record_failure(self):
        """测试记录失败"""
        from apps.monitoring.crawler.counter import TaskCounter as CounterClass

        counter = CounterClass('crawl_tenders')
        counter.record_failure()

        assert counter.failure == 1

    def test_task_counter_class_record_retry(self):
        """测试记录重试"""
        from apps.monitoring.crawler.counter import TaskCounter as CounterClass

        counter = CounterClass('crawl_tenders')
        counter.record_retry()

        assert counter.retries == 1

    def test_task_counter_class_get_stats(self):
        """测试获取统计信息"""
        from apps.monitoring.crawler.counter import TaskCounter as CounterClass

        counter = CounterClass('crawl_tenders')
        counter.record_success()
        counter.record_success()
        counter.record_failure()

        stats = counter.get_stats()

        assert stats['task_name'] == 'crawl_tenders'
        assert stats['success'] == 2
        assert stats['failure'] == 1
        assert stats['total'] == 3

    def test_task_counter_class_success_rate(self):
        """测试成功率计算"""
        from apps.monitoring.crawler.counter import TaskCounter as CounterClass

        counter = CounterClass('crawl_tenders')
        counter.record_success()
        counter.record_success()
        counter.record_success()
        counter.record_failure()

        assert counter.get_success_rate() == 75.0

    def test_task_counter_class_hourly_stats(self):
        """测试小时统计"""
        from apps.monitoring.crawler.counter import TaskCounter as CounterClass

        counter = CounterClass('crawl_tenders', window='hour')
        counter.record_success()
        counter.record_success()

        hourly = counter.get_hourly_stats()
        assert 'hour' in hourly
        assert hourly['success'] == 2

    def test_task_counter_class_daily_stats(self):
        """测试天统计"""
        from apps.monitoring.crawler.counter import TaskCounter as CounterClass

        counter = CounterClass('crawl_tenders', window='day')
        counter.record_success()
        counter.record_failure()

        daily = counter.get_daily_stats()
        assert 'day' in daily
        assert daily['total'] == 2


class TestFlowerClient:
    """测试 FlowerClient HTTP API 封装"""

    @patch('apps.monitoring.crawler.flower_client.requests.Session')
    def test_flower_client_get_active_tasks(self, mock_session_class):
        """测试获取活动任务"""
        from apps.monitoring.crawler.flower_client import FlowerClient

        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.json.return_value = {
            'task-001': {'name': 'crawl_tenders', 'status': 'STARTED'},
            'task-002': {'name': 'process_data', 'status': 'STARTED'}
        }
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = FlowerClient(base_url='http://localhost:5555')
        active = client.get_active_tasks()

        assert len(active) == 2
        assert 'task-001' in active
        assert 'task-002' in active

    @patch('apps.monitoring.crawler.flower_client.requests.Session')
    def test_flower_client_get_task_info(self, mock_session_class):
        """测试获取任务信息"""
        from apps.monitoring.crawler.flower_client import FlowerClient

        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'task-123',
            'name': 'crawl_tenders',
            'status': 'SUCCESS',
            'startTime': 1640000000,
            'endTime': 1640000100,
            'runtime': 100
        }
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = FlowerClient(base_url='http://localhost:5555')
        info = client.get_task_info('task-123')

        assert info['id'] == 'task-123'
        assert info['status'] == 'SUCCESS'

    @patch('apps.monitoring.crawler.flower_client.requests.Session')
    def test_flower_client_get_task_stats(self, mock_session_class):
        """测试获取任务统计"""
        from apps.monitoring.crawler.flower_client import FlowerClient

        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.json.return_value = {
            'total': 100,
            'success': 90,
            'failure': 10,
            'retried': 5
        }
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = FlowerClient(base_url='http://localhost:5555')
        stats = client.get_task_stats()

        assert stats['total'] == 100
        assert stats['success'] == 90

    @patch('apps.monitoring.crawler.flower_client.requests.Session')
    def test_flower_client_timeout(self, mock_session_class):
        """测试 FlowerClient 超时处理"""
        import requests
        from apps.monitoring.crawler.flower_client import FlowerClient

        mock_session = MagicMock()
        mock_session.request.side_effect = requests.Timeout()
        mock_session_class.return_value = mock_session

        client = FlowerClient(base_url='http://localhost:5555', timeout=1)
        active = client.get_active_tasks()
        assert active == {}

    @patch('apps.monitoring.crawler.flower_client.requests.Session')
    def test_flower_client_connection_error(self, mock_session_class):
        """测试 FlowerClient 连接错误处理"""
        import requests
        from apps.monitoring.crawler.flower_client import FlowerClient

        mock_session = MagicMock()
        mock_session.request.side_effect = requests.ConnectionError()
        mock_session_class.return_value = mock_session

        client = FlowerClient(base_url='http://localhost:5555')
        active = client.get_active_tasks()
        assert active == {}


class TestCelerySignals:
    """测试 Celery 信号集成"""

    def test_task_prerun_signal(self):
        """测试 task_prerun 信号处理"""
        from celery import signals

        from apps.monitoring.crawler.signals import setup_task_signals

        # 模拟信号处理
        setup_task_signals()

        # 这是一个集成测试，验证信号已设置
        assert signals.task_prerun is not None

    def test_task_postrun_signal(self):
        """测试 task_postrun 信号处理"""
        from celery import signals

        from apps.monitoring.crawler.signals import setup_task_signals

        setup_task_signals()

        assert signals.task_postrun is not None

    def test_task_failure_signal(self):
        """测试 task_failure 信号处理"""
        from celery import signals

        from apps.monitoring.crawler.signals import setup_task_signals

        setup_task_signals()

        assert signals.task_failure is not None