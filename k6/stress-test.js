/**
 * K6 Stress Test
 * Task 070: Stress Testing (400-600 concurrent users)
 *
 * Run with: k6 run k6/stress-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { CONFIG, getApiUrl } from './config.js';

// Test configuration
export const options = {
  stages: CONFIG.stressTest.stages,
  thresholds: {
    ...CONFIG.thresholds,
    http_req_failed: ['rate<0.05'], // Allow up to 5% errors under stress
  },
  ...CONFIG.options,
};

// Endpoints with weights (more common endpoints get higher weight)
const WEIGHTED_ENDPOINTS = [
  { path: '/api/tenders/', weight: 40 },
  { path: '/api/tenders/stats/', weight: 20 },
  { path: '/api/dashboard/', weight: 20 },
  { path: '/api/regions/', weight: 10 },
  { path: '/api/industries/', weight: 10 },
];

// Build weighted array
const ENDPOINTS = [];
WEIGHTED_ENDPOINTS.forEach(({ path, weight }) => {
  for (let i = 0; i < weight; i++) {
    ENDPOINTS.push(path);
  }
});

export default function () {
  // Select endpoint based on weights
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
  const url = getApiUrl(endpoint);

  const response = http.get(url, {
    headers: {
      'Accept': 'application/json',
      'X-Test-Run': 'k6-stress-test',
    },
  });

  // More lenient checks for stress test
  check(response, {
    'status is 200': (r) => r.status === 200,
    'status is not 5xx': (r) => r.status < 500,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  });

  // Variable sleep
  sleep(Math.random() * 2 + 0.5);
}

export function setup() {
  console.log('Stress Test Setup');
  console.log('This test will gradually increase load to find breaking points');
}

export function teardown(data) {
  console.log('Stress Test Complete');
}
