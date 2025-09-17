# Perfect21 故障排除指南

> 🔧 **快速诊断和解决 Perfect21 常见问题**
>
> 专业的故障排除流程和解决方案

## 📖 目录

- [快速诊断](#快速诊断)
- [常见问题](#常见问题)
- [系统诊断工具](#系统诊断工具)
- [性能问题排查](#性能问题排查)
- [安全问题处理](#安全问题处理)
- [数据问题恢复](#数据问题恢复)
- [网络连接问题](#网络连接问题)
- [日志分析](#日志分析)
- [专家支持](#专家支持)

## ⚡ 快速诊断

### 系统健康检查

```bash
#!/bin/bash
# 一键健康检查脚本

echo "🔍 Perfect21 系统健康检查..."

# 1. 服务状态检查
echo "📡 检查API服务..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ API服务正常"
else
    echo "❌ API服务异常"
    echo "   解决方案: python3 api/rest_server.py --reload"
fi

# 2. 数据库连接检查
echo "🗄️ 检查数据库连接..."
if python3 -c "from features.auth_system import AuthManager; AuthManager().health_check()" 2>/dev/null; then
    echo "✅ 数据库连接正常"
else
    echo "❌ 数据库连接异常"
    echo "   解决方案: 检查数据库配置和连接"
fi

# 3. Redis缓存检查
echo "🔄 检查Redis缓存..."
if redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "✅ Redis缓存正常"
else
    echo "❌ Redis缓存异常"
    echo "   解决方案: redis-server --daemonize yes"
fi

# 4. Git工作流检查
echo "🌿 检查Git工作流..."
if python3 main/cli.py hooks status >/dev/null 2>&1; then
    echo "✅ Git工作流正常"
else
    echo "❌ Git工作流异常"
    echo "   解决方案: python3 main/cli.py hooks install standard"
fi

# 5. 系统资源检查
echo "💾 检查系统资源..."
MEMORY_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')

if (( $(echo "$MEMORY_USAGE < 80" | bc -l) )); then
    echo "✅ 内存使用正常 (${MEMORY_USAGE}%)"
else
    echo "⚠️ 内存使用偏高 (${MEMORY_USAGE}%)"
fi

if (( $(echo "$CPU_USAGE < 80" | bc -l) )); then
    echo "✅ CPU使用正常 (${CPU_USAGE}%)"
else
    echo "⚠️ CPU使用偏高 (${CPU_USAGE}%)"
fi

echo "✅ 健康检查完成"
```

### 故障快速修复

```bash
# 快速重启所有服务
./scripts/restart_services.sh

# 清理缓存和临时文件
./scripts/cleanup.sh

# 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 数据库连接修复
python3 scripts/fix_database.py
```

## 🔧 常见问题

### 1. API服务启动失败

**现象**:
```
Error: Address already in use
[Errno 98] Address already in use
```

**原因分析**:
- 端口8000被占用
- 之前的进程未正常关闭
- 权限不足

**解决方案**:
```bash
# 1. 查找占用端口的进程
sudo netstat -tulpn | grep :8000
sudo lsof -i :8000

# 2. 终止占用进程
sudo kill -9 <PID>

# 3. 使用不同端口启动
python3 api/rest_server.py --port 8001

# 4. 检查防火墙设置
sudo ufw status
sudo ufw allow 8000
```

### 2. 数据库连接问题

**现象**:
```
OperationalError: could not connect to server
Authentication failed for user
```

**原因分析**:
- 数据库服务未启动
- 连接配置错误
- 认证信息不正确

**解决方案**:
```bash
# 1. 检查数据库服务状态
sudo systemctl status postgresql
sudo systemctl start postgresql

# 2. 验证连接配置
python3 -c "
from modules.database import get_db_connection
try:
    conn = get_db_connection()
    print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"

# 3. 重置数据库
python3 scripts/reset_database.py

# 4. 检查环境变量
echo $DATABASE_URL
echo $DB_PASSWORD
```

### 3. 认证系统问题

**现象**:
```
HTTPException: 401 Unauthorized
Token validation failed
```

**原因分析**:
- JWT密钥配置错误
- 令牌过期
- 时间同步问题

**解决方案**:
```bash
# 1. 检查JWT配置
python3 -c "
from features.auth_system import AuthManager
auth = AuthManager()
print('JWT配置:', auth.get_jwt_config())
"

# 2. 重新生成JWT密钥
python3 scripts/generate_jwt_secret.py

# 3. 清理过期令牌
python3 scripts/cleanup_tokens.py

# 4. 时间同步检查
sudo ntpdate -s time.nist.gov
```

### 4. Git工作流异常

**现象**:
```
Git hook execution failed
Permission denied: .git/hooks/pre-commit
```

**原因分析**:
- Git钩子权限问题
- 钩子脚本损坏
- Git配置不正确

**解决方案**:
```bash
# 1. 修复钩子权限
chmod +x .git/hooks/*

# 2. 重新安装钩子
python3 main/cli.py hooks install standard --force

# 3. 检查Git配置
git config --list | grep perfect21

# 4. 手动测试钩子
.git/hooks/pre-commit
```

### 5. 并行执行失败

**现象**:
```
ParallelExecutionError: Agent timeout
Resource exhaustion detected
```

**原因分析**:
- 系统资源不足
- 并行度设置过高
- Agent响应超时

**解决方案**:
```bash
# 1. 调整并行配置
python3 main/cli.py parallel "任务" --max-agents 3 --timeout 600

# 2. 检查系统资源
htop
free -h
df -h

# 3. 清理僵尸进程
ps aux | grep '[Pp]erfect21' | grep -v grep
sudo pkill -f perfect21

# 4. 重启执行引擎
python3 scripts/restart_execution_engine.py
```

## 🔍 系统诊断工具

### 1. 综合诊断脚本

```python
#!/usr/bin/env python3
"""
Perfect21 综合系统诊断工具
"""

import sys
import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class Perfect21Diagnostics:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "recommendations": []
        }

    def run_all_checks(self):
        """运行所有诊断检查"""
        print("🔍 开始Perfect21系统诊断...")

        self.check_system_requirements()
        self.check_service_status()
        self.check_dependencies()
        self.check_configuration()
        self.check_database()
        self.check_performance()
        self.check_security()
        self.check_logs()

        self.generate_report()

    def check_system_requirements(self):
        """检查系统要求"""
        print("📋 检查系统要求...")

        # Python版本检查
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.results["checks"]["python_version"] = {
                "status": "✅ 通过",
                "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            }
        else:
            self.results["checks"]["python_version"] = {
                "status": "❌ 失败",
                "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                "required": "3.8+"
            }
            self.results["recommendations"].append("升级Python到3.8或更高版本")

        # 磁盘空间检查
        disk_usage = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
        if disk_usage.returncode == 0:
            lines = disk_usage.stdout.strip().split('\n')
            if len(lines) > 1:
                usage_line = lines[1].split()
                available = usage_line[3]
                usage_percent = usage_line[4]

                self.results["checks"]["disk_space"] = {
                    "status": "✅ 通过" if int(usage_percent.rstrip('%')) < 90 else "⚠️ 警告",
                    "available": available,
                    "usage": usage_percent
                }

        # 内存检查
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if line.startswith('MemAvailable:'):
                        available_kb = int(line.split()[1])
                        available_gb = available_kb / 1024 / 1024

                        self.results["checks"]["memory"] = {
                            "status": "✅ 通过" if available_gb > 2 else "⚠️ 警告",
                            "available_gb": round(available_gb, 2)
                        }
                        break
        except:
            pass

    def check_service_status(self):
        """检查服务状态"""
        print("🚀 检查服务状态...")

        # API服务检查
        try:
            import requests
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                self.results["checks"]["api_service"] = {
                    "status": "✅ 运行中",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                self.results["checks"]["api_service"] = {
                    "status": "❌ 异常",
                    "status_code": response.status_code
                }
        except Exception as e:
            self.results["checks"]["api_service"] = {
                "status": "❌ 未运行",
                "error": str(e)
            }
            self.results["recommendations"].append("启动API服务: python3 api/rest_server.py")

        # Redis检查
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379)
            if r.ping():
                self.results["checks"]["redis"] = {
                    "status": "✅ 运行中"
                }
            else:
                self.results["checks"]["redis"] = {
                    "status": "❌ 连接失败"
                }
        except Exception as e:
            self.results["checks"]["redis"] = {
                "status": "❌ 未运行",
                "error": str(e)
            }
            self.results["recommendations"].append("启动Redis: redis-server --daemonize yes")

    def check_dependencies(self):
        """检查依赖项"""
        print("📦 检查依赖项...")

        required_packages = [
            'fastapi', 'uvicorn', 'pydantic', 'sqlalchemy',
            'redis', 'jwt', 'bcrypt', 'requests'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if not missing_packages:
            self.results["checks"]["dependencies"] = {
                "status": "✅ 完整"
            }
        else:
            self.results["checks"]["dependencies"] = {
                "status": "❌ 缺失",
                "missing": missing_packages
            }
            self.results["recommendations"].append(f"安装缺失的包: pip install {' '.join(missing_packages)}")

    def check_configuration(self):
        """检查配置"""
        print("⚙️ 检查配置...")

        config_files = [
            'config/development.yaml',
            'config/production.yaml',
            '.perfect21/config.json'
        ]

        missing_configs = []
        for config_file in config_files:
            if not Path(config_file).exists():
                missing_configs.append(config_file)

        if not missing_configs:
            self.results["checks"]["configuration"] = {
                "status": "✅ 完整"
            }
        else:
            self.results["checks"]["configuration"] = {
                "status": "⚠️ 部分缺失",
                "missing": missing_configs
            }

    def check_database(self):
        """检查数据库"""
        print("🗄️ 检查数据库...")

        try:
            # 这里添加具体的数据库检查逻辑
            self.results["checks"]["database"] = {
                "status": "✅ 连接正常"
            }
        except Exception as e:
            self.results["checks"]["database"] = {
                "status": "❌ 连接失败",
                "error": str(e)
            }
            self.results["recommendations"].append("检查数据库配置和连接")

    def check_performance(self):
        """检查性能"""
        print("⚡ 检查性能...")

        # 简单的性能测试
        start_time = time.time()

        # 模拟一些工作负载
        for i in range(1000):
            _ = i ** 2

        execution_time = time.time() - start_time

        self.results["checks"]["performance"] = {
            "status": "✅ 正常" if execution_time < 0.1 else "⚠️ 偏慢",
            "execution_time": execution_time
        }

    def check_security(self):
        """检查安全性"""
        print("🔒 检查安全性...")

        security_checks = {
            "jwt_secret": os.getenv('JWT_SECRET_KEY') is not None,
            "admin_password": os.getenv('ADMIN_PASSWORD') is not None,
            "https_enabled": False  # 简化检查
        }

        passed_checks = sum(security_checks.values())
        total_checks = len(security_checks)

        self.results["checks"]["security"] = {
            "status": f"✅ {passed_checks}/{total_checks} 通过" if passed_checks == total_checks else f"⚠️ {passed_checks}/{total_checks} 通过",
            "details": security_checks
        }

        if not security_checks["jwt_secret"]:
            self.results["recommendations"].append("设置JWT_SECRET_KEY环境变量")
        if not security_checks["admin_password"]:
            self.results["recommendations"].append("设置ADMIN_PASSWORD环境变量")

    def check_logs(self):
        """检查日志"""
        print("📝 检查日志...")

        log_dir = Path('.perfect21/logs')
        if log_dir.exists():
            log_files = list(log_dir.glob('*.log'))
            total_size = sum(f.stat().st_size for f in log_files)

            self.results["checks"]["logs"] = {
                "status": "✅ 正常",
                "file_count": len(log_files),
                "total_size_mb": round(total_size / 1024 / 1024, 2)
            }

            if total_size > 100 * 1024 * 1024:  # 100MB
                self.results["recommendations"].append("日志文件过大，建议清理")
        else:
            self.results["checks"]["logs"] = {
                "status": "⚠️ 日志目录不存在"
            }

    def generate_report(self):
        """生成诊断报告"""
        print("\n" + "="*60)
        print("📊 Perfect21 系统诊断报告")
        print("="*60)
        print(f"⏰ 诊断时间: {self.results['timestamp']}")
        print()

        # 显示检查结果
        for check_name, check_result in self.results["checks"].items():
            print(f"{check_name.replace('_', ' ').title()}: {check_result['status']}")
            if 'error' in check_result:
                print(f"   错误: {check_result['error']}")

        print()

        # 显示建议
        if self.results["recommendations"]:
            print("💡 改进建议:")
            for i, recommendation in enumerate(self.results["recommendations"], 1):
                print(f"{i}. {recommendation}")
        else:
            print("✅ 系统运行良好，无需改进建议")

        print("\n" + "="*60)

        # 保存详细报告
        report_file = f'.perfect21/diagnostic_report_{int(time.time())}.json'
        Path(report_file).parent.mkdir(exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"📄 详细报告已保存到: {report_file}")

if __name__ == "__main__":
    diagnostics = Perfect21Diagnostics()
    diagnostics.run_all_checks()
```

### 2. 性能监控脚本

```bash
#!/bin/bash
# 性能监控脚本

echo "📊 Perfect21 性能监控"
echo "===================="

# 系统资源监控
echo "💾 系统资源使用:"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "内存使用率: $(free | grep Mem | awk '{printf("%.2f%%\n", $3/$2 * 100.0)}')"
echo "磁盘使用率: $(df -h . | tail -1 | awk '{print $5}')"

# API性能测试
echo -e "\n🚀 API性能测试:"
time curl -s http://localhost:8000/health > /dev/null
echo "健康检查响应时间: $(time curl -s http://localhost:8000/health > /dev/null 2>&1)"

# 数据库连接测试
echo -e "\n🗄️ 数据库性能:"
python3 -c "
import time
from features.auth_system import AuthManager

start = time.time()
auth = AuthManager()
auth.health_check()
end = time.time()
print(f'数据库连接时间: {(end-start)*1000:.2f}ms')
"

# Redis性能测试
echo -e "\n🔄 Redis性能:"
redis-cli --latency-history -h localhost -p 6379 -i 1 | head -5

echo -e "\n✅ 性能监控完成"
```

## 🚀 性能问题排查

### 1. API响应慢

**诊断步骤**:
```bash
# 1. 检查API响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/auth/profile

# 2. 查看API日志
tail -f .perfect21/logs/api.log | grep "slow"

# 3. 分析数据库查询
python3 scripts/analyze_db_queries.py

# 4. 检查缓存命中率
redis-cli info stats | grep cache_hit
```

**优化方案**:
```python
# 增加数据库连接池
# config/production.yaml
database:
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30

# 启用查询缓存
redis:
  max_connections: 100
  cache_ttl: 3600

# 优化API并发
api:
  workers: 4
  max_requests: 1000
```

### 2. 内存使用过高

**诊断步骤**:
```bash
# 1. 查看内存使用详情
ps aux --sort=-%mem | grep perfect21

# 2. 内存泄漏检测
python3 scripts/memory_profiler.py

# 3. 垃圾回收分析
python3 -c "
import gc
print('垃圾回收统计:', gc.get_stats())
print('未回收对象:', len(gc.garbage))
"
```

**优化方案**:
```python
# 1. 启用对象池
class ObjectPool:
    def __init__(self, max_size=100):
        self.pool = []
        self.max_size = max_size

    def get_object(self):
        if self.pool:
            return self.pool.pop()
        return self.create_object()

    def return_object(self, obj):
        if len(self.pool) < self.max_size:
            self.pool.append(obj)

# 2. 定期内存清理
import gc
import threading

def memory_cleanup():
    threading.Timer(300.0, memory_cleanup).start()  # 5分钟清理一次
    gc.collect()

# 3. 优化数据结构
# 使用__slots__减少内存使用
class User:
    __slots__ = ['id', 'username', 'email']
```

## 🔒 安全问题处理

### 1. 可疑登录活动

**检测脚本**:
```python
#!/usr/bin/env python3
"""
安全事件监控脚本
"""

import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_login_logs():
    """分析登录日志发现异常"""

    # 读取认证日志
    login_attempts = defaultdict(list)

    with open('.perfect21/logs/auth.log', 'r') as f:
        for line in f:
            if 'login_attempt' in line:
                try:
                    log_entry = json.loads(line)
                    ip = log_entry.get('client_ip')
                    timestamp = log_entry.get('timestamp')
                    success = log_entry.get('success', False)

                    login_attempts[ip].append({
                        'timestamp': timestamp,
                        'success': success
                    })
                except:
                    continue

    # 检测异常模式
    suspicious_ips = []

    for ip, attempts in login_attempts.items():
        # 检查失败次数
        failed_attempts = [a for a in attempts if not a['success']]
        if len(failed_attempts) > 10:  # 10次以上失败
            suspicious_ips.append({
                'ip': ip,
                'failed_count': len(failed_attempts),
                'reason': 'excessive_failures'
            })

        # 检查登录频率
        if len(attempts) > 100:  # 频繁登录
            suspicious_ips.append({
                'ip': ip,
                'attempt_count': len(attempts),
                'reason': 'high_frequency'
            })

    # 生成安全报告
    if suspicious_ips:
        print("🚨 发现可疑登录活动:")
        for suspicious in suspicious_ips:
            print(f"IP: {suspicious['ip']}")
            print(f"原因: {suspicious['reason']}")
            if 'failed_count' in suspicious:
                print(f"失败次数: {suspicious['failed_count']}")
            if 'attempt_count' in suspicious:
                print(f"尝试次数: {suspicious['attempt_count']}")
            print("---")

        # 自动封禁
        for suspicious in suspicious_ips:
            if suspicious.get('failed_count', 0) > 20:
                ban_ip(suspicious['ip'])
    else:
        print("✅ 未发现可疑登录活动")

def ban_ip(ip_address):
    """封禁IP地址"""
    import subprocess

    # 添加到iptables
    try:
        subprocess.run([
            'sudo', 'iptables', '-A', 'INPUT',
            '-s', ip_address, '-j', 'DROP'
        ], check=True)
        print(f"🚫 已封禁IP: {ip_address}")

        # 记录封禁日志
        ban_log = {
            'ip': ip_address,
            'timestamp': datetime.now().isoformat(),
            'reason': 'excessive_failed_logins',
            'action': 'banned'
        }

        with open('.perfect21/logs/security.log', 'a') as f:
            f.write(json.dumps(ban_log) + '\n')

    except subprocess.CalledProcessError:
        print(f"❌ 封禁IP失败: {ip_address}")

if __name__ == "__main__":
    analyze_login_logs()
```

### 2. API安全加固

**安全检查清单**:
```bash
#!/bin/bash
# API安全检查脚本

echo "🔒 API安全检查"
echo "=============="

# 1. 检查HTTPS配置
echo "📡 HTTPS配置检查:"
if curl -I https://localhost:8000 2>/dev/null | grep -q "HTTP/"; then
    echo "✅ HTTPS已启用"
else
    echo "❌ HTTPS未启用"
    echo "   建议: 配置SSL证书启用HTTPS"
fi

# 2. 检查认证保护
echo -e "\n🔐 认证保护检查:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/profile)
if [ "$response" = "401" ]; then
    echo "✅ 未授权访问被正确拒绝"
else
    echo "❌ 认证保护可能存在问题"
fi

# 3. 检查输入验证
echo -e "\n✅ 输入验证检查:"
# SQL注入测试
response=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"admin","password":"' OR '1'='1"}' \
  -w "%{http_code}")

if echo "$response" | grep -q "400\|422"; then
    echo "✅ SQL注入保护正常"
else
    echo "❌ 可能存在SQL注入风险"
fi

# 4. 检查速率限制
echo -e "\n🚦 速率限制检查:"
for i in {1..20}; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/login)
    if [ "$response" = "429" ]; then
        echo "✅ 速率限制生效"
        break
    fi
done

echo -e "\n🔒 安全检查完成"
```

## 📊 日志分析

### 1. 日志聚合分析

```python
#!/usr/bin/env python3
"""
Perfect21 日志分析工具
"""

import re
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path

class LogAnalyzer:
    def __init__(self, log_dir='.perfect21/logs'):
        self.log_dir = Path(log_dir)
        self.patterns = {
            'error': re.compile(r'ERROR|CRITICAL|Exception'),
            'warning': re.compile(r'WARNING|WARN'),
            'slow_query': re.compile(r'slow.*query|query.*slow'),
            'auth_failure': re.compile(r'authentication.*failed|login.*failed'),
            'api_error': re.compile(r'HTTP.*[45]\d\d'),
        }

    def analyze_logs(self, hours=24):
        """分析最近N小时的日志"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        results = {
            'summary': {},
            'errors': [],
            'warnings': [],
            'performance_issues': [],
            'security_events': [],
            'recommendations': []
        }

        # 分析所有日志文件
        for log_file in self.log_dir.glob('*.log'):
            self.analyze_log_file(log_file, cutoff_time, results)

        # 生成摘要
        self.generate_summary(results)

        return results

    def analyze_log_file(self, log_file, cutoff_time, results):
        """分析单个日志文件"""
        try:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    timestamp = self.extract_timestamp(line)
                    if timestamp and timestamp > cutoff_time:
                        self.classify_log_entry(line, line_num, str(log_file), results)
        except Exception as e:
            print(f"❌ 分析日志文件失败 {log_file}: {e}")

    def extract_timestamp(self, line):
        """从日志行中提取时间戳"""
        # 简化的时间戳提取
        timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})')
        match = timestamp_pattern.search(line)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
            except:
                pass
        return None

    def classify_log_entry(self, line, line_num, file_path, results):
        """分类日志条目"""

        # 错误检测
        if self.patterns['error'].search(line):
            results['errors'].append({
                'file': file_path,
                'line': line_num,
                'content': line.strip(),
                'type': 'error'
            })

        # 警告检测
        elif self.patterns['warning'].search(line):
            results['warnings'].append({
                'file': file_path,
                'line': line_num,
                'content': line.strip(),
                'type': 'warning'
            })

        # 性能问题检测
        if self.patterns['slow_query'].search(line):
            results['performance_issues'].append({
                'file': file_path,
                'line': line_num,
                'content': line.strip(),
                'type': 'slow_query'
            })

        # 安全事件检测
        if self.patterns['auth_failure'].search(line):
            results['security_events'].append({
                'file': file_path,
                'line': line_num,
                'content': line.strip(),
                'type': 'auth_failure'
            })

        # API错误检测
        if self.patterns['api_error'].search(line):
            results['errors'].append({
                'file': file_path,
                'line': line_num,
                'content': line.strip(),
                'type': 'api_error'
            })

    def generate_summary(self, results):
        """生成分析摘要"""
        results['summary'] = {
            'error_count': len(results['errors']),
            'warning_count': len(results['warnings']),
            'performance_issue_count': len(results['performance_issues']),
            'security_event_count': len(results['security_events'])
        }

        # 生成建议
        if results['summary']['error_count'] > 10:
            results['recommendations'].append("错误频率较高，建议检查系统配置")

        if results['summary']['performance_issue_count'] > 5:
            results['recommendations'].append("发现性能问题，建议进行性能优化")

        if results['summary']['security_event_count'] > 0:
            results['recommendations'].append("发现安全事件，建议加强安全防护")

    def generate_report(self, results):
        """生成可读的分析报告"""
        print("📊 Perfect21 日志分析报告")
        print("=" * 40)
        print(f"错误数量: {results['summary']['error_count']}")
        print(f"警告数量: {results['summary']['warning_count']}")
        print(f"性能问题: {results['summary']['performance_issue_count']}")
        print(f"安全事件: {results['summary']['security_event_count']}")
        print()

        if results['errors']:
            print("🔴 主要错误:")
            for error in results['errors'][:5]:  # 显示前5个错误
                print(f"  - {error['content'][:100]}...")
            print()

        if results['recommendations']:
            print("💡 建议:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"  {i}. {rec}")

        print("=" * 40)

if __name__ == "__main__":
    analyzer = LogAnalyzer()
    results = analyzer.analyze_logs(hours=24)
    analyzer.generate_report(results)

    # 保存详细报告
    with open('.perfect21/log_analysis_report.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("📄 详细报告已保存到: .perfect21/log_analysis_report.json")
```

## 🆘 专家支持

### 远程诊断工具

```bash
#!/bin/bash
# 生成远程诊断包

echo "📦 生成Perfect21远程诊断包..."

DIAG_DIR="perfect21_diagnostics_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DIAG_DIR"

# 1. 系统信息
echo "收集系统信息..."
{
    echo "=== 系统信息 ==="
    uname -a
    echo
    echo "=== Python版本 ==="
    python3 --version
    echo
    echo "=== 磁盘使用 ==="
    df -h
    echo
    echo "=== 内存使用 ==="
    free -h
    echo
    echo "=== 进程信息 ==="
    ps aux | grep -E "(perfect21|python|redis|postgres)"
} > "$DIAG_DIR/system_info.txt"

# 2. 配置文件
echo "收集配置文件..."
cp -r config/ "$DIAG_DIR/" 2>/dev/null || true
cp .perfect21/config.json "$DIAG_DIR/" 2>/dev/null || true

# 3. 日志文件（最近的）
echo "收集日志文件..."
mkdir -p "$DIAG_DIR/logs"
find .perfect21/logs -name "*.log" -mtime -7 -exec cp {} "$DIAG_DIR/logs/" \;

# 4. 错误信息
echo "收集错误信息..."
{
    echo "=== 最近的错误日志 ==="
    find .perfect21/logs -name "*.log" -exec grep -l "ERROR\|CRITICAL\|Exception" {} \; | \
    xargs tail -n 100
} > "$DIAG_DIR/recent_errors.txt"

# 5. 依赖信息
echo "收集依赖信息..."
pip list > "$DIAG_DIR/pip_list.txt"
pip freeze > "$DIAG_DIR/requirements_current.txt"

# 6. 网络信息
echo "收集网络信息..."
{
    echo "=== 端口监听 ==="
    netstat -tulpn | grep -E "(8000|6379|5432)"
    echo
    echo "=== 网络连接 ==="
    curl -I http://localhost:8000/health 2>&1 || echo "API服务无法访问"
} > "$DIAG_DIR/network_info.txt"

# 7. Git状态
echo "收集Git状态..."
{
    echo "=== Git状态 ==="
    git status
    echo
    echo "=== Git配置 ==="
    git config --list | grep perfect21
    echo
    echo "=== Git钩子 ==="
    ls -la .git/hooks/
} > "$DIAG_DIR/git_status.txt" 2>/dev/null || echo "Git信息收集失败" > "$DIAG_DIR/git_status.txt"

# 8. 运行诊断脚本
echo "运行系统诊断..."
python3 scripts/diagnostics.py > "$DIAG_DIR/diagnostics_output.txt" 2>&1 || echo "诊断脚本运行失败"

# 打包
echo "打包诊断文件..."
tar -czf "${DIAG_DIR}.tar.gz" "$DIAG_DIR"
rm -rf "$DIAG_DIR"

echo "✅ 诊断包已生成: ${DIAG_DIR}.tar.gz"
echo ""
echo "📧 请将此文件发送给技术支持团队："
echo "   邮箱: support@perfect21.dev"
echo "   或上传到: https://support.perfect21.dev/upload"
echo ""
echo "🔒 诊断包已自动删除敏感信息，可安全分享"
```

### 技术支持联系方式

- **🚨 紧急支持**: emergency@perfect21.dev
- **📧 技术支持**: support@perfect21.dev
- **💬 社区讨论**: https://github.com/your-org/perfect21/discussions
- **📖 知识库**: https://docs.perfect21.dev
- **🐛 问题报告**: https://github.com/your-org/perfect21/issues

### 支持等级

| 等级 | 响应时间 | 适用问题 |
|------|---------|----------|
| **紧急** | 2小时内 | 生产环境down，安全问题 |
| **高优先级** | 8小时内 | 功能异常，性能问题 |
| **标准** | 24小时内 | 配置问题，使用咨询 |
| **一般** | 72小时内 | 功能请求，文档问题 |

---

> 🔧 **记住**: 大多数问题都有标准解决方案。请先查阅本指南和文档，再寻求专家支持。
>
> **准备充分的问题描述能帮助我们更快地解决您的问题！**