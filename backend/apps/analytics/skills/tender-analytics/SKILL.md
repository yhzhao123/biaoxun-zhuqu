---
name: tender-analytics
description: 招标信息智能分析 Skill - 提供分类、商机识别、趋势分析能力
version: 1.0.0
author: biaoxun-team
license: MIT
allowed-tools:
  - classify_tender
  - score_opportunity
  - analyze_trends
  - aggregate_data
---

# Tender Analytics Skill

## 概述

本 Skill 提供招标信息的智能分析能力，包括：

- 招标信息自动分类
- 商机智能识别与评分
- 市场趋势分析
- 数据聚合与可视化

## 可用工具

### classify_tender

对招标信息进行智能分类，包括招标人、地区、行业、金额等维度。

**参数：**
- `tender_id`: 招标唯一标识
- `tenderer`: 招标人名称
- `region`: 地区名称
- `industry`: 行业名称
- `amount`: 预算金额（可选）

**返回：**
JSON 字符串，包含完整的分类结果

### score_opportunity

对招标商机进行5维评分，识别高价值商机。

**参数：**
- `tender_id`: 招标唯一标识
- `tenderer`: 招标人名称
- `region`: 地区名称
- `industry`: 行业名称
- `amount`: 预算金额（可选）
- `deadline`: 截止日期（可选）

**返回：**
JSON 字符串，包含5维评分（需求匹配度、预算合理性、竞争程度、时效性、战略价值）

### analyze_trends

对招标数据进行趋势分析，包括时间序列、地区分布、行业热度等。

**参数：**
- `start_date`: 开始日期
- `end_date`: 结束日期
- `region`: 地区名称（可选）
- `industry`: 行业名称（可选）
- `group_by`: 分组字段（可选，默认为 "date"）

**返回：**
JSON 字符串，包含趋势数据

### aggregate_data

提供统一的数据聚合接口，支持概览、分类统计、商机列表、趋势分析等。

**参数：**
- `tenderer`: 招标人名称（可选）
- `region`: 地区名称（可选）
- `industry`: 行业名称（可选）
- `min_amount`: 最小金额（可选）
- `max_amount`: 最大金额（可选）
- `page`: 页码（可选，默认为 1）
- `page_size`: 每页数量（可选，默认为 20）

**返回：**
JSON 字符串，包含聚合数据

## 使用场景

### 场景1：招标分类

用户：帮我分类这批招标信息

Agent：我来为您分类这些招标信息。

```
[调用 classify_tender Tool 对每个招标进行分类]
```

### 场景2：商机识别

用户：找出这批招标中的高价值商机

Agent：我来分析这些招标的商机价值。

```
[调用 score_opportunity 进行评分]
[筛选出 >=80分的高价值商机]
```

### 场景3：趋势分析

用户：分析北京地区的招标趋势

Agent：我来为您分析北京地区的招标趋势。

```
[调用 analyze_trends 进行分析]
```

### 场景4：数据仪表板

用户：给我一个完整的数据概览

Agent：我来为您生成完整的数据仪表板。

```
[调用 aggregate_data 获取所有统计信息]
```

## 最佳实践

1. **批量处理时使用并行调用**：多个招标分析可并行执行
2. **先分类再评分**：先进行分类可提高评分准确性
3. **使用 aggregate_data 获取完整仪表板**：一个调用获取所有聚合数据
4. **关注高价值商机**：筛选 80 分以上的商机优先跟进
5. **定期趋势分析**：每周/每月分析趋势，洞察市场变化

## 集成说明

本 Skill 整合了以下核心分析能力：

- **分类引擎** (`classification/engine.py`)：基于规则的智能分类
- **商机评分器** (`opportunity/scorer.py`)：多维度商机评估
- **趋势分析器** (`trends/analyzer.py`)：时间序列与分布分析
- **数据聚合器** (`services.py`)：统一数据聚合接口

通过 deer-flow 的工具系统，这些能力被封装为可被 LLM 调用的工具，支持智能体进行复杂的招标信息分析任务。