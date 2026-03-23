# Task 024: 行业分类测试

## 任务信息

- **任务ID**: 024
- **任务名称**: 行业分类测试
- **任务类型**: test
- **依赖任务**: 023 (NLP置信度实现)

## BDD Scenario

```gherkin
Scenario: 自动识别招标所属行业
  Given 招标文本内容：
    """
    某市人民医院CT设备采购项目招标公告
    采购内容：64排螺旋CT 1台
    预算金额：800万元
    """
  When 系统执行行业分类分析
  Then 应识别出行业为"医疗健康"
  And 置信度应大于0.80
```

## 测试目标

测试行业自动分类功能，基于招标标题和描述内容智能识别所属行业领域。

## 创建的文件

- `apps/analysis/tests/test_industry_classifier.py` - 行业分类器测试

## 测试用例

### Test Case 1: 医疗健康行业识别
```python
def test_classify_healthcare_industry():
    """从医疗设备采购文本中识别医疗健康行业"""
    # Given: 医疗设备采购的招标公告
    text = """
    某市人民医院CT设备采购项目招标公告
    采购内容：64排螺旋CT 1台，用于放射科诊断
    预算金额：800万元
    """

    # When: 执行行业分类
    result = industry_classifier.classify(text)

    # Then: 应识别为医疗健康行业
    assert result['industry'] == "医疗健康"
    assert result['industry_code'] == "F06"
    assert result['confidence'] > 0.80
```

### Test Case 2: IT信息技术行业识别
```python
def test_classify_it_industry():
    """从软件开发项目中识别IT行业"""
    text = """
    某市政府智慧政务平台建设项目招标公告
    采购内容：政务云平台软件开发服务
    技术要求：云计算、大数据、微服务架构
    """

    result = industry_classifier.classify(text)

    assert result['industry'] == "信息技术"
    assert result['industry_code'] == "I65"
    assert result['confidence'] > 0.80
```

### Test Case 3: 建筑工程行业识别
```python
def test_classify_construction_industry():
    """从工程项目中识别建筑行业"""
    text = """
    某学校教学楼新建工程招标公告
    建设内容：教学楼土建、装修、机电安装
    建筑面积：15000平方米
    """

    result = industry_classifier.classify(text)

    assert result['industry'] == "建筑工程"
    assert result['industry_code'] == "E47"
    assert result['confidence'] > 0.80
```

### Test Case 4: 模糊内容处理
```python
def test_handle_ambiguous_industry():
    """处理行业不明确的文本"""
    text = "本项目欢迎各供应商参与投标"

    result = industry_classifier.classify(text)

    assert result['industry'] is None
    assert result['confidence'] < 0.50
```

### Test Case 5: 多行业混合识别
```python
def test_classify_mixed_industry_content():
    """从包含多行业关键词的文本中选择最匹配的行业"""
    text = """
    智慧医院信息化建设项目
    包含：医疗设备采购、软件系统开发、网络基础设施建设
    """

    result = industry_classifier.classify(text)

    # 应以主要内容（医疗健康）为主
    assert result['industry'] in ["医疗健康", "信息技术"]
    assert result['secondary_industries'] is not None
```

## 实施步骤

1. 创建测试文件和目录
2. 使用 pytest 标记测试
3. 使用参数化测试覆盖多种行业场景
4. 运行测试确认失败(RED状态)

## 验证步骤

```bash
pytest apps/analysis/tests/test_industry_classifier.py::test_classify_healthcare_industry -v
pytest apps/analysis/tests/test_industry_classifier.py::test_classify_it_industry -v
pytest apps/analysis/tests/test_industry_classifier.py::test_classify_construction_industry -v
```

**预期**: 测试失败，因为行业分类器未实现

## 提交信息

```
test: add industry classification tests

- Test healthcare industry recognition
- Test IT industry recognition
- Test construction industry recognition
- Test ambiguous content handling
- Test multi-industry content classification
- All tests currently failing (RED)
```
