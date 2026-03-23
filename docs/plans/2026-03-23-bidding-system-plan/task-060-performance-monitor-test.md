# Task 060: Performance Monitoring Test

## Task Header

| Field | Value |
|-------|-------|
| Task ID | 060 |
| Task Name | Performance Monitoring Test |
| Task Type | test |
| Dependencies | 061 (performance-monitor-impl) - blocked-by: 061 |
| Priority | medium |
| Estimated Effort | 4 hours |

## Description

Create comprehensive test suite for the performance monitoring module. Tests should verify API response time tracking, database connection monitoring, and Celery queue length measurement.

## Files to Create/Modify

### Create
- `tests/monitoring/performance/test_api_metrics.py` - API response time tests
- `tests/monitoring/performance/test_db_metrics.py` - Database connection tests
- `tests/monitoring/performance/test_queue_metrics.py` - Celery queue tests
- `tests/monitoring/performance/test_alerts.py` - Performance alert tests
- `tests/monitoring/performance/fixtures.py` - Test fixtures
- `tests/monitoring/performance/conftest.py` - pytest configuration

### Modify
- `tests/monitoring/conftest.py` - Add performance monitoring fixtures
- `.github/workflows/ci.yml` - Ensure monitoring tests run in CI

## Implementation Steps

1. **Setup test infrastructure**
   - Create test directory for performance monitoring
   - Define fixtures for mock database connections
   - Create fixtures for mock Celery broker
   - Setup test data for API endpoints

2. **Write API metrics tests**
   - Test response time measurement middleware
   - Test endpoint-level aggregation
   - Test percentile calculations (p50, p95, p99)
   - Test slow endpoint detection
   - Test request count tracking

3. **Write database metrics tests**
   - Test connection pool size monitoring
   - Test active connection counting
   - Test connection wait time measurement
   - Test query execution time tracking
   - Test database health check

4. **Write Celery queue tests**
   - Test queue length measurement
   - Test worker count detection
   - Test task processing rate calculation
   - Test queue depth alerting thresholds
   - Test multiple queue support

5. **Write alert tests**
   - Test threshold violation detection
   - Test alert notification triggers
   - Test cooldown period handling
   - Test alert severity levels

6. **Write integration tests**
   - Test end-to-end metrics collection
   - Test metrics export to monitoring dashboard
   - Test concurrent metric collection

## Verification Steps

- [ ] All unit tests pass: `pytest tests/monitoring/performance/ -v`
- [ ] Test coverage >= 80% for performance monitoring module
- [ ] API metrics tests verify timing accuracy
- [ ] Database metrics tests verify connection tracking
- [ ] Queue metrics tests pass with mocked broker
- [ ] Alert tests verify threshold logic
- [ ] Tests run successfully in CI pipeline

## Git Commit Message

```
test: add performance monitoring test suite

Add comprehensive tests for performance monitoring:
- API response time tracking and percentile calculation
- Database connection pool monitoring
- Celery queue length and worker metrics
- Alert threshold and notification testing
- End-to-end integration tests

Coverage: 82% for monitoring/performance module
```
