# Task 070: Performance Testing (性能测试)

## Task Header

| Field | Value |
|-------|-------|
| Task ID | 070 |
| Name | Performance Testing |
| Type | test |
| Dependencies | Task 067 (Database Optimization), Task 068 (Cache Strategy) |
| Created | 2026-03-23 |
| Estimated Effort | 8-12 hours |

## Description

Implement comprehensive performance testing for the bidding system using k6 and Lighthouse. Cover load testing, stress testing, spike testing, and endurance testing to validate system behavior under various traffic patterns. Validate that database optimizations and caching strategies provide expected performance improvements.

## Files to Create/Modify

### Create
- `performance/k6/config.js` - K6 configuration and thresholds
- `performance/k6/scenarios/load-test.js` - Standard load test
- `performance/k6/scenarios/stress-test.js` - Stress test
- `performance/k6/scenarios/spike-test.js` - Spike test
- `performance/k6/scenarios/soak-test.js` - Endurance test
- `performance/k6/scenarios/bid-race.js` - Concurrent bidding simulation
- `performance/k6/helpers.js` - Test utilities and data generators
- `performance/lighthouse/config.js` - Lighthouse CI configuration
- `performance/benchmarks/baseline.json` - Performance baseline data
- `performance/reports/template.md` - Report template

### Modify
- `.github/workflows/performance.yml` - CI workflow
- `package.json` - Add performance test scripts
- `docker-compose.perf.yml` - Performance test environment

## Implementation Steps

### Step 1: K6 Configuration

```javascript
// performance/k6/config.js
export const config = {
  // Performance thresholds (SLA)
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% < 500ms, 99% < 1s
    http_req_failed: ['rate<0.01'], // < 1% error rate
    iteration_duration: ['p(95)<2000'], // 95% iterations < 2s
  },

  // Load patterns
  stages: {
    smoke: [
      { duration: '1m', target: 1 },
    ],
    load: [
      { duration: '2m', target: 100 }, // Ramp up
      { duration: '5m', target: 100 }, // Steady state
      { duration: '2m', target: 200 }, // Ramp up
      { duration: '5m', target: 200 }, // Steady state
      { duration: '2m', target: 0 },   // Ramp down
    ],
    stress: [
      { duration: '2m', target: 200 },
      { duration: '5m', target: 200 },
      { duration: '2m', target: 400 },
      { duration: '5m', target: 400 },
      { duration: '2m', target: 600 },
      { duration: '5m', target: 600 },
      { duration: '2m', target: 0 },
    ],
    spike: [
      { duration: '10s', target: 100 },
      { duration: '1m', target: 1000 }, // Spike
      { duration: '10s', target: 100 },
      { duration: '2m', target: 100 },
      { duration: '10s', target: 0 },
    ],
    soak: [
      { duration: '1h', target: 100 }, // 1 hour endurance
    ],
  },

  // Test environment
  baseUrl: __ENV.BASE_URL || 'http://localhost:3000',
  apiUrl: __ENV.API_URL || 'http://localhost:3000/api',
};
```

### Step 2: Load Test Scenario

```javascript
// performance/k6/scenarios/load-test.js
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { config } from '../config.js';
import { getAuthToken, randomAuctionId, randomBidAmount } from '../helpers.js';

// Custom metrics
const bidSuccessRate = new Rate('bid_success_rate');
const auctionLoadTime = new Trend('auction_load_time');
const cacheHitRate = new Rate('cache_hit_rate');
const dbQueryTime = new Trend('db_query_time');

export const options = {
  stages: config.stages.load,
  thresholds: config.thresholds,
};

export function setup() {
  // Create test users and auctions
  const users = [];
  for (let i = 0; i < 50; i++) {
    users.push(getAuthToken(`user${i}@test.com`, 'password123'));
  }
  return { users };
}

export default function(data) {
  const user = data.users[Math.floor(Math.random() * data.users.length)];

  group('Browse Auctions', () => {
    const start = Date.now();
    const res = http.get(`${config.apiUrl}/auctions?status=active&page=1&limit=20`, {
      headers: { 'Authorization': `Bearer ${user.token}` },
    });
    auctionLoadTime.add(Date.now() - start);

    check(res, {
      'auctions list status is 200': (r) => r.status === 200,
      'auctions list returns data': (r) => r.json().data.length > 0,
      'response time < 500ms': (r) => r.timings.duration < 500,
    });

    // Check cache header
    const cacheStatus = res.headers['X-Cache-Status'];
    cacheHitRate.add(cacheStatus === 'HIT');

    sleep(Math.random() * 3 + 1); // 1-4 seconds think time
  });

  group('View Auction Detail', () => {
    const auctionId = randomAuctionId();
    const res = http.get(`${config.apiUrl}/auctions/${auctionId}`, {
      headers: { 'Authorization': `Bearer ${user.token}` },
    });

    check(res, {
      'auction detail status is 200': (r) => r.status === 200,
      'auction has required fields': (r) => {
        const data = r.json();
        return data.id && data.title && data.currentPrice;
      },
    });

    sleep(Math.random() * 5 + 2); // 2-7 seconds think time
  });

  group('Place Bid', () => {
    const auctionId = randomAuctionId();
    const amount = randomBidAmount();

    const payload = JSON.stringify({ auctionId, amount });
    const res = http.post(`${config.apiUrl}/bids`, payload, {
      headers: {
        'Authorization': `Bearer ${user.token}`,
        'Content-Type': 'application/json',
      },
    });

    const success = res.status === 201 || res.status === 200;
    bidSuccessRate.add(success);

    check(res, {
      'bid accepted or valid rejection': (r) =>
        r.status === 201 || r.status === 200 || r.status === 409,
      'bid response time < 200ms': (r) => r.timings.duration < 200,
    });

    // Track DB performance from response header
    const dbTime = res.headers['X-DB-Query-Time'];
    if (dbTime) {
      dbQueryTime.add(parseInt(dbTime));
    }

    sleep(Math.random() * 5 + 3); // 3-8 seconds think time
  });
}

export function teardown(data) {
  // Cleanup test data
  console.log('Load test completed');
}
```

### Step 3: Concurrent Bidding Race Test

```javascript
// performance/k6/scenarios/bid-race.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { config } from '../config.js';

const concurrentBids = new Rate('concurrent_bids_successful');
const raceConditions = new Rate('race_condition_rate');

export const options = {
  scenarios: {
    bid_race: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 100 },
        { duration: '1m', target: 100 },
        { duration: '30s', target: 0 },
      ],
      gracefulRampDown: '10s',
    },
  },
};

// All VUs bid on the same auction
const TARGET_AUCTION_ID = 'test-auction-123';

export default function() {
  const userId = `user-${__VU}`;
  const bidAmount = 100 + (__ITER * 10) + (__VU * 0.01);

  const payload = JSON.stringify({
    auctionId: TARGET_AUCTION_ID,
    amount: bidAmount,
    userId: userId,
  });

  const res = http.post(`${config.apiUrl}/bids`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  const isSuccess = res.status === 201;
  concurrentBids.add(isSuccess);

  // Check for race conditions (multiple successful bids at same amount)
  if (res.status === 409) {
    raceConditions.add(1);
  }

  check(res, {
    'bid request handled': (r) => r.status === 201 || r.status === 200 || r.status === 409,
    'no duplicate bids accepted': (r) => {
      // Server should reject if bid amount already exists and not highest
      return r.status !== 201 || r.json().isHighest;
    },
  });

  sleep(0.1); // Minimal delay for maximum concurrency
}
```

### Step 4: Stress Test Scenario

```javascript
// performance/k6/scenarios/stress-test.js
import http from 'k6/http';
import { check } from 'k6';
import { config } from '../config.js';

export const options = {
  stages: config.stages.stress,
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed: ['rate<0.05'],
  },
};

export default function() {
  // Mixed workload: 60% reads, 30% auction detail, 10% bids
  const rand = Math.random();

  if (rand < 0.6) {
    // Browse auctions
    const res = http.get(`${config.apiUrl}/auctions?status=active`);
    check(res, { 'list OK': (r) => r.status === 200 });
  } else if (rand < 0.9) {
    // View detail
    const res = http.get(`${config.apiUrl}/auctions/${Math.floor(Math.random() * 1000)}`);
    check(res, { 'detail OK': (r) => r.status === 200 || r.status === 404 });
  } else {
    // Place bid (may fail under stress)
    const res = http.post(`${config.apiUrl}/bids`, JSON.stringify({
      auctionId: Math.floor(Math.random() * 1000),
      amount: 100 + Math.random() * 1000,
    }), { headers: { 'Content-Type': 'application/json' } });
    check(res, { 'bid handled': (r) => r.status < 500 });
  }
}
```

### Step 5: Lighthouse CI Configuration

```javascript
// performance/lighthouse/config.js
module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/auctions',
        'http://localhost:3000/auctions/123',
      ],
      numberOfRuns: 3,
      settings: {
        preset: 'desktop',
        throttlingMethod: 'simulate',
        throttling: {
          cpuSlowdownMultiplier: 2,
          downloadThroughputKbps: 15000,
          uploadThroughputKbps: 7500,
          rttMs: 40,
        },
      },
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['warn', { minScore: 0.9 }],
        'categories:seo': ['warn', { minScore: 0.9 }],

        // Core Web Vitals
        'first-contentful-paint': ['warn', { maxNumericValue: 1800 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 200 }],
        'speed-index': ['warn', { maxNumericValue: 3400 }],
      },
    },
    upload: {
      target: 'filesystem',
      outputDir: './performance/lighthouse-report',
    },
  },
};
```

### Step 6: Package.json Scripts

```json
{
  "scripts": {
    "perf:smoke": "k6 run performance/k6/scenarios/load-test.js --env STAGE=smoke",
    "perf:load": "k6 run performance/k6/scenarios/load-test.js",
    "perf:stress": "k6 run performance/k6/scenarios/stress-test.js",
    "perf:spike": "k6 run performance/k6/scenarios/spike-test.js",
    "perf:soak": "k6 run performance/k6/scenarios/soak-test.js --duration 1h",
    "perf:bid-race": "k6 run performance/k6/scenarios/bid-race.js",
    "perf:lighthouse": "lhci autorun --config=performance/lighthouse/config.js",
    "perf:ci": "npm run perf:smoke && npm run perf:load && npm run perf:lighthouse"
  },
  "devDependencies": {
    "@lhci/cli": "^0.12.0"
  }
}
```

## Verification Steps

### Load Test Verification
- [ ] System handles 200 concurrent users
- [ ] p95 response time < 500ms for auction list
- [ ] p95 response time < 200ms for bid submission
- [ ] Error rate < 1%
- [ ] Database CPU < 70% at peak load
- [ ] Redis memory usage remains stable

### Stress Test Verification
- [ ] System degrades gracefully under 600 concurrent users
- [ ] No unhandled errors or crashes
- [ ] Response times increase linearly, not exponentially
- [ ] Database connection pool does not exhaust
- [ ] Cache hit rate remains > 70%

### Spike Test Verification
- [ ] System recovers within 2 minutes after spike
- [ ] No data inconsistency after spike
- [ ] Queue-based operations (bids) process without loss
- [ ] WebSocket connections remain stable

### Race Condition Verification
- [ ] Concurrent bids on same auction handled correctly
- [ ] Only highest bid wins
- [ ] No duplicate bids accepted
- [ ] Bid count remains accurate under concurrency

### Lighthouse Verification
- [ ] Performance score > 90
- [ ] Accessibility score > 95
- [ ] LCP < 2.5s
- [ ] FID/TBT < 200ms
- [ ] CLS < 0.1

### Benchmark Comparison
```bash
# Compare against baseline
k6 run --out json=results.json performance/k6/scenarios/load-test.js
node scripts/compare-benchmark.js results.json performance/benchmarks/baseline.json
```

## Rollback Plan

1. Document performance baseline before optimization
2. Keep previous configuration values in version control
3. Create rollback script to revert DB/index changes
4. Disable performance tests in CI if causing instability

## Git Commit Message

```
test(perf): implement comprehensive performance testing suite

- Add k6 configuration with load, stress, spike, and soak patterns
- Implement load test for auction browsing and bidding workflows
- Create concurrent bidding race condition test
- Add stress test to validate graceful degradation
- Configure spike test for traffic surge scenarios
- Add 1-hour endurance/soak test for memory leak detection
- Integrate Lighthouse CI for Core Web Vitals monitoring
- Set performance budgets: p95 < 500ms, error rate < 1%
- Add custom metrics for cache hit rate and DB query time
- Create benchmark comparison scripts

Task: 070
```

## Notes

- Run smoke tests before each commit
- Run full load test suite before releases
- Stress test should identify breaking point, not cause damage
- Coordinate with Task 067 and 068 to measure optimization impact
- Schedule soak tests during off-peak hours (weekends)
- Monitor infrastructure costs during performance testing
