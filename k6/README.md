# Performance Testing

Task 070: Performance Testing Documentation

## Overview

This directory contains comprehensive performance testing tools for the BiaoXun system.

## Backend Performance Tests

Located in `apps/core/performance/`

### Test Types

1. **API Benchmark Tests** (`test_api_benchmark.py`)
   - Individual endpoint performance testing
   - 100 concurrent requests
   - P95 < 500ms, P99 < 1000ms

2. **Load Tests** (`test_load.py`)
   - 100-200 concurrent users
   - Sustained load over time
   - Target: 100 RPS

3. **Stress Tests** (`test_stress.py`)
   - 400-600 concurrent users
   - Gradual ramp-up to find breaking point
   - Step-based load increase

4. **Spike Tests** (`test_spike.py`)
   - Sudden traffic surge: 100 -> 1000 users
   - Recovery time measurement
   - Multiple spike events

5. **Soak Tests** (`test_soak.py`)
   - 1 hour sustained load (200 users)
   - Memory leak detection
   - Performance degradation monitoring

### Running Backend Tests

```bash
# Run all performance tests
cd apps/core/performance
python -m pytest -v -m performance

# Run specific test types
python -m pytest test_load.py -v
python -m pytest test_stress.py -v
python -m pytest test_spike.py -v
python -m pytest test_soak.py -v  # Slow test - 1 hour+

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

## Frontend Performance Tests

Located in `k6/`

### Test Types

1. **Load Test** (`load-test.js`)
   - 100-200 concurrent users
   - Gradual ramp up

2. **Stress Test** (`stress-test.js`)
   - Up to 600 concurrent users
   - Step-based increase

3. **Spike Test** (`spike-test.js`)
   - Sudden surge to 1000 users

4. **Soak Test** (`soak-test.js`)
   - Extended duration testing

### Running K6 Tests

```bash
# Install k6 first
# macOS: brew install k6
# Windows: choco install k6
# Linux: https://k6.io/docs/get-started/installation/

# Run tests
k6 run k6/load-test.js
k6 run k6/stress-test.js
k6 run k6/spike-test.js
k6 run k6/soak-test.js

# Run with custom base URL
k6 run -e BASE_URL=https://example.com k6/load-test.js

# Run with more VUs
k6 run --vus 200 --duration 5m k6/load-test.js
```

## Lighthouse CI

Located in `lighthouse/`

### Configuration

- Performance score: >= 80
- Accessibility score: >= 90
- Best Practices: >= 90
- SEO: >= 90

### Core Web Vitals

- First Contentful Paint: < 1.8s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
- Total Blocking Time: < 200ms

### Running Lighthouse

```bash
# Install Lighthouse CI
npm install -g @lhci/cli

# Run audit
lhci autorun --config=lighthouse/config.js

# Run specific URL
lighthouse http://localhost:3000 --output=html --output-path=./report.html
```

## SLA Thresholds

| Metric | Threshold |
|--------|-----------|
| P95 Response Time | < 500ms |
| P99 Response Time | < 1000ms |
| Error Rate | < 1% |
| Throughput | 100 RPS |

## Performance Metrics

### Collected Metrics

- Total requests
- Successful/failed requests
- Success rate
- Error rate
- Average response time
- Min/Max response time
- P50, P95, P99 percentiles

### Output Format

```json
{
  "total_requests": 1000,
  "successful_requests": 995,
  "failed_requests": 5,
  "success_rate": 99.5,
  "error_rate": 0.5,
  "avg_response_time_ms": 150.5,
  "min_response_time_ms": 45.2,
  "max_response_time_ms": 850.3,
  "p50_ms": 120.0,
  "p95_ms": 380.0,
  "p99_ms": 750.0
}
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run performance tests
        run: |
          cd apps/core/performance
          pytest test_load.py test_stress.py -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run k6 tests
        uses: grafana/k6-action@v0.3.1
        with:
          filename: k6/load-test.js

  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun --config=lighthouse/config.js
```

## Best Practices

1. **Always warm up** - Run tests for a few minutes before collecting metrics
2. **Run multiple times** - Performance varies; run tests 3+ times
3. **Monitor resources** - Watch CPU, memory, and network during tests
4. **Test in isolation** - Run on dedicated environment when possible
5. **Baseline and compare** - Establish baselines and watch for regressions
