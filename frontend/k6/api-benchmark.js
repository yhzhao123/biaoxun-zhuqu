/**
 * K6 API Benchmark Test
 * Quick benchmark tests for API endpoints
 */

import http from 'k6/http';
import { check } from 'k6';
import { BASE_URL, headers } from './config.js';

export const options = {
  // Quick benchmark - low VUs, short duration
  vus: 10,
  duration: '30s',

  // Strict thresholds for benchmarking
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

// Endpoints to benchmark
const endpoints = [
  { path: '/api/v1/tenders/', name: 'tenders_list', expectedStatus: 200 },
  { path: '/api/v1/tenders/1/', name: 'tender_detail', expectedStatus: [200, 404] },
  { path: '/api/v1/statistics/', name: 'statistics_overview', expectedStatus: 200 },
  { path: '/api/v1/statistics/trend/', name: 'statistics_trend', expectedStatus: 200 },
  { path: '/api/v1/statistics/budget/', name: 'statistics_budget', expectedStatus: 200 },
  { path: '/api/v1/statistics/top-tenderers/', name: 'statistics_top_tenderers', expectedStatus: 200 },
  { path: '/api/v1/opportunities/', name: 'opportunities', expectedStatus: 200 },
  { path: '/api/v1/opportunities/high-value/', name: 'opportunities_high_value', expectedStatus: 200 },
  { path: '/api/v1/opportunities/urgent/', name: 'opportunities_urgent', expectedStatus: 200 },
  { path: '/api/v1/reports/daily/', name: 'reports_daily', expectedStatus: 200 },
  { path: '/api/v1/reports/weekly/', name: 'reports_weekly', expectedStatus: 200 },
];

export default function () {
  endpoints.forEach((endpoint) => {
    const url = `${BASE_URL}${endpoint.path}`;
    const res = http.get(url, { headers });

    // Check status
    const statusValid = Array.isArray(endpoint.expectedStatus)
      ? endpoint.expectedStatus.includes(res.status)
      : res.status === endpoint.expectedStatus;

    check(res, {
      [`${endpoint.name} status`]: () => statusValid,
      [`${endpoint.name} duration < 500ms`]: () => res.timings.duration < 500,
    });

    // Log slow responses
    if (res.timings.duration > 500) {
      console.warn(`${endpoint.name} slow response: ${res.timings.duration}ms`);
    }
  });
}

export function handleSummary(data) {
  // Generate benchmark report
  const report = {
    timestamp: new Date().toISOString(),
    endpoints: {},
  };

  // Extract metrics for each endpoint
  for (const [key, value] of Object.entries(data.metrics)) {
    if (key.startsWith('http_req_duration')) {
      const endpoint = key.match(/\{endpoint:([^}]+)\}/)?.[1] || 'unknown';
      if (!report.endpoints[endpoint]) {
        report.endpoints[endpoint] = {};
      }
      report.endpoints[endpoint].duration = {
        avg: value.values.avg?.toFixed(2),
        p95: value.values['p(95)']?.toFixed(2),
        p99: value.values['p(99)']?.toFixed(2),
      };
    }
  }

  console.log('\n=== API Benchmark Report ===');
  for (const [endpoint, metrics] of Object.entries(report.endpoints)) {
    console.log(`\n${endpoint}:`);
    console.log(`  avg: ${metrics.duration.avg}ms`);
    console.log(`  p95: ${metrics.duration.p95}ms`);
    console.log(`  p99: ${metrics.duration.p99}ms`);
  }

  return {
    stdout: JSON.stringify(report, null, 2),
  };
}