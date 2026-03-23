# Task 021: NLP金额提取实现

## Task Header
- **ID**: 021
- **Name**: NLP金额提取实现
- **Type**: impl
- **Depends-on**: 020
- **Status**: pending
- **Created**: 2026-03-23

## Description

实现金额提取模块，支持从招标文件文本中识别、提取和标准化各类金额信息。该模块需要处理多种金额格式（阿拉伯数字、中文大写）、多种货币类型，并实现金额的统一归一化。

金额提取是招标信息抽取的核心功能之一，涉及预算金额、投标保证金、合同估算价等多种金额类型，需要准确识别并建立金额与上下文的关联。

## Files to Create/Modify

### New Files
- `src/nlp/extractors/amount_extractor.py` - 金额提取器主类
- `src/nlp/patterns/amount_patterns.py` - 金额相关正则模式
- `src/nlp/schemas/amount_schema.py` - 金额数据模型
- `src/nlp/utils/amount_normalizer.py` - 金额标准化工具
- `src/nlp/utils/currency_converter.py` - 货币转换工具
- `src/nlp/prompts/amount_extraction.txt` - LLM提取Prompt模板

### Modify Files
- `src/nlp/extractors/__init__.py` - 注册金额提取器
- `src/nlp/config.py` - 添加金额提取配置
- `requirements.txt` - 添加 cn2an（中文数字转换）依赖

## Implementation Steps

### Step 1: 创建金额数据模型
在 `src/nlp/schemas/amount_schema.py` 中定义：

```python
class AmountSchema(BaseModel):
    """金额数据模型"""
    value: float  # 标准化后的数值（单位：元）
    original_value: str  # 原始文本
    currency: str  # 货币类型：CNY/USD/EUR/JPY等
    amount_type: str  # 金额类型：budget/deposit/estimate等
    min_value: Optional[float]  # 区间最小值
    max_value: Optional[float]  # 区间最大值
    is_range: bool  # 是否为区间金额
    confidence: float  # 置信度评分
    source: str  # 提取来源
    context: str  # 上下文片段
```

### Step 2: 定义正则提取模式
在 `src/nlp/patterns/amount_patterns.py` 中实现：

```python
# 数字金额模式
AMOUNT_NUMBER_PATTERN = re.compile(
    r'(\d{1,3}(?:,\d{3})*|\d+)(?:\.(\d{1,2}))?\s*([万亿])?\s*(?:元|人民币|RMB|CNY)?',
    re.IGNORECASE
)

# 中文大写金额模式
AMOUNT_CHINESE_PATTERN = re.compile(
    r'[零壹贰叁肆伍陆柒捌玖拾佰仟万亿]+元(?:整|正)?',
    re.UNICODE
)

# 货币类型识别模式
CURRENCY_PATTERNS = {
    'CNY': [r'元', r'人民币', r'RMB', r'CNY', r'￥', r'¥'],
    'USD': [r'美元', r'USD', r'\$', r'US\$'],
    'EUR': [r'欧元', r'EUR', r'€'],
    'JPY': [r'日元', r'JPY', r'円'],
    'GBP': [r'英镑', r'GBP', r'£'],
    'HKD': [r'港币', r'港元', r'HKD', r'HK\$'],
}

# 金额类型上下文模式
AMOUNT_TYPE_PATTERNS = {
    'budget': [r'预算', r'预算金额', r'采购预算'],
    'deposit': [r'保证金', r'投标保证金', r'履约保证金'],
    'estimate': [r'估算价', r'合同估算价', r'预计金额'],
    'control': [r'控制价', r'最高限价', r'招标控制价'],
}

# 区间金额模式
RANGE_PATTERN = re.compile(
    r'(?:(不低于|不少于|大于)\s*)?(\d[\d,\.]*)(?:\s*[万亿])?\s*[-~至到]\s*(?:(不高于|不高于|小于)\s*)?(\d[\d,\.]*)(?:\s*[万亿])?',
    re.IGNORECASE
)
```

### Step 3: 实现金额标准化工具
在 `src/nlp/utils/amount_normalizer.py` 中实现：

```python
class AmountNormalizer:
    """金额标准化工具"""

    @staticmethod
    def normalize_chinese_to_arabic(chinese_amount: str) -> float:
        """中文大写金额转阿拉伯数字"""
        pass

    @staticmethod
    def normalize_unit(amount: float, unit: str) -> float:
        """统一单位为"元""""
        unit_multipliers = {
            '万': 10000,
            '亿': 100000000,
        }
        pass

    @staticmethod
    def parse_range(text: str) -> Tuple[float, float]:
        """解析区间金额"""
        pass
```

### Step 4: 实现货币转换工具
在 `src/nlp/utils/currency_converter.py` 中实现：

```python
class CurrencyConverter:
    """货币转换工具"""

    # 汇率配置（实际使用时从API获取或定期更新）
    EXCHANGE_RATES = {
        'USD': 7.2,
        'EUR': 7.8,
        'JPY': 0.048,
        'GBP': 9.1,
        'HKD': 0.92,
    }

    @classmethod
    def to_cny(cls, amount: float, currency: str) -> float:
        """转换为人民币"""
        pass
```

### Step 5: 实现金额提取器
在 `src/nlp/extractors/amount_extractor.py` 中创建 AmountExtractor 类：

```python
class AmountExtractor(BaseExtractor):
    """金额提取器"""

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.normalizer = AmountNormalizer()
        self.currency_converter = CurrencyConverter()

    def extract(self, text: str) -> List[AmountSchema]:
        """提取金额信息"""
        amounts = []

        # 1. 正则提取
        regex_results = self._extract_with_regex(text)
        amounts.extend(regex_results)

        # 2. LLM补充提取（针对复杂情况）
        if self.config.get('ENABLE_LLM_FALLBACK'):
            llm_results = self._extract_with_llm(text)
            amounts = self._merge_results(amounts, llm_results)

        # 3. 去重和排序
        amounts = self._deduplicate_and_sort(amounts)

        return amounts

    def _extract_with_regex(self, text: str) -> List[AmountSchema]:
        """使用正则提取金额"""
        pass

    def _extract_with_llm(self, text: str) -> List[AmountSchema]:
        """使用LLM提取金额"""
        pass

    def _merge_results(self, regex_results: List[AmountSchema],
                      llm_results: List[AmountSchema]) -> List[AmountSchema]:
        """合并正则和LLM结果"""
        pass

    def _calculate_confidence(self, match: re.Match, pattern_type: str) -> float:
        """计算提取结果的置信度"""
        pass
```

### Step 6: 创建LLM Prompt模板
在 `src/nlp/prompts/amount_extraction.txt` 中编写Prompt：

```
你是一位专业的招标文件信息提取专家。请从以下文本中提取所有金额信息。

要求：
1. 识别所有金额数值，包括阿拉伯数字和中文大写
2. 识别货币类型（元/美元/欧元/日元等）
3. 识别金额类型（预算/保证金/估算价/控制价等）
4. 处理区间金额（如"100-200万元"）

输出格式（JSON）：
{
  "amounts": [
    {
      "original_value": "原始文本",
      "normalized_value": 1000000,
      "currency": "CNY",
      "amount_type": "budget",
      "is_range": false,
      "confidence": 0.95
    }
  ]
}

待提取文本：
{text}
```

### Step 7: 集成与配置
- 注册到 `extractors/__init__.py`
- 在 `config.py` 中添加配置
- 更新 `requirements.txt` 添加 `cn2an>=0.5.0`

## Verification Steps

1. **功能验证**
   - 运行单元测试：`pytest tests/nlp/extractors/test_amount_extractor.py -v`
   - 验证所有测试用例通过

2. **准确率验证**
   - 使用测试数据集验证提取准确率
   - 数字格式金额 >= 98%
   - 中文大写金额 >= 95%
   - 货币识别 >= 95%

3. **标准化验证**
   - 验证所有金额统一转换为"元"为单位
   - 验证外汇金额正确换算为人民币

4. **性能验证**
   - 单文档处理时间 < 300ms
   - 内存占用合理

## Git Commit Message

```
feat: implement NLP amount extraction with normalization

- Add AmountSchema for structured amount data
- Implement regex patterns for various amount formats
- Add Chinese capital amount to arabic conversion
- Implement currency detection and conversion
- Add amount type classification (budget/deposit/estimate)
- Support range amount extraction
- Create hybrid extraction with LLM fallback

Closes task-021
```
