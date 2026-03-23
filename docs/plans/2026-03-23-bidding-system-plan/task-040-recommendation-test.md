# Task 040: 智能推荐测试 (Recommendation System Test)

## Task Header

| Field | Value |
|-------|-------|
| **Task ID** | 040 |
| **Task Name** | 智能推荐测试 |
| **Type** | test |
| **Depends On** | - |
| **Status** | pending |

## Description

为智能推荐系统编写测试套件，覆盖协同过滤和内容推荐两种算法的单元测试、推荐结果质量评估测试以及推荐API的集成测试。

## Files to Create/Modify

### New Files
- `test/modules/bidding/recommendation/recommendation.service.spec.ts` - 推荐服务测试
- `test/modules/bidding/recommendation/collaborative-filtering.spec.ts` - 协同过滤算法测试
- `test/modules/bidding/recommendation/content-based.spec.ts` - 内容推荐算法测试
- `test/modules/bidding/recommendation/quality-evaluator.spec.ts` - 推荐质量评估测试
- `test/fixtures/recommendation-data.ts` - 推荐测试数据
- `test/mocks/recommendation-engine.mock.ts` - 推荐引擎mock

### Modified Files
- None (test-only task)

## Implementation Steps

### Step 1: Setup Test Data
1. **User-Opportunity Interaction Matrix**:
   - Create test users (20+)
   - Create test opportunities (50+)
   - Generate interaction history (views, bids, wins)

2. **Content Feature Vectors**:
   - Opportunity tags and categories
   - User preference profiles
   - Historical behavior patterns

### Step 2: Write Collaborative Filtering Tests
1. **User-Based CF Tests**:
   - Similarity calculation (cosine, Pearson)
   - Neighbor selection (top-k)
   - Rating prediction
   - Cold start handling

2. **Item-Based CF Tests**:
   - Item similarity matrix
   - Co-occurrence counting
   - Recommendation ranking

3. **Matrix Factorization Tests**:
   - SVD factorization accuracy
   - Latent factor interpretation
   - Prediction error metrics (RMSE, MAE)

### Step 3: Write Content-Based Tests
1. **Feature Extraction Tests**:
   - TF-IDF vectorization
   - Category encoding
   - Tag weighting

2. **Similarity Tests**:
   - Content similarity scoring
   - Profile matching
   - Preference learning

3. **Hybrid Combination Tests**:
   - Weighted hybrid scoring
   - Switching hybrid strategy
   - Feature combination

### Step 4: Write Quality Evaluation Tests
1. **Accuracy Metrics**:
   - Precision@K
   - Recall@K
   - F1 Score
   - NDCG (Normalized Discounted Cumulative Gain)

2. **Diversity Tests**:
   - Intra-list similarity
   - Category coverage
   - Novelty measurement

3. **A/B Test Framework**:
   - Control vs treatment groups
   - CTR (Click-Through Rate) comparison
   - Conversion rate analysis

## Verification Steps

1. **Algorithm Validation**:
   - CF predictions within expected range (0-1)
   - Content similarity scores are normalized
   - Hybrid recommendations combine both sources

2. **Test Coverage**:
   - 80%+ coverage for recommendation module
   - All public methods tested
   - Edge cases (cold start, sparse data)

3. **Performance Tests**:
   - Recommendation generation < 100ms
   - Batch recommendations < 1s for 100 users
   - Memory usage within limits

4. **Example Test Case**:
   ```typescript
   it('should recommend similar opportunities based on user history', async () => {
     const userId = 'USER-001';
     const recommendations = await service.recommend(userId, 10);

     expect(recommendations).toHaveLength(10);
     expect(recommendations[0].score).toBeGreaterThan(0.7);
     expect(recommendations).not.toContain(alreadyBidOpportunity);
   });
   ```

## Git Commit Message

```
test: add recommendation system test suite with CF and content-based tests

- Create test fixtures for user-opportunity interactions
- Add collaborative filtering algorithm tests
- Add content-based recommendation tests
- Implement recommendation quality evaluation metrics
```
