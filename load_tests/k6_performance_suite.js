/**
 * Perfect21 K6 Performance Testing Suite
 * =====================================
 *
 * Comprehensive performance testing using K6 framework.
 * Includes load testing, stress testing, and spike testing scenarios.
 *
 * Usage:
 *   k6 run --stage="2m:50,5m:50,2m:0" k6_performance_suite.js
 *   k6 run --env SCENARIO=stress k6_performance_suite.js
 *   k6 run --env SCENARIO=spike k6_performance_suite.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';

// Custom metrics
export let errorRate = new Rate('errors');
export let responseTime = new Trend('response_time');
export let authSuccessRate = new Rate('auth_success');
export let cacheHitRate = new Rate('cache_hits');
export let slowResponsesRate = new Rate('slow_responses');
export let apiCallsCounter = new Counter('api_calls_total');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const SCENARIO = __ENV.SCENARIO || 'load';

// Test scenarios configuration
const scenarios = {
  load: {
    stages: [
      { duration: '2m', target: 50 },    // Warm up
      { duration: '5m', target: 50 },    // Stay at 50 users
      { duration: '3m', target: 200 },   // Ramp up to 200 users
      { duration: '10m', target: 200 },  // Stay at 200 users
      { duration: '3m', target: 0 },     // Cool down
    ],
    thresholds: {
      'http_req_duration': ['p(95)<500', 'p(99)<1000'],
      'http_req_duration{name:login}': ['p(95)<200'],
      'http_req_duration{name:dashboard}': ['p(95)<300'],
      'errors': ['rate<0.01'],
      'http_req_failed': ['rate<0.01'],
      'http_reqs': ['rate>500'],
    }
  },

  stress: {
    stages: [
      { duration: '1m', target: 100 },   // Warm up
      { duration: '3m', target: 500 },   // Ramp to stress level
      { duration: '5m', target: 500 },   // Maintain stress
      { duration: '3m', target: 1000 },  // Push to breaking point
      { duration: '2m', target: 1000 },  // Hold at breaking point
      { duration: '3m', target: 0 },     // Cool down
    ],
    thresholds: {
      'http_req_duration': ['p(95)<1000', 'p(99)<2000'],
      'errors': ['rate<0.05'],
      'http_req_failed': ['rate<0.05'],
    }
  },

  spike: {
    stages: [
      { duration: '1m', target: 50 },    // Normal load
      { duration: '30s', target: 1000 }, // Spike!
      { duration: '1m', target: 1000 },  // Hold spike
      { duration: '30s', target: 50 },   // Return to normal
      { duration: '2m', target: 50 },    // Stay normal
      { duration: '30s', target: 2000 }, // Bigger spike!
      { duration: '1m', target: 2000 },  // Hold bigger spike
      { duration: '1m', target: 0 },     // Cool down
    ],
    thresholds: {
      'http_req_duration': ['p(95)<2000'],
      'errors': ['rate<0.1'],
      'http_req_failed': ['rate<0.1'],
    }
  }
};

// Set configuration based on scenario
export let options = scenarios[SCENARIO] || scenarios.load;

// Test data
const users = [];
for (let i = 0; i < 1000; i++) {
  users.push({
    email: `testuser${i}@perfect21.test`,
    password: 'TestPassword123!',
    firstName: `Test${i}`,
    lastName: 'User'
  });
}

// Utility functions
function getRandomUser() {
  return users[Math.floor(Math.random() * users.length)];
}

function randomChoice(array) {
  return array[Math.floor(Math.random() * array.length)];
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Authentication helper
function authenticate() {
  const user = getRandomUser();

  // Register user (for load testing)
  http.post(`${BASE_URL}/api/auth/register`, JSON.stringify({
    email: user.email,
    password: user.password,
    first_name: user.firstName,
    last_name: user.lastName
  }), {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'register' }
  });

  // Login
  let loginResponse = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: user.email,
    password: user.password
  }), {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'login' }
  });

  let authSuccess = check(loginResponse, {
    'login successful': (r) => r.status === 200,
    'login response time < 200ms': (r) => r.timings.duration < 200,
    'has access token': (r) => r.json('access_token') !== undefined,
  });

  authSuccessRate.add(authSuccess);
  apiCallsCounter.add(1);

  if (!authSuccess) {
    errorRate.add(1);
    return null;
  }

  return {
    token: loginResponse.json('access_token'),
    user_id: loginResponse.json('user_id'),
    user: user
  };
}

// Main test function
export default function() {
  // Authenticate user
  let authData = authenticate();
  if (!authData) {
    return; // Skip if authentication failed
  }

  let headers = {
    'Authorization': `Bearer ${authData.token}`,
    'Content-Type': 'application/json'
  };

  // Test different user behavior patterns based on scenario
  if (SCENARIO === 'stress') {
    stressTestBehavior(headers);
  } else if (SCENARIO === 'spike') {
    spikeTestBehavior(headers);
  } else {
    normalUserBehavior(headers);
  }
}

function normalUserBehavior(headers) {
  group('Normal User Journey', function() {

    // 1. Load Dashboard (most common)
    group('Dashboard Access', function() {
      let dashboardResponse = http.get(`${BASE_URL}/api/user/dashboard`, {
        headers: headers,
        tags: { name: 'dashboard' }
      });

      let dashboardSuccess = check(dashboardResponse, {
        'dashboard loaded': (r) => r.status === 200,
        'dashboard response time < 300ms': (r) => r.timings.duration < 300,
        'dashboard has data': (r) => r.json('data') !== undefined,
      });

      if (!dashboardSuccess) errorRate.add(1);
      apiCallsCounter.add(1);

      // Check for cache headers
      if (dashboardResponse.headers['X-Cache-Status']) {
        cacheHitRate.add(dashboardResponse.headers['X-Cache-Status'] === 'HIT');
      }
    });

    sleep(randomInt(1, 3));

    // 2. Profile Management
    group('Profile Operations', function() {
      // View profile
      let profileResponse = http.get(`${BASE_URL}/api/user/profile`, {
        headers: headers,
        tags: { name: 'profile' }
      });

      check(profileResponse, {
        'profile loaded': (r) => r.status === 200,
        'profile response time < 200ms': (r) => r.timings.duration < 200,
      }) || errorRate.add(1);

      apiCallsCounter.add(1);

      sleep(1);

      // Update preferences (30% chance)
      if (Math.random() < 0.3) {
        let preferences = {
          theme: randomChoice(['light', 'dark', 'auto']),
          language: randomChoice(['en', 'zh', 'es', 'fr']),
          notifications: {
            email: Math.random() < 0.7,
            push: Math.random() < 0.5,
            sms: Math.random() < 0.3
          }
        };

        let updateResponse = http.put(`${BASE_URL}/api/user/preferences`,
          JSON.stringify(preferences), {
          headers: headers,
          tags: { name: 'preferences_update' }
        });

        check(updateResponse, {
          'preferences updated': (r) => r.status === 200,
          'update response time < 500ms': (r) => r.timings.duration < 500,
        }) || errorRate.add(1);

        apiCallsCounter.add(1);
      }
    });

    sleep(randomInt(2, 4));

    // 3. Data Operations
    group('Data Browsing', function() {
      let page = randomInt(1, 5);
      let limit = randomChoice([10, 20, 50]);

      let dataResponse = http.get(`${BASE_URL}/api/data/browse`, {
        headers: headers,
        params: {
          page: page,
          limit: limit,
          sort_by: randomChoice(['created_at', 'updated_at', 'name']),
          order: 'desc'
        },
        tags: { name: 'data_browse' }
      });

      check(dataResponse, {
        'data loaded': (r) => r.status === 200,
        'data response time < 400ms': (r) => r.timings.duration < 400,
        'has pagination': (r) => r.json('pagination') !== undefined,
      }) || errorRate.add(1);

      apiCallsCounter.add(1);

      // Mark slow responses
      if (dataResponse.timings.duration > 1000) {
        slowResponsesRate.add(1);
      }
    });

    sleep(randomInt(1, 2));

    // 4. Search (20% chance)
    if (Math.random() < 0.2) {
      group('Search Operations', function() {
        let query = randomChoice(['test', 'user', 'data', 'project', 'report']);

        let searchResponse = http.get(`${BASE_URL}/api/search`, {
          headers: headers,
          params: { q: query, limit: 20 },
          tags: { name: 'search' }
        });

        check(searchResponse, {
          'search completed': (r) => r.status === 200,
          'search response time < 600ms': (r) => r.timings.duration < 600,
        }) || errorRate.add(1);

        apiCallsCounter.add(1);
      });
    }

    // Random think time
    sleep(randomInt(2, 5));
  });
}

function stressTestBehavior(headers) {
  group('Stress Test Behavior', function() {
    // Rapid-fire requests
    for (let i = 0; i < randomInt(3, 8); i++) {
      let endpoint = randomChoice([
        '/api/user/dashboard',
        '/api/user/profile',
        '/api/data/summary',
        '/api/notifications/check'
      ]);

      let response = http.get(`${BASE_URL}${endpoint}`, {
        headers: headers,
        tags: { name: 'stress_request' }
      });

      check(response, {
        'stress request successful': (r) => r.status === 200,
      }) || errorRate.add(1);

      apiCallsCounter.add(1);

      // Very short delay between requests
      sleep(0.1);
    }

    // Heavy database operation
    let analyticsResponse = http.post(`${BASE_URL}/api/analytics/complex`, JSON.stringify({
      start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: new Date().toISOString(),
      metrics: ['users', 'sessions', 'revenue'],
      group_by: ['day', 'source'],
      filters: {
        country: randomChoice(['US', 'UK', 'DE', 'FR']),
        device_type: randomChoice(['desktop', 'mobile', 'tablet'])
      }
    }), {
      headers: headers,
      tags: { name: 'heavy_analytics' }
    });

    check(analyticsResponse, {
      'analytics completed': (r) => r.status === 200,
      'analytics response time < 5s': (r) => r.timings.duration < 5000,
    }) || errorRate.add(1);

    apiCallsCounter.add(1);

    sleep(randomInt(1, 2));
  });
}

function spikeTestBehavior(headers) {
  group('Spike Test Behavior', function() {
    // Simulate sudden burst of activity
    let requests = randomInt(5, 15);

    for (let i = 0; i < requests; i++) {
      let response = http.get(`${BASE_URL}/api/user/dashboard`, {
        headers: headers,
        tags: { name: 'spike_dashboard' }
      });

      check(response, {
        'spike request successful': (r) => r.status === 200,
      }) || errorRate.add(1);

      apiCallsCounter.add(1);

      // Minimal delay to create spike
      sleep(0.05);
    }

    // Brief pause
    sleep(0.5);
  });
}

// Custom summary function
export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

  return {
    [`performance_report_${SCENARIO}_${timestamp}.html`]: htmlReport(data),
    [`performance_summary_${SCENARIO}_${timestamp}.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

// Performance thresholds validation
export function teardown(data) {
  // Custom teardown logic
  console.log('\n==== PERFORMANCE TEST ANALYSIS ====');

  const httpReqDuration = data.metrics.http_req_duration;
  const errorRate = data.metrics.errors ? data.metrics.errors.rate : 0;
  const httpReqFailed = data.metrics.http_req_failed ? data.metrics.http_req_failed.rate : 0;

  console.log(`Response Time P95: ${httpReqDuration.p95.toFixed(2)}ms`);
  console.log(`Response Time P99: ${httpReqDuration.p99.toFixed(2)}ms`);
  console.log(`Error Rate: ${(errorRate * 100).toFixed(2)}%`);
  console.log(`Failed Requests: ${(httpReqFailed * 100).toFixed(2)}%`);

  // Performance scoring
  let score = 100;

  if (httpReqDuration.p95 > 500) score -= 20;
  if (httpReqDuration.p99 > 1000) score -= 20;
  if (errorRate > 0.01) score -= 30;
  if (httpReqFailed > 0.01) score -= 30;

  console.log(`\nPerformance Score: ${Math.max(0, score)}/100`);

  if (score < 70) {
    console.log('❌ Performance test FAILED - Score below acceptable threshold');
  } else if (score < 85) {
    console.log('⚠️  Performance test PASSED with warnings');
  } else {
    console.log('✅ Performance test PASSED - Excellent performance!');
  }

  console.log('=====================================\n');
}