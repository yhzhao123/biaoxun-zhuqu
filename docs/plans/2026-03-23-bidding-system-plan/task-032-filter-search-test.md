# Task 032: Filter Search Tests (Multi-condition Filtering Test)

## Task Header
| Field | Value |
|-------|-------|
| ID | 032 |
| Name | 筛选搜索测试 |
| Type | test |
| Depends-on | 031 |

## Description

Write comprehensive tests for the multi-condition filtering search functionality. Tests should cover region, industry, budget range, and date range filters both individually and in combination.

## Files to Create/Modify

### New Files
- `src/modules/search/__tests__/filter-search.service.spec.ts` - Unit tests for filter search service
- `src/modules/search/__tests__/filter-search.e2e-spec.ts` - E2E tests for filter search endpoints
- `test/fixtures/search/bidding-search.fixtures.ts` - Test data for filter scenarios

### Modify Files
- `jest.config.js` - Add search module test coverage settings if needed

## Implementation Steps

1. **Test Fixtures Setup**
   - Create 50+ bidding records with varied attributes:
     - Regions: Beijing, Shanghai, Guangdong, Jiangsu, Zhejiang, etc.
     - Industries: IT, Construction, Healthcare, Education, Manufacturing
     - Budget ranges: 0-100k, 100k-1M, 1M-10M, 10M+
     - Date ranges: Past 7 days, 30 days, 90 days, 1 year
   - Include edge cases: null values, boundary values

2. **Unit Tests - Individual Filters**
   - `should filter by single region`
   - `should filter by multiple regions (OR logic)`
   - `should filter by single industry`
   - `should filter by multiple industries`
   - `should filter by budget min threshold`
   - `should filter by budget max threshold`
   - `should filter by budget range`
   - `should filter by publish date after`
   - `should filter by publish date before`
   - `should filter by date range`

3. **Unit Tests - Combined Filters**
   - `should filter by region AND industry`
   - `should filter by region AND budget range`
   - `should filter by all conditions together`
   - `should return empty result for impossible combination`

4. **Unit Tests - Edge Cases**
   - `should handle empty filter object (return all)`
   - `should handle invalid region gracefully`
   - `should handle negative budget values`
   - `should handle future dates`
   - `should handle inverted date range (end < start)`

5. **E2E Tests**
   - `POST /api/search/filter` endpoint tests
   - Validate response structure and pagination
   - Test query parameter serialization for arrays
   - Verify SQL injection prevention

6. **Test Data Builders**
   - Create helper functions for building filter DTOs
   - Create matchers for asserting filter results

## Verification Steps

1. Run unit tests: `npm test -- filter-search.service`
2. Run E2E tests: `npm run test:e2e -- filter-search`
3. Verify coverage: `npm run test:cov -- --collectCoverageFrom='src/modules/search/**/*.ts'`
4. Target coverage: 90%+ lines, 85%+ branches for filter logic
5. Check all test cases pass including edge cases

## Git Commit Message

```
test(search): add filter search unit and e2e tests

- Create test fixtures with 50+ varied bidding records
- Add unit tests for individual and combined filters
- Test region, industry, budget, and date filters
- Include edge cases: nulls, boundaries, invalid inputs
- Add E2E tests for POST /api/search/filter endpoint
- Achieve 90%+ coverage on filter search logic

Refs: #032
```
