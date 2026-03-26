/**
 * K6 Performance Test Configuration
 * Task 070: Frontend Performance Testing
 */

export const CONFIG = {
  // Base URL for testing
  baseUrl: __ENV.BASE_URL || 'http://localhost:3000',

  // API base URL
  apiUrl: __ENV.API_URL || 'http://localhost:8000',

  // SLA Thresholds (same as backend)
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% < 500ms, 99% < 1000ms
    http_req_failed: ['rate<0.01'], // Error rate < 1%
  },

  // Load test stages
  loadTest: {
    stages: [
      { duration: '1m', target: 50 },   // Ramp up to 50 users
      { duration: '3m', target: 100 },  // Ramp up to 100 users
      { duration: '5m', target: 100 },  // Stay at 100 users
      { duration: '2m', target: 200 },  // Ramp up to 200 users
      { duration: '5m', target: 200 },  // Stay at 200 users
      { duration: '2m', target: 0 },    // Ramp down
    ],
  },

  // Stress test stages
  stressTest: {
    stages: [
      { duration: '2m', target: 100 },  // Base load
      { duration: '2m', target: 200 },
      { duration: '2m', target: 400 },
      { duration: '2m', target: 600 },  // Peak load
      { duration: '2m', target: 400 },  // Scale down
      { duration: '2m', target: 200 },
      { duration: '2m', target: 100 },
      { duration: '2m', target: 0 },
    ],
  },

  // Spike test stages
  spikeTest: {
    stages: [
      { duration: '2m', target: 100 },   // Base load
      { duration: '30s', target: 1000 }, // Spike to 1000 users
      { duration: '3m', target: 1000 },  // Stay at spike
      { duration: '30s', target: 100 },  // Recover
      { duration: '2m', target: 100 },   // Verify recovery
      { duration: '1m', target: 0 },     // Ramp down
    ],
  },

  // Soak test stages (shorter for testing)
  soakTest: {
    stages: [
      { duration: '5m', target: 100 },   // Ramp up
      { duration: '55m', target: 200 },  // Sustained load for 1 hour
      { duration: '5m', target: 0 },     // Ramp down
    ],
  },

  // Options
  options: {
    discardResponseBodies: true,
    noConnectionReuse: false,
    userAgent: 'K6PerformanceTest/1.0',
  },
};

// Export default thresholds for easy import
export const THRESHOLDS = CONFIG.thresholds;

// Helper to get full URL
export function getUrl(path) {
  return `${CONFIG.baseUrl}${path}`;
}

// Helper to get API URL
export function getApiUrl(path) {
  return `${CONFIG.apiUrl}${path}`;
}
