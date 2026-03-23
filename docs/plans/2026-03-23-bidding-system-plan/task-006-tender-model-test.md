# Task 006: 招标模型测试

## 任务信息

- **任务ID**: 006
- **任务名称**: 招标模型测试
- **任务类型**: test
- **依赖任务**: 004 (创建基础模型和Admin)

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

编写招标信息模型(TenderNotice)的单元测试，验证模型字段、约束和业务方法。

## 创建的文件

- `apps/tenders/tests/test_models.py` - 模型单元测试

## 测试用例

### Test Case 1: 模型字段验证
```python
def test_tender_notice_has_required_fields():
    """验证招标模型包含所有必需字段"""
    # Arrange: 创建招标实例
    # Act: 检查字段存在性
    # Assert: 验证 title, notice_id, tenderer 等字段存在
```

### Test Case 2: 唯一性约束
```python
def test_notice_id_must_be_unique():
    """验证notice_id字段的唯一性约束"""
    # Arrange: 创建一个招标记录
    # Act: 尝试创建相同notice_id的记录
    # Assert: 应抛出 IntegrityError
```

### Test Case 3: 默认值验证
```python
def test_default_values():
    """验证字段默认值"""
    # Arrange: 创建最小字段的招标实例
    # Assert: 验证 status='pending', currency='CNY' 等默认值
```

### Test Case 4: 字符串表示
```python
def test_str_representation():
    """验证模型的字符串表示"""
    # Arrange: 创建招标实例
    # Assert: str(tender) 应包含 notice_id 和 title
```

### Test Case 5: 状态流转
```python
def test_status_transitions():
    """验证状态字段的可选值"""
    # Assert: 验证 Status.choices 包含 pending, processed, analyzed
```

## 实施步骤

1. **创建测试文件**
   ```bash
   touch apps/tenders/tests/__init__.py
   touch apps/tenders/tests/test_models.py
   ```

2. **编写测试类**
   - 使用 `pytest.mark.django_db` 标记
   - 使用 factory_boy 创建测试数据
   - 测试所有模型字段和约束

3. **运行测试**
   ```bash
   pytest apps/tenders/tests/test_models.py -v
   ```

## 验证步骤

运行测试命令:
```bash
pytest apps/tenders/tests/test_models.py::test_tender_notice_has_required_fields -v
pytest apps/tenders/tests/test_models.py::test_notice_id_must_be_unique -v
pytest apps/tenders/tests/test_models.py::test_default_values -v
pytest apps/tenders/tests/test_models.py::test_str_representation -v
pytest apps/tenders/tests/test_models.py::test_status_transitions -v
```

**预期结果**: 所有测试失败(RED状态)，因为模型尚未实现

## 提交信息

```
test: add TenderNotice model tests

- Test required fields (title, notice_id, tenderer)
- Test unique constraint on notice_id
- Test default values (status, currency)
- Test status choices
- All tests currently failing (RED state)
```
