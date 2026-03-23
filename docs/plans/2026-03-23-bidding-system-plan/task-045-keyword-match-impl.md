# Task 045: Keyword Matching - Implementation

## Task Header
| Field | Value |
|-------|-------|
| Task ID | 045 |
| Task Name | Keyword Matching Algorithm Implementation |
| Task Type | impl |
| Dependencies | 044 (Keyword Matching Algorithm Test Implementation) |
| Status | pending |

## Description
Implement the keyword matching algorithm and rule engine for the bidding system. This module matches incoming bidding opportunities against user subscription keywords using various match types (exact, contains, starts_with, ends_with, regex). The rule engine evaluates matches with weighted scoring and supports complex matching logic with AND/OR combinations.

## Files to Create/Modify

### Create Files
1. `utils/matchers.py` - Matcher classes for different match types
2. `rules/engine.py` - Rule evaluation engine
3. `rules/match_result.py` - Match result data structures
4. `services/matching_service.py` - High-level matching service
5. `services/matching_worker.py` - Background matching worker
6. `core/matching_config.py` - Matching configuration settings

### Modify Files
1. `services/__init__.py` - Export matching service
2. `core/config.py` - Add matching configuration
3. `models/subscription.py` - Add matching-related methods if needed

## Implementation Steps

### Step 1: Implement Matcher Classes
1. Create base `Matcher` abstract class:
   - `match(text: str, pattern: str) -> bool` abstract method
   - `validate_pattern(pattern: str) -> bool` method
   - Case sensitivity configuration

2. Implement `ExactMatcher`:
   - Exact string equality comparison
   - Support case insensitive matching
   - Unicode normalization option

3. Implement `ContainsMatcher`:
   - Substring search using `in` operator
   - Support case insensitive matching
   - Handle overlapping matches

4. Implement `StartsWithMatcher`:
   - Prefix matching using `str.startswith()`
   - Support case insensitive matching

5. Implement `EndsWithMatcher`:
   - Suffix matching using `str.endswith()`
   - Support case insensitive matching

6. Implement `RegexMatcher`:
   - Compile and cache regex patterns
   - Validate regex syntax on pattern creation
   - Support case insensitive flag
   - Handle regex compilation errors gracefully
   - Support common regex patterns (word boundaries, character classes)

7. Create `MatcherFactory`:
   - `get_matcher(match_type: str) -> Matcher` method
   - Singleton pattern for matcher instances
   - Register custom matchers

### Step 2: Implement Rule Engine
1. Create `MatchResult` dataclass:
   - subscription_id (UUID)
   - matched_keywords (list of matched keyword details)
   - score (float, weighted sum)
   - match_details (dict with positions, confidence)
   - timestamp (datetime)

2. Create `Rule` class:
   - subscription reference
   - keyword rules (required vs optional)
   - weight configuration
   - minimum threshold

3. Implement `RuleEngine` class:
   - `evaluate(opportunity, rules) -> List[MatchResult]`
   - AND logic: all required keywords must match
   - OR logic: at least one keyword matches
   - Weighted scoring based on keyword weights
   - Sort results by score descending
   - Apply minimum score threshold
   - Limit maximum results

4. Implement scoring algorithm:
   - Base score per matched keyword
   - Weight multiplier from subscription-keyword association
   - Bonus for multiple keyword matches
   - Penalty for partial matches

### Step 3: Implement Matching Service
1. Create `MatchingService` class:
   - `match_opportunity(opportunity_id) -> List[MatchResult]`
   - `match_batch(opportunity_ids) -> Dict[UUID, List[MatchResult]]`
   - `get_active_subscriptions_with_keywords()` query

2. Implement opportunity fetching:
   - Retrieve opportunity by ID
   - Extract searchable text (title, description, category)
   - Preprocess text (normalize, tokenize)

3. Implement subscription fetching:
   - Query active subscriptions
   - Eager load associated keywords
   - Cache results for performance

4. Implement matching orchestration:
   - For each opportunity, match against all subscriptions
   - Use appropriate matcher for each keyword
   - Aggregate results per subscription
   - Apply rule engine scoring

5. Implement result persistence:
   - Store match results in database
   - Track match history
   - Update opportunity match status

### Step 4: Implement Matching Worker
1. Create `MatchingWorker` class:
   - Process opportunities from message queue
   - Batch processing for efficiency
   - Error handling and retry logic
   - Dead letter queue for failed matches

2. Implement worker lifecycle:
   - `start()` - Begin processing
   - `stop()` - Graceful shutdown
   - `pause()` / `resume()` - Flow control

3. Implement metrics collection:
   - Processing rate (opportunities/minute)
   - Match rate (matches/opportunity)
   - Average processing time
   - Error rates

### Step 5: Configuration
1. Create `matching_config.py`:
   - `MATCHING_BATCH_SIZE` (default: 100)
   - `MATCHING_TIMEOUT_SECONDS` (default: 30)
   - `MIN_MATCH_SCORE` (default: 0.5)
   - `MAX_MATCH_RESULTS` (default: 100)
   - `REGEX_CACHE_SIZE` (default: 1000)
   - `MATCHER_CACHE_TTL` (default: 3600 seconds)

2. Add to main config:
   - Feature flags for match types
   - Performance tuning parameters

### Step 6: Performance Optimizations
1. Implement caching:
   - LRU cache for compiled regex patterns
   - Cache matcher instances
   - Cache active subscription queries

2. Implement indexing:
   - Full-text search index on opportunity text
   - Keyword value index with match type

3. Implement batching:
   - Process opportunities in batches
   - Database query batching
   - Result write batching

## Verification Steps

### Step 1: Run Tests
```bash
pytest tests/unit/utils/test_matchers.py -v
pytest tests/unit/rules/test_rule_engine.py -v
pytest tests/unit/services/test_matching_service.py -v
pytest tests/integration/test_keyword_matching.py -v
```
- All tests should pass

### Step 2: Manual Testing
```bash
# Test exact matching
python -c "from utils.matchers import ExactMatcher; m = ExactMatcher(); print(m.match('Construction Project', 'Construction Project'))"

# Test contains matching
python -c "from utils.matchers import ContainsMatcher; m = ContainsMatcher(); print(m.match('Building Construction Project', 'Construction'))"

# Test regex matching
python -c "from utils.matchers import RegexMatcher; m = RegexMatcher(); print(m.match('Construction 2024', r'\\d{4}'))"

# Test rule engine
python -c "from rules.engine import RuleEngine; engine = RuleEngine(); print('Rule engine initialized')"
```

### Step 3: Performance Benchmarking
```bash
python -m pytest tests/performance/test_matching_performance.py -v
```
- Single opportunity matching < 10ms with 100 subscriptions
- Batch processing 1000 opportunities/minute

### Step 4: Load Testing
```bash
# Run matching service under load
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```
- System stable under expected load
- Response times within SLAs

### Step 5: Code Quality
```bash
mypy utils/matchers.py rules/engine.py services/matching_service.py
pylint utils/matchers.py rules/engine.py
black --check utils/matchers.py rules/engine.py services/matching_service.py
```
- No type errors
- No linting errors
- Code formatted

## Git Commit Message
```
feat: implement keyword matching algorithm and rule engine

- Add matcher classes for exact, contains, starts/ends with, and regex
- Implement rule engine with weighted scoring and AND/OR logic
- Create matching service for opportunity-to-subscription matching
- Add background matching worker with queue processing
- Implement caching for regex patterns and matcher instances
- Add configuration for matching performance tuning
- Include metrics collection for monitoring

Performance targets:
- Single opportunity: <10ms with 100 subscriptions
- Batch processing: 1000 opportunities/minute

Refs: task-045
```
