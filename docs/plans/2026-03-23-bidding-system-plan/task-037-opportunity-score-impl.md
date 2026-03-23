# Task 037: 商机评分实现 (Opportunity Score Implementation)

## Task Header

| Field | Value |
|-------|-------|
| **Task ID** | 037 |
| **Task Name** | 商机评分实现 |
| **Type** | impl |
| **Depends On** | 036 |
| **Status** | pending |

## Description

实现多因子商机评分算法，综合考虑时间紧迫度、匹配度、竞争强度、价值和胜率五个维度，为每个商机计算综合评分，支持排序和筛选。

## Files to Create/Modify

### New Files
- `src/modules/bidding/scoring/opportunity-scorer.ts` - 核心评分算法
- `src/modules/bidding/scoring/factors/time-urgency.ts` - 时间紧迫度因子
- `src/modules/bidding/scoring/factors/match-score.ts` - 匹配度因子
- `src/modules/bidding/scoring/factors/competition-intensity.ts` - 竞争强度因子
- `src/modules/bidding/scoring/factors/value-assessment.ts` - 价值评估因子
- `src/modules/bidding/scoring/factors/win-rate.ts` - 胜率因子
- `src/modules/bidding/scoring/types.ts` - 评分类型定义
- `src/modules/bidding/scoring/score-calculator.ts` - 分数计算器

### Modified Files
- `src/modules/bidding/opportunity/opportunity.service.ts` - 集成评分功能
- `src/modules/bidding/opportunity/opportunity.entity.ts` - 添加评分字段

## Implementation Steps

### Step 1: Define Types and Interfaces
1. Create `types.ts` with:
   - `ScoreFactor` interface
   - `ScoringWeights` configuration
   - `OpportunityScore` result type
   - Factor-specific input types

### Step 2: Implement Individual Factors
1. **Time Urgency Factor**:
   - Calculate days until bid deadline
   - Score inversely proportional to remaining time
   - Handle urgent (<7 days), normal (7-30 days), long-term (>30 days)

2. **Match Score Factor**:
   - Compare opportunity requirements with company capabilities
   - Tag matching percentage
   - Historical success rate for similar opportunities

3. **Competition Intensity Factor**:
   - Number of competitors (from historical data)
   - Market saturation indicator
   - Inverse scoring (less competition = higher score)

4. **Value Assessment Factor**:
   - Bid amount tier scoring
   - Strategic value weighting
   - Long-term relationship potential

5. **Win Rate Factor**:
   - Historical win rate for similar opportunities
   - Success rate by industry/category
   - Trend-adjusted prediction

### Step 3: Build Score Calculator
1. Create weighted aggregation algorithm
2. Normalize scores to 0-100 range
3. Implement configurable weights
4. Add caching for performance

### Step 4: Integration
1. Add `score` field to Opportunity entity
2. Create scoring service method
3. Trigger recalculation on opportunity update
4. Expose scoring API endpoint

## Verification Steps

1. **Unit Tests**:
   - Test each factor calculation independently
   - Verify weight aggregation
   - Test edge cases (zero competitors, past deadlines)

2. **Integration Tests**:
   - Full scoring pipeline test
   - Performance test with 1000+ opportunities
   - API endpoint test

3. **Validation**:
   - Score distribution analysis
   - Compare with manual expert scoring
   - Verify sorting effectiveness

4. **Example Output**:
   ```json
   {
     "opportunityId": "OPP-2026-001",
     "totalScore": 87.5,
     "factors": {
       "timeUrgency": 95,
       "matchScore": 82,
       "competitionIntensity": 75,
       "valueAssessment": 90,
       "winRate": 95
     },
     "weights": {
       "timeUrgency": 0.2,
       "matchScore": 0.25,
       "competitionIntensity": 0.2,
       "valueAssessment": 0.2,
       "winRate": 0.15
     }
   }
   ```

## Git Commit Message

```
feat: implement multi-factor opportunity scoring algorithm

- Add five scoring factors: time urgency, match score, competition
  intensity, value assessment, and win rate
- Implement weighted score calculator with normalization
- Integrate scoring into opportunity service
- Add configurable weights and caching support
```
