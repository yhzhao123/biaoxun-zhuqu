# Task 012: 政府采购网爬虫测试

## 任务信息

- **任务ID**: 012
- **任务名称**: 政府采购网爬虫测试
- **任务类型**: test
- **依赖任务**: 011 (爬虫基础架构实现)

## BDD Scenario

```gherkin
Scenario: 成功爬取政府采购网信息
  Given 爬虫任务"政府采购网-每日更新"已配置
  And 目标URL为"http://www.ccgp.gov.cn/"
  When 爬虫在每日凌晨2:00启动
  Then 应在4小时内完成爬取
  And 成功提取的招标信息数量应大于0
  And 所有提取的数据应包含title、notice_id、tenderer字段
```

## 测试目标

测试政府采购网爬虫的页面解析和数据提取功能。

## 创建的文件

- `apps/crawler/tests/test_gov_spider.py` - 政府网爬虫测试

## 测试用例

### Test Case 1: 列表页解析
```python
def test_parse_list_page():
    """解析招标列表页"""
    # Given: 模拟列表页HTML
    html = load_fixture('gov_list_page.html')

    # When: 解析列表
    items = spider.parse_list(html)

    # Then: 应提取招标链接
    assert len(items) > 0
    assert all('url' in item for item in items)
    assert all('title' in item for item in items)
```

### Test Case 2: 详情页解析
```python
def test_parse_detail_page():
    """解析招标详情页"""
    html = load_fixture('gov_detail_page.html')

    data = spider.parse_detail(html)

    assert data['title'] is not None
    assert data['notice_id'] is not None
    assert data['tenderer'] is not None
    assert data['publish_date'] is not None
```

### Test Case 3: 反爬处理
```python
@pytest.mark.vcr
def test_handle_rate_limit():
    """处理请求频率限制"""
    # Given: 模拟429响应
    responses.add(responses.GET, URL, status=429)

    # When: 执行爬取
    result = spider.crawl_with_retry(URL)

    # Then: 应重试并最终成功
    assert result is not None
```

### Test Case 4: 数据标准化
```python
def test_normalize_extracted_data():
    """验证提取数据的标准化"""
    raw_data = {
        'title': '  某项目招标公告  ',
        'budget': '¥1,000,000.00',
        'date': '2024年03月23日'
    }

    normalized = spider.normalize_data(raw_data)

    assert normalized['title'] == '某项目招标公告'
    assert normalized['budget'] == 1000000.00
    assert normalized['date'] == '2024-03-23'
```

## 实施步骤

1. 创建测试目录和文件
2. 准备HTML测试夹具
3. 编写解析测试用例
4. 使用responses库模拟HTTP

## 验证步骤

```bash
pytest apps/crawler/tests/test_gov_spider.py -v
```

**预期**: 测试失败，因为爬虫实现不存在

## 提交信息

```
test: add gov.cn spider tests

- Test list page parsing
- Test detail page parsing
- Test rate limit handling
- Test data normalization
- Add HTML fixtures
- All tests currently failing (RED)
```
