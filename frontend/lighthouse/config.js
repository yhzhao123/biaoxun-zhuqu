/**
 * Lighthouse CI Configuration
 * Configuration for running Lighthouse performance audits
 */

module.exports = {
  // Lighthouse CI configuration
  ci: {
    collect: {
      // URLs to audit
      urls: [
        'http://localhost:3000/',  // Frontend home page
        'http://localhost:3000/tenders',
        'http://localhost:3000/statistics',
        'http://localhost:3000/opportunities',
        'http://localhost:3000/reports',
      ],

      // Number of runs to average
      numberOfRuns: 3,

      // Settings for Chrome
      chromeFlags: '--headless --no-sandbox --disable-gpu --disable-dev-shm-usage',

      // Performance settings
      performance: true,
      accessibility: true,
      'best-practices': true,
      seo: true,
      pwa: false,  // Disable PWA audit for API-focused testing
    },

    upload: {
      // Target for uploading results (optional)
      target: 'temporary-public-storage',
    },

    assert: {
      // Assertions for pass/fail
      assertions: {
        // Performance thresholds
        'categories:performance': ['warn', { minScore: 0.7 }],
        'first-contentful-paint': ['error', { maxNumericValue: 2000, aggregationMethod: 'optimistic' }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500, aggregationMethod: 'optimistic' }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.25 }],
        'total-blocking-time': ['error', { maxNumericValue: 500, aggregationMethod: 'optimistic' }],
        'speed-index': ['error', { maxNumericValue: 3000, aggregationMethod: 'optimistic' }],

        // Accessibility
        'categories:accessibility': ['warn', { minScore: 0.7 }],

        // Best practices
        'categories:best-practices': ['warn', { minScore: 0.7 }],

        // SEO
        'categories:seo': ['warn', { minScore: 0.7 }],
      },
    },
  },
};

// Performance thresholds (SLA)
const PERFORMANCE_THRESHOLDS = {
  // Core Web Vitals
  'first-contentful-paint': 2000,      // FCP < 2s
  'largest-contentful-paint': 2500,   // LCP < 2.5s
  'cumulative-layout-shift': 0.25,     // CLS < 0.25
  'total-blocking-time': 500,          // TBT < 500ms
  'speed-index': 3000,                 // SI < 3s

  // Other metrics
  'time-to-first-byte': 600,           // TTFB < 600ms
  'first-meaningful-paint': 2000,      // FMP < 2s
};

// Export for use in scripts
module.exports.PERFORMANCE_THRESHOLDS = PERFORMANCE_THRESHOLDS;