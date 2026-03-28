# TenderOrchestratorV2 - 4智能体团队协作系统

## 系统概述

基于 DeerFlow 框架的增强型招标信息提取系统，由 **4个智能体团队** 协同工作，实现高效、稳定、智能的招标信息提取。

## 4个智能体团队

### 团队1: 并发控制智能体 (ConcurrencyControlAgent)

**职责**: 管理并发执行，防止资源耗尽和目标网站压力

**核心功能**:
- 信号量控制: HTTP请求(5)、LLM调用(3)、详情页爬取(10)
- 速率限制: 请求间隔(1s)、LLM调用间隔(0.5s)
- 批量处理: `execute_batch_with_limit()`
- 指数退避: `execute_with_backoff()`

**集成点**:
```python
async with concurrency_agent.request_semaphore:
    return await fetch_data(url)
```

---

### 团队2: 重试机制智能体 (RetryMechanismAgent)

**职责**: 处理429限流、503错误、超时等瞬态故障

**核心功能**:
- 指数退避 + 抖动 (Exponential Backoff + Jitter)
- 断路器模式 (Circuit Breaker): 连续失败5次后暂停60秒
- 按错误类型分队列: RATE_LIMIT, SERVICE_UNAVAILABLE, TIMEOUT, CONNECTION_ERROR
- 失败项重试队列: `retry_failed_items()`
- 与并发控制集成: 遇到429时自动降低并发

**配置**:
```python
RetryConfig(
    max_retries=3,
    base_delay=2.0,
    max_delay=60.0,
    jitter=True,
    circuit_breaker_threshold=5,
    circuit_breaker_timeout=60.0,
)
```

**集成点**:
```python
result = await retry_agent.execute_with_retry(
    fetch_func, url, retry_config=custom_config
)
```

---

### 团队3: 缓存系统智能体 (CacheAgent)

**职责**: 避免重复爬取，提高响应速度

**核心功能**:
- **内存LRU缓存**: OrderedDict实现，自动淘汰
- **磁盘缓存**: 两级目录结构，URL哈希作为键
- **TTL失效**: 可配置的缓存有效期
- **智能缓存键**: URL + source_id + source_version
- **缓存统计**: 命中率、大小、条目数

**配置**:
```python
CacheConfig(
    memory_cache_size=1000,
    disk_cache_dir=".cache/crawler",
    default_ttl=3600,
    max_disk_cache_size_mb=500,
)
```

**集成点**:
```python
# 尝试从缓存获取
cached = cache_agent.get(url, source_id)
if cached:
    return cached

# 缓存结果
cache_agent.set(url, content, ttl=7200, source_id=source_id)
```

---

### 团队4: 字段提取优化智能体 (FieldOptimizationAgent)

**职责**: 减少LLM调用，从列表页预提取字段

**核心功能**:
- **列表页字段提取**: 利用列表页已有数据
- **字段映射配置**: 列表字段 → 详情字段映射
- **智能缺失检测**: 只调用LLM提取缺失字段
- **正则预提取**: 日期、金额、招标人等常见模式
- **置信度评分**: 决定是否需要LLM补充

**配置**:
```python
FieldOptimizationConfig(
    required_fields=['title', 'tenderer', 'budget_amount', ...],
    list_to_detail_mapping={
        'title': 'title',
        'publish_date': 'publish_date',
    },
    use_regex_preprocessing=True,
    llm_fallback_threshold=0.6,
)
```

**集成点**:
```python
result = await field_optimizer.optimize_extraction(
    list_item, html, url, llm_extractor
)

if result.llm_called:
    # LLM被调用
    stats['llm_calls_made'] += 1
else:
    # 完全从列表+正则提取，节省LLM调用
    stats['llm_calls_saved'] += 1
```

---

## 协同工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                   TenderOrchestratorV2                          │
│                      (统一编排器)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────────┐
│   获取列表     │   │   批量处理    │   │     重试失败项     │
│  (带缓存)     │   │  (并发控制)   │   │   (重试机制)      │
└───────────────┘   └───────────────┘   └───────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────────────────────────────────────────────────────┐
│                     处理单个列表项                             │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐ │
│  │ 检查缓存     │→│ 获取详情页  │→│   字段提取优化         │ │
│  │ CacheAgent  │  │ (并发控制)  │  │ FieldOptimizationAgent │ │
│  └─────────────┘  └─────────────┘  └───────────────────────┘ │
│                                             │                 │
│                                             ▼                 │
│                              ┌──────────────────────────┐    │
│                              │  列表预提取 → 正则提取   │    │
│                              │  → LLM补充(仅缺失字段)   │    │
│                              └──────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

## 代码示例

### 基础使用

```python
from apps.crawler.agents import TenderOrchestratorV2, OrchestratorV2Config

# 配置
config = OrchestratorV2Config(
    max_concurrent_llm_calls=1,  # 保守设置避免429
    cache_enabled=True,
    use_list_data=True,          # 启用字段优化
    max_items_per_source=50,
)

# 创建编排器
orchestrator = TenderOrchestratorV2(config)

# 执行提取
results = await orchestrator.extract_tenders(source_config, max_pages=3)

# 清理
await orchestrator.close()
```

### 统计信息

```python
print(f"缓存命中率: {orchestrator._calc_cache_rate():.1%}")
print(f"LLM节省率: {orchestrator._calc_savings_rate():.1%}")
print(f"LLM调用: {orchestrator.stats['llm_calls_made']}")
print(f"LLM节省: {orchestrator.stats['llm_calls_saved']}")
```

## 文件结构

```
backend/apps/crawler/agents/
├── __init__.py                    # 导出所有组件
├── orchestrator_v2.py             # V2编排器 (4智能体集成)
├── tender_orchestrator.py         # V1基础编排器
├── schema.py                      # 数据模型
├── workers/                       # 4智能体团队
│   ├── __init__.py
│   ├── concurrency_agent.py       # 团队1: 并发控制
│   ├── retry_agent.py             # 团队2: 重试机制
│   ├── cache_agent.py             # 团队3: 缓存系统
│   └── field_optimizer.py         # 团队4: 字段优化
└── agents/                        # 基础智能体
    ├── fetcher_agents.py
    ├── field_extractor.py
    └── pdf_processor.py
```

## 优势对比

| 特性 | V1 (基础版) | V2 (4智能体版) |
|------|------------|---------------|
| 并发控制 | 无 | 信号量 + 速率限制 |
| 重试机制 | 简单重试 | 指数退避 + 断路器 + 分类队列 |
| 缓存系统 | 无 | 内存 + 磁盘 + TTL |
| 字段优化 | 直接LLM | 列表预提取 + 正则 + 智能合并 |
| 429处理 | 无 | 自动退避 + 并发调整 |
| 失败恢复 | 无 | 失败队列 + 批量重试 |

## 测试结果

运行测试:
```bash
cd backend
python test_orchestrator_v2.py
```

预期输出:
```
============================================================
Testing TenderOrchestratorV2 (4 Agent Teams)
============================================================
Source: xxx

============================================================
Starting extraction...
============================================================

==================================================
Extraction complete: 20 items
==================================================

============================================================
Final Statistics:
============================================================
  Total items: 20
  Cache hits: 5
  Cache misses: 15
  LLM calls made: 8
  LLM calls saved: 12
  Retries: 2
```

## 性能指标

- **缓存命中率**: 预计 20-40% (重复爬取)
- **LLM节省率**: 预计 40-60% (字段优化)
- **429错误减少**: 预计 80%+ (并发控制 + 重试)
- **总体速度提升**: 预计 2-3x (缓存 + 优化)
