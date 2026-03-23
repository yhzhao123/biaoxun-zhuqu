# Task 014: 重复数据检测测试

## 任务信息

- **任务ID**: 014
- **任务名称**: 重复数据检测测试
- **任务类型**: test
- **依赖任务**: 013 (政府采购网爬虫实现)

## BDD Scenario

```gherkin
Scenario: 检测到重复的招标信息
  Given 数据库中已存在招标公告
  And 爬虫抓取到相似的公告内容
  When 执行重复检测
  Then 应识别出重复/相似的内容
  And 对高相似度内容标记为重复
  And 对疑似重复内容进行人工审核标记
```

## 测试目标

测试重复数据检测系统：基于公告ID的精确匹配、基于内容的相似度检测、疑似重复的人工审核队列。

## 创建的文件

- `apps/crawler/tests/test_duplicate_checker.py` - 重复检测测试
- `apps/crawler/tests/test_similarity.py` - 相似度算法测试
- `apps/crawler/tests/fixtures/duplicate_samples.json` - 重复样本数据

## 测试用例

### Test Case 1: 精确重复检测
```python
def test_exact_duplicate_by_notice_id():
    """基于公告ID的精确重复检测"""
    # Given: 已存在的公告
    existing = TenderNotice.objects.create(
        notice_id='TEST-2024-001',
        title='测试项目招标公告',
        source_url='http://example.com/1'
    )

    # When: 检测重复
    new_data = {'notice_id': 'TEST-2024-001', 'title': '测试项目招标公告'}
    is_duplicate = checker.is_duplicate_by_id(new_data['notice_id'])

    # Then: 应识别为重复
    assert is_duplicate is True
```

### Test Case 2: 标题相似度检测
```python
def test_title_similarity_detection():
    """标题相似度检测"""
    # Given: 相似标题
    title1 = "某市政府采购项目招标公告"
    title2 = "某市政府采购项目招标公告（更正）"

    # When: 计算相似度
    similarity = checker.calculate_similarity(title1, title2)

    # Then: 相似度应超过阈值
    assert similarity > 0.85
```

### Test Case 3: 内容相似度检测
```python
def test_content_similarity_detection():
    """内容相似度检测"""
    content1 = "本项目预算100万元，采购服务器10台..."
    content2 = "本项目预算100万元，采购服务器10台（更正为12台）..."

    similarity = checker.calculate_content_similarity(content1, content2)

    assert similarity > 0.70
```

### Test Case 4: 疑似重复标记
```python
def test_suspected_duplicate_flagging():
    """疑似重复标记"""
    # Given: 中等相似度的内容
    data = {
        'notice_id': 'TEST-2024-002',
        'title': '类似项目招标',
        'similarity_score': 0.65
    }

    # When: 检查并标记
    result = checker.check_and_flag(data)

    # Then: 应标记为疑似重复
    assert result['status'] == 'suspected_duplicate'
    assert result['requires_review'] is True
```

### Test Case 5: 批量重复检测
```python
def test_batch_duplicate_detection():
    """批量重复检测"""
    # Given: 批量数据
    batch_data = [
        {'notice_id': 'DUP-001', 'title': '重复项目'},  # 已存在
        {'notice_id': 'NEW-001', 'title': '新项目'},    # 新数据
        {'notice_id': 'DUP-002', 'title': '重复项目2'}, # 已存在
    ]

    # When: 批量检测
    results = checker.check_batch(batch_data)

    # Then: 正确分类
    assert len(results['duplicates']) == 2
    assert len(results['new']) == 1
```

### Test Case 6: 相似度算法
```python
def test_jaccard_similarity():
    """测试Jaccard相似度算法"""
    text1 = "招标公告 采购项目 服务器"
    text2 = "招标公告 采购项目 网络设备"

    similarity = similarity.jaccard(text1, text2)

    assert 0 < similarity < 1
    assert similarity == 0.5  # 2/4共同词
```

### Test Case 7: 余弦相似度
```python
def test_cosine_similarity():
    """测试余弦相似度算法"""
    text1 = "政府采购项目招标公告"
    text2 = "政府采购项目招标公告（更正版）"

    similarity = similarity.cosine(text1, text2)

    assert similarity > 0.8
```

## 实施步骤

1. 创建测试文件和目录
2. 准备重复样本数据
3. 编写重复检测单元测试
4. 编写相似度算法测试
5. 准备测试夹具

## 验证步骤

```bash
pytest apps/crawler/tests/test_duplicate_checker.py -v
pytest apps/crawler/tests/test_similarity.py -v
```

**预期**: 测试失败，因为重复检测实现不存在

## 提交信息

```
test: add duplicate detection tests

- Test exact duplicate detection by notice_id
- Test title and content similarity detection
- Test suspected duplicate flagging logic
- Test batch duplicate detection workflow
- Test Jaccard and Cosine similarity algorithms
- Add duplicate sample fixtures
- All tests currently failing (RED)
```
