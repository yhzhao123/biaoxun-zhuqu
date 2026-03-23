# Task 020: NLP金额提取测试

## Task Header
- **ID**: 020
- **Name**: NLP金额提取测试
- **Type**: test
- **Depends-on**: 018
- **Status**: pending
- **Created**: 2026-03-23

## Description

为金额提取模块编写全面的测试用例，覆盖各种金额格式、货币类型和边界情况。金额是招标文件中的核心信息，需要精确提取并统一换算为标准化格式。

测试应覆盖中文大写金额、阿拉伯数字金额、带货币符号的金额、区间金额等多种格式，确保提取器能够正确处理各种实际场景。

## Files to Create/Modify

### New Files
- `tests/nlp/extractors/test_amount_extractor.py` - 金额提取器主测试文件
- `tests/nlp/extractors/fixtures/amount_samples.json` - 测试样本数据
- `tests/nlp/patterns/test_amount_patterns.py` - 金额正则模式测试

### Modify Files
- `tests/nlp/conftest.py` - 添加金额提取器fixture

## Implementation Steps

### Step 1: 准备测试样本数据
在 `tests/nlp/extractors/fixtures/amount_samples.json` 中定义测试样本：

**样本分类：**
1. **基本数字格式**
   - "1000000元"
   - "1,000,000.00元"
   - "100万"
   - "100.5万"

2. **中文大写金额**
   - "壹佰万元整"
   - "人民币叁拾伍万陆仟元整"
   - "贰佰伍拾万零捌仟元"

3. **带货币类型**
   - "$100,000"
   - "USD 50000"
   - "€80,000"
   - "100万日元"

4. **区间金额**
   - "100万-200万元"
   - "不低于50万元"
   - "不超过300万元"

5. **特殊格式**
   - "预算金额：约150万元"
   - "投标保证金：5万元"
   - "合同估算价：800万元"

### Step 2: 创建测试用例
在 `test_amount_extractor.py` 中实现测试类：

```python
class TestAmountExtractor:
    """金额提取器测试类"""

    def test_extract_basic_amount(self):
        """测试基本金额格式提取"""
        pass

    def test_extract_chinese_capital_amount(self):
        """测试中文大写金额提取"""
        pass

    def test_extract_with_currency(self):
        """测试带货币类型的金额提取"""
        pass

    def test_extract_range_amount(self):
        """测试区间金额提取"""
        pass

    def test_extract_special_context(self):
        """测试特殊上下文中的金额提取"""
        pass

    def test_normalize_to_standard(self):
        """测试金额标准化"""
        pass

    def test_calculate_confidence(self):
        """测试置信度计算"""
        pass

    def test_handle_multiple_amounts(self):
        """测试多金额共存场景"""
        pass

    def test_edge_cases(self):
        """测试边界情况"""
        pass
```

### Step 3: 实现正则模式测试
在 `test_amount_patterns.py` 中测试各正则模式：
- `AMOUNT_NUMBER_PATTERN`: 数字金额模式
- `AMOUNT_CHINESE_PATTERN`: 中文大写模式
- `CURRENCY_PATTERN`: 货币类型模式
- `RANGE_PATTERN`: 区间模式
- `CONTEXT_PATTERN`: 上下文模式

### Step 4: 添加测试Fixtures
修改 `conftest.py`：
- 添加 `amount_extractor` fixture
- 添加 `sample_amount_texts` fixture
- 添加 `expected_amount_results` fixture

### Step 5: 定义测试通过标准

**准确率要求：**
- 基本数字格式：>= 98%
- 中文大写金额：>= 95%
- 货币类型识别：>= 95%
- 区间金额识别：>= 90%

**性能要求：**
- 单条测试执行时间 < 100ms
- 全部测试执行时间 < 5s

## Verification Steps

1. **运行测试**
   ```bash
   pytest tests/nlp/extractors/test_amount_extractor.py -v
   pytest tests/nlp/patterns/test_amount_patterns.py -v
   ```

2. **覆盖率检查**
   ```bash
   pytest --cov=src.nlp.extractors.amount_extractor --cov-report=html
   ```
   - 要求行覆盖率 >= 90%
   - 要求分支覆盖率 >= 85%

3. **边界情况验证**
   - 空字符串处理
   - 极大金额（百亿级）
   - 极小金额（分/厘级）
   - 无效金额格式

4. **回归测试**
   - 确保所有历史bug案例都被包含在测试中

## Git Commit Message

```
test: add comprehensive tests for NLP amount extraction

- Add test samples for various amount formats
- Implement unit tests for amount extractor
- Add regex pattern validation tests
- Define accuracy thresholds and performance benchmarks
- Include edge cases and regression tests

Closes task-020
```
