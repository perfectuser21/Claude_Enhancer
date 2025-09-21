// Perfect21 性能测试套件
// 使用 K6 进行负载测试和性能基准测试

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// 自定义性能指标
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const requestCount = new Counter('request_count');

// 性能基准目标
const PERFORMANCE_THRESHOLDS = {
  // 响应时间要求
  'http_req_duration': ['p(95)<200'], // 95%的请求在200ms内完成
  'http_req_duration{scenario:normal_load}': ['p(90)<150'],
  'http_req_duration{scenario:stress_test}': ['p(90)<300'],

  // 错误率要求
  'error_rate': ['rate<0.01'], // 错误率低于1%
  'http_req_failed': ['rate<0.01'],

  // 吞吐量要求
  'http_reqs': ['count>1000'], // 总请求数
  'http_reqs{scenario:normal_load}': ['rate>50'], // 每秒50个请求
};

// 测试场景配置
export let options = {
  scenarios: {
    // 常规负载测试
    normal_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 20 },   // 30秒内逐渐增加到20个用户
        { duration: '2m', target: 20 },    // 保持20个用户2分钟
        { duration: '30s', target: 0 },    // 30秒内减少到0
      ],
      gracefulRampDown: '10s',
      tags: { scenario: 'normal_load' },
    },

    // 压力测试
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 50 },    // 1分钟内增加到50个用户
        { duration: '3m', target: 50 },    // 保持50个用户3分钟
        { duration: '2m', target: 100 },   // 2分钟内增加到100个用户
        { duration: '2m', target: 100 },   // 保持100个用户2分钟
        { duration: '1m', target: 0 },     // 1分钟内减少到0
      ],
      startTime: '4m',                     // 在常规负载测试后开始
      tags: { scenario: 'stress_test' },
    },

    // 峰值测试 (突发流量)
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 200 },  // 10秒内突增到200个用户
        { duration: '30s', target: 200 },  // 保持200个用户30秒
        { duration: '10s', target: 0 },    // 10秒内减少到0
      ],
      startTime: '10m',                    // 在其他测试后进行峰值测试
      tags: { scenario: 'spike_test' },
    },

    // 持久性测试 (长时间运行)
    endurance_test: {
      executor: 'constant-vus',
      vus: 30,
      duration: '10m',                     // 30个用户持续10分钟
      startTime: '12m',
      tags: { scenario: 'endurance_test' },
    },
  },

  thresholds: PERFORMANCE_THRESHOLDS,

  // 输出配置
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

// 测试配置
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const TEST_USER_EMAIL = 'loadtest@perfect21.com';
const TEST_USER_PASSWORD = 'LoadTest123!';

// 测试数据
const TEST_ENDPOINTS = {
  health: `${BASE_URL}/health`,
  api_v1: `${BASE_URL}/api/v1`,
  auth_register: `${BASE_URL}/api/v1/auth/register`,
  auth_login: `${BASE_URL}/api/v1/auth/login`,
  user_profile: `${BASE_URL}/api/v1/user/profile`,
  admin_users: `${BASE_URL}/api/v1/admin/users`,
};

// 测试用户数据生成器
function generateTestUser() {
  const randomId = Math.random().toString(36).substring(7);
  return {
    email: `test-${randomId}@perfect21.com`,
    password: 'TestPassword123!',
    firstName: `TestUser${randomId}`,
    lastName: 'LoadTest',
    username: `testuser_${randomId}`
  };
}

// 认证令牌存储
let authToken = '';

export function setup() {
  console.log('🚀 开始Perfect21性能测试套件');
  console.log(`🎯 目标服务器: ${BASE_URL}`);

  // 健康检查
  group('Setup - 系统健康检查', () => {
    const healthResponse = http.get(TEST_ENDPOINTS.health);
    check(healthResponse, {
      '健康检查成功': (r) => r.status === 200,
      '健康检查响应时间 < 100ms': (r) => r.timings.duration < 100,
    });
  });

  return { baseUrl: BASE_URL };
}

export default function(data) {
  // 随机选择测试场景
  const scenarios = [
    'test_health_endpoint',
    'test_user_authentication_flow',
    'test_user_registration',
    'test_api_endpoints_with_auth',
    'test_static_content'
  ];

  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];

  switch(scenario) {
    case 'test_health_endpoint':
      testHealthEndpoint();
      break;
    case 'test_user_authentication_flow':
      testUserAuthenticationFlow();
      break;
    case 'test_user_registration':
      testUserRegistration();
      break;
    case 'test_api_endpoints_with_auth':
      testAPIEndpointsWithAuth();
      break;
    case 'test_static_content':
      testStaticContent();
      break;
  }

  // 模拟用户思考时间
  sleep(Math.random() * 2 + 1); // 1-3秒随机间隔
}

function testHealthEndpoint() {
  group('健康检查端点测试', () => {
    const response = http.get(TEST_ENDPOINTS.health);

    const result = check(response, {
      '状态码为200': (r) => r.status === 200,
      '响应时间 < 50ms': (r) => r.timings.duration < 50,
      '返回正确格式': (r) => {
        try {
          const data = JSON.parse(r.body);
          return data.status === 'healthy';
        } catch {
          return false;
        }
      },
    });

    errorRate.add(!result);
    responseTime.add(response.timings.duration);
    requestCount.add(1);
  });
}

function testUserAuthenticationFlow() {
  group('用户认证流程测试', () => {
    // 用户登录
    const loginPayload = {
      email: TEST_USER_EMAIL,
      password: TEST_USER_PASSWORD
    };

    const loginResponse = http.post(
      TEST_ENDPOINTS.auth_login,
      JSON.stringify(loginPayload),
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    const loginSuccess = check(loginResponse, {
      '登录状态码正确': (r) => r.status === 200 || r.status === 201,
      '登录响应时间 < 200ms': (r) => r.timings.duration < 200,
      '返回访问令牌': (r) => {
        try {
          const data = JSON.parse(r.body);
          return data.tokens && data.tokens.access_token;
        } catch {
          return false;
        }
      },
    });

    if (loginSuccess) {
      try {
        const loginData = JSON.parse(loginResponse.body);
        authToken = loginData.tokens.access_token;
      } catch (e) {
        console.error('解析登录响应失败:', e);
      }
    }

    errorRate.add(!loginSuccess);
    responseTime.add(loginResponse.timings.duration);
    requestCount.add(1);
  });
}

function testUserRegistration() {
  group('用户注册测试', () => {
    const newUser = generateTestUser();

    const registrationResponse = http.post(
      TEST_ENDPOINTS.auth_register,
      JSON.stringify(newUser),
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    const registrationSuccess = check(registrationResponse, {
      '注册状态码正确': (r) => r.status === 200 || r.status === 201,
      '注册响应时间 < 300ms': (r) => r.timings.duration < 300,
      '返回用户信息': (r) => {
        try {
          const data = JSON.parse(r.body);
          return data.user && data.user.email === newUser.email;
        } catch {
          return false;
        }
      },
    });

    errorRate.add(!registrationSuccess);
    responseTime.add(registrationResponse.timings.duration);
    requestCount.add(1);
  });
}

function testAPIEndpointsWithAuth() {
  if (!authToken) {
    // 如果没有认证令牌，先获取一个
    testUserAuthenticationFlow();
  }

  if (authToken) {
    group('认证API端点测试', () => {
      const headers = {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      };

      // 测试用户资料端点
      const profileResponse = http.get(TEST_ENDPOINTS.user_profile, { headers });

      const profileSuccess = check(profileResponse, {
        '用户资料状态码正确': (r) => r.status === 200,
        '用户资料响应时间 < 150ms': (r) => r.timings.duration < 150,
        '返回用户资料': (r) => {
          try {
            const data = JSON.parse(r.body);
            return data.user && data.user.email;
          } catch {
            return false;
          }
        },
      });

      errorRate.add(!profileSuccess);
      responseTime.add(profileResponse.timings.duration);
      requestCount.add(1);
    });
  }
}

function testStaticContent() {
  group('静态内容测试', () => {
    // 测试API文档端点
    const docsResponse = http.get(`${BASE_URL}/docs`);

    const docsSuccess = check(docsResponse, {
      'API文档可访问': (r) => r.status === 200,
      'API文档响应时间 < 100ms': (r) => r.timings.duration < 100,
    });

    errorRate.add(!docsSuccess);
    responseTime.add(docsResponse.timings.duration);
    requestCount.add(1);
  });
}

export function teardown(data) {
  console.log('🏁 Perfect21性能测试完成');
}

// 自定义摘要报告
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_duration: data.state.testRunDurationMs / 1000,
    scenarios: {},
    metrics: {},
    performance_analysis: {
      response_time_analysis: analyzeResponseTimes(data),
      error_analysis: analyzeErrors(data),
      throughput_analysis: analyzeThroughput(data),
      recommendations: generateRecommendations(data)
    }
  };

  // 处理场景数据
  Object.keys(data.metrics).forEach(metricName => {
    const metric = data.metrics[metricName];
    if (metric.values) {
      summary.metrics[metricName] = {
        avg: metric.values.avg,
        min: metric.values.min,
        max: metric.values.max,
        p90: metric.values['p(90)'],
        p95: metric.values['p(95)'],
        p99: metric.values['p(99)'],
        count: metric.values.count || 0
      };
    }
  });

  // 生成JSON报告
  const jsonReport = JSON.stringify(summary, null, 2);

  // 生成HTML报告
  const htmlReport = generateHTMLReport(summary);

  return {
    'test-results/performance-summary.json': jsonReport,
    'test-results/performance-report.html': htmlReport,
    stdout: generateConsoleReport(summary)
  };
}

function analyzeResponseTimes(data) {
  const httpReqDuration = data.metrics.http_req_duration;
  if (!httpReqDuration || !httpReqDuration.values) return {};

  return {
    average: httpReqDuration.values.avg,
    p95_threshold: httpReqDuration.values['p(95)'] < 200 ? 'PASS' : 'FAIL',
    p99_performance: httpReqDuration.values['p(99)'],
    consistency: httpReqDuration.values.max - httpReqDuration.values.min
  };
}

function analyzeErrors(data) {
  const errorRate = data.metrics.error_rate;
  const httpReqFailed = data.metrics.http_req_failed;

  return {
    error_rate: errorRate ? errorRate.values.rate : 0,
    failed_requests: httpReqFailed ? httpReqFailed.values.rate : 0,
    error_threshold_met: (errorRate?.values.rate || 0) < 0.01 ? 'PASS' : 'FAIL'
  };
}

function analyzeThroughput(data) {
  const httpReqs = data.metrics.http_reqs;
  const testDuration = data.state.testRunDurationMs / 1000;

  return {
    total_requests: httpReqs ? httpReqs.values.count : 0,
    requests_per_second: httpReqs ? (httpReqs.values.count / testDuration) : 0,
    throughput_target_met: httpReqs ? (httpReqs.values.count / testDuration) > 50 ? 'PASS' : 'FAIL' : 'UNKNOWN'
  };
}

function generateRecommendations(data) {
  const recommendations = [];
  const responseTime = data.metrics.http_req_duration;
  const errorRate = data.metrics.error_rate;

  if (responseTime && responseTime.values['p(95)'] > 200) {
    recommendations.push({
      type: 'performance',
      level: 'warning',
      message: '95%响应时间超过200ms，建议优化服务器性能或增加缓存'
    });
  }

  if (errorRate && errorRate.values.rate > 0.01) {
    recommendations.push({
      type: 'reliability',
      level: 'critical',
      message: '错误率超过1%，需要检查应用程序稳定性'
    });
  }

  if (responseTime && responseTime.values.max > 1000) {
    recommendations.push({
      type: 'performance',
      level: 'warning',
      message: '最大响应时间超过1秒，可能存在性能瓶颈'
    });
  }

  return recommendations;
}

function generateHTMLReport(summary) {
  return `
<!DOCTYPE html>
<html>
<head>
    <title>Perfect21 性能测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
        .metric-card { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 20px; }
        .metric-value { font-size: 32px; font-weight: bold; color: #2196F3; margin: 10px 0; }
        .metric-label { color: #666; font-size: 14px; text-transform: uppercase; }
        .status-pass { color: #4CAF50; font-weight: bold; }
        .status-fail { color: #F44336; font-weight: bold; }
        .recommendations { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 10px; padding: 20px; margin: 20px 0; }
        .recommendation { margin: 10px 0; padding: 10px; border-left: 4px solid #ff9f00; background: white; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Perfect21 性能测试报告</h1>
            <p>测试时间: ${summary.timestamp}</p>
            <p>测试持续时间: ${summary.test_duration}秒</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">平均响应时间</div>
                <div class="metric-value">${summary.metrics.http_req_duration?.avg?.toFixed(2) || 'N/A'}ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">95%响应时间</div>
                <div class="metric-value">${summary.metrics.http_req_duration?.p95?.toFixed(2) || 'N/A'}ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">总请求数</div>
                <div class="metric-value">${summary.metrics.http_reqs?.count || 0}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">错误率</div>
                <div class="metric-value">${((summary.performance_analysis.error_analysis.error_rate || 0) * 100).toFixed(2)}%</div>
            </div>
        </div>

        <h2>📊 性能分析</h2>
        <table>
            <tr>
                <th>指标</th>
                <th>结果</th>
                <th>状态</th>
            </tr>
            <tr>
                <td>95%响应时间 < 200ms</td>
                <td>${summary.performance_analysis.response_time_analysis.p95_threshold}</td>
                <td class="${summary.performance_analysis.response_time_analysis.p95_threshold === 'PASS' ? 'status-pass' : 'status-fail'}">${summary.performance_analysis.response_time_analysis.p95_threshold}</td>
            </tr>
            <tr>
                <td>错误率 < 1%</td>
                <td>${summary.performance_analysis.error_analysis.error_threshold_met}</td>
                <td class="${summary.performance_analysis.error_analysis.error_threshold_met === 'PASS' ? 'status-pass' : 'status-fail'}">${summary.performance_analysis.error_analysis.error_threshold_met}</td>
            </tr>
            <tr>
                <td>吞吐量 > 50 RPS</td>
                <td>${summary.performance_analysis.throughput_analysis.throughput_target_met}</td>
                <td class="${summary.performance_analysis.throughput_analysis.throughput_target_met === 'PASS' ? 'status-pass' : 'status-fail'}">${summary.performance_analysis.throughput_analysis.throughput_target_met}</td>
            </tr>
        </table>

        ${summary.performance_analysis.recommendations.length > 0 ? `
        <div class="recommendations">
            <h3>💡 性能优化建议</h3>
            ${summary.performance_analysis.recommendations.map(rec => `
                <div class="recommendation">
                    <strong>${rec.type.toUpperCase()}</strong>: ${rec.message}
                </div>
            `).join('')}
        </div>
        ` : ''}
    </div>
</body>
</html>`;
}

function generateConsoleReport(summary) {
  return `
🎯 Perfect21 性能测试结果摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 总体指标:
  • 总请求数: ${summary.metrics.http_reqs?.count || 0}
  • 平均响应时间: ${summary.metrics.http_req_duration?.avg?.toFixed(2) || 'N/A'}ms
  • 95%响应时间: ${summary.metrics.http_req_duration?.p95?.toFixed(2) || 'N/A'}ms
  • 错误率: ${((summary.performance_analysis.error_analysis.error_rate || 0) * 100).toFixed(2)}%

🎯 性能目标达成情况:
  • 响应时间目标: ${summary.performance_analysis.response_time_analysis.p95_threshold}
  • 错误率目标: ${summary.performance_analysis.error_analysis.error_threshold_met}
  • 吞吐量目标: ${summary.performance_analysis.throughput_analysis.throughput_target_met}

${summary.performance_analysis.recommendations.length > 0 ? `
💡 优化建议:
${summary.performance_analysis.recommendations.map(rec => `  • ${rec.message}`).join('\n')}
` : ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  `;
}