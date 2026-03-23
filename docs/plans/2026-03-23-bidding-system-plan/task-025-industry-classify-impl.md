# Task 025: 行业分类实现

## Task Header
- **ID**: 025
- **Name**: 行业分类实现
- **Type**: impl
- **Depends-on**: 024
- **Status**: pending
- **Created**: 2026-03-23

## Description

实现行业自动分类模块，基于招标标题和描述内容智能识别所属行业领域。该模块采用关键词匹配+机器学习分类的混合策略，支持国家标准行业分类(GB/T 4754)映射。

行业分类是招标数据分析的基础维度，用于行业趋势分析、竞争对手监控、商机筛选等场景。需要覆盖主要招标行业：医疗健康、信息技术、建筑工程、能源环保、交通物流、教育科研、金融保险、农林牧渔、制造业、商贸服务等。

## Files to Create/Modify

### New Files
- `src/analysis/classifiers/industry_classifier.py` - 行业分类器主类
- `src/analysis/classifiers/industry_keywords.py` - 行业关键词词典
- `src/analysis/models/industry_model.py` - 行业分类模型
- `src/analysis/schemas/industry_schema.py` - 行业数据模型
- `data/industry_mapping.json` - 行业分类映射表

### Modify Files
- `src/analysis/classifiers/__init__.py` - 注册行业分类器
- `src/analysis/config.py` - 添加行业分类配置
- `apps/tenders/models.py` - 添加行业字段到招标模型

## Implementation Steps

### Step 1: 创建行业数据模型
在 `src/analysis/schemas/industry_schema.py` 中定义：
- IndustrySchema 类，包含字段：
  - industry: 行业名称（中文）
  - industry_code: 行业代码（GB/T 4754）
  - parent_industry: 上级行业分类
  - confidence: 置信度评分（0.0-1.0）
  - keywords_matched: 匹配的关键词列表
  - secondary_industries: 次要行业候选

### Step 2: 构建行业关键词词典
在 `src/analysis/classifiers/industry_keywords.py` 中定义：
- `INDUSTRY_KEYWORDS`: 行业关键词映射字典
  - 医疗健康: [医院, 医疗器械, 药品, 医疗设备, 诊疗...]
  - 信息技术: [软件, 系统开发, 云计算, 大数据, 网络安全...]
  - 建筑工程: [土建, 装修, 机电安装, 钢结构, 市政工程...]
  - 能源环保: [新能源, 环保设备, 节能改造, 污水处理...]
  - 交通物流: [交通运输, 物流仓储, 智能交通, 港口码头...]
  - 教育科研: [学校, 教学设备, 实验室, 科研仪器...]
  - 金融保险: [银行, 保险, 证券, 金融科技...]
  - 制造业: [生产线, 自动化设备, 机床, 工业机器人...]

### Step 3: 实现行业分类器
在 `src/analysis/classifiers/industry_classifier.py` 中创建 IndustryClassifier 类：
- 继承 BaseClassifier
- 实现 classify() 方法：
  1. 文本预处理（分词、去停用词）
  2. 关键词匹配打分
  3. 机器学习模型预测（可选）
  4. 结果融合与排序
  5. 返回最佳匹配行业
- 实现 _keyword_match() 私有方法
- 实现 _calculate_confidence() 置信度计算
- 实现 _get_secondary_industries() 获取次要行业

### Step 4: 创建行业分类映射表
在 `data/industry_mapping.json` 中定义：
- GB/T 4754 标准行业分类映射
- 行业代码与名称对应关系
- 行业层级结构
- 同义词映射

### Step 5: 训练分类模型（可选）
在 `src/analysis/models/industry_model.py` 中实现：
- 基于历史招标数据的TF-IDF特征提取
- 使用朴素贝叶斯/SVM/随机森林等算法
- 模型持久化和加载机制
- 定期重训练策略

### Step 6: 集成到分类器注册表
修改 `src/analysis/classifiers/__init__.py`：
- 导入 IndustryClassifier
- 添加到 CLASSIFIER_REGISTRY 字典

### Step 7: 添加数据库字段
修改 `apps/tenders/models.py`：
- 添加 `industry` 字段（CharField）
- 添加 `industry_code` 字段（CharField）
- 添加 `industry_confidence` 字段（FloatField）
- 创建数据库迁移

### Step 8: 添加配置项
修改 `src/analysis/config.py`：
- 添加 INDUSTRY_CLASSIFICATION 配置段
- 配置项包括：
  - KEYWORD_MATCH_THRESHOLD: 关键词匹配阈值
  - CONFIDENCE_THRESHOLD: 分类置信度阈值
  - ENABLE_ML_MODEL: 是否启用ML模型
  - SECONDARY_INDUSTRY_COUNT: 次要行业返回数量

## Verification Steps

1. **单元测试验证**
   - 运行 `pytest tests/analysis/classifiers/test_industry_classifier.py -v`
   - 验证关键词匹配准确率 >= 85%
   - 验证分类置信度计算正确

2. **集成测试验证**
   - 使用100份真实招标文件进行测试
   - 检查行业分类正确率 >= 80%
   - 验证次要行业识别效果

3. **性能验证**
   - 单文档分类时间 < 200ms
   - 批量分类吞吐量 >= 100 doc/s

4. **边界情况测试**
   - 测试跨行业项目分类
   - 测试新兴行业识别
   - 测试历史数据兼容性

## Git Commit Message

```
feat: implement industry classification module

- Add IndustrySchema for structured data modeling
- Build comprehensive industry keywords dictionary
- Implement keyword-based classification algorithm
- Support GB/T 4754 standard industry codes
- Add secondary industry detection
- Integrate with tender model database schema
- Add configuration options for classification thresholds

Closes task-025
```
