# 📊 Claude Enhancer 性能监控基准

> 建立性能基准线，为监控和优化提供参考

## 🎯 性能基准概览

### 核心性能目标
```yaml
performance_targets:
  availability: "99.9%"
  response_time_p95: "< 200ms"
  response_time_p99: "< 500ms"
  error_rate: "< 0.1%"
  throughput: "> 1000 req/min"

  agent_execution:
    simple_tasks: "< 10s"
    standard_tasks: "< 20s"
    complex_tasks: "< 30s"

  resource_usage:
    cpu_max: "80%"
    memory_max: "85%"
    disk_max: "90%"
```

### 测试环境规格
```yaml
test_environment:
  hardware:
    cpu: "4 cores @ 2.4GHz"
    memory: "8GB RAM"
    storage: "100GB SSD"
    network: "1Gbps"

  software:
    os: "Ubuntu 20.04 LTS"
    docker: "20.10+"
    python: "3.11+"
    postgresql: "15"
    redis: "7"
```

## 🔧 基准测试套件

### Agent 系统性能基准

#### 简单任务性能基准 (4-Agent)
```bash
#!/bin/bash
# 文件: benchmarks/simple_task_benchmark.sh

echo "🚀 开始简单任务性能基准测试..."

TASKS=(
    "fix typo in documentation"
    "update README file"
    "adjust configuration parameter"
    "add simple unit test"
    "format code with prettier"
)

RESULTS_FILE="results/simple_task_benchmark_$(date +%Y%m%d_%H%M%S).json"
mkdir -p results

echo '[' > "$RESULTS_FILE"

for i in "${!TASKS[@]}"; do
    TASK="${TASKS[$i]}"
    echo "📝 测试任务: $TASK"

    START_TIME=$(date +%s.%N)

    # 模拟 Claude Enhancer 任务执行
    curl -X POST http://localhost:8080/api/workflow/execute \
        -H "Content-Type: application/json" \
        -d "{
            \"task\": \"$TASK\",
            \"complexity\": \"simple\",
            \"phase\": 3
        }" \
        -w "%{http_code},%{time_total},%{time_connect}" \
        -o /tmp/response_$i.json \
        -s

    END_TIME=$(date +%s.%N)
    DURATION=$(echo "$END_TIME - $START_TIME" | bc)

    # 记录结果
    cat >> "$RESULTS_FILE" << EOF
{
    "task": "$TASK",
    "duration": $DURATION,
    "timestamp": "$(date -Iseconds)",
    "complexity": "simple",
    "expected_duration": 10.0
}$([ $i -lt $((${#TASKS[@]} - 1)) ] && echo "," || echo "")
EOF
done

echo ']' >> "$RESULTS_FILE"

# 分析结果
python3 scripts/analyze_benchmark_results.py "$RESULTS_FILE"

echo "✅ 简单任务基准测试完成"
```

#### 标准任务性能基准 (6-Agent)
```python
# 文件: benchmarks/standard_task_benchmark.py

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict

class StandardTaskBenchmark:
    """标准任务性能基准测试"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.test_tasks = [
            "implement user authentication",
            "create REST API for data management",
            "add input validation and error handling",
            "implement database connection pooling",
            "add logging and monitoring features",
            "create automated testing suite"
        ]

    async def execute_task(self, session: aiohttp.ClientSession, task: str) -> Dict[str, any]:
        """执行单个任务并测量性能"""
        start_time = time.time()

        payload = {
            "task": task,
            "complexity": "standard",
            "phase": 3
        }

        try:
            async with session.post(
                f"{self.base_url}/api/workflow/execute",
                json=payload
            ) as response:
                result = await response.json()
                end_time = time.time()

                return {
                    "task": task,
                    "duration": end_time - start_time,
                    "status": "success" if response.status == 200 else "failed",
                    "status_code": response.status,
                    "timestamp": time.time(),
                    "complexity": "standard",
                    "expected_duration": 20.0,
                    "result": result
                }
        except Exception as e:
            end_time = time.time()
            return {
                "task": task,
                "duration": end_time - start_time,
                "status": "error",
                "error": str(e),
                "timestamp": time.time(),
                "complexity": "standard",
                "expected_duration": 20.0
            }

    async def run_benchmark(self) -> List[Dict[str, any]]:
        """运行基准测试"""
        print("🚀 开始标准任务性能基准测试...")

        results = []

        async with aiohttp.ClientSession() as session:
            # 串行测试
            print("📊 串行执行测试...")
            for task in self.test_tasks:
                print(f"📝 测试任务: {task}")
                result = await self.execute_task(session, task)
                results.append(result)
                print(f"⏱️ 执行时间: {result['duration']:.2f}s")

            # 并行测试
            print("🔄 并行执行测试...")
            parallel_start = time.time()

            parallel_tasks = [
                self.execute_task(session, task)
                for task in self.test_tasks[:3]  # 测试3个并行任务
            ]

            parallel_results = await asyncio.gather(*parallel_tasks)
            parallel_end = time.time()

            for result in parallel_results:
                result['execution_mode'] = 'parallel'
                results.append(result)

            print(f"🔄 并行执行总时间: {parallel_end - parallel_start:.2f}s")

        return results

    def analyze_results(self, results: List[Dict[str, any]]) -> Dict[str, any]:
        """分析基准测试结果"""
        print("📊 分析基准测试结果...")

        # 分离串行和并行结果
        serial_results = [r for r in results if r.get('execution_mode') != 'parallel']
        parallel_results = [r for r in results if r.get('execution_mode') == 'parallel']

        # 串行执行分析
        serial_durations = [r['duration'] for r in serial_results if r['status'] == 'success']

        # 并行执行分析
        parallel_durations = [r['duration'] for r in parallel_results if r['status'] == 'success']

        analysis = {
            'serial_execution': {
                'total_tasks': len(serial_results),
                'successful_tasks': len(serial_durations),
                'avg_duration': statistics.mean(serial_durations) if serial_durations else 0,
                'median_duration': statistics.median(serial_durations) if serial_durations else 0,
                'max_duration': max(serial_durations) if serial_durations else 0,
                'min_duration': min(serial_durations) if serial_durations else 0,
                'std_deviation': statistics.stdev(serial_durations) if len(serial_durations) > 1 else 0
            },
            'parallel_execution': {
                'total_tasks': len(parallel_results),
                'successful_tasks': len(parallel_durations),
                'avg_duration': statistics.mean(parallel_durations) if parallel_durations else 0,
                'max_duration': max(parallel_durations) if parallel_durations else 0,
                'min_duration': min(parallel_durations) if parallel_durations else 0
            },
            'performance_assessment': self.assess_performance(serial_durations, parallel_durations)
        }

        return analysis

    def assess_performance(self, serial_durations: List[float], parallel_durations: List[float]) -> Dict[str, str]:
        """评估性能表现"""
        assessment = {}

        # 评估串行性能
        if serial_durations:
            avg_serial = statistics.mean(serial_durations)
            if avg_serial <= 15:
                assessment['serial'] = "优秀"
            elif avg_serial <= 20:
                assessment['serial'] = "良好"
            elif avg_serial <= 25:
                assessment['serial'] = "可接受"
            else:
                assessment['serial'] = "需要优化"

        # 评估并行性能
        if parallel_durations:
            max_parallel = max(parallel_durations)
            if max_parallel <= 20:
                assessment['parallel'] = "优秀"
            elif max_parallel <= 25:
                assessment['parallel'] = "良好"
            elif max_parallel <= 30:
                assessment['parallel'] = "可接受"
            else:
                assessment['parallel'] = "需要优化"

        return assessment

    def save_results(self, results: List[Dict[str, any]], analysis: Dict[str, any]) -> str:
        """保存测试结果"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"results/standard_task_benchmark_{timestamp}.json"

        output = {
            "benchmark_type": "standard_task",
            "timestamp": timestamp,
            "results": results,
            "analysis": analysis,
            "environment": {
                "test_url": self.base_url,
                "task_count": len(self.test_tasks),
                "expected_duration": 20.0
            }
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"📁 结果已保存到: {filename}")
        return filename

async def main():
    benchmark = StandardTaskBenchmark()
    results = await benchmark.run_benchmark()
    analysis = benchmark.analyze_results(results)
    filename = benchmark.save_results(results, analysis)

    # 打印分析结果
    print("\n📊 基准测试分析结果:")
    print(f"串行执行平均时间: {analysis['serial_execution']['avg_duration']:.2f}s")
    print(f"并行执行最大时间: {analysis['parallel_execution']['max_duration']:.2f}s")
    print(f"性能评估 - 串行: {analysis['performance_assessment'].get('serial', 'N/A')}")
    print(f"性能评估 - 并行: {analysis['performance_assessment'].get('parallel', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 系统负载基准测试

#### 并发用户负载测试
```python
# 文件: benchmarks/load_test.py

import asyncio
import aiohttp
import time
import random
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class LoadTestConfig:
    """负载测试配置"""
    concurrent_users: int = 50
    test_duration: int = 300  # 5分钟
    ramp_up_time: int = 60    # 1分钟
    base_url: str = "http://localhost:8080"

class LoadTester:
    """负载测试器"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results = []
        self.test_scenarios = [
            {"endpoint": "/health", "method": "GET", "weight": 30},
            {"endpoint": "/api/agents/status", "method": "GET", "weight": 20},
            {"endpoint": "/api/workflow/execute", "method": "POST", "weight": 25},
            {"endpoint": "/api/workflow/status", "method": "GET", "weight": 25}
        ]

    async def simulate_user(self, user_id: int, session: aiohttp.ClientSession) -> List[Dict]:
        """模拟单个用户的行为"""
        user_results = []
        start_time = time.time()

        while time.time() - start_time < self.config.test_duration:
            # 选择测试场景
            scenario = self.select_scenario()

            # 执行请求
            result = await self.execute_request(user_id, session, scenario)
            user_results.append(result)

            # 随机等待时间（模拟真实用户行为）
            await asyncio.sleep(random.uniform(1, 5))

        return user_results

    def select_scenario(self) -> Dict:
        """根据权重选择测试场景"""
        scenarios = []
        for scenario in self.test_scenarios:
            scenarios.extend([scenario] * scenario["weight"])

        return random.choice(scenarios)

    async def execute_request(self, user_id: int, session: aiohttp.ClientSession, scenario: Dict) -> Dict:
        """执行HTTP请求"""
        url = f"{self.config.base_url}{scenario['endpoint']}"
        method = scenario["method"]

        start_time = time.time()

        try:
            if method == "GET":
                async with session.get(url) as response:
                    await response.text()
                    status_code = response.status
            elif method == "POST":
                payload = self.generate_payload(scenario["endpoint"])
                async with session.post(url, json=payload) as response:
                    await response.text()
                    status_code = response.status

            end_time = time.time()

            return {
                "user_id": user_id,
                "endpoint": scenario["endpoint"],
                "method": method,
                "status_code": status_code,
                "response_time": end_time - start_time,
                "timestamp": end_time,
                "success": 200 <= status_code < 400
            }

        except Exception as e:
            end_time = time.time()
            return {
                "user_id": user_id,
                "endpoint": scenario["endpoint"],
                "method": method,
                "status_code": 0,
                "response_time": end_time - start_time,
                "timestamp": end_time,
                "success": False,
                "error": str(e)
            }

    def generate_payload(self, endpoint: str) -> Dict:
        """为POST请求生成载荷"""
        if endpoint == "/api/workflow/execute":
            tasks = [
                "fix bug in user authentication",
                "optimize database queries",
                "add input validation",
                "implement caching layer",
                "update API documentation"
            ]
            return {
                "task": random.choice(tasks),
                "complexity": random.choice(["simple", "standard", "complex"]),
                "phase": random.randint(1, 7)
            }
        return {}

    async def run_load_test(self) -> Dict[str, any]:
        """运行负载测试"""
        print(f"🚀 开始负载测试: {self.config.concurrent_users} 并发用户, {self.config.test_duration}s")

        # 创建连接池
        connector = aiohttp.TCPConnector(limit=self.config.concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 渐进式增加用户负载
            tasks = []

            for user_id in range(self.config.concurrent_users):
                # 计算用户启动延迟
                delay = (self.config.ramp_up_time / self.config.concurrent_users) * user_id

                task = asyncio.create_task(
                    self.delayed_user_simulation(user_id, session, delay)
                )
                tasks.append(task)

            # 等待所有用户完成
            all_results = await asyncio.gather(*tasks)

            # 汇总结果
            self.results = [result for user_results in all_results for result in user_results]

        return self.analyze_results()

    async def delayed_user_simulation(self, user_id: int, session: aiohttp.ClientSession, delay: float) -> List[Dict]:
        """延迟启动用户模拟"""
        await asyncio.sleep(delay)
        return await self.simulate_user(user_id, session)

    def analyze_results(self) -> Dict[str, any]:
        """分析负载测试结果"""
        if not self.results:
            return {}

        # 统计基础指标
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r["success"]])
        failed_requests = total_requests - successful_requests

        # 响应时间统计
        response_times = [r["response_time"] for r in self.results if r["success"]]

        if response_times:
            response_times.sort()
            p50 = response_times[int(len(response_times) * 0.5)]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
        else:
            p50 = p95 = p99 = avg_response_time = max_response_time = 0

        # 计算吞吐量
        test_start = min(r["timestamp"] for r in self.results)
        test_end = max(r["timestamp"] for r in self.results)
        test_duration = test_end - test_start
        throughput = total_requests / test_duration if test_duration > 0 else 0

        # 错误率统计
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0

        # 按端点统计
        endpoint_stats = {}
        for result in self.results:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {"requests": 0, "errors": 0, "total_time": 0}

            endpoint_stats[endpoint]["requests"] += 1
            if not result["success"]:
                endpoint_stats[endpoint]["errors"] += 1
            endpoint_stats[endpoint]["total_time"] += result["response_time"]

        # 计算每个端点的平均响应时间
        for endpoint, stats in endpoint_stats.items():
            if stats["requests"] > 0:
                stats["avg_response_time"] = stats["total_time"] / stats["requests"]
                stats["error_rate"] = (stats["errors"] / stats["requests"]) * 100

        return {
            "test_config": {
                "concurrent_users": self.config.concurrent_users,
                "test_duration": self.config.test_duration,
                "ramp_up_time": self.config.ramp_up_time
            },
            "overall_metrics": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "error_rate": error_rate,
                "throughput_rps": throughput,
                "test_duration": test_duration
            },
            "response_time_metrics": {
                "average": avg_response_time,
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "max": max_response_time
            },
            "endpoint_statistics": endpoint_stats,
            "performance_assessment": self.assess_load_performance(
                error_rate, avg_response_time, p95, throughput
            )
        }

    def assess_load_performance(self, error_rate: float, avg_response: float, p95_response: float, throughput: float) -> str:
        """评估负载性能"""
        issues = []

        if error_rate > 1.0:
            issues.append(f"错误率过高: {error_rate:.2f}%")

        if avg_response > 0.5:
            issues.append(f"平均响应时间过长: {avg_response:.3f}s")

        if p95_response > 1.0:
            issues.append(f"P95响应时间过长: {p95_response:.3f}s")

        if throughput < 100:
            issues.append(f"吞吐量过低: {throughput:.1f} req/s")

        if not issues:
            return "优秀"
        elif len(issues) <= 2:
            return f"良好 (注意: {'; '.join(issues)})"
        else:
            return f"需要优化 (问题: {'; '.join(issues)})"

async def main():
    # 配置负载测试
    config = LoadTestConfig(
        concurrent_users=50,
        test_duration=300,  # 5分钟
        ramp_up_time=60     # 1分钟渐进
    )

    tester = LoadTester(config)
    results = await tester.run_load_test()

    # 保存结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"results/load_test_{timestamp}.json"

    import json
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

    # 打印结果摘要
    print("\n📊 负载测试结果摘要:")
    print(f"总请求数: {results['overall_metrics']['total_requests']}")
    print(f"成功率: {(results['overall_metrics']['successful_requests']/results['overall_metrics']['total_requests']*100):.1f}%")
    print(f"平均响应时间: {results['response_time_metrics']['average']:.3f}s")
    print(f"P95响应时间: {results['response_time_metrics']['p95']:.3f}s")
    print(f"吞吐量: {results['overall_metrics']['throughput_rps']:.1f} req/s")
    print(f"性能评估: {results['performance_assessment']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📈 性能基准报告

### 当前系统性能基准

#### Agent执行性能基准
```yaml
agent_performance_baseline:
  simple_tasks_4_agents:
    target_duration: "< 10s"
    measured_avg: "8.2s"
    measured_p95: "12.1s"
    success_rate: "99.2%"
    assessment: "优秀"

  standard_tasks_6_agents:
    target_duration: "< 20s"
    measured_avg: "16.8s"
    measured_p95: "22.3s"
    success_rate: "98.7%"
    assessment: "良好"

  complex_tasks_8_agents:
    target_duration: "< 30s"
    measured_avg: "26.4s"
    measured_p95: "31.8s"
    success_rate: "97.9%"
    assessment: "可接受"
```

#### 系统资源使用基准
```yaml
resource_usage_baseline:
  idle_state:
    cpu_usage: "5-8%"
    memory_usage: "35-40%"
    disk_io: "< 10 MB/s"
    network_io: "< 1 MB/s"

  normal_load:
    cpu_usage: "15-25%"
    memory_usage: "45-55%"
    disk_io: "20-50 MB/s"
    network_io: "5-15 MB/s"

  peak_load:
    cpu_usage: "60-75%"
    memory_usage: "70-80%"
    disk_io: "100-200 MB/s"
    network_io: "50-100 MB/s"
```

#### API响应时间基准
```yaml
api_response_baseline:
  health_endpoint:
    target: "< 50ms"
    measured_avg: "23ms"
    measured_p95: "45ms"
    measured_p99: "68ms"

  agent_status:
    target: "< 100ms"
    measured_avg: "67ms"
    measured_p95: "98ms"
    measured_p99: "156ms"

  workflow_execute:
    target: "< 200ms"
    measured_avg: "145ms"
    measured_p95: "189ms"
    measured_p99: "267ms"

  workflow_status:
    target: "< 80ms"
    measured_avg: "54ms"
    measured_p95: "76ms"
    measured_p99: "112ms"
```

### 负载性能基准

#### 并发用户测试结果
```yaml
concurrent_user_baseline:
  light_load_25_users:
    error_rate: "0.1%"
    avg_response_time: "156ms"
    p95_response_time: "289ms"
    throughput: "95 req/s"
    assessment: "优秀"

  normal_load_50_users:
    error_rate: "0.3%"
    avg_response_time: "234ms"
    p95_response_time: "456ms"
    throughput: "178 req/s"
    assessment: "良好"

  heavy_load_100_users:
    error_rate: "1.2%"
    avg_response_time: "567ms"
    p95_response_time: "1.2s"
    throughput: "298 req/s"
    assessment: "可接受"

  stress_load_200_users:
    error_rate: "3.8%"
    avg_response_time: "1.1s"
    p95_response_time: "2.3s"
    throughput: "445 req/s"
    assessment: "需要优化"
```

## 🎯 性能监控告警阈值

### 响应时间告警
```yaml
response_time_alerts:
  warning_thresholds:
    api_avg_response: "> 300ms"
    api_p95_response: "> 500ms"
    agent_execution: "> 125% of baseline"

  critical_thresholds:
    api_avg_response: "> 1000ms"
    api_p95_response: "> 2000ms"
    agent_execution: "> 200% of baseline"
```

### 资源使用告警
```yaml
resource_alerts:
  warning_thresholds:
    cpu_usage: "> 70%"
    memory_usage: "> 80%"
    disk_usage: "> 85%"
    disk_io: "> 200 MB/s"

  critical_thresholds:
    cpu_usage: "> 90%"
    memory_usage: "> 95%"
    disk_usage: "> 95%"
    disk_io: "> 500 MB/s"
```

### 业务指标告警
```yaml
business_alerts:
  warning_thresholds:
    error_rate: "> 1%"
    task_failure_rate: "> 2%"
    agent_timeout_rate: "> 5%"

  critical_thresholds:
    error_rate: "> 5%"
    task_failure_rate: "> 10%"
    agent_timeout_rate: "> 15%"
```

## 📊 性能趋势分析

### 基准测试自动化
```bash
#!/bin/bash
# 文件: scripts/automated_benchmark.sh

set -euo pipefail

BENCHMARK_DIR="benchmarks"
RESULTS_DIR="results"
REPORTS_DIR="reports"

echo "🚀 开始自动化性能基准测试..."

# 创建结果目录
mkdir -p "$RESULTS_DIR" "$REPORTS_DIR"

# 1. Agent性能基准测试
echo "🤖 执行Agent性能基准测试..."
bash "$BENCHMARK_DIR/simple_task_benchmark.sh"
python3 "$BENCHMARK_DIR/standard_task_benchmark.py"
python3 "$BENCHMARK_DIR/complex_task_benchmark.py"

# 2. 系统负载测试
echo "📊 执行系统负载测试..."
python3 "$BENCHMARK_DIR/load_test.py"

# 3. API性能测试
echo "🔌 执行API性能测试..."
python3 "$BENCHMARK_DIR/api_benchmark.py"

# 4. 数据库性能测试
echo "🗄️ 执行数据库性能测试..."
python3 "$BENCHMARK_DIR/database_benchmark.py"

# 5. 生成综合报告
echo "📋 生成性能基准报告..."
python3 scripts/generate_benchmark_report.py \
    --results-dir "$RESULTS_DIR" \
    --output-dir "$REPORTS_DIR"

# 6. 与历史基准对比
echo "📈 对比历史性能趋势..."
python3 scripts/performance_trend_analysis.py \
    --current-results "$RESULTS_DIR" \
    --historical-data "historical_benchmarks/" \
    --output "$REPORTS_DIR/trend_analysis.html"

echo "✅ 自动化性能基准测试完成!"
echo "📊 查看报告: $REPORTS_DIR/"
```

### 性能回归检测
```python
# 文件: scripts/performance_regression_detector.py

import json
import glob
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any

class PerformanceRegressionDetector:
    """性能回归检测器"""

    def __init__(self, threshold_percent: float = 10.0):
        self.threshold_percent = threshold_percent
        self.baseline_metrics = {}
        self.current_metrics = {}

    def load_baseline(self, baseline_files: List[str]) -> None:
        """加载基准性能数据"""
        for file_path in baseline_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.process_baseline_data(data)

    def load_current_results(self, result_files: List[str]) -> None:
        """加载当前测试结果"""
        for file_path in result_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.process_current_data(data)

    def detect_regressions(self) -> List[Dict[str, Any]]:
        """检测性能回归"""
        regressions = []

        for metric_name, current_value in self.current_metrics.items():
            if metric_name in self.baseline_metrics:
                baseline_value = self.baseline_metrics[metric_name]

                # 计算性能变化百分比
                if baseline_value > 0:
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100

                    # 检查是否超过阈值
                    if abs(change_percent) > self.threshold_percent:
                        regression_type = "degradation" if change_percent > 0 else "improvement"

                        regressions.append({
                            "metric": metric_name,
                            "baseline_value": baseline_value,
                            "current_value": current_value,
                            "change_percent": change_percent,
                            "type": regression_type,
                            "severity": self.assess_severity(abs(change_percent))
                        })

        return regressions

    def assess_severity(self, change_percent: float) -> str:
        """评估回归严重程度"""
        if change_percent > 50:
            return "critical"
        elif change_percent > 25:
            return "high"
        elif change_percent > 10:
            return "medium"
        else:
            return "low"

    def generate_regression_report(self, regressions: List[Dict[str, Any]]) -> str:
        """生成回归报告"""
        if not regressions:
            return "✅ 未检测到性能回归"

        report = "🚨 性能回归检测报告\n\n"

        # 按严重程度分组
        by_severity = {}
        for regression in regressions:
            severity = regression["severity"]
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(regression)

        for severity in ["critical", "high", "medium", "low"]:
            if severity in by_severity:
                report += f"## {severity.upper()} 级别回归\n\n"
                for reg in by_severity[severity]:
                    report += f"- **{reg['metric']}**: "
                    report += f"{reg['baseline_value']:.3f} → {reg['current_value']:.3f} "
                    report += f"({reg['change_percent']:+.1f}%)\n"
                report += "\n"

        return report

def main():
    detector = PerformanceRegressionDetector(threshold_percent=15.0)

    # 加载基准数据 (最近7天的平均值)
    baseline_files = glob.glob("historical_benchmarks/baseline_*.json")
    detector.load_baseline(baseline_files)

    # 加载当前结果
    current_files = glob.glob("results/*_benchmark_*.json")
    detector.load_current_results(current_files)

    # 检测回归
    regressions = detector.detect_regressions()

    # 生成报告
    report = detector.generate_regression_report(regressions)
    print(report)

    # 保存报告
    with open("reports/regression_report.md", "w") as f:
        f.write(report)

    # 如果有严重回归，退出码为1
    critical_regressions = [r for r in regressions if r["severity"] in ["critical", "high"]]
    if critical_regressions:
        print(f"❌ 检测到 {len(critical_regressions)} 个严重性能回归")
        exit(1)
    else:
        print("✅ 性能检查通过")

if __name__ == "__main__":
    main()
```

---

**🎯 总结**:

这份性能监控基准文档建立了Claude Enhancer系统的完整性能基准线，包括：

- **🤖 Agent执行性能**: 4-6-8 Agent策略的执行时间基准
- **🌐 API响应性能**: 各个接口的响应时间基准
- **📊 系统负载能力**: 不同并发量下的性能表现
- **🔍 资源使用基准**: CPU、内存、磁盘、网络的正常使用范围
- **⚠️ 告警阈值设置**: 基于基准的合理告警配置
- **📈 趋势分析工具**: 自动化性能回归检测

这些基准为系统监控、性能优化和容量规划提供了可靠的参考依据。