# Task 028: 招标人聚类测试

## 任务信息

- **任务ID**: 028
- **任务名称**: 招标人聚类测试
- **任务类型**: test
- **依赖任务**: 019 (NLP招标人提取实现)

## BDD Scenario

```gherkin
Scenario: 聚类识别同一招标人的不同名称变体
  Given 招标文本中包含以下招标人名称：
    - "某市人民医院"
    - "某市第一人民医院"
    - "某市人民医院（新院区）"
  When 系统执行招标人聚类分析
  Then 应将以上名称识别为同一实体
  And 返回规范化名称"某市人民医院"
```

## 测试目标

测试招标人实体聚类功能，识别不同文本中同一招标人的名称变体，并进行规范化处理。

## 创建的文件

- `apps/analysis/tests/test_tenderer_clustering.py` - 招标人聚类测试

## 测试用例

### Test Case 1: 医院名称变体聚类
```python
def test_cluster_hospital_name_variants():
    """聚类医院名称的不同变体"""
    # Given: 同一医院的多种名称表述
    names = [
        "某市人民医院",
        "某市第一人民医院",
        "某市人民医院（新院区）",
        "某市人民 医院",
    ]

    # When: 执行聚类分析
    clusters = tenderer_clusterer.cluster(names)

    # Then: 应聚类为同一实体
    assert len(clusters) == 1
    assert clusters[0]['canonical_name'] == "某市人民医院"
    assert len(clusters[0]['variants']) == 4
```

### Test Case 2: 公司名称规范化
```python
def test_normalize_company_names():
    """规范化公司名称的不同写法"""
    names = [
        "中国移动通信集团有限公司",
        "中国移动",
        "中国移动公司",
        "China Mobile",
    ]

    result = tenderer_clusterer.cluster(names)

    assert result[0]['canonical_name'] == "中国移动通信集团有限公司"
    assert result[0]['short_name'] == "中国移动"
```

### Test Case 3: 政府部门名称聚类
```python
def test_cluster_government_department_names():
    """聚类政府部门名称变体"""
    names = [
        "某市财政局",
        "某市财政局政府采购中心",
        "某市财政 局",
        "某市财政局（本级）",
    ]

    result = tenderer_clusterer.cluster(names)

    assert len(result) == 1
    assert "财政局" in result[0]['canonical_name']
```

### Test Case 4: 相似但不相同名称区分
```python
def test_distinguish_similar_but_different_entities():
    """区分相似但不同的招标人"""
    names = [
        "某市人民医院",      # 市级
        "某县人民医院",      # 县级 - 不同实体
        "某市第二人民医院",  # 不同医院
    ]

    result = tenderer_clusterer.cluster(names)

    # 应识别为3个不同实体
    assert len(result) == 3
```

### Test Case 5: 别名识别与合并
```python
def test_recognize_and_merge_aliases():
    """识别招标人别名并合并"""
    names = [
        "北京大学",
        "北大",
        "Peking University",
        "PKU",
    ]

    result = tenderer_clusterer.cluster(names)

    assert len(result) == 1
    assert result[0]['canonical_name'] == "北京大学"
    assert "北大" in result[0]['aliases']
```

### Test Case 6: 增量聚类测试
```python
def test_incremental_clustering():
    """测试增量聚类功能"""
    # 初始聚类
    initial_names = ["A公司", "A股份有限公司"]
    cluster_id = tenderer_clusterer.create_cluster(initial_names)

    # 增量添加
    new_name = "A公司（本部）"
    result = tenderer_clusterer.add_to_cluster(cluster_id, new_name)

    assert new_name in result['variants']
    assert result['cluster_size'] == 3
```

## 实施步骤

1. 创建测试文件和目录
2. 使用 pytest 标记测试
3. 使用参数化测试覆盖多种聚类场景
4. 运行测试确认失败(RED状态)

## 验证步骤

```bash
pytest apps/analysis/tests/test_tenderer_clustering.py::test_cluster_hospital_name_variants -v
pytest apps/analysis/tests/test_tenderer_clustering.py::test_normalize_company_names -v
pytest apps/analysis/tests/test_tenderer_clustering.py::test_distinguish_similar_but_different_entities -v
```

**预期**: 测试失败，因为招标人聚类功能未实现

## 提交信息

```
test: add tenderer clustering tests

- Test hospital name variant clustering
- Test company name normalization
- Test government department name clustering
- Test similar but different entity distinction
- Test alias recognition and merging
- Test incremental clustering functionality
- All tests currently failing (RED)
```
