/**
 * K6 Load Test
 * Task 070: Load Testing (100-200 concurrent users)
 *
 * Run with: k6 run k6/load-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { CONFIG, getApiUrl } from './config.js';

// Test configuration
export const options = {
  stages: CONFIG.loadTest.stages,
  thresholds: CONFIG.thresholds,
  ...CONFIG.options,
};

// Endpoints to test
const ENDPOINTS = [
  '/api/tenders/',
  '/api/tenders/stats/',
  '/api/dashboard/',
  '/api/regions/',
  '/api/industries/',
];

// Random sleep between requests (think time)
const MIN_SLEEP = 1;
const MAX_SLEEP = 3;

export default function () {
  // Randomly select an endpoint
  const endpoint = ENDPOINTS[Math.floor(Math.random() * ENDPOINTS.length)];
  const url = getApiUrl(endpoint);

  // Make request
  const response = http.get(url, {
    headers: {
      'Accept': 'application/json',
      'X-Test-Run': 'k6-load-test',
    },
  });

  // Check response
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'content-type is JSON': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
  });

  // Random sleep to simulate user think time
  sleep(Math.random() * (MAX_SLEEP - MIN_SLEEP) + MIN_SLEEP);
}

// Setup function
export function setup() {
  console.log('Load Test Setup');
  console.log(`Base URL: ${CONFIG.baseUrl}`);
  console.log(`API URL: ${CONFIG.apiUrl}`);

  // Verify API is accessible
  const response = http.get(getApiUrl('/api/tenders/'));
  if (response.status !== 200) {
    console.error(`API not accessible: ${response.status}`);
  } else {
    console.log('API is accessible');
  }

  return {};
}

// Teardown function
export function teardown(data) {
  console.log('Load Test Complete');
}
