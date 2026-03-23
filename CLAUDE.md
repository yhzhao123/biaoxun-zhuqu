# 招标信息爬取与分析系统

## 项目概述
全栈应用，用于爬取招标网站信息、分类整理、深度分析并可视化展示。

## 技术栈
- 后端: Python (FastAPI) + Celery + Redis
- 爬虫: Scrapy / Playwright
- 数据库: PostgreSQL + Elasticsearch
- 前端: React + TypeScript + Tailwind CSS + ECharts
- 部署: Docker + Docker Compose

## 项目结构
```
.
├── backend/          # FastAPI 后端 API
├── crawler/          # 爬虫系统
├── frontend/         # React 前端
├── analytics/        # 数据分析模块
├── docs/             # 文档
└── docker-compose.yml
```

## 开发规范
- 遵循 PEP8 (Python)
- 使用 TypeScript 严格模式
- BDD 测试驱动开发
- 所有代码需经过 code-reviewer 审查

## 核心功能
1. 多源招标网站爬取
2. 信息提取与结构化（招标/中标、招标人、中标人、金额、采购物品）
3. 按单位/招标人智能分类
4. 深度分析引擎（商机识别、趋势分析）
5. 可视化仪表盘
