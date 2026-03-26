/**
 * K6 Soak Test
 * Task 070: Soak/Endurance Testing (1 hour sustained load)
 *
 * Run with: k6 run k6/soak-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { CONFIG, getApiUrl } from './config.js';

// Test configuration (shortened for testing)
export const options = {
  stages: [
    { duration: '5m', target: 100 },   // Ramp up
    { duration: '5m', target: 200 },   // Increase
    { duration: '20m', target: 200 },  // Sustained load (shortened)
    { duration: '5m', target: 100 },   // Decrease
    { duration: '5m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.02'], // Slightly higher threshold for long test
  },
  ...CONFIG.options,
};

const ENDPOINTS = [
  '/api/tenders/',
  '/api/tenders/stats/',
  '/api/dashboard/',
  '/api/regions/',
  '/api/industries/',
];

export default function () {
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
  const url = getApiUrl(endpoint);

  const response = http.get(url, {
    headers: {
      'Accept': 'application/json',
      'X-Test-Run': 'k6-soak-test',
    },
  });

  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(Math.random() * 2 + 1);
}

export function setup() {
  console.log('Soak Test Setup');
  console.log('This test runs for an extended period to detect memory leaks and performance degradation');
}

export function teardown(data) {
  console.log('Soak Test Complete');
}
