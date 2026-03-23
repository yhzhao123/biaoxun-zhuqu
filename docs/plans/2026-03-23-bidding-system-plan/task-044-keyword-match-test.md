# Task 044: Keyword Matching - Test Implementation

## Task Header
| Field | Value |
|-------|-------|
| Task ID | 044 |
| Task Name | Keyword Matching Algorithm Test Implementation |
| Task Type | test |
| Dependencies | 043 (Subscription Management Implementation) |
| Status | pending |

## Description
Implement comprehensive test suite for the keyword matching algorithm and rule engine. This includes unit tests for different match types (exact, contains, starts_with, ends_with, regex), integration tests for the matching engine, and performance tests to ensure matching can handle high volumes of bidding data efficiently.

## Files to Create/Modify

### Create Files
1. `tests/unit/services/test_matching_service.py` - Unit tests for matching service
2. `tests/unit/utils/test_matchers.py` - Unit tests for matcher utilities
3. `tests/unit/rules/test_rule_engine.py` - Unit tests for rule engine
4. `tests/integration/test_keyword_matching.py` - Integration tests for matching flow
5. `tests/performance/test_matching_performance.py` - Performance/load tests
6. `tests/fixtures/matching_fixtures.py` - Test fixtures for matching scenarios

### Modify Files
1. `tests/conftest.py` - Add matching test fixtures
2. `pytest.ini` - Add performance test markers

## Implementation Steps

### Step 1: Create Test Fixtures
1. Create bidding opportunity fixtures with various titles/descriptions
2. Create keyword fixtures for each match type:
   - Exact match keywords
   - Contains match keywords
   - Starts_with match keywords
   - Ends_with match keywords
   - Regex pattern keywords
3. Create subscription-rule association fixtures
4. Create expected match result fixtures

### Step 2: Implement Matcher Utility Tests
1. Test `ExactMatcher` class:
   - Match exact text (case sensitive and insensitive)
   - No match on partial text
   - Handle special characters
   - Handle unicode characters

2. Test `ContainsMatcher` class:
   - Match substring anywhere in text
   - Case sensitivity variations
   - Match multiple occurrences
   - Handle empty search text

3. Test `StartsWithMatcher` class:
   - Match at beginning of text
   - Case sensitivity variations
   - No match when not at start

4. Test `EndsWithMatcher` class:
   - Match at end of text
   - Case sensitivity variations
   - No match when not at end

5. Test `RegexMatcher` class:
   - Valid regex patterns match correctly
   - Invalid regex patterns raise appropriate errors
   - Case insensitive flag works
   - Complex patterns (groups, alternations)
   - Performance with complex patterns

### Step 3: Implement Rule Engine Tests
1. Test rule evaluation logic:
   - Single keyword rule evaluation
   - Multiple keyword AND logic
   - Multiple keyword OR logic
   - Mixed required and optional keywords
   - Weighted keyword scoring

2. Test rule priority handling:
   - Higher weight rules rank first
   - Tie-breaking strategies
   - Rule exclusion logic

3. Test rule engine configuration:
   - Minimum score thresholds
   - Maximum results limits
   - Timeout handling

### Step 4: Implement Matching Service Tests
1. Test `match_bidding_opportunity()` method:
   - Match single opportunity against subscriptions
   - Return matching subscription IDs
   - Return match scores and details
   - Handle no matches case

2. Test `batch_match()` method:
   - Process multiple opportunities
   - Return aggregated results
   - Handle partial failures

3. Test `get_matcher_for_type()` factory:
   - Return correct matcher for each type
   - Raise error for invalid type

4. Test caching behavior:
   - Cache compiled regex patterns
   - Cache matcher instances
   - Cache invalidation on pattern update

### Step 5: Implement Integration Tests
1. Test end-to-end matching flow:
   - Create subscription with keywords
   - Insert bidding opportunity
   - Trigger matching process
   - Verify notifications queued

2. Test database transaction handling:
   - Rollback on matching error
   - Consistent state after failures

3. Test with realistic data volumes:
   - 1000+ subscriptions
   - 10000+ keywords
   - 100+ opportunities per batch

### Step 6: Implement Performance Tests
1. Test single opportunity matching performance:
   - Target: <10ms per opportunity with 100 subscriptions
   - Benchmark different match types

2. Test batch matching performance:
   - Target: process 1000 opportunities/minute
   - Memory usage profiling

3. Test regex compilation caching:
   - Measure compilation overhead
   - Verify cache hit rates

## Verification Steps

### Step 1: Run Unit Tests
```bash
pytest tests/unit/utils/test_matchers.py -v --cov=utils.matchers
pytest tests/unit/rules/test_rule_engine.py -v --cov=rules.engine
pytest tests/unit/services/test_matching_service.py -v --cov=services.matching
```
- All unit tests should pass
- Coverage should be >= 85%

### Step 2: Run Integration Tests
```bash
pytest tests/integration/test_keyword_matching.py -v
```
- All integration tests should pass
- End-to-end flow verified

### Step 3: Run Performance Tests
```bash
pytest tests/performance/test_matching_performance.py -v -m performance
```
- Performance benchmarks meet targets
- No memory leaks detected

### Step 4: Coverage Report
```bash
pytest --cov=utils.matchers --cov=rules.engine --cov=services.matching --cov-report=html
```
- Overall coverage >= 85%
- All matcher types covered
- Rule engine paths covered

### Step 5: Edge Case Testing
```bash
# Test with unicode
python -m pytest tests/unit/utils/test_matchers.py -k unicode -v

# Test with special regex characters
python -m pytest tests/unit/utils/test_matchers.py -k regex -v

# Test with empty/null inputs
python -m pytest tests/unit/utils/test_matchers.py -k empty -v
```

## Git Commit Message
```
test: add keyword matching algorithm test suite

- Add unit tests for all matcher types (exact, contains, starts/ends with, regex)
- Add rule engine tests for AND/OR logic and weighted scoring
- Add matching service tests with caching verification
- Add integration tests for end-to-end matching flow
- Add performance benchmarks for matching throughput
- Test edge cases: unicode, special chars, empty inputs
- Achieve 87% code coverage

Refs: task-044
```
