# 招标信息爬取与分析系统 (BiaoXun)

> 智能招标信息聚合与商机洞察平台

## 已实现功能

### ✅ Phase 1: 基础设施 (Task 001-005)
- Django + Celery + Redis 项目结构
- React + TypeScript + Tailwind CSS 前端
- PostgreSQL 数据库
- Docker Compose 配置

### ✅ Phase 2: 核心数据层 (Task 006-009)
- TenderNotice 招标公告模型 (27字段)
- TenderRepository 数据访问层
- 完整的 BDD 测试覆盖

### ✅ Phase 3: 爬虫功能 (Task 010-017)
- **Task 010-011**: BaseSpider 爬虫基类 + CrawlTask 任务管理 + Celery 重试机制
- **Task 012-013**: GovSpider 政府采购网爬虫 + HTML 解析 + 字段提取
- **Task 014-015**: DuplicateChecker 数据去重服务 (URL+相似度)
- **Task 016-017**: Celery Beat 定时调度 (每日凌晨 02:00)

### ✅ Phase 4: 前端开发 (Task 018-025)
- **Task 018-019**: React 项目结构 + API 服务层
- **Task 020-021**: TenderList 招标列表组件 + 分页
- **Task 022-023**: TenderDetail 招标详情页面
- **Task 024-025**: SearchFilter 搜索筛选组件
- **页面**: Dashboard 仪表盘, Tenders 列表页

### ✅ Phase 5: 数据分析 (Task 026-035)
- **Task 026-027**: DataCleaningService 数据清洗服务
- **Task 028-031**: StatisticsService 统计分析引擎
- **Task 030-031**: 趋势分析 (日/周/月趋势)
- **Task 032-033**: OpportunityAnalyzer 商机识别算法
- **Task 034-035**: ReportGenerator 日报/周报生成

### ✅ Phase 6: API开发 (Task 036-045)
- **Task 036-037**: TenderViewSet CRUD API
- **Task 038-039**: 全文搜索 API
- **Task 040-041**: Filter API 筛选选项
- **Task 042-043**: Statistics API 统计接口
- **Task 044**: Opportunity API 商机接口
- **Task 045**: Report API 报告接口

## 技术架构

- **后端**: Django 4.2 + Django REST Framework + Celery
- **爬虫**: BeautifulSoup + requests + 反爬策略
- **数据库**: PostgreSQL
- **前端**: React 18 + TypeScript + Tailwind CSS
- **缓存/队列**: Redis
- **部署**: Docker + Docker Compose

## 项目结构

```
.
├── backend/
│   ├── apps/
│   │   ├── users/         # 用户管理
│   │   ├── tenders/       # 招标公告 (Phase 2)
│   │   ├── crawler/       # 爬虫系统 (Phase 3)
│   │   │   ├── spiders/
│   │   │   │   ├── base.py       # BaseSpider
│   │   │   │   └── gov_spider.py # GovSpider
│   │   │   ├── services/
│   │   │   │   └── duplicate.py  # DuplicateChecker
│   │   │   ├── scheduler.py      # Celery Beat 配置
│   │   │   └── tests/            # 57个测试 ✅
│   │   ├── analytics/     # 数据分析 (Phase 5)
│   │   │   └── services.py
│   │   └── api/           # API接口 (Phase 6)
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   ├── config/            # Django配置
│   ├── manage.py
│   └── requirements.txt
├── frontend/              # React前端 (Phase 4)
│   ├── src/
│   │   ├── components/
│   │   │   ├── TenderList.tsx
│   │   │   ├── TenderDetail.tsx
│   │   │   └── SearchFilter.tsx
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx
│   │   │   └── TendersPage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── index.ts
│   └── package.json
└── docker-compose.yml
```

## 快速开始

### Docker Compose 部署

```bash
# 启动所有服务
docker-compose up -d

# 执行数据库迁移
docker-compose exec backend python manage.py migrate

# 创建超级用户
docker-compose exec backend python manage.py createsuperuser

# 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8000/api/v1/
# Admin: http://localhost:8000/admin/
```

### 手动开发环境

**后端:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/tenders/` | GET/POST | 招标列表/创建 |
| `/api/v1/tenders/<id>/` | GET/PUT/DELETE | 招标详情 |
| `/api/v1/tenders/search/` | GET | 全文搜索 |
| `/api/v1/tenders/filter_options/` | GET | 筛选项 |
| `/api/v1/statistics/` | GET | 总览统计 |
| `/api/v1/statistics/trend/` | GET | 趋势数据 |
| `/api/v1/opportunities/` | GET | 商机列表 |
| `/api/v1/reports/daily/` | GET | 日报 |
| `/api/v1/crawler/trigger/` | POST | 触发爬虫 |

## 爬虫配置

爬虫调度在 `apps/crawler/scheduler.py` 中配置：

```python
# 默认每日凌晨 02:00 执行
beat_schedule = {
    'daily-crawl': {
        'task': 'apps.crawler.tasks.scheduled_daily_crawl',
        'schedule': crontab(hour=2, minute=0),
    }
}
```

## 测试

```bash
# 运行所有测试
cd backend
python -m pytest apps/ -v --cov=apps

# 爬虫模块测试 (57个)
python -m pytest apps/crawler/tests/ -v
```

## 开发规范

- 遵循 PEP8 (Python) / ESLint (TypeScript)
- BDD 测试驱动开发 (RED-GREEN-REFACTOR)
- 代码审查 (code-reviewer agent)
- Git 工作流: feature → PR → merge

## License

MIT
