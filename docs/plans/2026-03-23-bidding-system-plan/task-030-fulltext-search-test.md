# Task 030: 全文搜索测试

## 任务信息

- **任务ID**: 030
- **任务名称**: 全文搜索测试
- **任务类型**: test
- **依赖任务**: 009 (Repository层实现)

## BDD Scenario

```gherkin
Scenario: 关键词全文搜索
  Given 数据库中有10000条招标记录
  When 用户搜索关键词"云计算"
  Then 应在1秒内返回结果
  And 结果应包含标题或描述中包含"云计算"的记录
  And 应按相关性排序
```

## 测试目标

测试招标信息的全文搜索功能，包括搜索速度、准确性和排序。

## 创建的文件

- `apps/tenders/tests/test_search.py` - 搜索功能测试

## 测试用例

### Test Case 1: 标题搜索
```python
def test_search_by_title():
    """按标题关键词搜索"""
    # Given: 创建测试数据
    TenderFactory(title='云计算平台建设项目')
    TenderFactory(title='医疗设备采购')

    # When: 搜索'云计算'
    results = search_service.search(keywords='云计算')

    # Then: 应返回匹配的招标
    assert len(results) == 1
    assert '云计算' in results[0].title
```

### Test Case 2: 描述搜索
```python
def test_search_by_description():
    """按描述关键词搜索"""
    TenderFactory(
        title='信息化项目',
        description='本项目采用云计算技术构建'
    )

    results = search_service.search(keywords='云计算')

    assert len(results) == 1
```

### Test Case 3: 性能测试
```python
def test_search_performance():
    """搜索响应时间应小于1秒"""
    # Given: 创建10000条测试数据
    TenderFactory.create_batch(10000)

    # When: 执行搜索并计时
    start = time.time()
    results = search_service.search(keywords='设备')
    elapsed = time.time() - start

    # Then: 应在1秒内返回
    assert elapsed < 1.0
```

### Test Case 4: 排序验证
```python
def test_search_results_sorted_by_relevance():
    """结果按相关性排序"""
    # Given: 创建不同相关度的数据
    tender_high = TenderFactory(
        title='云计算平台',
        ai_keywords=['云计算', '平台']
    )
    tender_low = TenderFactory(
        title='普通项目',
        description='可能涉及云计算'
    )

    # When: 搜索
    results = search_service.search(keywords='云计算平台')

    # Then: 高相关性应在前面
    assert results[0].id == tender_high.id
```

### Test Case 5: 分页测试
```python
def test_search_pagination():
    """搜索结果分页"""
    TenderFactory.create_batch(50)

    page1 = search_service.search(keywords='', page=1, per_page=20)
    page2 = search_service.search(keywords='', page=2, per_page=20)

    assert len(page1) == 20
    assert len(page2) == 20
    assert page1[0].id != page2[0].id
```

## 实施步骤

1. 创建测试文件
2. 使用 Factory Boy 批量创建测试数据
3. 编写搜索测试用例
4. 添加性能测试

## 验证步骤

```bash
pytest apps/tenders/tests/test_search.py -v
```

**预期**: 测试失败，因为搜索服务未实现

## 提交信息

```
test: add full-text search tests

- Test title keyword search
- Test description keyword search
- Test search performance (<1s)
- Test relevance-based sorting
- Test pagination
- All tests currently failing (RED)
```
