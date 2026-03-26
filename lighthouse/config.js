/**
 * Lighthouse CI Configuration
 * Task 070: Frontend Performance Auditing
 *
 * Run with: lhci autorun
 */

module.exports = {
  ci: {
    // Collect configuration
    collect: {
      // Number of runs to average
      numberOfRuns: 3,

      // URL to test
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/tenders',
        'http://localhost:3000/dashboard',
      ],

      // Use Chrome
      settings: {
        preset: 'desktop',
        chromeFlags: '--no-sandbox --headless',
      },

      // Start server if needed
      // startServerCommand: 'npm run preview',
      // startServerReadyPattern: 'Local:',
      // startServerReadyTimeout: 60000,
    },

    // Upload configuration
    upload: {
      target: 'temporary-public-storage',
      // For GitHub integration:
      // target: 'lhci',
      // serverBaseUrl: 'https://your-lhci-server.com',
      // token: process.env.LHCI_TOKEN,
    },

    // Assertion configuration
    assert: {
      preset: 'lighthouse:recommended',

      // Custom assertions
      assertions: {
        // Performance
        'categories:performance': ['warn', { minScore: 0.8 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.9 }],
        'categories:seo': ['warn', { minScore: 0.9 }],

        // Core Web Vitals
        'first-contentful-paint': ['warn', { maxNumericValue: 1800 }], // < 1.8s
        'largest-contentful-paint': ['warn', { maxNumericValue: 2500 }], // < 2.5s
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }], // < 0.1
        'total-blocking-time': ['warn', { maxNumericValue: 200 }], // < 200ms

        // Other metrics
        'speed-index': ['warn', { maxNumericValue: 3400 }],
        'interactive': ['warn', { maxNumericValue: 3800 }],

        // Resource budgets
        'resource-summary:script:size': ['warn', { maxNumericValue: 500000 }], // 500KB JS
        'resource-summary:image:size': ['warn', { maxNumericValue: 1000000 }], // 1MB images
        'resource-summary:total:size': ['warn', { maxNumericValue: 3000000 }], // 3MB total

        // Disable some strict recommendations
        'unused-javascript': 'off',
        'uses-responsive-images': 'off',
      },
    },

    // Server configuration (if running local server)
    server: {
      // port: 9001,
      // storage: {
      //   storageMethod: 'sql',
      //   sqlDialect: 'sqlite',
      //   sqlDatabasePath: '/data/lhci.db',
      // },
    },
  },
};
