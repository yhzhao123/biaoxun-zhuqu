# Task 027: 地区分类实现

## Task Header
- **ID**: 027
- **Name**: 地区分类实现
- **Type**: impl
- **Depends-on**: 026
- **Status**: pending
- **Created**: 2026-03-23

## Description

实现地区自动分类模块，基于招标标题、描述、招标人信息和地址文本智能识别所属行政区域。该模块采用行政区划字典+地址解析+NER实体识别的混合策略，支持国家标准行政区划代码(GB/T 2260)。

地区分类是招标数据地域分析的基础，用于区域市场分析、本地化商机推送、区域竞争态势监控等场景。需要准确识别省、市、县/区三级行政区划，支持地名别名识别和地址文本解析。

## Files to Create/Modify

### New Files
- `src/analysis/classifiers/region_classifier.py` - 地区分类器主类
- `src/analysis/classifiers/region_dictionary.py` - 行政区划字典
- `src/analysis/extractors/address_extractor.py` - 地址提取器
- `src/analysis/schemas/region_schema.py` - 地区数据模型
- `data/region_mapping.json` - 行政区划映射表

### Modify Files
- `src/analysis/classifiers/__init__.py` - 注册地区分类器
- `src/analysis/config.py` - 添加地区分类配置
- `apps/tenders/models.py` - 添加地区字段到招标模型

## Implementation Steps

### Step 1: 创建地区数据模型
在 `src/analysis/schemas/region_schema.py` 中定义：
- RegionSchema 类，包含字段：
  - province: 省级行政区名称
  - province_code: 省级行政区划代码（GB/T 2260）
  - city: 市级行政区名称
  - city_code: 市级行政区划代码
  - district: 区县级行政区名称
  - district_code: 区县级行政区划代码
  - full_address: 完整地址文本
  - confidence: 置信度评分（0.0-1.0）
  - source: 提取来源（title/tenderer/address/keywords）
  - mentioned_regions: 文中提及的所有地区列表

### Step 2: 构建行政区划字典
在 `src/analysis/classifiers/region_dictionary.py` 中定义：
- `PROVINCE_MAP`: 省级行政区映射
  - 名称 -> 代码
  - 别名 -> 标准名称（如："沪"->"上海市", "粤"->"广东省"）
- `CITY_MAP`: 市级行政区映射
  - 按省组织城市列表
  - 支持地级市、自治州、地区等
- `DISTRICT_MAP`: 区县级行政区映射
  - 按市组织区县列表
  - 支持市辖区、县级市、县等
- `ALIAS_MAP`: 地区别名映射
  - 城市简称（如："申城"->"上海"）
  - 区域别称（如："魔都"->"上海"）

### Step 3: 实现地址提取器
在 `src/analysis/extractors/address_extractor.py` 中创建 AddressExtractor 类：
- 实现 extract() 方法：
  1. 使用正则匹配地址模式
  2. 识别行政区划层级
  3. 解析详细街道地址
  4. 标准化输出格式
- 实现地址解析模式库
- 支持多种地址格式（省市区街道门牌号）

### Step 4: 实现地区分类器
在 `src/analysis/classifiers/region_classifier.py` 中创建 RegionClassifier 类：
- 继承 BaseClassifier
- 实现 classify() 方法：
  1. 从标题提取地区关键词
  2. 从招标人名称提取地区
  3. 从地址文本解析地区
  4. 多源结果融合与冲突解决
  5. 计算最终置信度
- 实现 _extract_from_title() 标题提取
- 实现 _extract_from_tenderer() 招标人提取
- 实现 _extract_from_address() 地址提取
- 实现 _resolve_conflicts() 冲突解决逻辑

### Step 5: 创建行政区划映射表
在 `data/region_mapping.json` 中定义：
- 完整的GB/T 2260行政区划数据
- 包含省-市-区县的层级关系
- 地区别名和同义词映射
- 定期更新机制

### Step 6: 集成到分类器注册表
修改 `src/analysis/classifiers/__init__.py`：
- 导入 RegionClassifier
- 添加到 CLASSIFIER_REGISTRY 字典

### Step 7: 添加数据库字段
修改 `apps/tenders/models.py`：
- 添加 `province` 字段（CharField）
- 添加 `province_code` 字段（CharField）
- 添加 `city` 字段（CharField）
- 添加 `city_code` 字段（CharField）
- 添加 `district` 字段（CharField）
- 添加 `district_code` 字段（CharField）
- 添加 `region_confidence` 字段（FloatField）
- 创建数据库迁移

### Step 8: 添加配置项
修改 `src/analysis/config.py`：
- 添加 REGION_CLASSIFICATION 配置段
- 配置项包括：
  - PROVINCE_MATCH_WEIGHT: 省级匹配权重
  - CITY_MATCH_WEIGHT: 市级匹配权重
  - DISTRICT_MATCH_WEIGHT: 区县级匹配权重
  - CONFIDENCE_THRESHOLD: 分类置信度阈值
  - ENABLE_ADDRESS_PARSER: 是否启用地址解析

## Verification Steps

1. **单元测试验证**
   - 运行 `pytest tests/analysis/classifiers/test_region_classifier.py -v`
   - 验证行政区划匹配准确率 >= 90%
   - 验证地址解析准确率 >= 85%

2. **集成测试验证**
   - 使用200份真实招标文件进行测试
   - 检查地区分类正确率 >= 85%
   - 验证多源冲突解决效果

3. **性能验证**
   - 单文档分类时间 < 150ms
   - 字典加载时间 < 500ms

4. **边界情况测试**
   - 测试直辖市识别（北京、上海、天津、重庆）
   - 测试自治区、自治州识别
   - 测试跨地区项目处理
   - 测试历史地名识别

## Git Commit Message

```
feat: implement region classification module

- Add RegionSchema for structured region data
- Build comprehensive administrative region dictionary
- Implement multi-source region extraction (title/tenderer/address)
- Add address parser for detailed location extraction
- Support GB/T 2260 standard region codes
- Add region alias recognition (e.g., 沪->上海)
- Implement conflict resolution for multiple regions
- Integrate with tender model database schema
- Add configuration for region classification weights

Closes task-027
```
