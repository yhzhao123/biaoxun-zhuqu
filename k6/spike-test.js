/**
 * K6 Spike Test
 * Task 070: Spike Testing (100 -> 1000 users sudden increase)
 *
 * Run with: k6 run k6/spike-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { CONFIG, getApiUrl } from './config.js';

// Test configuration
export const options = {
  stages: CONFIG.spikeTest.stages,
  thresholds: {
    // More lenient during spike
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed: ['rate<0.10'], // Allow up to 10% errors during spike
  },
  ...CONFIG.options,
};

const ENDPOINTS = [
  '/api/tenders/',
  '/api/dashboard/',
  '/api/tenders/stats/',
];

export default function () {
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
  const url = getApiUrl(endpoint);

  const response = http.get(url, {
    headers: {
      'Accept': 'application/json',
      'X-Test-Run': 'k6-spike-test',
    },
  });

  check(response, {
    'status is 200': (r) => r.status === 200,
    'status is not 5xx': (r) => r.status < 500,
  });

  sleep(Math.random() * 1 + 0.5);
}

export function setup() {
  console.log('Spike Test Setup');
  console.log('This test simulates sudden traffic surges');
}

export function teardown(data) {
  console.log('Spike Test Complete');
}
