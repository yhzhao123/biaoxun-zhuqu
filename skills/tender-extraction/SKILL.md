---
name: tender-extraction
version: 2.0.0
description: 招标信息提取标准流程 - 支持 API 型、静态 HTML 型、动态 JS 型网站，集成 deer-flow Tools 和 Workflow
author: Biaoxun Team
dependencies: []
tags: [extraction, crawler, tender, deer-flow]
priority: 100
---

# Tender Extraction Skill

## 1. 概述

本 Skill 提供标准化的招标信息提取流程，支持三种类型的招标网站：

| 类型 | 特征 | 提取策略 |
|------|------|----------|
| **API 型** | 返回 JSON 数据，有明确接口 | 直接解析 API 响应，映射字段 |
| **静态 HTML 型** | 服务端渲染，HTML 包含完整内容 | 使用 IntelligentExtractor + 规则提取 |
| **动态 JS 型** | 客户端渲染，需要执行 JS | 使用 Playwright 渲染后提取 |

## 2. deer-flow Tools 使用

本 Skill 封装了两个核心 Tools，可直接在 deer-flow Agent 中使用：

### 2.1 fetch_tender_list - 列表获取 Tool

**用途**: 从招标网站获取公告列表

**参数**:
```python
{
    "source_url": "http://api.example.com/tender/list",  # 必需：源 URL
    "site_type": "api",                                   # 可选：api/static/dynamic
    "max_pages": 5,                                       # 可选：最大页数
    "api_config": json.dumps({                            # 可选：API 配置
        "url": "http://api.example.com/tender/list",
        "method": "GET",
        "params": {"page": 1},
        "headers": {},
        "response_path": "data.list",
        "field_mapping": {
            "title_field": "title",
            "url_field": "detailUrl",
            "date_field": "publishTime",
            "budget_field": "budget"
        }
    })
}
```

**返回值**:
```python
{
    "items": [
        {
            "title": "办公设备采购招标公告",
            "url": "http://example.com/detail/123",
            "publish_date": "2024-01-15",
            "budget": "500000",
            "tenderer": "XX市政府"
        }
    ],
    "total_count": 50,
    "pages_fetched": 5,
    "success": True,
    "error_message": None
}
```

**使用示例**:
```python
from apps.crawler.tools.list_fetcher_tool import fetch_tender_list

# 在 deer-flow Agent 中调用
result = await fetch_tender_list(
    source_url="http://api.example.com/tender/list",
    site_type="api",
    max_pages=3,
    api_config=json.dumps({
        "url": "http://api.example.com/tender/list",
        "method": "GET",
        "response_path": "data.list",
        "field_mapping": {
            "title_field": "title",
            "url_field": "url"
        }
    })
)
```

### 2.2 fetch_tender_detail - 详情获取 Tool

**用途**: 获取招标公告详情页内容（支持 HTML 和 PDF）

**参数**:
```python
{
    "url": "http://example.com/detail/123",  # 必需：详情页 URL
    "title": "办公设备采购招标公告",          # 可选：标题
    "extract_pdf": True                       # 可选：是否提取 PDF 内容
}
```

**返回值**:
```python
{
    "url": "http://example.com/detail/123",
    "html": "<html>...</html>",
    "success": True,
    "attachments_count": 2,
    "has_pdf_content": True,
    "main_pdf_url": "http://example.com/doc/notice.pdf",
    "main_pdf_filename": "notice.pdf",
    "content_type": "html"  # 或 "pdf"
}
```

**使用示例**:
```python
from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

# 获取详情页
result = await fetch_tender_detail(
    url="http://example.com/detail/123",
    title="办公设备采购招标公告",
    extract_pdf=True
)

# 解析结果
data = json.loads(result)
if data["success"]:
    html_content = data["html"]
    has_pdf = data["has_pdf_content"]
```

## 3. Workflow 编排

### 3.1 TenderExtractionWorkflow

**用途**: 组合 List/Detail Tools，提供完整的提取流程

**配置**:
```python
from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow, WorkflowConfig

config = WorkflowConfig(
    max_concurrent_requests=5,  # 最大并发请求数
    max_retries=3,              # 最大重试次数
    request_delay=1.0,          # 请求间隔（秒）
    max_items_per_source=100    # 每源最大项目数
)

workflow = TenderExtractionWorkflow(config=config)
```

### 3.2 方法说明

#### extract() - 仅获取列表

```python
result = await workflow.extract(
    source_url="http://api.example.com/list",
    site_type="api",
    max_pages=5,
    api_config=json.dumps({...}),
    max_items=50
)

# 返回 ExtractionResult
# result.items - 列表项
# result.total_fetched - 获取数量
# result.success - 是否成功
```

#### extract_with_details() - 获取列表 + 详情

```python
result = await workflow.extract_with_details(
    source_url="http://api.example.com/list",
    site_type="api",
    max_pages=5,
    max_items=50,
    concurrent_limit=5,  # 并发获取详情
    fetch_details=True    # 是否获取详情
)

# 返回 ExtractionResult
# result.items - 列表项
# result.details - 详情内容列表
# result.total_with_details - 成功获取详情的数量
```

#### extract_batch() - 批量处理多源

```python
sources = [
    {"url": "http://source1.com/api", "type": "api"},
    {"url": "http://source2.com/api", "type": "api"}
]

results = await workflow.extract_batch(
    sources=sources,
    max_items_per_source=50,
    fetch_details=True
)

# 返回 List[ExtractionResult]
```

### 3.3 完整 Workflow 示例

```python
import json
import asyncio
from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

async def main():
    workflow = TenderExtractionWorkflow()

    # 提取列表 + 详情
    result = await workflow.extract_with_details(
        source_url="http://ggzy.zwfw.gov.cn/api/tender/list",
        site_type="api",
        api_config=json.dumps({
            "url": "http://ggzy.zwfw.gov.cn/api/tender/list",
            "method": "GET",
            "response_path": "data.records",
            "field_mapping": {
                "title_field": "tenderName",
                "url_field": "detailUrl",
                "date_field": "publishTime"
            }
        }),
        max_items=10,
        concurrent_limit=5
    )

    if result.success:
        print(f"获取 {result.total_fetched} 条公告")
        print(f"详情获取成功 {result.total_with_details} 条")

        for item, detail in zip(result.items, result.details):
            print(f"标题: {item['title']}")
            print(f"详情成功: {detail.get('success')}")

    # 查看指标
    metrics = workflow.get_metrics()
    print(f"列表调用: {metrics['list_calls']}")
    print(f"详情调用: {metrics['detail_calls']}")
    print(f"错误数: {metrics['errors']}")

asyncio.run(main())
```

## 4. 字段优先级和提取策略

### 2.1 核心字段优先级

```
P0 (必需): title, tenderer, publish_date
P1 (重要): budget_amount, notice_type, region, items[]
P2 (补充): project_number, industry, contact_info, description, technical_parameters[]
P3 (附件): pdf_content, attachments[]
```

### 2.2 提取策略层级

```
Level 1: 列表页预提取 (FieldOptimizationAgent)
  └── 置信度 ≥ 0.7 → 直接使用

Level 2: 正则规则提取 (IntelligentExtractor)
  └── 置信度 ≥ 0.6 → 直接使用

Level 3: LLM 智能提取 (LLMExtractionService)
  └── 置信度 ≥ 0.5 → 接受并记录

Level 4: 降级处理
  └── 标记为低质量数据，待人工审核
```

### 2.3 招标人提取增强（解决用户痛点）

```python
TENDERER_PATTERNS = {
    'primary': [
        r'采\s*购\s*人[：:]\s*([^\n]+)',
        r'招\s*标\s*人[：:]\s*([^\n]+)',
        r'采\s*购\s*单\s*位[：:]\s*([^\n]+)',
    ],
    'fallback': [
        r'(?:采购人|招标人|采购单位)\s*[：:]\s*([^\n]{2,50})',
    ],
    'cross_validate': [
        # 与标题中的单位名交叉验证
        # 与历史记录中的招标人匹配
    ]
}
```

## 3. 工作流程

### 3.1 API 型网站提取流程

```yaml
steps:
  - name: detect_api_endpoint
    action: analyze_url_pattern
    output: api_url

  - name: fetch_api_data
    action: http_get_with_retry
    params:
      url: "{api_url}"
      headers:
        User-Agent: "Biaoxun/1.0"
      retry_config:
        max_retries: 3
        base_delay: 1.0

  - name: parse_json_response
    action: json_path_extract
    params:
      mappings:
        title: "$.data.title"
        tenderer: "$.data.purchaser"
        budget: "$.data.budgetAmount"
        publish_date: "$.data.publishDate"

  - name: validate_and_normalize
    action: field_validation
    skills:
      - field-validation
```

### 3.2 静态 HTML 型网站提取流程

```yaml
steps:
  - name: fetch_html
    action: http_get_with_retry
    output: html_content

  - name: intelligent_extract
    action: run_extractor
    params:
      extractor: IntelligentExtractor
      input: "{html_content}"
      patterns:
        tenderer: "采购人：(.+?)(?=\\n|联系人)"
        contact_person: "联系人：(.+?)(?=\\n|电话)"
        contact_phone: "电话：([\\d-]+)"
    output: extracted_data

  - name: check_confidence
    condition: "{extracted_data.confidence} >= 0.6"
    on_true: accept_result
    on_false: fallback_to_llm

  - name: fallback_to_llm
    action: call_llm_service
    skills:
      - field-validation
```

### 3.3 动态 JS 型网站提取流程

```yaml
steps:
  - name: launch_browser
    action: playwright_init
    params:
      headless: true
      timeout: 30000

  - name: navigate_and_wait
    action: page_goto
    params:
      url: "{target_url}"
      wait_for: "networkidle"

  - name: extract_rendered_html
    action: page_content
    output: rendered_html

  - name: extract_with_pipeline
    action: run_extraction_pipeline
    input: "{rendered_html}"
```

## 4. 正文信息完整提取（解决用户痛点）

### 4.1 完整字段提取流程

```python
EXTRACTION_FIELDS = {
    # P0 - 必需字段
    'title': {'required': True, 'confidence_threshold': 0.8},
    'tenderer': {'required': True, 'confidence_threshold': 0.7},
    'publish_date': {'required': True, 'confidence_threshold': 0.8},

    # P1 - 重要字段
    'budget_amount': {'required': False, 'confidence_threshold': 0.6},
    'notice_type': {'required': False, 'confidence_threshold': 0.7},
    'region': {'required': False, 'confidence_threshold': 0.6},
    'items': {'required': False, 'confidence_threshold': 0.5, 'is_list': True},

    # P2 - 补充字段
    'project_number': {'required': False, 'confidence_threshold': 0.5},
    'industry': {'required': False, 'confidence_threshold': 0.5},
    'contact_person': {'required': False, 'confidence_threshold': 0.5},
    'contact_phone': {'required': False, 'confidence_threshold': 0.5},
    'description': {'required': False, 'confidence_threshold': 0.4},
    'technical_parameters': {'required': False, 'confidence_threshold': 0.4, 'is_list': True},

    # P3 - 附件字段
    'pdf_content': {'required': False, 'confidence_threshold': 0.3},
    'attachments': {'required': False, 'confidence_threshold': 0.3, 'is_list': True},
}
```

### 4.2 多源信息融合

```python
def merge_field_values(sources: list, field: str) -> tuple:
    """
    融合多个来源的字段值

    策略:
    1. 优先选择置信度最高的值
    2. 如果置信度相近，选择长度更长的（通常更完整）
    3. 对于数值字段，验证合理性
    """
    candidates = [
        (source[field], source.get(f'{field}_confidence', 0))
        for source in sources
        if field in source and source[field]
    ]

    if not candidates:
        return None, 0.0

    # 按置信度排序
    candidates.sort(key=lambda x: x[1], reverse=True)

    return candidates[0]
```

## 5. 工具调用序列

```python
# 工具定义
tools = [
    {"type": "function", "name": "analyze_website_type"},
    {"type": "function", "name": "fetch_list_page"},
    {"type": "function", "name": "fetch_detail_page"},
    {"type": "function", "name": "extract_with_rules"},
    {"type": "function", "name": "extract_with_llm"},
    {"type": "function", "name": "extract_pdf_content"},
    {"type": "function", "name": "validate_fields"},
    {"type": "function", "name": "calculate_confidence"},
]

# 调用序列示例
tool_calls = [
    # Step 1: 分析网站类型
    {"tool": "analyze_website_type", "args": {"url": "..."}},

    # Step 2: 获取列表页
    {"tool": "fetch_list_page", "args": {"url": "...", "strategy": "..."}},

    # Step 3: 提取列表数据
    {"tool": "extract_with_rules", "args": {"html": "..."}},

    # Step 4: 遍历详情页
    {"tool": "fetch_detail_page", "args": {"url": "..."}},

    # Step 5: 提取详情字段
    {"tool": "extract_with_llm", "args": {"html": "...", "fields": "..."}},

    # Step 6: 如有 PDF，提取内容
    {"tool": "extract_pdf_content", "args": {"pdf_url": "..."}},

    # Step 7: 验证字段
    {"tool": "validate_fields", "args": {"data": "..."}},

    # Step 8: 计算置信度
    {"tool": "calculate_confidence", "args": {"data": "..."}},
]
```

## 6. 最佳实践

### 6.1 网站类型识别

```python
def classify_website_type(url: str, sample_html: str) -> str:
    """
    识别网站类型

    判断逻辑:
    1. 检查 URL 是否包含 api/open/interface 等关键词
    2. 检查响应 Content-Type 是否为 application/json
    3. 检查 HTML 是否包含大量 script 标签但内容稀少
    4. 检查是否有 __NEXT_DATA__ 等 SSR 标记
    """
    if '/api/' in url or '/open/' in url:
        return 'api'

    soup = BeautifulSoup(sample_html, 'html.parser')
    scripts = len(soup.find_all('script'))
    text_length = len(soup.get_text(strip=True))

    if scripts > 10 and text_length < 500:
        return 'dynamic_js'

    return 'static_html'
```

### 6.2 字段置信度计算

```python
CONFIDENCE_WEIGHTS = {
    'title': 0.20,
    'tenderer': 0.20,
    'publish_date': 0.15,
    'budget_amount': 0.15,
    'items': 0.15,
    'notice_type': 0.08,
    'region': 0.05,
    'project_number': 0.02,
}

def calculate_confidence(extracted_data: dict) -> float:
    score = 0.0
    for field, weight in CONFIDENCE_WEIGHTS.items():
        if extracted_data.get(field):
            value = extracted_data[field]
            field_confidence = 0.0

            if isinstance(value, str) and len(value.strip()) > 0:
                field_confidence = min(len(value.strip()) / 100, 1.0)
            elif isinstance(value, (int, float)) and value > 0:
                field_confidence = 1.0
            elif isinstance(value, list) and len(value) > 0:
                field_confidence = 0.8

            score += field_confidence * weight

    return score
```

## 7. 质量保证

### 7.1 数据验证规则

```yaml
validation_rules:
  title:
    - not_empty: true
    - min_length: 5
    - max_length: 500
    - contains_keywords: ["招标", "采购", "中标", "成交"]

  tenderer:
    - not_empty: true
    - min_length: 2
    - max_length: 200
    - pattern: "(公司|中心|局|委|办|院|校|医院)"

  budget_amount:
    - type: "number"
    - min: 100
    - max: 999999999999

  publish_date:
    - type: "date"
    - not_future: true
    - within_days: 365
```

### 7.2 质量等级定义

```yaml
quality_levels:
  HIGH:
    min_score: 0.8
    actions:
      - 直接进入数据库
      - 可用于分析和推荐

  MEDIUM:
    min_score: 0.6
    actions:
      - 进入数据库
      - 标记"待复核"

  LOW:
    max_score: 0.59
    actions:
      - 进入临时表
      - 需要人工审核
```

## 8. 错误处理

参考 `error-recovery` Skill 处理：
- HTTP 429 限流 → 指数退避 + 降低并发
- HTTP 503 服务不可用 → 断路器 + 延迟重试
- 请求超时 → 递增超时 + 重试
- 验证码 → 切换代理/人工介入
- 页面结构变更 → 触发告警 + 规则更新

## 9. 相关资源

### 9.1 deer-flow Tools

- [ListFetcherTool](../../backend/apps/crawler/tools/list_fetcher_tool.py) - 列表页爬取 Tool
  - `fetch_tender_list()` - 获取招标公告列表
- [DetailFetcherTool](../../backend/apps/crawler/tools/detail_fetcher_tool.py) - 详情页爬取 Tool
  - `fetch_tender_detail()` - 获取招标详情页内容

### 9.2 deer-flow Workflow

- [TenderExtractionWorkflow](../../backend/apps/crawler/deer_flow/workflow.py) - 完整提取 Workflow
  - `extract()` - 仅获取列表
  - `extract_with_details()` - 获取列表 + 详情
  - `extract_batch()` - 批量处理多源

### 9.3 原有提取器

- [FieldExtractor](../../backend/apps/crawler/agents/agents/field_extractor.py) - 字段提取 Agent
- [IntelligentExtractor](../../backend/apps/crawler/extractors/intelligent_extractor.py) - 智能提取器
- [LLMExtractionService](../../backend/apps/crawler/extractors/llm_extraction_service.py) - LLM 提取服务
