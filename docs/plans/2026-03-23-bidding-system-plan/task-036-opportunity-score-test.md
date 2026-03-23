# Task 036: 商机评分测试

## 任务信息

- **任务ID**: 036
- **任务名称**: 商机评分测试
- **任务类型**: test
- **依赖任务**: 009 (Repository层实现)

## BDD Scenario

```gherkin
Scenario: 生成商机评分
  Given 用户关注关键词为"医疗设备、信息化"
  And 招标信息为"某县人民医院智慧医疗系统建设项目"
  And 预算金额为500万
  And 距离截止还有30天
  When 系统计算商机评分
  Then 评分应大于70分
  And 应标记为"高优先级商机"
```

## 测试目标

测试商机评分算法的多因子加权计算功能。

## 创建的文件

- `apps/analysis/tests/test_opportunity_scoring.py` - 商机评分测试

## 测试用例

### Test Case 1: 高价值商机
```python
def test_high_value_opportunity_scoring():
    """高价值招标应获得高分"""
    # Given: 匹配度高、预算大、时间充裕的招标
    tender = {
        'title': '某县人民医院智慧医疗系统建设项目',
        'description': '医疗设备、信息化系统建设',
        'budget': 5000000,
        'publish_date': '2024-03-01',
        'deadline_date': '2024-04-01',  # 30天后
    }
    user = {'keywords': ['医疗设备', '信息化']}

    # When: 计算评分
    score = scoring_service.calculate(tender, user)

    # Then: 应获得高分
    assert score['total'] > 70
    assert score['priority'] == '高优先级商机'
```

### Test Case 2: 时效性评分
```python
def test_time_urgency_scoring():
    """测试时效性评分因子"""
    # Given: 即将截止的招标
    tender = {'deadline_date': '2024-03-24'}  # 1天后截止

    # When: 计算时效性评分
    time_score = scoring_service._calculate_time_urgency(tender)

    # Then: 应获得高分(100分)
    assert time_score == 100.0
```

### Test Case 3: 匹配度评分
```python
def test_match_scoring():
    """测试匹配度评分因子"""
    tender_text = '医疗设备采购项目'
    user_keywords = ['医疗设备', '信息化']

    match_score = scoring_service._calculate_match_score(
        tender_text, user_keywords
    )

    assert match_score > 80  # 至少80%匹配
```

### Test Case 4: 评分因子分解
```python
def test_score_breakdown():
    """验证评分因子分解正确"""
    tender = {...}
    user = {...}

    score = scoring_service.calculate(tender, user)

    # 验证分解包含所有因子
    assert 'time' in score['breakdown']
    assert 'match' in score['breakdown']
    assert 'competition' in score['breakdown']
    assert 'value' in score['breakdown']
    assert 'win_rate' in score['breakdown']

    # 验证总分等于加权和
    expected_total = sum(score['breakdown'].values()) / 5
    assert abs(score['total'] - expected_total) < 1
```

## 实施步骤

1. 创建测试目录和文件
2. 定义测试数据工厂
3. 编写各评分因子测试
4. 运行测试确认失败

## 验证步骤

```bash
pytest apps/analysis/tests/test_opportunity_scoring.py -v
```

**预期**: 测试失败，因为评分服务未实现

## 提交信息

```
test: add opportunity scoring algorithm tests

- Test high-value opportunity scoring
- Test time urgency factor calculation
- Test match score calculation
- Test score breakdown structure
- All tests currently failing (RED)
```
