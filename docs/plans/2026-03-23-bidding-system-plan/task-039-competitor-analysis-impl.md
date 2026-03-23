# Task 039: 竞争对手分析实现 (Competitor Analysis Implementation)

## Task Header

| Field | Value |
|-------|-------|
| **Task ID** | 039 |
| **Task Name** | 竞争对手分析实现 |
| **Type** | impl |
| **Depends On** | 038 |
| **Status** | pending |

## Description

实现竞争对手分析模块，包括胜率分析算法、趋势图表数据生成、竞争对手画像构建等功能，为投标决策提供数据支持。

## Files to Create/Modify

### New Files
- `src/modules/bidding/competitor/competitor-analysis.service.ts` - 竞争对手分析服务
- `src/modules/bidding/competitor/win-rate-analyzer.ts` - 胜率分析器
- `src/modules/bidding/competitor/trend-calculator.ts` - 趋势计算器
- `src/modules/bidding/competitor/competitor-profile.builder.ts` - 画像构建器
- `src/modules/bidding/competitor/dto/competitor-stats.dto.ts` - 统计数据DTO
- `src/modules/bidding/competitor/dto/trend-data.dto.ts` - 趋势数据DTO
- `src/modules/bidding/competitor/competitor.controller.ts` - REST API控制器

### Modified Files
- `src/modules/bidding/bidding.module.ts` - 注册新服务
- `src/modules/bidding/competitor/competitor.entity.ts` - 添加分析字段

## Implementation Steps

### Step 1: Implement Win Rate Analyzer
1. **Core Calculation Logic**:
   - Query bid history database
   - Calculate win/loss/total ratios
   - Support filtering by date range, category, amount

2. **Segmented Analysis**:
   ```typescript
   interface WinRateAnalysis {
     overall: number;
     byCategory: Record<string, number>;
     byAmountRange: Array<{ range: string; rate: number }>;
     byTimePeriod: Array<{ period: string; rate: number }>;
   }
   ```

3. **Comparative Analysis**:
   - Compare vs industry average
   - Compare vs top 3 competitors
   - Market position indicator

### Step 2: Implement Trend Calculator
1. **Time Series Analysis**:
   - Group data by month/quarter/year
   - Calculate moving averages (3-month, 6-month)
   - Detect trends (rising, falling, stable)

2. **Chart Data Generation**:
   ```typescript
   interface TrendChartData {
     labels: string[];
     datasets: Array<{
       label: string;
       data: number[];
       color: string;
     }>;
   }
   ```

3. **Prediction Support**:
   - Simple linear projection
   - Seasonal adjustment
   - Confidence intervals

### Step 3: Build Competitor Profile
1. **Profile Components**:
   - Company basic info
   - Historical performance
   - Strengths/weaknesses analysis
   - Preferred categories
   - Typical bid ranges

2. **Threat Assessment**:
   - Direct competition score
   - Capability overlap analysis
   - Recent activity level

### Step 4: Create API Endpoints
1. **Endpoints**:
   - GET `/api/v1/competitors/:id/analysis` - 综合分析
   - GET `/api/v1/competitors/:id/win-rate` - 胜率详情
   - GET `/api/v1/competitors/:id/trends` - 趋势数据
   - GET `/api/v1/competitors/leaderboard` - 竞争对手排名

2. **Response Format**:
   ```json
   {
     "competitorId": "COMP-001",
     "name": "ABC Corp",
     "winRate": {
       "overall": 0.35,
       "trend": "rising",
       "vsIndustry": -0.05
     },
     "trends": {
       "last6Months": [0.30, 0.32, 0.35, 0.38, 0.40, 0.42],
       "prediction": 0.43
     },
     "profile": {
       "topCategories": ["IT", "Construction"],
       "avgBidAmount": 500000,
       "threatLevel": "high"
     }
   }
   ```

## Verification Steps

1. **Functionality Tests**:
   - Verify win rate calculations accuracy
   - Check trend detection with known patterns
   - Validate profile completeness

2. **Performance Tests**:
   - Query response < 500ms for single competitor
   - Batch analysis < 3s for 50 competitors
   - Chart generation < 200ms

3. **API Tests**:
   - All endpoints return valid JSON
   - Error handling for invalid IDs
   - Pagination for list endpoints

4. **Integration Verification**:
   - Test with real historical data
   - Compare results with manual calculations
   - Verify chart data renders correctly

## Git Commit Message

```
feat: implement competitor analysis module with win rate and trends

- Add win rate analyzer with segmented analysis capabilities
- Implement trend calculator with moving averages and predictions
- Build competitor profile builder with threat assessment
- Create REST API endpoints for analysis data access
```
