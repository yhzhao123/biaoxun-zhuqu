# Task 029: 招标人聚类实现

## Task Header
- **ID**: 029
- **Name**: 招标人聚类实现
- **Type**: impl
- **Depends-on**: 028
- **Status**: pending
- **Created**: 2026-03-23

## Description

实现招标人实体聚类模块，识别不同文本中同一招标人的名称变体，进行规范化处理和实体消歧。该模块采用文本相似度算法+规则引擎+知识图谱的混合策略，支持增量聚类和动态更新。

招标人聚类是招标数据分析的核心功能，用于识别同一客户的多次招标行为、分析客户历史、建立客户关系图谱等场景。需要处理名称缩写、别名、部门层级、拼写变体等多种情况。

## Files to Create/Modify

### New Files
- `src/analysis/clustering/tenderer_clusterer.py` - 招标人聚类器主类
- `src/analysis/clustering/similarity_calculator.py` - 相似度计算器
- `src/analysis/clustering/name_normalizer.py` - 名称规范化器
- `src/analysis/clustering/entity_resolver.py` - 实体消歧器
- `src/analysis/schemas/cluster_schema.py` - 聚类数据模型
- `src/analysis/knowledge/tenderer_kb.py` - 招标人知识库
- `data/tenderer_aliases.json` - 招标人别名词典

### Modify Files
- `src/analysis/clustering/__init__.py` - 注册聚类器
- `src/analysis/config.py` - 添加聚类配置
- `apps/tenders/models.py` - 添加招标人聚类关联

## Implementation Steps

### Step 1: 创建聚类数据模型
在 `src/analysis/schemas/cluster_schema.py` 中定义：
- TendererClusterSchema 类，包含字段：
  - cluster_id: 聚类唯一标识
  - canonical_name: 规范化名称（标准名称）
  - short_name: 简称
  - aliases: 别名列表
  - variants: 所有名称变体列表
  - entity_type: 实体类型（医院/政府/企业/学校等）
  - unified_code: 统一社会信用代码
  - region: 所属地区
  - confidence: 聚类置信度
  - created_at: 创建时间
  - updated_at: 更新时间

### Step 2: 实现名称规范化器
在 `src/analysis/clustering/name_normalizer.py` 中创建 NameNormalizer 类：
- 实现 normalize() 方法：
  1. 去除多余空格和特殊字符
  2. 统一全角/半角字符
  3. 扩展缩写形式
  4. 标准化组织机构后缀
- 定义 `ORG_SUFFIX_MAP`: 机构后缀映射
  - "公司"、"有限公司"、"股份有限公司"标准化
  - "局"、"厅"、"部"等政府机构后缀处理
  - "院"、"所"、"中心"等事业单位后缀处理
- 实现 `_remove_noise()` 噪声去除
- 实现 `_standardize_suffix()` 后缀标准化

### Step 3: 实现相似度计算器
在 `src/analysis/clustering/similarity_calculator.py` 中创建 SimilarityCalculator 类：
- 实现 calculate() 方法：
  1. 编辑距离相似度（Levenshtein）
  2. Jaccard相似度（字符集合）
  3. 余弦相似度（TF-IDF向量）
  4. 组合相似度评分
- 实现 `_levenshtein_similarity()` 编辑距离
- 实现 `_jaccard_similarity()` Jaccard相似度
- 实现 `_cosine_similarity()` 余弦相似度
- 实现 `_combine_scores()` 加权组合

### Step 4: 实现实体消歧器
在 `src/analysis/clustering/entity_resolver.py` 中创建 EntityResolver 类：
- 实现 resolve() 方法：
  1. 基于规则的快速匹配
  2. 相似度阈值判断
  3. 上下文信息辅助消歧
  4. 返回最佳匹配实体
- 实现 `_rule_based_match()` 规则匹配
- 实现 `_context_aware_disambiguation()` 上下文消歧
- 实现 `_get_conflict_resolution()` 冲突解决

### Step 5: 实现招标人聚类器
在 `src/analysis/clustering/tenderer_clusterer.py` 中创建 TendererClusterer 类：
- 实现 cluster() 方法（批量聚类）：
  1. 预处理所有名称
  2. 计算名称间相似度矩阵
  3. 使用层次聚类或DBSCAN算法
  4. 为每个聚类选择规范名称
  5. 返回聚类结果
- 实现 add_to_cluster() 方法（增量聚类）：
  1. 计算新名称与现有聚类的相似度
  2. 判断是否加入现有聚类或创建新聚类
  3. 更新聚类信息
- 实现 merge_clusters() 方法（聚类合并）：
  1. 检测可合并的聚类
  2. 执行合并操作
  3. 更新关联数据
- 实现 `_select_canonical_name()` 规范名称选择
- 实现 `_update_cluster_metadata()` 元数据更新

### Step 6: 构建招标人知识库
在 `src/analysis/knowledge/tenderer_kb.py` 中创建 TendererKnowledgeBase 类：
- 实现实体存储和查询
- 支持别名映射管理
- 维护实体关系图谱
- 提供增量更新机制

### Step 7: 创建别名词典
在 `data/tenderer_aliases.json` 中定义：
- 常见招标人别名映射
- 知名企业简称对照
- 政府机构别名词典
- 高校中英文名称映射

### Step 8: 集成到聚类注册表
修改 `src/analysis/clustering/__init__.py`：
- 导入 TendererClusterer
- 添加到 CLUSTERER_REGISTRY 字典

### Step 9: 添加数据库模型
修改 `apps/tenders/models.py`：
- 创建 `TendererCluster` 模型
- 添加 `TendererClusterMembership` 关联模型
- 添加招标人与聚类的外键关联
- 创建数据库迁移

### Step 10: 添加配置项
修改 `src/analysis/config.py`：
- 添加 TENDERER_CLUSTERING 配置段
- 配置项包括：
  - SIMILARITY_THRESHOLD: 相似度阈值（默认0.85）
  - MIN_CLUSTER_SIZE: 最小聚类大小
  - CANONICAL_NAME_STRATEGY: 规范名称选择策略
  - ENABLE_INCREMENTAL: 启用增量聚类
  - BATCH_SIZE: 批量处理大小

## Verification Steps

1. **单元测试验证**
   - 运行 `pytest tests/analysis/clustering/test_tenderer_clusterer.py -v`
   - 验证相似度计算准确率 >= 90%
   - 验证聚类准确率 >= 85%

2. **集成测试验证**
   - 使用500个真实招标人名称进行测试
   - 检查聚类正确率 >= 80%
   - 验证规范名称选择合理性

3. **性能验证**
   - 批量聚类1000个名称 < 30s
   - 增量聚类单次操作 < 100ms
   - 相似度计算 < 5ms/对

4. **边界情况测试**
   - 测试包含特殊字符的名称
   - 测试中英文混合名称
   - 测试历史数据兼容性
   - 测试大规模聚类稳定性

## Git Commit Message

```
feat: implement tenderer entity clustering module

- Add TendererClusterSchema for structured cluster data
- Implement name normalizer for standardizing variants
- Add multi-algorithm similarity calculator (Levenshtein, Jaccard, Cosine)
- Create entity resolver for disambiguation
- Implement hierarchical clustering algorithm
- Support incremental clustering for new entities
- Build tenderer knowledge base for entity management
- Add alias dictionary for common name variations
- Integrate with tender database models
- Add configuration for clustering thresholds and strategies

Closes task-029
```
