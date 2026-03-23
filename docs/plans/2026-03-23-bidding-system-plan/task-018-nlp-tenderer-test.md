# Task 018: 招标人提取测试

## 任务信息

- **任务ID**: 018
- **任务名称**: 招标人提取测试
- **任务类型**: test
- **依赖任务**: 009 (Repository层实现)

## BDD Scenario

```gherkin
Scenario: 提取招标人信息
  Given 招标文本内容：
    """
    某市人民医院医疗设备采购项目招标公告
    招标人：某市人民医院
    招标代理机构：某招标代理有限公司
    """
  When 系统执行NLP实体提取
  Then 应识别出招标人为"某市人民医院"
  And 置信度应大于0.85
```

## 测试目标

测试NLP服务从招标文本中提取招标人实体的功能。

## 创建的文件

- `apps/analysis/tests/test_nlp_service.py` - NLP服务测试

## 测试用例

### Test Case 1: 标准格式提取
```python
def test_extract_tenderer_from_standard_format():
    """从标准格式文本中提取招标人"""
    # Given: 标准格式的招标公告文本
    text = """
    某市人民医院医疗设备采购项目招标公告
    招标人：某市人民医院
    招标代理机构：某招标代理有限公司
    """

    # When: 执行NLP提取
    result = nlp_service.extract_tenderer(text)

    # Then: 应识别出招标人
    assert result['entity'] == "某市人民医院"
    assert result['confidence'] > 0.85
```

### Test Case 2: 采购单位格式
```python
def test_extract_tenderer_from_procurement_format():
    """从'采购单位'格式中提取"""
    text = "采购单位：某市教育局信息中心"

    result = nlp_service.extract_tenderer(text)

    assert result['entity'] == "某市教育局信息中心"
    assert result['confidence'] > 0.85
```

### Test Case 3: 模糊文本处理
```python
def test_handle_ambiguous_tenderer():
    """处理招标人不明确的文本"""
    text = "本项目欢迎各投标人参与"

    result = nlp_service.extract_tenderer(text)

    assert result['entity'] is None
    assert result['confidence'] < 0.6
```

### Test Case 4: 多个候选处理
```python
def test_select_best_tenderer_candidate():
    """从多个候选中选择最佳招标人"""
    text = """
    委托单位：某市政府
    采购单位：某市交通运输局
    代理机构：某招标代理公司
    """

    result = nlp_service.extract_tenderer(text)

    # 应选择'采购单位'而非'委托单位'
    assert "交通运输局" in result['entity']
```

## 实施步骤

1. 创建测试文件和目录
2. 使用 pytest 标记测试
3. 使用参数化测试覆盖多种场景
4. 运行测试确认失败(RED状态)

## 验证步骤

```bash
pytest apps/analysis/tests/test_nlp_service.py::test_extract_tenderer_from_standard_format -v
pytest apps/analysis/tests/test_nlp_service.py::test_extract_tenderer_from_procurement_format -v
pytest apps/analysis/tests/test_nlp_service.py::test_handle_ambiguous_tenderer -v
```

**预期**: 测试失败，因为NLP服务未实现

## 提交信息

```
test: add NLP tenderer extraction tests

- Test standard format extraction
- Test alternative format (采购单位)
- Test ambiguous text handling
- Test multi-candidate selection
- All tests currently failing (RED)
```
