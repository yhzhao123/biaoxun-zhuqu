# 招标信息系统实施计划

> 基于 BDD 的迭代实施计划
> 设计来源: docs/plans/2026-03-23-bidding-system-design/

---

## 执行计划

### 实施阶段划分

```yaml
tasks:
  # Phase 1: 基础设施 (001-005)
  - id: "001"
    subject: "初始化Django项目结构"
    slug: "setup-django-project"
    type: "setup"
    depends-on: []
  - id: "002"
    subject: "配置PostgreSQL和Redis"
    slug: "setup-database-cache"
    type: "setup"
    depends-on: ["001"]
  - id: "003"
    subject: "配置Celery异步任务"
    slug: "setup-celery"
    type: "setup"
    depends-on: ["002"]
  - id: "004"
    subject: "创建基础模型和Admin"
    slug: "setup-base-models"
    type: "setup"
    depends-on: ["002"]
  - id: "005"
    subject: "搭建前端React项目"
    slug: "setup-frontend"
    type: "setup"
    depends-on: []

  # Phase 2: 核心数据层 (006-009)
  - id: "006"
    subject: "招标模型测试"
    slug: "tender-model-test"
    type: "test"
    depends-on: ["004"]
  - id: "007"
    subject: "招标模型实现"
    slug: "tender-model-impl"
    type: "impl"
    depends-on: ["006"]
  - id: "008"
    subject: "Repository层测试"
    slug: "repository-test"
    type: "test"
    depends-on: ["007"]
  - id: "009"
    subject: "Repository层实现"
    slug: "repository-impl"
    type: "impl"
    depends-on: ["008"]

  # Phase 3: 爬虫功能 (010-017)
  - id: "010"
    subject: "爬虫基础架构测试"
    slug: "crawler-base-test"
    type: "test"
    depends-on: ["003"]
  - id: "011"
    subject: "爬虫基础架构实现"
    slug: "crawler-base-impl"
    type: "impl"
    depends-on: ["010"]
  - id: "012"
    subject: "政府采购网爬虫测试"
    slug: "gov-spider-test"
    type: "test"
    depends-on: ["011"]
  - id: "013"
    subject: "政府采购网爬虫实现"
    slug: "gov-spider-impl"
    type: "impl"
    depends-on: ["012"]
  - id: "014"
    subject: "数据去重测试"
    slug: "duplicate-check-test"
    type: "test"
    depends-on: ["009"]
  - id: "015"
    subject: "数据去重实现"
    slug: "duplicate-check-impl"
    type: "impl"
    depends-on: ["014"]
  - id: "016"
    subject: "爬虫任务调度测试"
    slug: "crawler-schedule-test"
    type: "test"
    depends-on: ["011"]
  - id: "017"
    subject: "爬虫任务调度实现"
    slug: "crawler-schedule-impl"
    type: "impl"
    depends-on: ["016"]

  # Phase 4: NLP实体提取 (018-023)
  - id: "018"
    subject: "招标人提取测试"
    slug: "nlp-tenderer-test"
    type: "test"
    depends-on: ["009"]
  - id: "019"
    subject: "招标人提取实现"
    slug: "nlp-tenderer-impl"
    type: "impl"
    depends-on: ["018"]
  - id: "020"
    subject: "金额提取测试"
    slug: "nlp-amount-test"
    type: "test"
    depends-on: ["009"]
  - id: "021"
    subject: "金额提取实现"
    slug: "nlp-amount-impl"
    type: "impl"
    depends-on: ["020"]
  - id: "022"
    subject: "NLP置信度处理测试"
    slug: "nlp-confidence-test"
    type: "test"
    depends-on: ["009"]
  - id: "023"
    subject: "NLP置信度处理实现"
    slug: "nlp-confidence-impl"
    type: "impl"
    depends-on: ["022"]

  # Phase 5: 智能分类 (024-029)
  - id: "024"
    subject: "行业分类测试"
    slug: "industry-classify-test"
    type: "test"
    depends-on: ["009"]
  - id: "025"
    subject: "行业分类实现"
    slug: "industry-classify-impl"
    type: "impl"
    depends-on: ["024"]
  - id: "026"
    subject: "地区分类测试"
    slug: "region-classify-test"
    type: "test"
    depends-on: ["009"]
  - id: "027"
    subject: "地区分类实现"
    slug: "region-classify-impl"
    type: "impl"
    depends-on: ["026"]
  - id: "028"
    subject: "招标人聚类测试"
    slug: "tenderer-cluster-test"
    type: "test"
    depends-on: ["009"]
  - id: "029"
    subject: "招标人聚类实现"
    slug: "tenderer-cluster-impl"
    type: "impl"
    depends-on: ["028"]

  # Phase 6: 搜索与查询 (030-035)
  - id: "030"
    subject: "全文搜索测试"
    slug: "fulltext-search-test"
    type: "test"
    depends-on: ["009"]
  - id: "031"
    subject: "全文搜索实现"
    slug: "fulltext-search-impl"
    type: "impl"
    depends-on: ["030"]
  - id: "032"
    subject: "多条件筛选测试"
    slug: "filter-search-test"
    type: "test"
    depends-on: ["009"]
  - id: "033"
    subject: "多条件筛选实现"
    slug: "filter-search-impl"
    type: "impl"
    depends-on: ["032"]
  - id: "034"
    subject: "搜索结果高亮测试"
    slug: "search-highlight-test"
    type: "test"
    depends-on: ["031"]
  - id: "035"
    subject: "搜索结果高亮实现"
    slug: "search-highlight-impl"
    type: "impl"
    depends-on: ["034"]

  # Phase 7: 商机分析 (036-041)
  - id: "036"
    subject: "商机评分测试"
    slug: "opportunity-score-test"
    type: "test"
    depends-on: ["009"]
  - id: "037"
    subject: "商机评分实现"
    slug: "opportunity-score-impl"
    type: "impl"
    depends-on: ["036"]
  - id: "038"
    subject: "竞品分析测试"
    slug: "competitor-analysis-test"
    type: "test"
    depends-on: ["009"]
  - id: "039"
    subject: "竞品分析实现"
    slug: "competitor-analysis-impl"
    type: "impl"
    depends-on: ["038"]
  - id: "040"
    subject: "个性化推荐测试"
    slug: "recommendation-test"
    type: "test"
    depends-on: ["037"]
  - id: "041"
    subject: "个性化推荐实现"
    slug: "recommendation-impl"
    type: "impl"
    depends-on: ["040"]

  # Phase 8: 订阅与通知 (042-047)
  - id: "042"
    subject: "订阅规则管理测试"
    slug: "subscription-manage-test"
    type: "test"
    depends-on: ["009"]
  - id: "043"
    subject: "订阅规则管理实现"
    slug: "subscription-manage-impl"
    type: "impl"
    depends-on: ["042"]
  - id: "044"
    subject: "关键词匹配测试"
    slug: "keyword-match-test"
    type: "test"
    depends-on: ["043"]
  - id: "045"
    subject: "关键词匹配实现"
    slug: "keyword-match-impl"
    type: "impl"
    depends-on: ["044"]
  - id: "046"
    subject: "通知服务测试"
    slug: "notification-test"
    type: "test"
    depends-on: ["043"]
  - id: "047"
    subject: "通知服务实现"
    slug: "notification-impl"
    type: "impl"
    depends-on: ["046"]

  # Phase 9: 用户权限 (048-051)
  - id: "048"
    subject: "角色权限控制测试"
    slug: "rbac-test"
    type: "test"
    depends-on: ["001"]
  - id: "049"
    subject: "角色权限控制实现"
    slug: "rbac-impl"
    type: "impl"
    depends-on: ["048"]
  - id: "050"
    subject: "数据权限隔离测试"
    slug: "data-isolation-test"
    type: "test"
    depends-on: ["049"]
  - id: "051"
    subject: "数据权限隔离实现"
    slug: "data-isolation-impl"
    type: "impl"
    depends-on: ["050"]

  # Phase 10: 数据可视化 (052-057)
  - id: "052"
    subject: "趋势图表组件测试"
    slug: "trend-chart-test"
    type: "test"
    depends-on: ["005"]
  - id: "053"
    subject: "趋势图表组件实现"
    slug: "trend-chart-impl"
    type: "impl"
    depends-on: ["052"]
  - id: "054"
    subject: "招标人画像组件测试"
    slug: "tenderer-profile-test"
    type: "test"
    depends-on: ["005"]
  - id: "055"
    subject: "招标人画像组件实现"
    slug: "tenderer-profile-impl"
    type: "impl"
    depends-on: ["054"]
  - id: "056"
    subject: "数据导出功能测试"
    slug: "data-export-test"
    type: "test"
    depends-on: ["009"]
  - id: "057"
    subject: "数据导出功能实现"
    slug: "data-export-impl"
    type: "impl"
    depends-on: ["056"]

  # Phase 11: 系统监控 (058-061)
  - id: "058"
    subject: "爬虫监控测试"
    slug: "crawler-monitor-test"
    type: "test"
    depends-on: ["017"]
  - id: "059"
    subject: "爬虫监控实现"
    slug: "crawler-monitor-impl"
    type: "impl"
    depends-on: ["058"]
  - id: "060"
    subject: "性能监控测试"
    slug: "performance-monitor-test"
    type: "test"
    depends-on: ["001"]
  - id: "061"
    subject: "性能监控实现"
    slug: "performance-monitor-impl"
    type: "impl"
    depends-on: ["060"]

  # Phase 12: API与集成 (062-065)
  - id: "062"
    subject: "Tender API测试"
    slug: "tender-api-test"
    type: "test"
    depends-on: ["031", "033", "035"]
  - id: "063"
    subject: "Tender API实现"
    slug: "tender-api-impl"
    type: "impl"
    depends-on: ["062"]
  - id: "064"
    subject: "前端API集成测试"
    slug: "frontend-api-test"
    type: "test"
    depends-on: ["063", "005"]
  - id: "065"
    subject: "前端API集成实现"
    slug: "frontend-api-impl"
    type: "impl"
    depends-on: ["064"]

  # Phase 13: 部署与优化 (066-070)
  - id: "066"
    subject: "Docker配置"
    slug: "docker-config"
    type: "config"
    depends-on: ["065"]
  - id: "067"
    subject: "数据库优化"
    slug: "database-optimize"
    type: "config"
    depends-on: ["063"]
  - id: "068"
    subject: "缓存策略配置"
    slug: "cache-config"
    type: "config"
    depends-on: ["063"]
  - id: "069"
    subject: "E2E测试"
    slug: "e2e-test"
    type: "test"
    depends-on: ["065"]
  - id: "070"
    subject: "性能测试"
    slug: "performance-test"
    type: "test"
    depends-on: ["067", "068"]
```

---

## Task File References

### Phase 1: 基础设施
- [Task 001: 初始化Django项目结构](./task-001-setup-django-project.md)
- [Task 002: 配置PostgreSQL和Redis](./task-002-setup-database-cache.md)
- [Task 003: 配置Celery异步任务](./task-003-setup-celery.md)
- [Task 004: 创建基础模型和Admin](./task-004-setup-base-models.md)
- [Task 005: 搭建前端React项目](./task-005-setup-frontend.md)

### Phase 2: 核心数据层
- [Task 006: 招标模型测试](./task-006-tender-model-test.md)
- [Task 007: 招标模型实现](./task-007-tender-model-impl.md)
- [Task 008: Repository层测试](./task-008-repository-test.md)
- [Task 009: Repository层实现](./task-009-repository-impl.md)

### Phase 3: 爬虫功能
- [Task 010: 爬虫基础架构测试](./task-010-crawler-base-test.md)
- [Task 011: 爬虫基础架构实现](./task-011-crawler-base-impl.md)
- [Task 012: 政府采购网爬虫测试](./task-012-gov-spider-test.md)
- [Task 013: 政府采购网爬虫实现](./task-013-gov-spider-impl.md)
- [Task 014: 数据去重测试](./task-014-duplicate-check-test.md)
- [Task 015: 数据去重实现](./task-015-duplicate-check-impl.md)
- [Task 016: 爬虫任务调度测试](./task-016-crawler-schedule-test.md)
- [Task 017: 爬虫任务调度实现](./task-017-crawler-schedule-impl.md)

### Phase 4: NLP实体提取
- [Task 018: 招标人提取测试](./task-018-nlp-tenderer-test.md)
- [Task 019: 招标人提取实现](./task-019-nlp-tenderer-impl.md)
- [Task 020: 金额提取测试](./task-020-nlp-amount-test.md)
- [Task 021: 金额提取实现](./task-021-nlp-amount-impl.md)
- [Task 022: NLP置信度处理测试](./task-022-nlp-confidence-test.md)
- [Task 023: NLP置信度处理实现](./task-023-nlp-confidence-impl.md)

### Phase 5: 智能分类
- [Task 024: 行业分类测试](./task-024-industry-classify-test.md)
- [Task 025: 行业分类实现](./task-025-industry-classify-impl.md)
- [Task 026: 地区分类测试](./task-026-region-classify-test.md)
- [Task 027: 地区分类实现](./task-027-region-classify-impl.md)
- [Task 028: 招标人聚类测试](./task-028-tenderer-cluster-test.md)
- [Task 029: 招标人聚类实现](./task-029-tenderer-cluster-impl.md)

### Phase 6: 搜索与查询
- [Task 030: 全文搜索测试](./task-030-fulltext-search-test.md)
- [Task 031: 全文搜索实现](./task-031-fulltext-search-impl.md)
- [Task 032: 多条件筛选测试](./task-032-filter-search-test.md)
- [Task 033: 多条件筛选实现](./task-033-filter-search-impl.md)
- [Task 034: 搜索结果高亮测试](./task-034-search-highlight-test.md)
- [Task 035: 搜索结果高亮实现](./task-035-search-highlight-impl.md)

### Phase 7: 商机分析
- [Task 036: 商机评分测试](./task-036-opportunity-score-test.md)
- [Task 037: 商机评分实现](./task-037-opportunity-score-impl.md)
- [Task 038: 竞品分析测试](./task-038-competitor-analysis-test.md)
- [Task 039: 竞品分析实现](./task-039-competitor-analysis-impl.md)
- [Task 040: 个性化推荐测试](./task-040-recommendation-test.md)
- [Task 041: 个性化推荐实现](./task-041-recommendation-impl.md)

### Phase 8: 订阅与通知
- [Task 042: 订阅规则管理测试](./task-042-subscription-manage-test.md)
- [Task 043: 订阅规则管理实现](./task-043-subscription-manage-impl.md)
- [Task 044: 关键词匹配测试](./task-044-keyword-match-test.md)
- [Task 045: 关键词匹配实现](./task-045-keyword-match-impl.md)
- [Task 046: 通知服务测试](./task-046-notification-test.md)
- [Task 047: 通知服务实现](./task-047-notification-impl.md)

### Phase 9: 用户权限
- [Task 048: 角色权限控制测试](./task-048-rbac-test.md)
- [Task 049: 角色权限控制实现](./task-049-rbac-impl.md)
- [Task 050: 数据权限隔离测试](./task-050-data-isolation-test.md)
- [Task 051: 数据权限隔离实现](./task-051-data-isolation-impl.md)

### Phase 10: 数据可视化
- [Task 052: 趋势图表组件测试](./task-052-trend-chart-test.md)
- [Task 053: 趋势图表组件实现](./task-053-trend-chart-impl.md)
- [Task 054: 招标人画像组件测试](./task-054-tenderer-profile-test.md)
- [Task 055: 招标人画像组件实现](./task-055-tenderer-profile-impl.md)
- [Task 056: 数据导出功能测试](./task-056-data-export-test.md)
- [Task 057: 数据导出功能实现](./task-057-data-export-impl.md)

### Phase 11: 系统监控
- [Task 058: 爬虫监控测试](./task-058-crawler-monitor-test.md)
- [Task 059: 爬虫监控实现](./task-059-crawler-monitor-impl.md)
- [Task 060: 性能监控测试](./task-060-performance-monitor-test.md)
- [Task 061: 性能监控实现](./task-061-performance-monitor-impl.md)

### Phase 12: API与集成
- [Task 062: Tender API测试](./task-062-tender-api-test.md)
- [Task 063: Tender API实现](./task-063-tender-api-impl.md)
- [Task 064: 前端API集成测试](./task-064-frontend-api-test.md)
- [Task 065: 前端API集成实现](./task-065-frontend-api-impl.md)

### Phase 13: 部署与优化
- [Task 066: Docker配置](./task-066-docker-config.md)
- [Task 067: 数据库优化](./task-067-database-optimize.md)
- [Task 068: 缓存策略配置](./task-068-cache-config.md)
- [Task 069: E2E测试](./task-069-e2e-test.md)
- [Task 070: 性能测试](./task-070-performance-test.md)

---

## BDD Coverage

| Feature | Scenarios | Task Coverage | Status |
|---------|-----------|---------------|--------|
| 招标信息爬取 | 4 | 010-017 | ✅ 全覆盖 |
| NLP实体提取 | 3 | 018-023 | ✅ 全覆盖 |
| 智能分类 | 3 | 024-029 | ✅ 全覆盖 |
| 商机分析与推荐 | 4 | 036-041 | ✅ 全覆盖 |
| 搜索与查询 | 3 | 030-035 | ✅ 全覆盖 |
| 数据可视化 | 3 | 052-057 | ✅ 全覆盖 |
| 用户权限管理 | 2 | 048-051 | ✅ 全覆盖 |
| 系统监控 | 2 | 058-061 | ✅ 全覆盖 |
| 订阅管理 | 2 | 042-047 | ✅ 全覆盖 |

**总计: 25个BDD场景 → 70个实施任务**

---

## Dependency Chain

```
Phase 1: 基础设施
[001] → [002] → [003]
            ↓
[004] ─────────────→ [006] → [007] → [008] → [009]
                         ↓
Phase 2-11: 核心功能 (并行开发)
[009] → [010-061] (各功能模块)
  ↓
Phase 12: API与集成
[031,033,035] → [062] → [063]
[063,005] → [064] → [065]
  ↓
Phase 13: 部署与优化
[065] → [066,069]
[063] → [067,068] → [070]
```

---

## 实施原则

1. **Red-Green循环**: 每个功能先写测试(Red)，再实现(Green)
2. **单一职责**: 每个任务只修改一个文件或一个功能点
3. **测试隔离**: 单元测试使用Mock隔离外部依赖
4. **提交边界**: 每个任务完成后提交Git
5. **文档同步**: 实现过程中更新文档

---

*本文档由 superpowers:writing-plans 技能生成*
