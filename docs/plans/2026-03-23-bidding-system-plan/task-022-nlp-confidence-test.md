# Task 022: NLP置信度处理测试

## Task Header
- **ID**: 022
- **Name**: NLP置信度处理测试
- **Type**: test
- **Depends-on**: 018
- **Status**: pending
- **Created**: 2026-03-23

## Description

为置信度处理模块编写全面的测试用例，确保NLP实体提取的置信度评分机制能够准确反映提取结果的可信程度。置信度处理是NLP模块的核心组件，直接影响最终输出结果的可靠性。

测试需要覆盖置信度计算、阈值控制、模糊实体处理、置信度校准等多个方面，确保系统能够正确处理高置信度、低置信度和边界情况。

## Files to Create/Modify

### New Files
- `tests/nlp/test_confidence_handler.py` - 置信度处理器主测试文件
- `tests/nlp/fixtures/confidence_test_cases.json` - 置信度测试用例数据
- `tests/nlp/test_fuzzy_entity_handler.py` - 模糊实体处理测试

### Modify Files
- `tests/nlp/conftest.py` - 添加置信度处理相关fixtures
- `tests/nlp/test_config.py` - 添加置信度配置测试

## Implementation Steps

### Step 1: 准备测试数据
在 `fixtures/confidence_test_cases.json` 中定义测试用例：

```json
{
  "test_cases": [
    {
      "id": "TC001",
      "name": "高置信度直接提取",
      "entity_type": "tenderer",
      "input_text": "招标人：北京市某某建设有限公司",
      "regex_match": {"score": 0.95, "pattern": "招标人：(.+?)公司"},
      "llm_result": null,
      "expected_confidence": 0.95,
      "expected_action": "accept",
      "expected_entity": "北京市某某建设有限公司"
    },
    {
      "id": "TC002",
      "name": "低置信度正则需LLM兜底",
      "entity_type": "tenderer",
      "input_text": "业主为某科技公司",
      "regex_match": {"score": 0.45, "pattern": "业主为(.+?)(公司|单位)"},
      "llm_result": {"entity": "某科技公司", "score": 0.88},
      "expected_confidence": 0.88,
      "expected_action": "accept",
      "expected_entity": "某科技公司"
    },
    {
      "id": "TC003",
      "name": "正则与LLM冲突",
      "entity_type": "amount",
      "input_text": "预算约100万元",
      "regex_match": {"value": "100", "score": 0.75},
      "llm_result": {"value": "1000000", "score": 0.82},
      "expected_confidence": 0.82,
      "expected_action": "accept_llm",
      "expected_entity": "1000000"
    },
    {
      "id": "TC004",
      "name": "双低置信度拒绝",
      "entity_type": "date",
      "input_text": "预计明年某时开标",
      "regex_match": null,
      "llm_result": {"date": "2026年", "score": 0.35},
      "expected_confidence": 0.35,
      "expected_action": "reject",
      "expected_entity": null
    },
    {
      "id": "TC005",
      "name": "模糊实体匹配",
      "entity_type": "tenderer",
      "input_text": "招标人为中建集团",
      "existing_entities": ["中国建筑集团有限公司", "中建三局"],
      "expected_match": "中国建筑集团有限公司",
      "expected_similarity": 0.85,
      "expected_action": "fuzzy_match"
    }
  ]
}
```

### Step 2: 实现置信度计算测试
在 `test_confidence_handler.py` 中创建测试类：

```python
class TestConfidenceCalculator:
    """置信度计算测试"""

    def test_calculate_from_regex_match(self):
        """测试基于正则匹配的置信度计算"""
        # 验证：
        # - 完整匹配 vs 部分匹配
        # - 模糊匹配（编辑距离）
        # - 上下文完整性
        pass

    def test_calculate_from_llm_result(self):
        """测试基于LLM结果的置信度计算"""
        # 验证：
        # - LLM原始置信度
        # - 与正则结果的一致性修正
        pass

    def test_calculate_combined_confidence(self):
        """测试组合置信度计算"""
        # 验证：
        # - 正则+LLM双重验证的置信度提升
        # - 冲突情况的处理
        pass

    def test_confidence_with_context(self):
        """测试基于上下文的置信度调整"""
        # 验证：
        # - 上下文完整性检查
        # - 关键词邻近度
        pass
```

### Step 3: 实现阈值控制测试
```python
class TestConfidenceThreshold:
    """置信度阈值控制测试"""

    def test_high_confidence_threshold(self):
        """测试高置信度阈值（直接接受）"""
        # ACCEPT_THRESHOLD = 0.85
        pass

    def test_medium_confidence_threshold(self):
        """测试中置信度阈值（人工审核）"""
        # REVIEW_THRESHOLD = 0.60
        pass

    def test_low_confidence_reject(self):
        """测试低置信度拒绝"""
        # < REVIEW_THRESHOLD 直接拒绝
        pass

    def test_threshold_configurability(self):
        """测试阈值可配置性"""
        # 验证可以从配置动态调整
        pass
```

### Step 4: 实现模糊实体处理测试
在 `test_fuzzy_entity_handler.py` 中创建：

```python
class TestFuzzyEntityHandler:
    """模糊实体匹配测试"""

    def test_exact_match(self):
        """测试精确匹配"""
        # 相似度 = 1.0
        pass

    def test_fuzzy_match_high_similarity(self):
        """测试高相似度模糊匹配"""
        # 相似度 >= 0.80
        pass

    def test_fuzzy_match_medium_similarity(self):
        """测试中相似度模糊匹配"""
        # 0.60 <= 相似度 < 0.80
        pass

    def test_fuzzy_match_low_similarity(self):
        """测试低相似度（不匹配）"""
        # 相似度 < 0.60
        pass

    def test_similarity_algorithms(self):
        """测试不同相似度算法"""
        # - Levenshtein距离
        # - Jaro-Winkler
        # - 余弦相似度
        pass

    def test_entity_deduplication(self):
        """测试实体去重"""
        # 验证模糊匹配后的去重逻辑
        pass
```

### Step 5: 实现置信度校准测试
```python
class TestConfidenceCalibration:
    """置信度校准测试"""

    def test_calibration_with_historical_data(self):
        """测试基于历史数据的校准"""
        pass

    def test_temperature_scaling(self):
        """测试温度缩放校准"""
        pass

    def test_platt_scaling(self):
        """测试Platt缩放校准"""
        pass
```

### Step 6: 添加Fixtures
修改 `conftest.py`：

```python
@pytest.fixture
def confidence_handler():
    """置信度处理器fixture"""
    from src.nlp.confidence import ConfidenceHandler
    return ConfidenceHandler()

@pytest.fixture
def fuzzy_entity_handler():
    """模糊实体处理器fixture"""
    from src.nlp.fuzzy import FuzzyEntityHandler
    return FuzzyEntityHandler()

@pytest.fixture
def sample_test_cases():
    """加载测试用例"""
    import json
    with open('tests/nlp/fixtures/confidence_test_cases.json') as f:
        return json.load(f)
```

### Step 7: 定义通过标准

**覆盖率要求：**
- 代码覆盖率 >= 90%
- 分支覆盖率 >= 85%

**准确率要求：**
- 置信度评分与实际准确率相关性 >= 0.85
- 模糊匹配准确率 >= 90%
- 阈值决策准确率 >= 95%

**性能要求：**
- 单条置信度计算 < 10ms
- 批量1000条处理 < 5s

## Verification Steps

1. **运行测试**
   ```bash
   pytest tests/nlp/test_confidence_handler.py -v
   pytest tests/nlp/test_fuzzy_entity_handler.py -v
   ```

2. **覆盖率报告**
   ```bash
   pytest --cov=src.nlp.confidence --cov-report=html
   ```

3. **验证校准效果**
   - 检查置信度与实际准确率的对应关系
   - 确保高置信度（>0.9）对应高准确率（>95%）

4. **边界测试**
   - 空值处理
   - 极端置信度值（0.0, 1.0）
   - 并发处理

## Git Commit Message

```
test: add comprehensive tests for NLP confidence handling

- Add confidence calculation tests for regex and LLM results
- Implement threshold control test cases
- Add fuzzy entity matching tests with various similarity levels
- Create confidence calibration validation tests
- Include edge cases and boundary conditions
- Define accuracy and performance benchmarks

Closes task-022
```
