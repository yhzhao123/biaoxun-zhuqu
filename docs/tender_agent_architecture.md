# 招标信息智能提取系统架构设计

基于 DeerFlow 框架重构招标信息提取系统

---

## 核心问题分析

### 当前系统局限
```
┌─────────────────────────────────────────────────────────────┐
│                    当前架构                                   │
├─────────────────────────────────────────────────────────────┤
│  列表API → 基础字段(title, budget, date) → 数据库             │
│           ↓                                                  │
│        缺失: tenderer, description, 附件, 联系方式...          │
└─────────────────────────────────────────────────────────────┘
```

### 目标架构
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TenderAgent 智能体系统                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │ Orchestrator │────→│  Lead Agent  │────→│ Sub-agents   │            │
│  │   (编排器)    │     │   (主控智能体)  │     │  (专业智能体)  │            │
│  └──────────────┘     └──────────────┘     └──────────────┘            │
│                                                        │                 │
│  ┌─────────────────────────────────────────────────────┘                 │
│  │                                                                        │
│  ▼                                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │URL Analyzer │  │  Fetcher    │  │  Extractor  │  │ PDF Proc    │     │
│  │(URL分析)     │  │ (爬取器)     │  │ (字段提取)   │  │ (PDF处理)    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │  Validator  │  │  Composer   │  │  Memory     │                      │
│  │ (结果验证)   │  │ (数据合并)   │  │ (记忆存储)   │                      │
│  └─────────────┘  └─────────────┘  └─────────────┘                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 系统组件设计

### 1. TenderOrchestrator (编排器)

负责协调整个提取流程，管理子智能体的调用顺序。

```python
# backend/apps/crawler/agents/tender_orchestrator.py

class TenderOrchestrator:
    """
    招标信息提取编排器
    协调多个专业智能体完成完整的提取流程
    """

    def __init__(self):
        self.agents = {
            'url_analyzer': URLAnalyzerAgent(),
            'list_fetcher': ListFetcherAgent(),
            'detail_fetcher': DetailFetcherAgent(),
            'field_extractor': FieldExtractorAgent(),
            'pdf_processor': PDFProcessorAgent(),
            'validator': ValidatorAgent(),
            'composer': ComposerAgent(),
        }
        self.memory = TenderMemory()

    async def extract_tender(self, source_config: CrawlSource) -> List[TenderNoticeSchema]:
        """
        完整的招标信息提取流程
        """
        results = []

        # Step 1: 分析爬取源配置
        strategy = await self.agents['url_analyzer'].analyze(source_config)

        # Step 2: 获取列表页数据
        list_items = await self.agents['list_fetcher'].fetch(strategy)

        for item in list_items:
            try:
                # Step 3: 获取详情页
                detail_result = await self.agents['detail_fetcher'].fetch(item)

                # Step 4: 提取字段（HTML）
                extracted = await self.agents['field_extractor'].extract(
                    html=detail_result.html,
                    url=detail_result.url
                )

                # Step 5: 处理PDF附件（如果有）
                if detail_result.attachments:
                    for pdf in detail_result.attachments:
                        pdf_data = await self.agents['pdf_processor'].process(pdf)
                        extracted = await self.agents['composer'].merge(extracted, pdf_data)

                # Step 6: 验证结果
                validation = await self.agents['validator'].validate(extracted)

                # Step 7: 如需要，补充缺失字段
                if not validation.is_complete:
                    extracted = await self._complete_missing_fields(
                        extracted,
                        validation.missing_fields,
                        detail_result.html
                    )

                # Step 8: 保存到记忆
                self.memory.save_extraction(item['url'], extracted)

                results.append(extracted)

            except Exception as e:
                logger.error(f"Failed to extract {item.get('url')}: {e}")
                continue

        return results
```

### 2. URLAnalyzerAgent (URL分析智能体)

分析爬取源，决定最佳爬取策略。

```python
# backend/apps/crawler/agents/url_analyzer.py

class URLAnalyzerAgent:
    """
    URL分析智能体
    分析招标网站结构，决定爬取策略
    """

    SYSTEM_PROMPT = """
    你是一个专业的招标网站结构分析专家。

    给定一个招标网站的配置信息，分析其结构特点，输出最佳爬取策略。

    需要分析的内容：
    1. 网站类型（API驱动/静态页面/动态渲染）
    2. 列表页结构（分页方式、条目定位）
    3. 详情页结构（字段位置、附件位置）
    4. 反爬策略（延迟、请求头、验证）

    输出格式（JSON）：
    {
        "site_type": "api|static|dynamic",
        "list_strategy": {
            "pagination_type": "page_number|offset|cursor",
            "page_param": "page|p|offset",
            "items_per_page": 20
        },
        "detail_strategy": {
            "content_selector": "div.content",
            "attachment_selector": "a[href$=.pdf]",
            "field_hints": {
                "tenderer": "招标人|采购人",
                "contact": "联系人|联系方式"
            }
        },
        "anti_detection": {
            "delay_seconds": 1.5,
            "headers": {...}
        }
    }
    """

    async def analyze(self, source_config: CrawlSource) -> ExtractionStrategy:
        """分析爬取源，返回提取策略"""
        # 可以基于规则或LLM分析
        if source_config.extraction_mode == 'api':
            return self._analyze_api_source(source_config)
        else:
            return await self._analyze_with_llm(source_config)
```

### 3. Fetcher Agents (爬取智能体)

分别处理列表页和详情页爬取。

```python
# backend/apps/crawler/agents/fetcher_agents.py

class ListFetcherAgent:
    """
    列表页爬取智能体
    """

    async def fetch(self, strategy: ExtractionStrategy) -> List[Dict]:
        """
        爬取列表页，获取所有条目基本信息
        """
        items = []

        for page in range(1, strategy.max_pages + 1):
            # 根据策略选择爬取方式
            if strategy.site_type == 'api':
                page_items = await self._fetch_api(strategy, page)
            else:
                page_items = await self._fetch_html(strategy, page)

            if not page_items:
                break

            items.extend(page_items)
            await asyncio.sleep(strategy.delay_seconds)

        return items


class DetailFetcherAgent:
    """
    详情页爬取智能体
    爬取详情页HTML和附件链接
    """

    async def fetch(self, list_item: Dict) -> DetailResult:
        """
        爬取详情页
        """
        url = list_item.get('url')

        # 爬取详情页HTML
        response = await self._fetch_with_retry(url)
        html = response.text

        # 提取附件链接
        attachments = self._extract_attachments(html)

        return DetailResult(
            url=url,
            html=html,
            attachments=attachments,
            list_data=list_item
        )

    def _extract_attachments(self, html: str) -> List[Attachment]:
        """提取PDF等附件链接"""
        soup = BeautifulSoup(html, 'html.parser')
        attachments = []

        # 查找PDF链接
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf'):
                attachments.append(Attachment(
                    url=urljoin(self.base_url, href),
                    filename=link.get_text(strip=True) or 'attachment.pdf',
                    type='pdf'
                ))

        return attachments
```

### 4. FieldExtractorAgent (字段提取智能体)

使用LLM从HTML中提取结构化字段。

```python
# backend/apps/crawler/agents/field_extractor.py

class FieldExtractorAgent:
    """
    字段提取智能体
    使用LLM从HTML/PDF文本中提取招标信息字段
    """

    SYSTEM_PROMPT = """
    你是一个专业的招标信息提取专家。从给定的网页内容中提取招标公告的结构化信息。

    提取字段：
    - title: 公告标题
    - tenderer: 招标人/采购人名称
    - winner: 中标人/成交供应商（中标公告）
    - budget_amount: 预算金额（转换为元）
    - budget_unit: 金额单位（元/万元/亿元）
    - publish_date: 发布日期（YYYY-MM-DD格式）
    - deadline_date: 截止日期/开标日期
    - project_number: 项目编号
    - region: 地区/省份
    - industry: 行业分类
    - contact_person: 联系人姓名
    - contact_phone: 联系电话
    - description: 项目简要描述
    - notice_type: 公告类型（bidding/win/change）

    规则：
    1. 只返回JSON格式，不要其他文字
    2. 无法确定的字段设为null
    3. 金额统一转换为"元"为单位
    4. 日期使用ISO 8601格式
    """

    async def extract(self, html: str, url: str) -> TenderNoticeSchema:
        """
        从HTML中提取字段
        """
        # 预处理HTML，转换为文本
        text_content = self._preprocess_html(html)

        # 构建prompt
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""
            从以下招标公告网页内容中提取结构化信息：

            来源URL: {url}

            网页内容:
            {text_content[:8000]}

            请返回JSON格式的提取结果。
            """}
        ]

        # 调用LLM
        response = await self.llm_service.chat(messages)

        # 解析JSON响应
        return self._parse_extraction_response(response)
```

### 5. PDFProcessorAgent (PDF处理智能体)

下载并解析PDF附件，提取文本和表格。

```python
# backend/apps/crawler/agents/pdf_processor.py

class PDFProcessorAgent:
    """
    PDF处理智能体
    下载并解析招标公告PDF附件
    """

    def __init__(self):
        self.pdf_extractor = PDFTextExtractor()
        self.llm_service = LLMExtractionService()

    async def process(self, attachment: Attachment) -> Dict:
        """
        处理PDF附件
        """
        # 下载PDF
        pdf_bytes = await self._download_pdf(attachment.url)

        # 提取文本
        text = self.pdf_extractor.extract_text(pdf_bytes)

        # 提取表格（招标公告通常有重要信息表格）
        tables = self.pdf_extractor.extract_tables(pdf_bytes)

        # 使用LLM从PDF内容提取字段
        extracted = await self._extract_from_pdf(text, tables)

        return extracted

    async def _extract_from_pdf(self, text: str, tables: List) -> Dict:
        """
        使用LLM从PDF文本提取结构化字段
        """
        prompt = f"""
        从以下PDF文档内容中提取招标信息：

        文档文本:
        {text[:10000]}

        提取的表格:
        {self._format_tables(tables)}

        请提取所有可能的招标字段，以JSON格式返回。
        """

        response = await self.llm_service.chat([
            {"role": "system", "content": FieldExtractorAgent.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])

        return self._parse_response(response)
```

### 6. ValidatorAgent (验证智能体)

验证提取结果的完整性和准确性。

```python
# backend/apps/crawler/agents/validator.py

class ValidatorAgent:
    """
    验证智能体
    验证提取结果的完整性和一致性
    """

    async def validate(self, data: TenderNoticeSchema) -> ValidationResult:
        """
        验证提取结果
        """
        missing_fields = []
        warnings = []

        # 必填字段检查
        required_fields = ['title', 'publish_date', 'notice_type']
        for field in required_fields:
            if not getattr(data, field):
                missing_fields.append(field)

        # 逻辑一致性检查
        if data.notice_type == 'win' and not data.winner:
            warnings.append("中标公告缺少中标人信息")

        if data.budget_amount and data.budget_amount > 1_000_000_000_000:
            warnings.append("预算金额异常，请检查单位转换")

        # 计算置信度
        confidence = self._calculate_confidence(data, missing_fields)

        return ValidationResult(
            is_complete=len(missing_fields) == 0,
            missing_fields=missing_fields,
            warnings=warnings,
            confidence=confidence
        )
```

### 7. ComposerAgent (合并智能体)

合并多源数据（列表页、详情页、PDF）。

```python
# backend/apps/crawler/agents/composer.py

class ComposerAgent:
    """
    数据合并智能体
    合并来自不同来源的招标信息
    """

    async def merge(
        self,
        base: TenderNoticeSchema,
        new_data: Dict,
        source_priority: List[str] = None
    ) -> TenderNoticeSchema:
        """
        合并数据，优先使用置信度高的字段
        """
        # 字段置信度权重
        source_weights = {
            'api_list': 0.7,
            'detail_page': 0.9,
            'pdf': 0.95,
            'llm_extraction': 0.85
        }

        merged = base.to_dict()

        for field, value in new_data.items():
            if value is None:
                continue

            # 如果新数据有更高的置信度，则替换
            current_confidence = merged.get(f'{field}_confidence', 0)
            new_confidence = source_weights.get(new_data.get('source'), 0.8)

            if new_confidence > current_confidence:
                merged[field] = value
                merged[f'{field}_confidence'] = new_confidence

        return TenderNoticeSchema.from_dict(merged)
```

---

## 数据流图

```
┌──────────────────────────────────────────────────────────────────────┐
│                           完整提取流程                                │
└──────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐
  │ CrawlSource │─────────────────┐
  │   (配置)     │                 │
  └─────────────┘                 ▼
                         ┌─────────────────┐
                         │ URLAnalyzerAgent │
                         │   (分析策略)      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ ListFetcherAgent │
                         │   (列表页爬取)    │
                         └────────┬────────┘
                                  │ List[Item]
                                  ▼
                         ┌─────────────────┐
                         │ DetailFetcherAgent│
                         │   (详情页爬取)    │
                         │  ├─ HTML         │
                         │  └─ Attachments  │
                         └────────┬────────┘
                                  │ DetailResult
                                  ▼
                    ┌─────────────────────────────┐
                    │      FieldExtractorAgent    │
                    │         (字段提取)           │
                    │  ┌───────────────────────┐  │
                    │  │  TenderNoticeSchema   │  │
                    │  │  - title              │  │
                    │  │  - budget             │  │
                    │  │  - tenderer           │  │
                    │  │  - ...                │  │
                    │  └───────────────────────┘  │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                             │
                    ▼                             ▼
       ┌─────────────────────┐       ┌─────────────────────┐
       │   PDFProcessorAgent │       │   ValidatorAgent    │
       │   (处理PDF附件)      │       │   (验证结果)         │
       │   ├─ 下载PDF        │       │   ├─ 完整性检查     │
       │   ├─ 提取文本       │       │   ├─ 一致性检查     │
       │   └─ LLM提取字段    │       │   └─ 置信度评分     │
       └──────────┬──────────┘       └──────────┬──────────┘
                  │                              │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                    ┌─────────────────────┐
                    │    ComposerAgent    │
                    │    (数据合并)        │
                    │  合并多源数据        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   TenderMemory      │
                    │   (记忆存储)         │
                    │  保存提取结果        │
                    └─────────────────────┘
```

---

## 与Django集成

```python
# backend/apps/crawler/agents/management/commands/run_tender_agents.py

from django.core.management.base import BaseCommand
from apps.crawler.agents.tender_orchestrator import TenderOrchestrator
from apps.crawler.models import CrawlSource

class Command(BaseCommand):
    help = 'Run tender extraction agents'

    async def handle(self, *args, **options):
        orchestrator = TenderOrchestrator()

        # 获取所有活跃的爬取源
        sources = CrawlSource.objects.filter(status='active')

        for source in sources:
            self.stdout.write(f"Processing source: {source.name}")

            try:
                results = await orchestrator.extract_tender(source)

                for result in results:
                    # 保存到数据库
                    await self.save_tender_notice(result)

                self.stdout.write(
                    self.style.SUCCESS(f"Extracted {len(results)} tenders from {source.name}")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to process {source.name}: {e}")
                )

    async def save_tender_notice(self, data: TenderNoticeSchema):
        """保存提取结果到数据库"""
        from apps.tenders.models import TenderNotice

        # 使用schema的to_model_fields方法
        fields = data.to_model_fields()

        # 检查是否已存在
        existing = TenderNotice.objects.filter(source_url=fields['source_url']).first()
        if existing:
            # 更新现有记录
            for key, value in fields.items():
                setattr(existing, key, value)
            existing.save()
        else:
            # 创建新记录
            TenderNotice.objects.create(**fields)
```

---

## 实施计划

### Phase 1: 核心框架 (2-3天)
- [ ] 复制 DeerFlow 核心代码到项目
- [ ] 创建 `TenderOrchestrator` 编排器
- [ ] 实现 `URLAnalyzerAgent` 和 `ListFetcherAgent`

### Phase 2: 详情提取 (2-3天)
- [ ] 实现 `DetailFetcherAgent`
- [ ] 实现 `FieldExtractorAgent` (LLM提取)
- [ ] 实现 `ValidatorAgent`

### Phase 3: PDF处理 (2-3天)
- [ ] 实现 `PDFProcessorAgent`
- [ ] 集成 pdfplumber/pymupdf
- [ ] 从PDF提取字段

### Phase 4: 集成测试 (1-2天)
- [ ] 集成到现有爬虫系统
- [ ] 编写测试用例
- [ ] 性能优化

---

## 下一步

1. 复制 DeerFlow 核心代码到项目
2. 开始实现 `TenderOrchestrator`
3. 逐个实现各个 Agent

要开始吗？先从复制 DeerFlow 代码开始？