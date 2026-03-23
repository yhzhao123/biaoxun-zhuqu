# Task 026: 地区分类测试

## 任务信息

- **任务ID**: 026
- **任务名称**: 地区分类测试
- **任务类型**: test
- **依赖任务**: 023 (NLP置信度实现)

## BDD Scenario

```gherkin
Scenario: 自动识别招标所属地区
  Given 招标文本内容：
    """
    北京市海淀区智慧城市建设项目招标公告
    采购单位：北京市海淀区政务服务管理局
    项目地点：海淀区中关村大街
    """
  When 系统执行地区分类分析
  Then 应识别出地区为"北京市-海淀区"
  And 置信度应大于0.85
```

## 测试目标

测试地区自动分类功能，基于招标标题、描述和招标人信息智能识别所属行政区域。

## 创建的文件

- `apps/analysis/tests/test_region_classifier.py` - 地区分类器测试

## 测试用例

### Test Case 1: 省级地区识别
```python
def test_classify_province_region():
    """从文本中识别省级地区"""
    # Given: 包含省级信息的招标公告
    text = """
    广东省交通基础设施建设项目招标公告
    采购单位：广东省交通运输厅
    """

    # When: 执行地区分类
    result = region_classifier.classify(text)

    # Then: 应识别为广东省
    assert result['province'] == "广东省"
    assert result['province_code'] == "440000"
    assert result['confidence'] > 0.85
```

### Test Case 2: 市级地区识别
```python
def test_classify_city_region():
    """从文本中识别市级地区"""
    text = """
    深圳市政务云平台建设项目
    采购单位：深圳市政务服务数据管理局
    """

    result = region_classifier.classify(text)

    assert result['province'] == "广东省"
    assert result['city'] == "深圳市"
    assert result['city_code'] == "440300"
    assert result['confidence'] > 0.85
```

### Test Case 3: 区县级地区识别
```python
def test_classify_district_region():
    """从文本中识别区县级地区"""
    text = """
    杭州市西湖区智慧校园建设项目
    采购单位：杭州市西湖区教育局
    项目地点：西湖区文三路
    """

    result = region_classifier.classify(text)

    assert result['province'] == "浙江省"
    assert result['city'] == "杭州市"
    assert result['district'] == "西湖区"
    assert result['district_code'] == "330106"
    assert result['confidence'] > 0.85
```

### Test Case 4: 地址文本提取
```python
def test_extract_address_from_text():
    """从详细地址文本中提取地区信息"""
    text = """
    项目地点：江苏省南京市鼓楼区中山路1号
    交货地点：上海浦东新区张江高科技园区
    """

    result = region_classifier.classify(text)

    assert result['province'] == "江苏省"
    assert result['city'] == "南京市"
    assert result['district'] == "鼓楼区"
    assert result['addresses'] is not None
```

### Test Case 5: 多地区冲突处理
```python
def test_resolve_multiple_regions():
    """处理文本中多个地区信息冲突的情况"""
    text = """
    采购单位：北京市财政局
    项目地点：河北省石家庄市
    交货地点：天津市滨海新区
    """

    result = region_classifier.classify(text)

    # 应以采购单位所在地区为主
    assert result['province'] == "北京市"
    assert result['mentioned_regions'] is not None
```

### Test Case 6: 地区别名识别
```python
def test_recognize_region_aliases():
    """识别地区别名和简称"""
    text = """
    沪上某医院医疗设备采购项目
    采购单位：申城医疗集团
    """

    result = region_classifier.classify(text)

    # "沪"和"申城"都是上海的别名
    assert result['province'] == "上海市"
```

## 实施步骤

1. 创建测试文件和目录
2. 使用 pytest 标记测试
3. 使用参数化测试覆盖多级行政区划
4. 运行测试确认失败(RED状态)

## 验证步骤

```bash
pytest apps/analysis/tests/test_region_classifier.py::test_classify_province_region -v
pytest apps/analysis/tests/test_region_classifier.py::test_classify_city_region -v
pytest apps/analysis/tests/test_region_classifier.py::test_classify_district_region -v
```

**预期**: 测试失败，因为地区分类器未实现

## 提交信息

```
test: add region classification tests

- Test province-level region recognition
- Test city-level region recognition
- Test district-level region recognition
- Test address text extraction
- Test multi-region conflict resolution
- Test region alias recognition
- All tests currently failing (RED)
```
