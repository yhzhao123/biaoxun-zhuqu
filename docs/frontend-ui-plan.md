# 招标信息分析系统 - 前端UI/UX规划

## 📋 项目概述

为 "biaoxun-zhuqu" 招标信息爬取与分析系统开发前端界面，对接已完成的 Phase 5 Harness 后端架构。

## 🎯 后端能力 (已就绪)

### Tools ( deer-flow )
1. **classify_tender** - 招标分类
2. **score_opportunity** - 商机评分
3. **analyze_trends** - 趋势分析
4. **aggregate_data** - 数据聚合

### Subagents
1. **ClassificationAgent** - 批量分类
2. **OpportunityAgent** - 商机分析
3. **TrendAnalysisAgent** - 趋势报告

### Skill
- **tender-analytics** - 统一技能入口

## 🎨 页面规划

### 1. 首页 / 仪表板 (Dashboard)
**功能**：系统概览，快速数据展示
**组件**：
- 统计卡片 (今日新增/总数量/总金额)
- 实时推送消息
- 高价值商机预览
- 快速筛选入口

### 2. 招标列表页 (Tender List)
**功能**：查看所有招标信息
**组件**：
- 数据表格 (标题/招标人/地区/金额/状态)
- 分页器
- 筛选器 (地区/行业/金额/时间)
- 搜索框
- 批量操作按钮

### 3. 招标详情页 (Tender Detail)
**功能**：单个招标详情展示
**组件**：
- 基本信息卡片
- 分类标签展示
- 商机评分展示
- 相关推荐

### 4. 商机分析页 (Opportunity Analysis)
**功能**：商机识别与分析
**组件**：
- 商机评分卡片
- 5维雷达图
- 推荐建议列表
- 风险因素提示
- TOP-N 商机排行

### 5. 趋势分析页 (Trend Analysis)
**功能**：市场趋势可视化
**组件**：
- 时间序列折线图
- 地区分布饼图/地图
- 行业热度柱状图
- 金额区间分布图
- 洞察与建议面板

### 6. 数据分类页 (Classification)
**功能**：招标数据分类查看
**组件**：
- 地区分类树
- 行业分类列表
- 金额区间筛选
- 招标人分类

### 7. 实时推送页 (Realtime)
**功能**：WebSocket实时消息
**组件**：
- 消息列表
- 订阅管理
- 预警设置

### 8. 设置页 (Settings)
**功能**：系统配置
**组件**：
- API配置
- 推送设置
- 个人偏好

## 🛠️ 技术栈

- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 或 Tremor (数据可视化专用)
- **状态管理**: Zustand 或 Redux Toolkit
- **图表**: ECharts 或 Tremor Charts
- **样式**: Tailwind CSS
- **HTTP**: Axios + React Query
- **WebSocket**: Socket.io-client

## 📱 响应式设计

- **桌面端**: 1920x1080 (主要)
- **平板**: 1024x768
- **移动端**: 适配基础浏览

## 🎨 设计风格

- **主题**: 专业商务风格
- **主色**: 蓝色系 (#1890ff 或类似)
- **辅色**: 绿色(成功)/橙色(警告)/红色(危险)
- **布局**: 侧边导航 + 顶部栏 + 内容区

## 🔌 API对接

```typescript
// API 端点
const API = {
  // Tools
  classify: '/api/analytics/classify',
  score: '/api/analytics/score',
  trends: '/api/analytics/trends',
  aggregate: '/api/analytics/aggregate',

  // WebSocket
  realtime: 'ws://localhost:8000/ws'
}
```

## 📊 数据模型

```typescript
// Tender 数据类型
interface Tender {
  id: string;
  title: string;
  tenderer: string;
  region: string;
  industry: string;
  amount: number;
  publishDate: string;
  deadlineDate: string;
  status: 'pending' | 'bidding' | 'closed';
  classification?: ClassificationResult;
  opportunityScore?: OpportunityScore;
}

// 分类结果
interface ClassificationResult {
  tendererCategory: Category;
  regionCategory: Category;
  industryCategory: Category;
  amountCategory: Category;
}

// 商机评分
interface OpportunityScore {
  totalScore: number;
  level: 'high' | 'medium' | 'low';
  factors: {
    amountScore: number;
    competitionScore: number;
    timelineScore: number;
    relevanceScore: number;
    historyScore: number;
  };
  recommendations: string[];
  riskFactors: string[];
}
```

## 🚀 开发计划

### Phase 1: 基础架构
1. 项目初始化 (Vite + React + TypeScript)
2. UI库安装配置
3. 路由配置
4. 布局组件开发

### Phase 2: 核心页面
1. 仪表板页
2. 招标列表页
3. 招标详情页

### Phase 3: 分析功能
1. 商机分析页
2. 趋势分析页
3. 数据分类页

### Phase 4: 高级功能
1. 实时推送
2. 设置页
3. 性能优化

## 📝 待决策事项

1. **UI组件库选择**: Ant Design vs Tremor vs Shadcn/UI
2. **图表库选择**: ECharts vs Tremor Charts vs Recharts
3. **状态管理**: Zustand vs Redux Toolkit vs React Context
4. **是否使用前端Skill**: ai-ui-generation skill

## 👥 参与角色

- **UX设计师**: 设计交互流程
- **UI设计师**: 设计视觉稿
- **前端开发**: 实现代码
- **后端对接**: API联调

---

**下一步**: 确定技术栈，开始Phase 1开发
