# Task 023: NLP置信度处理实现

## Task Header
- **ID**: 023
- **Name**: NLP置信度处理实现
- **Type**: impl
- **Depends-on**: 022
- **Status**: pending
- **Created**: 2026-03-23

## Description

实现置信度处理模块，为NLP实体提取提供可靠的置信度评分和决策机制。该模块负责计算、校准和应用置信度阈值，支持模糊实体匹配，确保系统能够区分高可信度结果和需要进一步验证的结果。

置信度处理是保证NLP输出质量的关键组件，需要与正则提取器、LLM提取器和模糊匹配系统紧密协作。

## Files to Create/Modify

### New Files
- `src/nlp/confidence/confidence_calculator.py` - 置信度计算核心
- `src/nlp/confidence/confidence_calibrator.py` - 置信度校准器
- `src/nlp/confidence/threshold_manager.py` - 阈值管理器
- `src/nlp/confidence/__init__.py` - 模块导出
- `src/nlp/fuzzy/fuzzy_entity_handler.py` - 模糊实体处理器
- `src/nlp/fuzzy/similarity_calculator.py` - 相似度计算器
- `src/nlp/fuzzy/__init__.py` - 模块导出

### Modify Files
- `src/nlp/config.py` - 添加置信度和模糊匹配配置
- `src/nlp/extractors/base_extractor.py` - 集成置信度处理
- `requirements.txt` - 添加 rapidfuzz 依赖

## Implementation Steps

### Step 1: 实现置信度计算器
在 `src/nlp/confidence/confidence_calculator.py` 中创建：

```python
class ConfidenceCalculator:
    """置信度计算器"""

    # 置信度评分因子权重
    WEIGHTS = {
        'pattern_match': 0.30,
        'context_completeness': 0.25,
        'entity_consistency': 0.25,
        'historical_accuracy': 0.20,
    }

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.weights = self.config.get('weights', self.WEIGHTS)

    def calculate_from_regex(self, match: re.Match, pattern: str,
                            entity_type: str, context: str) -> float:
        """基于正则匹配计算置信度"""
        scores = {
            'pattern_match': self._score_pattern_match(match, pattern),
            'context_completeness': self._score_context(context, entity_type),
            'entity_consistency': self._score_entity_consistency(
                match.group(), entity_type
            ),
            'historical_accuracy': self._get_historical_accuracy(pattern),
        }

        confidence = sum(
            scores[key] * self.weights[key]
            for key in self.weights
        )

        return min(max(confidence, 0.0), 1.0)

    def calculate_from_llm(self, llm_result: Dict, context: str) -> float:
        """基于LLM结果计算置信度"""
        base_confidence = llm_result.get('confidence', 0.5)

        # 根据上下文验证调整
        context_score = self._verify_with_context(llm_result, context)

        # 根据历史准确性调整
        historical_factor = self._get_llm_historical_factor()

        confidence = base_confidence * context_score * historical_factor

        return min(max(confidence, 0.0), 1.0)

    def calculate_combined(self, regex_confidence: float,
                          llm_confidence: float,
                          agreement: float) -> float:
        """计算组合置信度"""
        if agreement > 0.9:  # 高度一致，提升置信度
            return min(0.95, max(regex_confidence, llm_confidence) * 1.05)
        elif agreement < 0.5:  # 严重冲突，降低置信度
            return max(regex_confidence, llm_confidence) * 0.8
        else:
            # 一般情况取加权平均
            return regex_confidence * 0.4 + llm_confidence * 0.6

    def _score_pattern_match(self, match: re.Match, pattern: str) -> float:
        """评分：正则匹配质量"""
        # 完整匹配得分更高
        if match.group() == match.string[match.start():match.end()]:
            return 1.0

        # 基于捕获组完整度评分
        groups = match.groups()
        if all(groups):
            return 0.9
        elif any(groups):
            return 0.7
        return 0.5

    def _score_context(self, context: str, entity_type: str) -> float:
        """评分：上下文完整性"""
        score = 0.5

        # 检查关键词邻近度
        keywords = self._get_keywords_for_type(entity_type)
        for keyword in keywords:
            if keyword in context:
                score += 0.1

        # 检查上下文长度
        context_len = len(context)
        if 20 <= context_len <= 200:
            score += 0.2
        elif context_len > 200:
            score += 0.1

        return min(score, 1.0)

    def _score_entity_consistency(self, entity: str, entity_type: str) -> float:
        """评分：实体一致性"""
        # 检查实体格式是否符合预期
        validators = {
            'tenderer': self._validate_company_name,
            'amount': self._validate_amount,
            'date': self._validate_date,
        }

        validator = validators.get(entity_type)
        if validator:
            return validator(entity)
        return 0.5

    def _get_keywords_for_type(self, entity_type: str) -> List[str]:
        """获取实体类型关键词"""
        keywords = {
            'tenderer': ['招标人', '采购人', '业主', '单位'],
            'amount': ['元', '万元', '金额', '预算', '价格'],
            'date': ['日期', '时间', '截止', '开标'],
        }
        return keywords.get(entity_type, [])
```

### Step 2: 实现置信度校准器
在 `src/nlp/confidence/confidence_calibrator.py` 中创建：

```python
class ConfidenceCalibrator:
    """置信度校准器 - 使用温度缩放和Platt缩放"""

    def __init__(self, calibration_method: str = 'temperature'):
        self.method = calibration_method
        self.temperature = 1.0
        self.platt_params = {'a': 1.0, 'b': 0.0}
        self.is_fitted = False

    def fit(self, confidences: np.ndarray, accuracies: np.ndarray):
        """拟合校准参数"""
        if self.method == 'temperature':
            self._fit_temperature(confidences, accuracies)
        elif self.method == 'platt':
            self._fit_platt(confidences, accuracies)
        self.is_fitted = True

    def calibrate(self, confidence: float) -> float:
        """校准置信度"""
        if not self.is_fitted:
            return confidence

        if self.method == 'temperature':
            return self._apply_temperature(confidence)
        elif self.method == 'platt':
            return self._apply_platt(confidence)
        return confidence

    def _fit_temperature(self, confidences: np.ndarray, accuracies: np.ndarray):
        """拟合温度参数"""
        from scipy.optimize import minimize

        def nll(temperature):
            scaled = confidences ** (1 / temperature)
            # 简化版负对数似然
            return -np.mean(
                accuracies * np.log(scaled + 1e-10) +
                (1 - accuracies) * np.log(1 - scaled + 1e-10)
            )

        result = minimize(nll, x0=1.0, bounds=[(0.1, 10.0)])
        self.temperature = result.x[0]

    def _apply_temperature(self, confidence: float) -> float:
        """应用温度缩放"""
        return confidence ** (1 / self.temperature)

    def _fit_platt(self, confidences: np.ndarray, accuracies: np.ndarray):
        """拟合Platt缩放参数"""
        from scipy.optimize import minimize

        def nll(params):
            a, b = params
            scaled = 1 / (1 + np.exp(-(a * confidences + b)))
            return -np.mean(
                accuracies * np.log(scaled + 1e-10) +
                (1 - accuracies) * np.log(1 - scaled + 1e-10)
            )

        result = minimize(nll, x0=[1.0, 0.0], method='L-BFGS-B')
        self.platt_params['a'], self.platt_params['b'] = result.x

    def _apply_platt(self, confidence: float) -> float:
        """应用Platt缩放"""
        a, b = self.platt_params['a'], self.platt_params['b']
        return 1 / (1 + np.exp(-(a * confidence + b)))
```

### Step 3: 实现阈值管理器
在 `src/nlp/confidence/threshold_manager.py` 中创建：

```python
class ThresholdManager:
    """阈值管理器"""

    # 默认阈值配置
    DEFAULT_THRESHOLDS = {
        'ACCEPT': 0.85,      # 直接接受
        'REVIEW': 0.60,      # 人工审核
        'REJECT': 0.00,      # 直接拒绝（低于此值）
    }

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.thresholds = self.config.get('thresholds', self.DEFAULT_THRESHOLDS)
        self.entity_specific = self.config.get('entity_specific', {})

    def get_thresholds(self, entity_type: str = None) -> Dict[str, float]:
        """获取阈值配置"""
        if entity_type and entity_type in self.entity_specific:
            return self.entity_specific[entity_type]
        return self.thresholds

    def decide(self, confidence: float, entity_type: str = None) -> str:
        """基于置信度做出决策"""
        thresholds = self.get_thresholds(entity_type)

        if confidence >= thresholds['ACCEPT']:
            return 'ACCEPT'
        elif confidence >= thresholds['REVIEW']:
            return 'REVIEW'
        else:
            return 'REJECT'

    def should_accept(self, confidence: float, entity_type: str = None) -> bool:
        """判断是否可以直接接受"""
        return self.decide(confidence, entity_type) == 'ACCEPT'

    def should_review(self, confidence: float, entity_type: str = None) -> bool:
        """判断是否需要人工审核"""
        return self.decide(confidence, entity_type) == 'REVIEW'

    def should_reject(self, confidence: float, entity_type: str = None) -> bool:
        """判断是否应拒绝"""
        return self.decide(confidence, entity_type) == 'REJECT'

    def update_thresholds(self, entity_type: str, **kwargs):
        """更新特定实体的阈值"""
        if entity_type not in self.entity_specific:
            self.entity_specific[entity_type] = self.thresholds.copy()
        self.entity_specific[entity_type].update(kwargs)
```

### Step 4: 实现模糊实体处理器
在 `src/nlp/fuzzy/fuzzy_entity_handler.py` 中创建：

```python
class FuzzyEntityHandler:
    """模糊实体处理器"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.similarity_threshold = self.config.get('similarity_threshold', 0.80)
        self.review_threshold = self.config.get('review_threshold', 0.60)
        self.calculator = SimilarityCalculator()

    def find_match(self, entity: str, candidates: List[str],
                   entity_type: str = None) -> Optional[Dict]:
        """在候选中查找最佳匹配"""
        if not candidates:
            return None

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            score = self.calculator.calculate(entity, candidate, entity_type)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= self.similarity_threshold:
            return {
                'entity': entity,
                'matched_to': best_match,
                'similarity': best_score,
                'action': 'ACCEPT',
            }
        elif best_score >= self.review_threshold:
            return {
                'entity': entity,
                'matched_to': best_match,
                'similarity': best_score,
                'action': 'REVIEW',
            }

        return None

    def deduplicate(self, entities: List[Dict],
                    similarity_threshold: float = 0.90) -> List[Dict]:
        """实体去重"""
        if not entities:
            return []

        unique = []
        for entity in entities:
            is_duplicate = False
            for existing in unique:
                sim = self.calculator.calculate(
                    entity['value'],
                    existing['value'],
                    entity.get('type')
                )
                if sim >= similarity_threshold:
                    # 保留置信度更高的
                    if entity.get('confidence', 0) > existing.get('confidence', 0):
                        existing.update(entity)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(entity)

        return unique
```

### Step 5: 实现相似度计算器
在 `src/nlp/fuzzy/similarity_calculator.py` 中创建：

```python
class SimilarityCalculator:
    """相似度计算器"""

    def __init__(self):
        # 使用 rapidfuzz 进行快速模糊匹配
        from rapidfuzz import fuzz, distance
        self.fuzz = fuzz
        self.distance = distance

    def calculate(self, s1: str, s2: str, entity_type: str = None) -> float:
        """计算两个字符串的相似度"""
        if not s1 or not s2:
            return 0.0

        # 预处理
        s1_norm = self._normalize(s1)
        s2_norm = self._normalize(s2)

        # 精确匹配
        if s1_norm == s2_norm:
            return 1.0

        # 根据实体类型选择算法
        if entity_type == 'tenderer':
            return self._company_similarity(s1_norm, s2_norm)
        elif entity_type == 'amount':
            return self._amount_similarity(s1_norm, s2_norm)
        else:
            return self._general_similarity(s1_norm, s2_norm)

    def _normalize(self, s: str) -> str:
        """字符串标准化"""
        import re
        # 移除空格和标点
        s = re.sub(r'\s+', '', s)
        s = re.sub(r'[，。！？、；：""''（）【】]', '', s)
        return s.lower()

    def _general_similarity(self, s1: str, s2: str) -> float:
        """通用相似度"""
        # 使用加权组合
        ratios = [
            self.fuzz.ratio(s1, s2) * 0.3,
            self.fuzz.partial_ratio(s1, s2) * 0.3,
            self.fuzz.token_sort_ratio(s1, s2) * 0.2,
            self.fuzz.token_set_ratio(s1, s2) * 0.2,
        ]
        return sum(ratios) / 100.0

    def _company_similarity(self, s1: str, s2: str) -> float:
        """公司名称相似度"""
        # 提取核心名称（去除公司类型后缀）
        core1 = self._extract_company_core(s1)
        core2 = self._extract_company_core(s2)

        # 核心名称相似度权重更高
        core_sim = self.fuzz.ratio(core1, core2) / 100.0

        # 完整名称相似度
        full_sim = self._general_similarity(s1, s2)

        return core_sim * 0.6 + full_sim * 0.4

    def _extract_company_core(self, name: str) -> str:
        """提取公司核心名称"""
        import re
        # 移除常见后缀
        suffixes = [
            '有限公司', '有限责任公司', '股份公司', '股份有限公司',
            '集团', '集团公司', '总公司', '分公司',
        ]
        core = name
        for suffix in suffixes:
            core = re.sub(suffix + '$', '', core)
        return core

    def _amount_similarity(self, s1: str, s2: str) -> float:
        """金额相似度"""
        # 尝试解析数值
        try:
            v1 = self._parse_amount(s1)
            v2 = self._parse_amount(s2)
            if v1 is not None and v2 is not None:
                # 数值越接近越相似
                ratio = min(v1, v2) / max(v1, v2)
                return ratio
        except:
            pass

        return self._general_similarity(s1, s2)

    def _parse_amount(self, s: str) -> Optional[float]:
        """解析金额数值"""
        import re
        match = re.search(r'(\d+(?:\.\d+)?)', s)
        if match:
            return float(match.group(1))
        return None
```

### Step 6: 集成到基础提取器
修改 `src/nlp/extractors/base_extractor.py`：

```python
from src.nlp.confidence import ConfidenceCalculator, ThresholdManager
from src.nlp.fuzzy import FuzzyEntityHandler

class BaseExtractor(ABC):
    """基础提取器类"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.confidence_calculator = ConfidenceCalculator(
            self.config.get('confidence', {})
        )
        self.threshold_manager = ThresholdManager(
            self.config.get('thresholds', {})
        )
        self.fuzzy_handler = FuzzyEntityHandler(
            self.config.get('fuzzy', {})
        )

    def extract_with_confidence(self, text: str) -> List[Dict]:
        """带置信度的提取"""
        raw_results = self.extract(text)

        results = []
        for result in raw_results:
            confidence = result.get('confidence', 0.5)
            decision = self.threshold_manager.decide(
                confidence, result.get('entity_type')
            )

            result['decision'] = decision
            results.append(result)

        return results
```

### Step 7: 添加配置和依赖
- 在 `src/nlp/config.py` 中添加置信度和模糊匹配配置
- 在 `requirements.txt` 中添加 `rapidfuzz>=3.0.0`

## Verification Steps

1. **功能验证**
   ```bash
   pytest tests/nlp/test_confidence_handler.py -v
   pytest tests/nlp/test_fuzzy_entity_handler.py -v
   ```

2. **置信度校准验证**
   - 验证校准后的置信度与实际准确率相关性 >= 0.85
   - 验证高置信度区间（>0.9）准确率 > 95%

3. **模糊匹配验证**
   - 验证公司名称匹配准确率 >= 90%
   - 验证去重效果

4. **阈值决策验证**
   - 验证决策分布合理
   - 验证误报率 < 5%

## Git Commit Message

```
feat: implement NLP confidence handling and fuzzy entity matching

- Add ConfidenceCalculator with multi-factor scoring
- Implement confidence calibration with temperature and Platt scaling
- Create ThresholdManager for decision control (ACCEPT/REVIEW/REJECT)
- Add FuzzyEntityHandler for approximate matching
- Implement SimilarityCalculator with entity-type-specific algorithms
- Integrate confidence pipeline into base extractor
- Add configuration for thresholds and similarity parameters

Closes task-023
```
