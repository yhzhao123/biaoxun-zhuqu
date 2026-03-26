/**
 * K6 Stress Test Script
 * Tests API endpoints under high load conditions (400-600 concurrent users)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL, headers } from './config.js';

export const options = {
  // Stress test scenarios
  scenarios: {
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 100 },   // Warm up
        { duration: '2m', target: 400 },   // Ramp to 400
        { duration: '3m', target: 600 },   // Ramp to 600 (peak)
        { duration: '2m', target: 600 },   // Hold peak
        { duration: '1m', target: 0 },     // Cool down
      ],
    },
  },

  // Thresholds - slightly relaxed for stress testing
  thresholds: {
    http_req_duration: ['p(95)<800', 'p(99)<1500'],
    http_req_failed: ['rate<0.05'],  // Allow up to 5% error rate
  },
};

export default function () {
  // Mix of different endpoints to stress test
  const endpoints = [
    '/api/v1/tenders/',
    '/api/v1/statistics/',
    '/api/v1/statistics/trend/',
    '/api/v1/statistics/budget/',
    '/api/v1/statistics/top-tenderers/',
    '/api/v1/opportunities/',
    '/api/v1/opportunities/high-value/',
    '/api/v1/opportunities/urgent/',
    '/api/v1/reports/daily/',
    '/api/v1/reports/weekly/',
  ];

  // Random endpoint selection
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const url = `${BASE_URL}${endpoint}`;

  const res = http.get(url, { headers });

  check(res, {
    [`${endpoint} status`]: (r) => r.status === 200 || r.status === 404,
    [`${endpoint} response time`]: (r) => r.timings.duration < 1500,
  });

  // Random think time
  sleep(Math.random() * 1 + 0.1);
}

export function handleSummary(data) {
  const summary = {
    'Total Requests': data.metrics.http_reqs.values.count,
    'Failed Requests': data.metrics.http_req_failed.values.passes,
    'Average Duration': `${data.metrics.http_req_duration.values.avg.toFixed(2)}ms`,
    'p95 Duration': `${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms`,
    'p99 Duration': `${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms`,
    'Error Rate': `${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%`,
  };

  console.log('\n=== Stress Test Summary ===');
  Object.entries(summary).forEach(([key, value]) => {
    console.log(`${key}: ${value}`);
  });

  return {
    stdout: JSON.stringify(data, null, 2),
  };
}