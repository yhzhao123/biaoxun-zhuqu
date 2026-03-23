# Task 061: Performance Monitoring Implementation

## Task Header

| Field | Value |
|-------|-------|
| Task ID | 061 |
| Task Name | Performance Monitoring Implementation |
| Task Type | impl |
| Dependencies | None (foundation task) |
| Priority | medium |
| Estimated Effort | 8 hours |

## Description

Implement the performance monitoring module to track API response times, monitor database connections, and measure Celery queue lengths. This module provides critical insights into system performance and bottlenecks.

## Files to Create/Modify

### Create
- `monitoring/performance/__init__.py` - Module initialization
- `monitoring/performance/api_metrics.py` - API response time tracking middleware
- `monitoring/performance/db_metrics.py` - Database connection monitoring
- `monitoring/performance/queue_metrics.py` - Celery queue monitoring
- `monitoring/performance/collector.py` - Metrics collection coordinator
- `monitoring/performance/alerts.py` - Performance alerting system
- `monitoring/performance/models.py` - Data models for performance metrics
- `monitoring/performance/config.py` - Configuration settings
- `monitoring/performance/dashboard.py` - Dashboard data provider

### Modify
- `middleware/__init__.py` - Register performance middleware
- `settings.py` - Add performance monitoring configuration
- `requirements.txt` - Add monitoring dependencies (prometheus-client, psutil)
- `urls.py` - Add metrics endpoint if exposing via HTTP

## Implementation Steps

1. **Create data models**
   - Define ApiMetric model: endpoint, method, response_time, status_code, timestamp
   - Define DbMetric model: pool_size, active_connections, wait_time, slow_queries
   - Define QueueMetric model: queue_name, length, worker_count, processing_rate
   - Define AlertRule model: metric_type, threshold, severity, cooldown

2. **Implement API metrics middleware**
   - Create ResponseTimeMiddleware class
   - Record request start time on process_request
   - Calculate duration on process_response
   - Store metrics with endpoint details
   - Implement percentile calculation (p50, p95, p99)
   - Track request counts and error rates per endpoint

3. **Implement database metrics**
   - Create DbMetricsCollector class
   - Implement connection pool monitoring using SQLAlchemy events
   - Track active connection count
   - Measure query execution times
   - Detect slow queries (configurable threshold)
   - Monitor connection wait times

4. **Implement Celery queue metrics**
   - Create QueueMetricsCollector class
   - Connect to Redis/RabbitMQ broker to get queue lengths
   - Count active workers via Celery inspect API
   - Calculate tasks per second processing rate
   - Support multiple queue monitoring
   - Track queue depth trends

5. **Implement metrics collector**
   - Create MetricsCollector to coordinate all metric sources
   - Implement periodic collection scheduling
   - Support both push and pull models
   - Add metrics export for Prometheus if enabled

6. **Implement alerting system**
   - Create AlertManager class
   - Define alert rules for:
     - API response time thresholds
     - Database connection pool exhaustion
     - Celery queue backlog
   - Implement notification channels (email, webhook)
   - Add cooldown period to prevent alert spam
   - Support severity levels (warning, critical)

7. **Create dashboard data provider**
   - Implement DashboardData class
   - Provide aggregated metrics for time ranges
   - Support filtering by endpoint, queue, etc.
   - Export data in JSON format for frontend

8. **Add configuration**
   - Enable/disable flags for each metric type
   - Collection intervals
   - Alert thresholds
   - Retention periods
   - Prometheus export settings

## Verification Steps

- [ ] All new files created with proper structure
- [ ] API middleware correctly measures response times
- [ ] Database metrics accurately track connections
- [ ] Queue metrics successfully read from broker
- [ ] Metrics collector runs on schedule
- [ ] Alerts trigger on threshold violations
- [ ] Dashboard data exports correctly
- [ ] Configuration loads from settings
- [ ] No performance impact on normal operations

## Git Commit Message

```
feat: implement performance monitoring module

Add performance monitoring with:
- ResponseTimeMiddleware for API metrics
- DbMetricsCollector for connection monitoring
- QueueMetricsCollector for Celery queues
- AlertManager with configurable thresholds
- Prometheus export support
- Dashboard data API for visualization

Tracks: response times (p50/p95/p99), DB connections,
        queue lengths, worker counts, processing rates
```
