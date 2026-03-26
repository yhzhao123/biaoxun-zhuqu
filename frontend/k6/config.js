/**
 * K6 Load Test Configuration
 * Configuration for running load tests against the API
 */

export const options = {
  // Scenarios to run
  scenarios: {
    // Ramp up to peak load
    ramp_up: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 100 },  // Ramp to 100 users
        { duration: '1m', target: 100 },   // Hold at 100
        { duration: '30s', target: 200 },  // Ramp to 200
        { duration: '2m', target: 200 },   // Hold at 200
        { duration: '30s', target: 0 },    // Ramp down
      ],
    },
  },

  // Thresholds for pass/fail
  thresholds: {
    // Response time thresholds
    http_req_duration: ['p(95)<500', 'p(99)<1000'],  // 95% < 500ms, 99% < 1000ms
    http_req_failed: ['rate<0.01'],  // Error rate < 1%

    // Custom thresholds for specific endpoints
    'http_req_duration{pethod:GET,endpoint:/api/v1/tenders/}': ['p(95)<500'],
    'http_req_duration{pethod:GET,endpoint:/api/v1/statistics/}': ['p(95)<500'],
    'http_req_duration{pethod:GET,endpoint:/api/v1/opportunities/}': ['p(95)<500'],
  },
};

// Base URL for API
export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Common headers
export const headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

// Get auth token if needed
export function getAuthToken() {
  // Implementation depends on auth system
  return null;
}