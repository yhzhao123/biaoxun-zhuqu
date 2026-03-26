/**
 * K6 Load Test Script
 * Tests API endpoints under normal load conditions
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL, headers } from './config.js';

// Test scenarios for different API endpoints

export default function () {
  // Test 1: Tenders List
  testTendersList();

  // Test 2: Statistics Overview
  testStatisticsOverview();

  // Test 3: Opportunities
  testOpportunities();

  // Test 4: Reports
  testReports();

  // Random think time
  sleep(Math.random() * 2 + 0.5);
}

function testTendersList() {
  const url = `${BASE_URL}/api/v1/tenders/`;

  const res = http.get(url, { headers });

  check(res, {
    'tenders list status 200': (r) => r.status === 200,
    'tenders list response time < 500ms': (r) => r.timings.duration < 500,
  });

  // Parse and validate response
  if (res.status === 200) {
    try {
      const data = JSON.parse(res.body);
      check(data, {
        'tenders list has results': (d) => d.results !== undefined || Array.isArray(d),
      });
    } catch (e) {
      console.error('Failed to parse tenders list response:', e);
    }
  }
}

function testStatisticsOverview() {
  const url = `${BASE_URL}/api/v1/statistics/`;

  const res = http.get(url, { headers });

  check(res, {
    'statistics overview status 200': (r) => r.status === 200,
    'statistics overview response time < 500ms': (r) => r.timings.duration < 500,
  });
}

function testStatisticsTrend() {
  const url = `${BASE_URL}/api/v1/statistics/trend/`;

  const res = http.get(url, { headers });

  check(res, {
    'statistics trend status 200': (r) => r.status === 200,
  });
}

function testStatisticsBudget() {
  const url = `${BASE_URL}/api/v1/statistics/budget/`;

  const res = http.get(url, { headers });

  check(res, {
    'statistics budget status 200': (r) => r.status === 200,
  });
}

function testStatisticsTopTenderers() {
  const url = `${BASE_URL}/api/v1/statistics/top-tenderers/`;

  const res = http.get(url, { headers });

  check(res, {
    'statistics top-tenderers status 200': (r) => r.status === 200,
  });
}

function testOpportunities() {
  const url = `${BASE_URL}/api/v1/opportunities/`;

  const res = http.get(url, { headers });

  check(res, {
    'opportunities status 200': (r) => r.status === 200,
    'opportunities response time < 500ms': (r) => r.timings.duration < 500,
  });
}

function testOpportunitiesHighValue() {
  const url = `${BASE_URL}/api/v1/opportunities/high-value/`;

  const res = http.get(url, { headers });

  check(res, {
    'opportunities high-value status 200': (r) => r.status === 200,
  });
}

function testOpportunitiesUrgent() {
  const url = `${BASE_URL}/api/v1/opportunities/urgent/`;

  const res = http.get(url, { headers });

  check(res, {
    'opportunities urgent status 200': (r) => r.status === 200,
  });
}

function testReports() {
  const endpoints = [
    '/api/v1/reports/daily/',
    '/api/v1/reports/weekly/',
  ];

  endpoints.forEach((endpoint) => {
    const url = `${BASE_URL}${endpoint}`;
    const res = http.get(url, { headers });

    check(res, {
      [`${endpoint} status 200`]: (r) => r.status === 200,
    });
  });
}

// Handle errors gracefully
export function handleSummary(data) {
  console.log('Test completed');
  console.log('Total requests:', data.metrics.http_reqs.values.count);
  console.log('Average response time:', data.metrics.http_req_duration.values.avg, 'ms');
  console.log('p95 response time:', data.metrics.http_req_duration.values['p(95)'], 'ms');
  console.log('Error rate:', data.metrics.http_req_failed.values.rate * 100, '%');

  return {
    stdout: JSON.stringify(data, null, 2),
  };
}