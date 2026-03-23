# Task 010: 爬虫基础架构测试

## 任务信息

- **任务ID**: 010
- **任务名称**: 爬虫基础架构测试
- **任务类型**: test
- **依赖任务**: 007 (招标模型实现)

## BDD Scenario

```gherkin
Scenario: 爬虫基础架构正常工作
  Given 爬虫系统已初始化
  And Celery任务队列已配置
  When 创建新的爬虫任务
  Then 应支持Scrapy集成
  And 应支持Celery分布式调度
  And 爬虫状态应可监控
```

## 测试目标

测试爬虫基础架构的核心组件：BaseSpider类、Scrapy集成和Celery任务调度。

## 创建的文件

- `apps/crawler/tests/test_base_spider.py` - BaseSpider基础测试
- `apps/crawler/tests/test_celery_tasks.py` - Celery任务测试
- `apps/crawler/tests/fixtures/` - 测试夹具目录

## 测试用例

### Test Case 1: BaseSpider初始化
```python
def test_base_spider_initialization():
    """测试BaseSpider基类初始化"""
    # Given: 爬虫配置
    config = {
        'name': 'test_spider',
        'start_urls': ['http://example.com'],
        'max_pages': 10
    }

    # When: 创建爬虫实例
    spider = BaseSpider(**config)

    # Then: 属性正确设置
    assert spider.name == 'test_spider'
    assert spider.start_urls == ['http://example.com']
    assert spider.max_pages == 10
```

### Test Case 2: Scrapy集成
```python
def test_scrapy_integration():
    """测试Scrapy框架集成"""
    # Given: Scrapy spider类
    from scrapy import Spider

    # When: 检查继承关系
    spider = GovSpider()

    # Then: 应继承自Scrapy Spider
    assert isinstance(spider, Spider)
    assert hasattr(spider, 'start_requests')
```

### Test Case 3: Celery任务注册
```python
def test_celery_task_registration():
    """测试Celery任务正确注册"""
    # Given: Celery应用
    from celery import current_app

    # When: 检查注册的任务
    tasks = current_app.tasks

    # Then: 爬虫任务应存在
    assert 'apps.crawler.tasks.run_spider' in tasks
    assert 'apps.crawler.tasks.schedule_crawlers' in tasks
```

### Test Case 4: 爬虫状态监控
```python
def test_crawler_status_tracking():
    """测试爬虫状态追踪"""
    # Given: 运行中的爬虫任务
    task_id = 'test-task-001'

    # When: 获取状态
    status = get_crawler_status(task_id)

    # Then: 状态信息完整
    assert 'status' in status
    assert 'start_time' in status
    assert 'pages_crawled' in status
    assert 'items_extracted' in status
```

### Test Case 5: 配置验证
```python
def test_spider_config_validation():
    """测试爬虫配置验证"""
    # Given: 无效配置
    invalid_config = {'name': '', 'start_urls': []}

    # When/Then: 应抛出验证错误
    with pytest.raises(ValidationError):
        BaseSpider(**invalid_config)
```

## 实施步骤

1. 创建测试目录结构
2. 编写BaseSpider单元测试
3. 编写Celery任务测试
4. 编写集成测试
5. 准备测试配置

## 验证步骤

```bash
pytest apps/crawler/tests/test_base_spider.py -v
pytest apps/crawler/tests/test_celery_tasks.py -v
```

**预期**: 测试失败，因为基础架构实现不存在

## 提交信息

```
test: add crawler base architecture tests

- Test BaseSpider initialization and configuration
- Test Scrapy framework integration
- Test Celery task registration
- Test crawler status tracking
- Add config validation tests
- All tests currently failing (RED)
```
