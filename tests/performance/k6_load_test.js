// Perfect21 K6 负载测试脚本
// 测试工作流编排器API的性能和可扩展性

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// 自定义指标
const errorRate = new Rate('errors');
const workflowCreationTime = new Trend('workflow_creation_time');
const workflowExecutionTime = new Trend('workflow_execution_time');
const concurrentWorkflowsCounter = new Counter('concurrent_workflows');

// 测试配置
export const options = {
  scenarios: {
    // 1. 烟雾测试
    smoke_test: {
      executor: 'constant-vus',
      vus: 1,
      duration: '30s',
      tags: { test_type: 'smoke' },
      env: { TEST_TYPE: 'smoke' }
    },

    // 2. 负载测试
    load_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 5 },   // 慢启动
        { duration: '5m', target: 10 },  // 稳定负载
        { duration: '2m', target: 15 },  // 增加负载
        { duration: '5m', target: 15 },  // 维持负载
        { duration: '2m', target: 0 }    // 缓慢停止
      ],
      tags: { test_type: 'load' },
      env: { TEST_TYPE: 'load' }
    },

    // 3. 压力测试
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },  // 快速增长到正常负载
        { duration: '5m', target: 20 },  // 维持正常负载
        { duration: '2m', target: 40 },  // 增加到压力负载
        { duration: '5m', target: 40 },  // 维持压力负载
        { duration: '2m', target: 60 },  // 推向极限
        { duration: '3m', target: 60 },  // 维持极限负载
        { duration: '5m', target: 0 }    // 恢复
      ],
      tags: { test_type: 'stress' },
      env: { TEST_TYPE: 'stress' }
    },

    // 4. 峰值测试
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 10 },  // 正常负载
        { duration: '1m', target: 10 },   // 维持正常
        { duration: '10s', target: 100 }, // 突然峰值
        { duration: '3m', target: 100 },  // 维持峰值
        { duration: '10s', target: 10 },  // 回到正常
        { duration: '3m', target: 10 },   // 维持正常
        { duration: '10s', target: 0 }    // 停止
      ],
      tags: { test_type: 'spike' },
      env: { TEST_TYPE: 'spike' }
    }
  },

  // 性能阈值
  thresholds: {
    // HTTP 错误率应该低于 1%
    'http_req_failed': ['rate<0.01'],

    // 95% 的请求应该在 2 秒内完成
    'http_req_duration': ['p(95)<2000'],

    // 平均响应时间应该低于 500ms
    'http_req_duration': ['avg<500'],

    // 自定义指标阈值
    'errors': ['rate<0.05'],
    'workflow_creation_time': ['p(95)<1000'],
    'workflow_execution_time': ['p(95)<5000']
  }
};

// 基础URL配置
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

// 测试数据生成
function generateWorkflowConfig(workflowId, complexity = 'medium') {
  const complexityConfigs = {
    simple: {
      stages: 2,
      agents: ['backend-architect', 'test-engineer'],
      execution_mode: 'sequential'
    },
    medium: {
      stages: 4,
      agents: ['backend-architect', 'frontend-specialist', 'database-specialist', 'test-engineer'],
      execution_mode: 'parallel'
    },
    complex: {
      stages: 6,
      agents: ['backend-architect', 'frontend-specialist', 'database-specialist',
               'test-engineer', 'security-auditor', 'devops-engineer'],
      execution_mode: 'hybrid'
    }
  };

  const config = complexityConfigs[complexity];

  return {
    name: `Load Test Workflow ${workflowId}`,
    description: `Performance test workflow with ${complexity} complexity`,
    project_type: 'web_application',
    complexity: complexity,
    global_context: {
      test_mode: true,
      workflow_id: workflowId,
      user_id: `test_user_${__VU}`,
      complexity: complexity
    },
    stages: generateStages(config.stages, config.agents, config.execution_mode)
  };
}

function generateStages(stageCount, agents, executionMode) {
  const stages = [];
  const stageNames = [
    'requirements_analysis',
    'architecture_design',
    'implementation',
    'testing',
    'security_review',
    'deployment_preparation'
  ];

  for (let i = 0; i < stageCount; i++) {
    const stage = {
      name: stageNames[i] || `stage_${i}`,
      description: `Test stage ${i + 1}`,
      execution_mode: i === 0 ? 'parallel' : executionMode,
      timeout: 300,
      tasks: generateStageTasks(agents.slice(0, Math.min(agents.length, i + 2)))
    };

    // 添加依赖关系
    if (i > 0) {
      stage.depends_on = [stageNames[i - 1] || `stage_${i - 1}`];
    }

    // 添加同步点
    if (i === Math.floor(stageCount / 2)) {
      stage.sync_point = {
        type: 'validation',
        validation_criteria: {
          'tasks_completed': '> 0',
          'quality_score': '> 80'
        },
        must_pass: true
      };
    }

    // 添加质量门
    if (i === stageCount - 1) {
      stage.quality_gate = {
        checklist: 'code_review,testing,security_scan',
        must_pass: true
      };
    }

    stages.push(stage);
  }

  return stages;
}

function generateStageTasks(agents) {
  return agents.map((agent, index) => ({
    agent: agent,
    description: `Execute ${agent} tasks`,
    priority: index + 1,
    timeout: 120,
    estimated_time: Math.floor(Math.random() * 60) + 30
  }));
}

// 主测试函数
export default function() {
  const testType = __ENV.TEST_TYPE || 'load';
  const workflowId = `${testType}_${__VU}_${__ITER}`;

  group('Perfect21 Workflow Performance Test', function() {

    // 1. 健康检查
    group('Health Check', function() {
      const healthResponse = http.get(`${BASE_URL}/health`);

      check(healthResponse, {
        'health check status is 200': (r) => r.status === 200,
        'health check response time < 100ms': (r) => r.timings.duration < 100
      });
    });

    // 2. 创建工作流
    let workflowCreated = false;
    let createdWorkflowId = null;

    group('Create Workflow', function() {
      const complexity = selectComplexity(testType);
      const workflowConfig = generateWorkflowConfig(workflowId, complexity);

      const createStart = new Date().getTime();

      const createResponse = http.post(
        `${BASE_URL}${API_VERSION}/workflows`,
        JSON.stringify(workflowConfig),
        {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          timeout: '30s'
        }
      );

      const createDuration = new Date().getTime() - createStart;
      workflowCreationTime.add(createDuration);

      const createSuccess = check(createResponse, {
        'workflow creation status is 201': (r) => r.status === 201,
        'workflow creation response time < 2s': (r) => r.timings.duration < 2000,
        'workflow creation returns workflow_id': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.workflow_id !== undefined;
          } catch (e) {
            return false;
          }
        }
      });

      if (createSuccess && createResponse.status === 201) {
        try {
          const responseBody = JSON.parse(createResponse.body);
          createdWorkflowId = responseBody.workflow_id;
          workflowCreated = true;
          concurrentWorkflowsCounter.add(1);
        } catch (e) {
          console.error('Failed to parse create response:', e);
          errorRate.add(1);
        }
      } else {
        errorRate.add(1);
        console.error(`Workflow creation failed: ${createResponse.status} - ${createResponse.body}`);
      }
    });

    // 3. 执行工作流阶段
    if (workflowCreated && createdWorkflowId) {
      group('Execute Workflow Stages', function() {
        const executionStart = new Date().getTime();

        // 获取工作流状态
        const statusResponse = http.get(`${BASE_URL}${API_VERSION}/workflows/${createdWorkflowId}/status`);

        check(statusResponse, {
          'status check successful': (r) => r.status === 200,
          'status response time < 500ms': (r) => r.timings.duration < 500
        });

        if (statusResponse.status === 200) {
          try {
            const status = JSON.parse(statusResponse.body);
            const stages = status.stages || [];

            // 执行第一个阶段
            if (stages.length > 0) {
              const firstStage = stages[0];
              const executeResponse = http.post(
                `${BASE_URL}${API_VERSION}/workflows/${createdWorkflowId}/stages/${firstStage.name}/execute`,
                JSON.stringify({ async: true }),
                {
                  headers: { 'Content-Type': 'application/json' }
                }
              );

              check(executeResponse, {
                'stage execution started': (r) => r.status === 202 || r.status === 200,
                'stage execution response time < 3s': (r) => r.timings.duration < 3000
              });

              if (executeResponse.status !== 202 && executeResponse.status !== 200) {
                errorRate.add(1);
              }
            }
          } catch (e) {
            console.error('Failed to parse status response:', e);
            errorRate.add(1);
          }
        }

        const executionDuration = new Date().getTime() - executionStart;
        workflowExecutionTime.add(executionDuration);
      });

      // 4. 监控工作流进度
      group('Monitor Workflow Progress', function() {
        const progressResponse = http.get(`${BASE_URL}${API_VERSION}/workflows/${createdWorkflowId}/progress`);

        check(progressResponse, {
          'progress check successful': (r) => r.status === 200,
          'progress response time < 200ms': (r) => r.timings.duration < 200,
          'progress includes completion percentage': (r) => {
            try {
              const body = JSON.parse(r.body);
              return body.completion_percentage !== undefined;
            } catch (e) {
              return false;
            }
          }
        });

        if (progressResponse.status !== 200) {
          errorRate.add(1);
        }
      });

      // 5. 清理（可选）
      if (Math.random() < 0.1) { // 10% 的概率进行清理
        group('Cleanup Workflow', function() {
          const deleteResponse = http.del(`${BASE_URL}${API_VERSION}/workflows/${createdWorkflowId}`);

          check(deleteResponse, {
            'cleanup successful': (r) => r.status === 204 || r.status === 200
          });
        });
      }
    }
  });

  // 模拟用户思考时间
  const thinkTime = selectThinkTime(testType);
  sleep(thinkTime);
}

// 辅助函数
function selectComplexity(testType) {
  switch (testType) {
    case 'smoke':
      return 'simple';
    case 'load':
      return Math.random() < 0.7 ? 'medium' : 'simple';
    case 'stress':
      return Math.random() < 0.5 ? 'complex' : 'medium';
    case 'spike':
      return 'complex';
    default:
      return 'medium';
  }
}

function selectThinkTime(testType) {
  switch (testType) {
    case 'smoke':
      return 1;
    case 'load':
      return Math.random() * 2 + 1; // 1-3秒
    case 'stress':
      return Math.random() * 1 + 0.5; // 0.5-1.5秒
    case 'spike':
      return Math.random() * 0.5; // 0-0.5秒
    default:
      return 1;
  }
}

// 测试设置和清理
export function setup() {
  console.log('🚀 Perfect21 Performance Test Setup');
  console.log(`Target URL: ${BASE_URL}`);
  console.log(`Test Type: ${__ENV.TEST_TYPE || 'load'}`);

  // 验证服务可用性
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    throw new Error(`Service not available: ${healthCheck.status}`);
  }

  return {
    startTime: new Date().getTime(),
    baseUrl: BASE_URL
  };
}

export function teardown(data) {
  const duration = (new Date().getTime() - data.startTime) / 1000;
  console.log(`✅ Perfect21 Performance Test Complete`);
  console.log(`Total test duration: ${duration}s`);
}

// 错误处理
export function handleSummary(data) {
  const summary = {
    test_run: {
      timestamp: new Date().toISOString(),
      duration: data.state.testRunDurationMs / 1000,
      scenarios: Object.keys(data.metrics)
    },
    performance_metrics: {
      http_req_duration: data.metrics.http_req_duration,
      http_req_rate: data.metrics.http_reqs,
      http_req_failed: data.metrics.http_req_failed,
      workflow_creation_time: data.metrics.workflow_creation_time,
      workflow_execution_time: data.metrics.workflow_execution_time,
      error_rate: data.metrics.errors
    },
    thresholds: data.thresholds
  };

  return {
    'tests/performance/results/k6_summary.json': JSON.stringify(summary, null, 2),
    'stdout': generateTextSummary(summary)
  };
}

function generateTextSummary(summary) {
  return `
🎯 Perfect21 K6 性能测试总结
======================================

📊 测试概览:
- 测试时间: ${summary.test_run.timestamp}
- 测试持续时间: ${summary.test_run.duration}秒
- 测试场景: ${summary.test_run.scenarios.join(', ')}

⚡ 性能指标:
- HTTP请求总数: ${summary.performance_metrics.http_req_rate?.count || 'N/A'}
- 平均响应时间: ${summary.performance_metrics.http_req_duration?.avg || 'N/A'}ms
- 95%响应时间: ${summary.performance_metrics.http_req_duration?.['p(95)'] || 'N/A'}ms
- 错误率: ${(summary.performance_metrics.http_req_failed?.rate || 0) * 100}%

🔥 工作流特定指标:
- 工作流创建时间(平均): ${summary.performance_metrics.workflow_creation_time?.avg || 'N/A'}ms
- 工作流执行时间(平均): ${summary.performance_metrics.workflow_execution_time?.avg || 'N/A'}ms

✅ 测试完成
`;
}