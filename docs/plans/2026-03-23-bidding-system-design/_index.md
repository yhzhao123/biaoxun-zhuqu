# 招标信息爬取与分析系统设计

> 设计日期: 2026-03-23
> 架构选型: 单体架构 (Django + Celery + PostgreSQL)
> 目标规模: 年处理100-1000万条招标信息

## 上下文与背景

### 业务目标
构建一个全栈应用，实现招标信息的自动爬取、智能分类、深度分析和可视化展示，帮助用户发现潜在商机。

### 核心功能需求
1. **多源爬取**: 支持政府采购网、招投标平台、行业网站、企业平台
2. **信息提取**: 自动提取招标人、中标人、金额、采购物品等关键字段
3. **智能分类**: 按招标人/单位自动聚类，支持多维度标签
4. **深度分析**: AI驱动的商机挖掘、智能推荐、风险预警
5. **可视化**: 实时数据仪表盘、交互式图表、自定义报表

### 约束条件
- **更新频率**: 每日更新
- **部署方式**: 私有化部署（企业内网/私有云）
- **数据规模**: 年处理100-1000万条记录
- **用户角色**: 销售/业务人员、系统管理员、管理层、数据分析师

---

## 需求清单

### 功能性需求

| ID | 需求描述 | 优先级 | 状态 |
|----|----------|--------|------|
| FR-001 | 支持多源招标网站爬取配置 | P0 | 设计中 |
| FR-002 | 招标信息自动去重 | P0 | 设计中 |
| FR-003 | NLP实体提取（招标人、金额、物品） | P0 | 设计中 |
| FR-004 | 按招标人/单位自动分类 | P0 | 设计中 |
| FR-005 | 商机评分与推荐 | P1 | 设计中 |
| FR-006 | 数据可视化仪表盘 | P1 | 设计中 |
| FR-007 | 用户订阅与通知 | P1 | 设计中 |
| FR-008 | 数据导出（Excel/PDF） | P2 | 设计中 |
| FR-009 | 用户权限管理 | P1 | 设计中 |
| FR-010 | 爬虫任务监控 | P2 | 设计中 |

### 非功能性需求

| ID | 需求描述 | 目标值 |
|----|----------|--------|
| NFR-001 | 系统可用性 | 99.9% |
| NFR-002 | 每日爬取完成时间 | < 4小时 |
| NFR-003 | API响应时间（P95） | < 500ms |
| NFR-004 | 并发用户数 | 100+ |
| NFR-005 | 数据保留期限 | 5年 |
| NFR-006 | 私有化部署支持 | 必须 |

---

## 技术选型与架构

### 核心技术栈

| 层级 | 技术选型 | 版本 |
|------|----------|------|
| Web框架 | Django | 4.2 LTS |
| API框架 | Django REST Framework | 3.14 |
| 任务队列 | Celery + Redis | 5.3 / 7.0 |
| 数据库 | PostgreSQL | 15 |
| 缓存 | Redis | 7.0 |
| 爬虫 | Scrapy + Playwright | 2.11 / 1.40 |
| 前端 | React + TypeScript | 18 / 5.0 |
| 部署 | Docker + Docker Compose | - |

### 架构模式

采用**分层架构 + 领域驱动设计（简化版）**：

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│     (React Frontend / Django Admin)    │
├─────────────────────────────────────────┤
│              API Layer                  │
│          (Django REST Framework)       │
├─────────────────────────────────────────┤
│            Service Layer                │
│   (TenderService, CrawlService,        │
│    AIService, NotificationService)     │
├─────────────────────────────────────────┤
│           Repository Layer              │
│     (TenderRepository, etc.)           │
├─────────────────────────────────────────┤
│            Domain Layer                 │
│   (Models: TenderNotice, CrawlTask)    │
└─────────────────────────────────────────┘
```

---

## 详细设计

### 数据库设计

#### 核心表结构

**tender_notices - 招标信息主表**
```sql
CREATE TABLE tender_notices (
    id              BIGSERIAL PRIMARY KEY,
    notice_id       VARCHAR(64) UNIQUE NOT NULL,
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    tenderer        VARCHAR(200),           -- 招标人
    budget          DECIMAL(15,2),          -- 预算金额
    currency        VARCHAR(3) DEFAULT 'CNY',
    publish_date    DATE NOT NULL,
    deadline_date   DATE,
    region          VARCHAR(100),
    industry        VARCHAR(100),
    source_url      VARCHAR(500) NOT NULL,
    source_site     VARCHAR(100),

    -- AI分析字段
    ai_summary      TEXT,
    ai_keywords     JSONB,
    ai_category     VARCHAR(50),
    relevance_score DECIMAL(5,4),

    -- 状态管理
    status          VARCHAR(20) DEFAULT 'pending',
    crawl_batch_id  BIGINT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**crawl_tasks - 爬取任务表**
```sql
CREATE TABLE crawl_tasks (
    id              BIGSERIAL PRIMARY KEY,
    task_name       VARCHAR(100) NOT NULL,
    source_url      VARCHAR(500) NOT NULL,
    crawl_status    VARCHAR(20) DEFAULT 'pending',
    items_crawled   INTEGER DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**user_subscriptions - 用户订阅表**
```sql
CREATE TABLE user_subscriptions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    keywords        JSONB NOT NULL,
    regions         JSONB,
    industries      JSONB,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### 索引策略

```sql
-- 常用查询索引
CREATE INDEX idx_tender_publish_date ON tender_notices(publish_date DESC);
CREATE INDEX idx_tender_region ON tender_notices(region);
CREATE INDEX idx_tender_industry ON tender_notices(industry);

-- 复合索引
CREATE INDEX idx_tender_region_date ON tender_notices(region, publish_date DESC);
CREATE INDEX idx_tender_industry_date ON tender_notices(industry, publish_date DESC);

-- 全文搜索索引
CREATE INDEX idx_tender_title_fts ON tender_notices
    USING GIN(to_tsvector('simple', title));
CREATE INDEX idx_tender_desc_fts ON tender_notices
    USING GIN(to_tsvector('simple', description));

-- GIN索引（JSONB）
CREATE INDEX idx_tender_ai_keywords ON tender_notices
    USING GIN(ai_keywords);
```

### 爬虫架构设计

#### 三层混合爬虫架构

```
┌─────────────────────────────────────────────┐
│           调度层 (Celery Beat)              │
│        定时任务 + 优先级管理                 │
└────────────────────┬────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌─────────┐ ┌──────────┐ ┌──────────┐
   │ 静态爬虫 │ │ 动态爬虫  │ │ API爬虫   │
   │ Scrapy  │ │Playwright│ │ 直接请求  │
   │  workers│ │  workers │ │ +签名验证 │
   └────┬────┘ └────┬─────┘ └────┬─────┘
        │           │            │
        └───────────┴────────────┘
                    │
                    ▼
        ┌───────────────────────┐
│    数据标准化 Pipeline       │
        └───────────────────────┘
```

#### 反爬策略

| 层级 | 策略 | 实现方式 |
|------|------|----------|
| 请求层 | IP代理池 | 自建代理池 + 第三方代理服务 |
| 请求层 | User-Agent轮换 | fake-useragent库 |
| 请求层 | 请求频率随机化 | jitter ±30% |
| 行为层 | 浏览器指纹模拟 | Playwright stealth模式 |
| 验证层 | 验证码识别 | 2Captcha / 本地OCR |

### AI分析模块设计

#### NLP实体提取流程

```
招标文本输入
      │
      ▼
┌─────────────────┐
│   文本预处理    │
│  - 编码转换     │
│  - 分句分段     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│      混合NLP处理            │
│  ┌─────────┐ ┌──────────┐  │
│  │ 规则引擎 │ │ LLM增强  │  │
│  │ - 正则   │ │ - GPT-4  │  │
│  │ - 模板   │ │ - ChatGLM│  │
│  └─────────┘ └──────────┘  │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│      实体融合层             │
│  - 实体对齐                 │
│  - 冲突解决                 │
│  - 置信度加权               │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│      结构化输出             │
│ {招标人, 中标人, 金额, ...} │
└─────────────────────────────┘
```

#### 商机评分算法

商机评分采用加权多因子模型：

```
Score = w1*时效性 + w2*匹配度 + w3*竞争度 + w4*价值度 + w5*历史胜率

其中：
- 时效性 (0-100): 基于发布时间与截止时间的紧迫程度
- 匹配度 (0-100): 招标需求与用户业务的语义相似度
- 竞争度 (0-100): 反比于竞标企业数量
- 价值度 (0-100): 归一化后的预算金额
- 历史胜率 (0-100): 用户在该品类的历史中标率

权重配置: w1=0.15, w2=0.30, w3=0.20, w4=0.20, w5=0.15
```

#### 推荐系统架构

采用**混合推荐**策略：
- **协同过滤**: 基于用户行为矩阵分解
- **内容推荐**: TF-IDF + BERT 文本匹配
- **知识图谱**: 企业关系网络推理

### 前端架构设计

#### 技术选型

| 技术 | 用途 |
|------|------|
| React 18 | UI框架 |
| TypeScript | 类型安全 |
| Tailwind CSS | 样式系统 |
| TanStack Query | 数据获取 |
| Zustand | 状态管理 |
| ECharts | 数据可视化 |
| React Router | 路由管理 |

#### 页面结构

```
/
├── /dashboard              # 数据仪表盘
│   ├── 招标趋势图表
│   ├── 商机推荐卡片
│   └── 快捷入口
├── /tenders                # 招标列表
│   ├── 高级筛选
│   ├── 列表视图
│   └── 详情页
├── /analysis               # 深度分析
│   ├── 商机挖掘
│   ├── 竞争对手分析
│   └── 采购趋势预测
├── /subscriptions          # 订阅管理
│   ├── 关键词订阅
│   └── 通知设置
├── /admin                  # 系统管理
│   ├── 爬虫配置
│   ├── 用户管理
│   └── 系统监控
└── /profile                # 个人中心
```

---

## 部署架构

### Docker Compose 配置

```yaml
version: '3.8'

services:
  # Web应用
  web:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/tenders
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  # Celery Worker
  worker:
    build: ./backend
    command: celery -A config worker -l info
    depends_on:
      - db
      - redis

  # Celery Beat (定时任务)
  beat:
    build: ./backend
    command: celery -A config beat -l info
    depends_on:
      - db
      - redis

  # 数据库
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=tenders
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

  # 缓存
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # 前端
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

---

## 性能与扩展

### 性能优化策略

| 层级 | 优化措施 | 预期效果 |
|------|----------|----------|
| 数据库 | 复合索引 + 分区表 | 查询提升10-100倍 |
| 数据库 | bulk_create批量插入 | 插入速度提升50倍 |
| 应用 | Redis缓存热门查询 | 响应时间<100ms |
| 应用 | 异步处理爬虫任务 | 系统响应无阻塞 |
| 前端 | CDN静态资源 | 加载时间<2s |

### 扩展性规划

| 数据规模 | 架构调整 |
|----------|----------|
| 当前-100万/年 | 单体架构足够 |
| 100-500万/年 | 添加只读副本 |
| 500-1000万/年 | 分离爬虫服务 |
| >1000万/年 | 微服务拆分 |

---

## 风险评估与缓解

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| 反爬策略升级 | 高 | 中 | 多IP代理 + 验证码识别服务 |
| 目标网站改版 | 高 | 中 | 模块化爬虫 + 快速更新 |
| AI分析准确率低 | 中 | 中 | 混合NLP + 人工审核流程 |
| 数据量增长超预期 | 中 | 低 | 水平扩展预留 |
| 私有化部署复杂 | 低 | 低 | Docker一键部署 |

---

## 里程碑规划

| 阶段 | 时间 | 交付物 |
|------|------|--------|
| Phase 1 | 第1-2周 | 基础爬虫 + 数据存储 |
| Phase 2 | 第3-4周 | NLP实体提取 + 分类 |
| Phase 3 | 第5-6周 | AI分析 + 推荐系统 |
| Phase 4 | 第7-8周 | 前端可视化 + 仪表盘 |
| Phase 5 | 第9-10周 | 订阅通知 + 权限管理 |
| Phase 6 | 第11-12周 | 部署优化 + 文档完善 |

---

## Design Documents

- [BDD Specifications](./bdd-specs.md) - 行为场景和测试策略
- [Architecture](./architecture.md) - 系统架构和组件详情
- [Best Practices](./best-practices.md) - 安全、性能和代码质量指南

---

## 附录

### A. 实体定义

```python
ENTITIES = {
    "招标人": ["采购单位", "甲方", "需求方", "招标单位"],
    "中标人": ["中标单位", "供应商", "乙方", "承包商", "中标企业"],
    "金额": ["中标金额", "合同金额", "预算金额", "采购预算"],
    "采购物品": ["项目名称", "货物名称", "服务类型", "采购内容"],
    "时间": ["招标时间", "开标时间", "公示时间", "截止日期"],
    "地点": ["项目地点", "服务区域", "交货地点"],
    "招标编号": ["项目编号", "公告编号", "采购编号"],
    "联系人": ["负责人", "联系电话", "邮箱", "联系人"]
}
```

### B. API 概览

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/tenders | GET | 获取招标列表 |
| /api/v1/tenders/{id} | GET | 获取招标详情 |
| /api/v1/tenders/search | POST | 高级搜索 |
| /api/v1/analysis/opportunities | GET | 获取商机推荐 |
| /api/v1/analysis/trends | GET | 获取趋势分析 |
| /api/v1/subscriptions | GET/POST | 订阅管理 |
| /api/v1/crawl/tasks | GET/POST | 爬虫任务管理 |
| /api/v1/admin/dashboard | GET | 管理仪表盘 |

---

*本文档基于 superpowers:brainstorming 技能生成*
