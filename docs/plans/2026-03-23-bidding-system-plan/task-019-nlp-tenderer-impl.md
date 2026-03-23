# Task 019: NLP招标人提取实现

## Task Header
- **ID**: 019
- **Name**: NLP招标人提取实现
- **Type**: impl
- **Depends-on**: 018
- **Status**: pending
- **Created**: 2026-03-23

## Description

实现招标人（Tenderer）实体提取模块，支持从招标文件文本中识别和提取招标人信息。该模块将结合正则表达式模式和LLM（大型语言模型）进行混合提取，以提高准确率和覆盖率。

招标人信息是招标文件中的关键实体，通常出现在标题、正文开头或特定的"招标人"字段中。需要处理多种表达形式，如"招标人"、"采购人"、"业主单位"等。

## Files to Create/Modify

### New Files
- `src/nlp/extractors/tenderer_extractor.py` - 招标人提取器主类
- `src/nlp/patterns/tenderer_patterns.py` - 招标人相关正则模式
- `src/nlp/schemas/tenderer_schema.py` - 招标人数据模型
- `src/nlp/prompts/tenderer_extraction.txt` - LLM提取Prompt模板

### Modify Files
- `src/nlp/extractors/__init__.py` - 注册招标人提取器
- `src/nlp/config.py` - 添加招标人提取配置

## Implementation Steps

### Step 1: 创建招标人数据模型
在 `src/nlp/schemas/tenderer_schema.py` 中定义：
- TendererSchema 类，包含字段：
  - name: 招标人名称（必填）
  - alias: 别名/简称
  - contact_person: 联系人
  - phone: 联系电话
  - address: 地址
  - unified_social_credit_code: 统一社会信用代码
  - confidence: 置信度评分（0.0-1.0）
  - source: 提取来源（regex/llm/hybrid）

### Step 2: 定义正则提取模式
在 `src/nlp/patterns/tenderer_patterns.py` 中实现：
- `TENDERER_KEYWORDS`: 招标人关键词列表
- `TENDERER_NAME_PATTERN`: 提取招标人名称的正则
- `CONTACT_PATTERN`: 联系人提取模式
- `PHONE_PATTERN`: 电话提取模式
- `ADDRESS_PATTERN`: 地址提取模式
- `USCC_PATTERN`: 统一社会信用代码模式

### Step 3: 实现招标人提取器
在 `src/nlp/extractors/tenderer_extractor.py` 中创建 TendererExtractor 类：
- 继承 BaseExtractor
- 实现 extract() 方法：
  1. 首先使用正则模式提取
  2. 对于正则未命中或低置信度的情况，调用LLM
  3. 合并并去重结果
  4. 计算最终置信度
- 实现 _extract_with_regex() 私有方法
- 实现 _extract_with_llm() 私有方法
- 实现 _merge_results() 结果合并逻辑

### Step 4: 创建LLM Prompt模板
在 `src/nlp/prompts/tenderer_extraction.txt` 中编写：
- 角色定义：作为招标文件信息提取专家
- 任务描述：从给定文本中提取招标人信息
- 输出格式：JSON Schema定义
- 示例：提供2-3个提取示例

### Step 5: 集成到提取器注册表
修改 `src/nlp/extractors/__init__.py`：
- 导入 TendererExtractor
- 添加到 EXTRACTOR_REGISTRY 字典

### Step 6: 添加配置项
修改 `src/nlp/config.py`：
- 添加 TENDERER_EXTRACTION 配置段
- 配置项包括：
  - ENABLE_LLM_FALLBACK: 是否启用LLM兜底
  - REGEX_CONFIDENCE_THRESHOLD: 正则提取置信度阈值
  - LLM_CONFIDENCE_THRESHOLD: LLM提取置信度阈值

## Verification Steps

1. **单元测试验证**
   - 运行 `pytest tests/nlp/extractors/test_tenderer_extractor.py -v`
   - 验证正则提取准确率 >= 85%
   - 验证混合提取准确率 >= 90%

2. **集成测试验证**
   - 使用10份真实招标文件进行测试
   - 检查招标人名称提取正确率
   - 验证辅助信息（联系人、电话等）提取效果

3. **性能验证**
   - 单文档处理时间 < 500ms
   - 内存占用 < 100MB

4. **边界情况测试**
   - 测试无招标人信息的文档
   - 测试多个招标人的情况
   - 测试招标人名称超长/超短的情况

## Git Commit Message

```
feat: implement NLP tenderer extraction module

- Add TendererSchema for structured data modeling
- Implement regex-based extraction for common patterns
- Add LLM fallback for complex cases
- Create hybrid extraction with confidence scoring
- Register extractor in NLP pipeline

Closes task-019
```
