# 智能体框架方案分析

## 当前架构问题

### 1. 数据流局限
```
列表API → 基础字段(title, budget, date) → 数据库
         ↓
      缺少: tenderer, description, 附件链接
```

### 2. 缺失能力
- 未进入详情页爬取
- 未下载 PDF 附件
- 未从详情页提取完整字段
- 无智能字段补全

---

## 方案对比

### 方案 A: 增强当前管道（推荐）

在现有 ExtractionPipeline 基础上增加：

```python
class EnhancedExtractionPipeline:
    """
    增强提取管道
    """
    def process_tender(self, list_item: Dict) -> TenderNoticeSchema:
        # 1. 基础字段（来自列表API）
        base_data = self.extract_from_list(list_item)

        # 2. 获取详情页（新）
        detail_url = list_item.get('url')
        if detail_url:
            detail_html = self.fetch_detail(detail_url)
            detail_data = self.extract_from_detail(detail_html)
            base_data.update(detail_data)

        # 3. 下载PDF附件（新）
        attachments = self.extract_attachments(detail_html)
        for pdf_url in attachments:
            pdf_content = self.download_pdf(pdf_url)
            pdf_text = self.extract_pdf_text(pdf_content)
            # 用PDF内容补全缺失字段
            pdf_data = self.extract_from_pdf(pdf_text)
            base_data = self.merge_data(base_data, pdf_data)

        # 4. LLM智能补全（已有）
        if base_data.confidence < 0.8:
            llm_data = self.llm_extraction_service.extract(
                html=detail_html,
                pdf_text=pdf_text if attachments else None
            )
            base_data = self.merge_with_confidence(base_data, llm_data)

        return base_data
```

**优点：**
- 渐进式改进，不影响现有功能
- 保持控制，每个步骤可配置
- 成本可控（只在必要时调用LLM）

**缺点：**
- 需要编写更多规则代码
- 状态管理较复杂

---

### 方案 B: 智能体框架（AutoGen/LangChain Agent）

使用多智能体协作架构：

```python
class TenderExtractionOrchestrator:
    """
    招标信息提取智能体编排器
    """

    def __init__(self):
        # 定义多个专业智能体
        self.agents = {
            'url_analyzer': URLAnalyzerAgent(),      # 分析URL结构
            'fetcher': FetchAgent(),                  # 爬取内容
            'field_extractor': FieldExtractorAgent(), # 字段提取
            'pdf_processor': PDFProcessorAgent(),     # PDF处理
            'validator': ValidatorAgent(),            # 结果验证
            'composer': ComposerAgent(),              # 数据合并
        }

    async def extract(self, tender_url: str) -> TenderNoticeSchema:
        """
        多智能体协作提取
        """
        # Agent 1: 分析URL决定策略
        strategy = await self.agents['url_analyzer'].analyze(tender_url)

        # Agent 2: 爬取详情页
        content = await self.agents['fetcher'].fetch(
            url=tender_url,
            strategy=strategy
        )

        # Agent 3: 提取字段（LLM驱动）
        extracted = await self.agents['field_extractor'].extract(
            html=content.html,
            instructions=strategy.extraction_hints
        )

        # Agent 4: 处理PDF附件（如果有）
        if content.has_attachments:
            for pdf in content.attachments:
                pdf_result = await self.agents['pdf_processor'].process(pdf)
                extracted = await self.agents['composer'].merge(
                    extracted,
                    pdf_result
                )

        # Agent 5: 验证完整性
        validation = await self.agents['validator'].check(extracted)

        # Agent 6: 补充缺失字段（通过LLM推理）
        if not validation.is_complete:
            extracted = await self.agents['field_extractor'].infer_missing(
                extracted,
                validation.missing_fields,
                content.html
            )

        return extracted
```

**优点：**
- 自适应性更强
- 代码结构清晰，每个Agent职责单一
- 可以自然语言描述提取规则
- 容易扩展新功能（如自动处理新网站）

**缺点：**
- 引入复杂依赖（AutoGen/LangChain）
- LLM调用次数更多，成本更高
- 调试更困难（黑盒推理）
- 响应时间更长
- 需要大量Few-shot示例

---

## 推荐方案：混合架构

对于招标信息提取这个场景，我建议采用**"规则为主，智能体为辅"**的混合架构：

### 核心原则

1. **确定性操作用规则**（爬取、PDF解析、数据存储）
2. **不确定性操作用智能体**（字段提取、内容理解、缺失推断）
3. **成本敏感操作降级**（先规则提取，置信度低时才用LLM）

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Extraction Pipeline                  │
├─────────────────────────────────────────────────────────┤
│  Stage 1: 数据获取（规则驱动）                            │
│  ├── 列表API/页面爬取                                    │
│  ├── 详情页爬取（新）                                    │
│  └── PDF下载（新）                                       │
├─────────────────────────────────────────────────────────┤
│  Stage 2: 内容提取（混合）                                │
│  ├── CSS选择器提取（优先，低成本）                         │
│  ├── 正则表达式提取（补充）                                │
│  └── LLM智能提取（兜底，高成本）                          │
├─────────────────────────────────────────────────────────┤
│  Stage 3: PDF处理（新）                                   │
│  ├── PDF转文本（pdfplumber/pymupdf）                      │
│  ├── 表格提取                                            │
│  └── LLM从PDF文本提取字段                                │
├─────────────────────────────────────────────────────────┤
│  Stage 4: 数据合并与验证（规则+LLM）                       │
│  ├── 字段置信度评分                                       │
│  ├── 冲突解决（多源数据）                                 │
│  └── LLM验证完整性                                       │
└─────────────────────────────────────────────────────────┘
```

### 具体实现建议

#### 1. 详情页爬取增强

```python
# backend/apps/crawler/spiders/detail_fetcher.py
class DetailFetcher:
    """
    详情页爬取器
    """
    async def fetch_and_extract(self, list_items: List[Dict]) -> List[Dict]:
        results = []
        for item in list_items:
            # 获取详情页
            detail_html = await self.fetch(item['url'])

            # 提取详情字段
            detail_data = {
                'tenderer': self.extract_tenderer(detail_html),
                'description': self.extract_description(detail_html),
                'contact_person': self.extract_contact(detail_html),
                'contact_phone': self.extract_phone(detail_html),
                'attachments': self.extract_attachments(detail_html),
            }

            # 合并列表页数据
            item.update(detail_data)
            results.append(item)

        return results
```

#### 2. PDF处理模块

```python
# backend/apps/crawler/processors/pdf_processor.py
class PDFProcessor:
    """
    PDF文档处理器
    """
    def __init__(self):
        self.pdf_extractor = PDFTextExtractor()
        self.llm_service = LLMExtractionService()

    async def process(self, pdf_url: str) -> Dict:
        # 下载PDF
        pdf_content = await self.download(pdf_url)

        # 提取文本
        text = self.pdf_extractor.extract_text(pdf_content)

        # 提取表格（招标公告通常有关键信息表格）
        tables = self.pdf_extractor.extract_tables(pdf_content)

        # LLM从PDF文本提取结构化字段
        extracted = self.llm_service.extract_from_text(
            text=text,
            tables=tables,
            schema=TenderNoticeSchema
        )

        return extracted
```

#### 3. 智能字段补全Agent

```python
# backend/apps/crawler/agents/field_completion_agent.py
class FieldCompletionAgent:
    """
    字段补全智能体
    当某些字段缺失时，智能推断补全
    """

    SYSTEM_PROMPT = """你是一个招标信息补全专家。
    给定部分提取的招标信息，请根据上下文和常识补全缺失字段。
    只补全有合理推断的字段，不确定的字段保持null。
    """

    async def complete(self, partial_data: Dict, context: str) -> Dict:
        prompt = f"""
        已提取字段：{json.dumps(partial_data, ensure_ascii=False)}

        上下文内容：
        {context[:3000]}

        请补全缺失字段，以JSON格式返回。
        """

        response = await self.llm.chat(self.SYSTEM_PROMPT, prompt)
        return self.parse_json(response)
```

---

## 实施优先级

### Phase 1: 详情页爬取（高优先级）
- 修改 `DynamicSpider` 支持详情页爬取
- 从详情页提取 tenderer、description 等字段
- 提取附件链接

### Phase 2: PDF下载与解析（中优先级）
- 添加 PDF 下载功能
- 使用 pdfplumber/pymupdf 提取文本
- 从 PDF 补充缺失字段

### Phase 3: 智能补全（低优先级）
- 实现字段补全 Agent
- 添加置信度评分
- 自动决策何时调用 LLM

---

## 总结

| 维度 | 增强当前管道 | 智能体框架 | 推荐 |
|------|------------|-----------|------|
| 开发成本 | 中 | 高 | ✅ 增强管道 |
| 运行成本 | 可控 | 较高 | ✅ 增强管道 |
| 可维护性 | 好 | 一般 | ✅ 增强管道 |
| 扩展性 | 一般 | 好 | 混合方案 |
| 自适应能力 | 弱 | 强 | 混合方案 |

**最终建议：**
使用增强的提取管道作为基础，在特定环节引入轻量级智能体（如字段补全）。这样既保持了系统的可控性，又获得了智能体的灵活性。
