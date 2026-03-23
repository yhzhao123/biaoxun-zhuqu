# 招标信息爬取与分析系统

> 智能招标信息聚合与商机洞察平台

## 功能特性

### 🕷️ 智能爬虫
- 支持多源招标网站爬取
- 动态渲染页面支持（Playwright）
- 反爬策略自动应对
- 增量更新与去重

### 📊 数据提取
- 自动提取关键字段：招标人、中标人、金额、采购物品
- NLP 智能实体识别
- 结构化数据存储

### 🏷️ 智能分类
- 按招标人/采购单位自动聚类
- 行业/地区多维度标签
- 自定义分类规则

### 🔍 深度分析
- 潜在商机识别
- 竞争对手分析
- 采购趋势预测
- 关系图谱构建

### 📈 可视化展示
- 实时数据仪表盘
- 交互式图表（ECharts/D3.js）
- 商机预警推送
- 自定义报表导出

## 快速开始

```bash
# 克隆项目
git clone <repo-url>

# 启动服务
docker-compose up -d

# 访问前端
open http://localhost:3000
```

## 技术架构
- **后端**: FastAPI + Celery + Redis
- **爬虫**: Scrapy + Playwright
- **数据库**: PostgreSQL + Elasticsearch
- **前端**: React + TypeScript + Tailwind CSS
- **部署**: Docker

## 开发指南
参见 [CLAUDE.md](./CLAUDE.md)

## License
MIT
