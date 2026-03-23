# Task 041: 智能推荐实现 (Recommendation System Implementation)

## Task Header

| Field | Value |
|-------|-------|
| **Task ID** | 041 |
| **Task Name** | 智能推荐实现 |
| **Type** | impl |
| **Depends On** | 040 |
| **Status** | pending |

## Description

实现智能推荐系统，结合协同过滤和内容推荐两种算法，为用户个性化推荐高价值商机，支持冷启动处理、实时更新和推荐解释。

## Files to Create/Modify

### New Files
- `src/modules/bidding/recommendation/recommendation.service.ts` - 推荐服务主入口
- `src/modules/bidding/recommendation/collaborative-filtering.service.ts` - 协同过滤实现
- `src/modules/bidding/recommendation/content-based.service.ts` - 内容推荐实现
- `src/modules/bidding/recommendation/hybrid-recommender.ts` - 混合推荐器
- `src/modules/bidding/recommendation/similarity-calculator.ts` - 相似度计算
- `src/modules/bidding/recommendation/recommendation.controller.ts` - API控制器
- `src/modules/bidding/recommendation/dto/recommendation.dto.ts` - 推荐结果DTO
- `src/modules/bidding/recommendation/types.ts` - 类型定义

### Modified Files
- `src/modules/bidding/bidding.module.ts` - 注册推荐服务
- `src/modules/bidding/user/user-preference.service.ts` - 集成偏好学习

## Implementation Steps

### Step 1: Implement Collaborative Filtering
1. **User-Based CF**:
   ```typescript
   interface UserBasedCF {
     calculateSimilarity(userA: User, userB: User): number;
     findNeighbors(userId: string, k: number): User[];
     predictRating(userId: string, opportunityId: string): number;
   }
   ```

2. **Similarity Algorithms**:
   - Cosine similarity
   - Pearson correlation
   - Adjusted cosine for sparse data

3. **Optimization**:
   - Pre-computed similarity matrix
   - Approximate nearest neighbors (ANN)
   - Incremental updates

### Step 2: Implement Content-Based Filtering
1. **Feature Extraction**:
   - TF-IDF for opportunity descriptions
   - Categorical encoding for industry/tags
   - Numerical normalization for bid amounts

2. **User Profile Building**:
   - Aggregate preferred features
   - Weighted by interaction strength
   - Time-decay for old interactions

3. **Content Matching**:
   - Vector space model
   - Cosine similarity between profile and items
   - Category boost factors

### Step 3: Build Hybrid Recommender
1. **Weighted Hybrid**:
   ```typescript
   interface HybridScore {
     cfScore: number;      // 60% weight
     contentScore: number; // 30% weight
     popularityScore: number; // 10% weight
     finalScore: number;
   }
   ```

2. **Contextual Switching**:
   - New user -> Content-based
   - Active user -> Collaborative
   - Sparse data -> Popularity-based

3. **Re-ranking**:
   - Diversity promotion
   - Business rules (exclude bid opportunities)
   - Recency boost

### Step 4: Handle Cold Start
1. **New User Strategies**:
   - Onboarding preference survey
   - Similar user matching (demographics)
   - Trending/popular recommendations

2. **New Item Strategies**:
   - Content-based initial placement
   - Exploration-exploitation balance
   - Category-based propagation

### Step 5: Create API and Features
1. **API Endpoints**:
   - GET `/api/v1/recommendations` - Get recommendations for current user
   - GET `/api/v1/recommendations/:id/explain` - Why this recommendation
   - POST `/api/v1/recommendations/feedback` - User feedback on recommendations

2. **Real-time Updates**:
   - Event-driven recalculation
   - Batch overnight model training
   - A/B test support

3. **Explanation Generation**:
   ```json
   {
     "recommendationId": "REC-001",
     "opportunity": { ... },
     "score": 0.92,
     "reasons": [
       "Similar to opportunities you've won before",
       "Matches your preferred IT category",
       "Popular among similar companies"
     ],
     "source": "hybrid"
   }
   ```

## Verification Steps

1. **Accuracy Validation**:
   - Offline evaluation on historical data
   - Precision@10 > 0.3
   - Recall@10 > 0.2
   - NDCG > 0.5

2. **Online Testing**:
   - A/B test for 2 weeks
   - CTR improvement > 15%
   - Conversion rate tracking

3. **Performance Checks**:
   - Single recommendation < 100ms
   - Batch generation < 500ms
   - Model training < 10 minutes

4. **Business Rules**:
   - Exclude already bid opportunities
   - Filter by user permissions
   - Respect category preferences

## Git Commit Message

```
feat: implement hybrid recommendation system with CF and content-based filtering

- Add collaborative filtering with user-based similarity
- Implement content-based recommendation with TF-IDF features
- Build weighted hybrid recommender with contextual switching
- Create recommendation API with explanation support
```
