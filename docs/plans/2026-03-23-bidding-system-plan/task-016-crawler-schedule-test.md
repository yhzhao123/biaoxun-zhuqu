# Task 016: 爬虫调度测试

## 任务信息

- **任务ID**: 016
- **任务名称**: 爬虫调度测试
- **任务类型**: test
- **依赖任务**: 015 (重复数据检测实现)

## BDD Scenario

```gherkin
Scenario: 定时调度爬虫任务
  Given Celery Beat已配置
  And 爬虫任务"政府采购网-每日更新"已注册
  When 到达每日凌晨2:00
  Then 应自动触发爬虫任务
  And 任务执行状态应可监控
  And 失败任务应自动重试
```

## 测试目标

测试爬虫调度系统：Celery Beat定时任务、任务监控、失败重试机制。

## 创建的文件

- `apps/crawler/tests/test_scheduler.py` - 调度器测试
- `apps/crawler/tests/test_monitoring.py` - 监控测试
- `apps/crawler/tests/test_retry.py` - 重试机制测试

## 测试用例

### Test Case 1: 定时任务配置
```python
def test_beat_schedule_configuration():
    """测试Celery Beat配置"""
    # Given: Celery配置
    from config.celery import app

    # When: 检查定时任务
    schedule = app.conf.beat_schedule

    # Then: 应包含爬虫任务
    assert 'schedule-crawlers' in schedule
    assert schedule['schedule-crawlers']['task'] == 'apps.crawler.tasks.schedule_crawlers'
```

### Test Case 2: 任务执行
```python
def test_scheduled_task_execution():
    """测试定时任务执行"""
    # Given: 模拟调度
    from apps.crawler.tasks import schedule_crawlers

    # When: 执行任务
    result = schedule_crawlers.delay()

    # Then: 任务应成功
    assert result.successful()
    assert 'scheduled' in result.result
```

### Test Case 3: 任务监控
```python
def test_task_monitoring():
    """测试任务监控"""
    # Given: 运行中的任务
    from apps.crawler.monitoring import TaskMonitor

    monitor = TaskMonitor()

    # When: 获取任务状态
    status = monitor.get_active_tasks()

    # Then: 返回状态信息
    assert 'active' in status
    assert 'scheduled' in status
    assert 'reserved' in status
```

### Test Case 4: 失败重试
```python
def test_task_retry_on_failure():
    """测试失败重试"""
    # Given: 失败的任务
    from apps.crawler.tasks import run_spider

    # When: 任务失败
    # 使用mock模拟失败
    with patch('apps.crawler.tasks.run_spider.run') as mock_run:
        mock_run.side_effect = Exception("Network error")

        # Then: 应触发重试
        task = run_spider.delay('gov_spider', {})
        # 验证重试次数
```

### Test Case 5: 任务超时检测
```python
def test_task_timeout_detection():
    """测试任务超时检测"""
    # Given: 长时间运行的任务
    from apps.crawler.models import CrawlJob, CrawlStatus

    job = CrawlJob.objects.create(
        task_id='timeout-test',
        spider_name='gov_spider',
        status=CrawlStatus.RUNNING,
        started_at=timezone.now() - timedelta(hours=5)
    )

    # When: 检查超时
    from apps.crawler.tasks import check_crawler_health
    result = check_crawler_health.delay()

    # Then: 任务应被标记为停滞
    job.refresh_from_db()
    assert job.status == CrawlStatus.STALLED
```

### Test Case 6: 并发控制
```python
def test_concurrent_task_limit():
    """测试并发任务限制"""
    # Given: 多个任务请求
    from apps.crawler.scheduler import TaskScheduler

    scheduler = TaskScheduler()

    # When: 超过并发限制
    for i in range(10):
        scheduler.submit_task(f'spider_{i}', {})

    # Then: 应限制并发数
    active_count = scheduler.get_active_count()
    assert active_count <= scheduler.max_concurrent
```

### Test Case 7: 任务优先级
```python
def test_task_priority():
    """测试任务优先级"""
    from apps.crawler.scheduler import TaskScheduler

    scheduler = TaskScheduler()

    # When: 提交不同优先级任务
    scheduler.submit_task('urgent_spider', {}, priority=9)
    scheduler.submit_task('normal_spider', {}, priority=5)

    # Then: 高优先级任务应先执行
    queue = scheduler.get_task_queue()
    assert queue[0]['priority'] >= queue[1]['priority']
```

## 实施步骤

1. 创建测试文件
2. 编写调度器单元测试
3. 编写监控测试
4. 编写重试机制测试
5. 准备测试配置

## 验证步骤

```bash
pytest apps/crawler/tests/test_scheduler.py -v
pytest apps/crawler/tests/test_monitoring.py -v
pytest apps/crawler/tests/test_retry.py -v
```

**预期**: 测试失败，因为调度系统实现不存在

## 提交信息

```
test: add crawler scheduler tests

- Test Celery Beat schedule configuration
- Test scheduled task execution
- Test task monitoring and status tracking
- Test retry mechanism on failure
- Test task timeout detection
- Test concurrent task limiting
- Test task priority handling
- All tests currently failing (RED)
```
