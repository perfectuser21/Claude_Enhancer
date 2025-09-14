#!/usr/bin/env python3
"""
VPS网络连接修复工具
解决从中国连接美国VPS的网络问题，包括WireGuard VPN和Web服务
"""

import subprocess
import json
import time
import requests
import socket
import os
import sys
from typing import Dict, List, Tuple

class NetworkFixer:
    def __init__(self):
        self.report = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "issues_found": [],
            "fixes_applied": [],
            "recommendations": []
        }

    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        print(f"[{level}] {message}")

    def run_command(self, cmd: str) -> Tuple[bool, str]:
        """执行系统命令"""
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def check_nginx_config(self) -> bool:
        """检查和修复Nginx配置"""
        self.log("🔍 检查Nginx配置...")

        # 检查nginx状态
        success, output = self.run_command("systemctl is-active nginx")
        if success:
            self.log("✅ Nginx正在运行")

            # 检查nginx配置
            success, config = self.run_command("nginx -T")
            if "server_name" in config and "listen 80" in config:
                self.report["issues_found"].append("Nginx占用端口80，可能与应用服务冲突")

                # 尝试重新配置nginx为反向代理
                return self.setup_nginx_proxy()
        else:
            self.log("ℹ️ Nginx未运行")

        return True

    def setup_nginx_proxy(self) -> bool:
        """设置Nginx反向代理"""
        self.log("🔧 配置Nginx反向代理...")

        nginx_config = """
server {
    listen 80;
    server_name 146.190.52.84;

    # VibePilot主服务
    location / {
        proxy_pass http://localhost:9999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://localhost:9999/health;
    }

    # API端点
    location /chat {
        proxy_pass http://localhost:9999/chat;
        proxy_set_header Content-Type application/json;
    }
}

server {
    listen 8001;
    server_name 146.190.52.84;

    location / {
        proxy_pass http://localhost:9999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
"""

        try:
            with open('/etc/nginx/sites-available/vibepilot', 'w') as f:
                f.write(nginx_config)

            # 启用配置
            os.system('ln -sf /etc/nginx/sites-available/vibepilot /etc/nginx/sites-enabled/')
            os.system('nginx -t && systemctl reload nginx')

            self.report["fixes_applied"].append("配置Nginx反向代理到VibePilot服务")
            self.log("✅ Nginx反向代理配置完成")
            return True

        except Exception as e:
            self.log(f"❌ Nginx配置失败: {e}", "ERROR")
            return False

    def check_port_conflicts(self) -> bool:
        """检查端口冲突"""
        self.log("🔍 检查端口占用情况...")

        target_ports = [80, 443, 8001, 9999, 3000]
        conflicts = []

        for port in target_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()

                if result == 0:
                    # 查找占用进程
                    success, output = self.run_command(f"lsof -i :{port}")
                    if success and output:
                        process = output.split('\n')[1] if len(output.split('\n')) > 1 else "未知"
                        conflicts.append(f"端口{port}: {process}")

            except Exception:
                continue

        if conflicts:
            self.log("⚠️ 发现端口冲突:")
            for conflict in conflicts:
                self.log(f"  - {conflict}")
            self.report["issues_found"].extend(conflicts)

        return len(conflicts) == 0

    def kill_conflicting_processes(self) -> bool:
        """终止冲突的进程"""
        self.log("🔧 清理冲突的后台进程...")

        # 终止多余的Python进程（保留9999端口的）
        success, output = self.run_command("pgrep -f 'port=8001\\|port=3000\\|port=80\\|simple_ai_butler\\|api_server'")
        if success and output:
            pids = output.split('\n')
            for pid in pids:
                if pid.strip():
                    os.system(f"kill -9 {pid}")
                    self.log(f"🔹 终止进程 PID {pid}")

        self.report["fixes_applied"].append("清理冲突的Python后台进程")
        return True

    def optimize_system_settings(self) -> bool:
        """优化系统网络设置"""
        self.log("🔧 优化系统网络设置...")

        # 优化TCP设置
        tcp_optimizations = [
            "echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf",
            "echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf",
            "echo 'net.ipv4.tcp_rmem = 4096 87380 134217728' >> /etc/sysctl.conf",
            "echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' >> /etc/sysctl.conf",
            "echo 'net.ipv4.tcp_congestion_control = bbr' >> /etc/sysctl.conf",
            "sysctl -p"
        ]

        for cmd in tcp_optimizations:
            os.system(cmd)

        self.report["fixes_applied"].append("应用TCP性能优化设置")
        return True

    def test_connectivity(self) -> Dict:
        """测试连接性"""
        self.log("🔍 测试服务连接性...")

        results = {}
        test_urls = [
            ("本地9999端口", "http://localhost:9999"),
            ("本地健康检查", "http://localhost:9999/health"),
            ("外网80端口", "http://146.190.52.84"),
            ("外网9999端口", "http://146.190.52.84:9999")
        ]

        for name, url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                results[name] = {
                    "status": "✅ 成功",
                    "code": response.status_code,
                    "time": f"{response.elapsed.total_seconds():.2f}s"
                }
                self.log(f"✅ {name}: HTTP {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
            except Exception as e:
                results[name] = {
                    "status": "❌ 失败",
                    "error": str(e)
                }
                self.log(f"❌ {name}: {e}", "ERROR")

        return results

    def create_startup_script(self) -> bool:
        """创建服务启动脚本"""
        self.log("🔧 创建VibePilot启动脚本...")

        startup_script = """#!/bin/bash
# VibePilot V2 服务启动脚本

cd /home/xx/dev/VibePilot_Kit_v2

# 检查并终止旧进程
pkill -f "uvicorn.*port=9999" 2>/dev/null

# 等待端口释放
sleep 2

# 启动VibePilot服务
nohup python3 -c "
from features.ai_butler.api import AIButlerAPI
import uvicorn
import signal
import sys

def signal_handler(sig, frame):
    print('VibePilot正在关闭...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

api = AIButlerAPI()
print('🚁 VibePilot V2 启动中...')
print('本地访问: http://localhost:9999')
print('外网访问: http://146.190.52.84:9999')
print('SSH隧道: ssh -L 9999:localhost:9999 root@146.190.52.84')

uvicorn.run(api.app, host='0.0.0.0', port=9999, log_level='warning')
" > /var/log/vibepilot.log 2>&1 &

echo "VibePilot V2 已启动在后台"
echo "日志文件: /var/log/vibepilot.log"
echo "访问地址: http://146.190.52.84:9999"
"""

        try:
            with open('/usr/local/bin/start_vibepilot.sh', 'w') as f:
                f.write(startup_script)
            os.chmod('/usr/local/bin/start_vibepilot.sh', 0o755)

            self.report["fixes_applied"].append("创建VibePilot启动脚本")
            self.log("✅ 启动脚本已创建: /usr/local/bin/start_vibepilot.sh")
            return True

        except Exception as e:
            self.log(f"❌ 创建启动脚本失败: {e}", "ERROR")
            return False

    def generate_client_config(self) -> bool:
        """生成客户端连接配置"""
        self.log("📝 生成客户端连接指南...")

        client_guide = """
# VibePilot V2 客户端连接指南

## 方法1: SSH隧道 (推荐)
```bash
# 建立SSH隧道
ssh -L 9999:localhost:9999 root@146.190.52.84

# 在新终端访问
open http://localhost:9999
```

## 方法2: 直接访问 (如果网络允许)
```
http://146.190.52.84:9999
```

## 方法3: 通过Nginx代理 (端口80)
```
http://146.190.52.84
```

## 故障排除
1. 如果连接失败，尝试重启VibePilot:
   ```bash
   /usr/local/bin/start_vibepilot.sh
   ```

2. 检查服务状态:
   ```bash
   curl http://localhost:9999/health
   ```

3. 查看日志:
   ```bash
   tail -f /var/log/vibepilot.log
   ```

## 网络诊断
如果仍有问题，运行网络诊断:
```bash
python3 /home/xx/dev/VibePilot_Kit_v2/network_fixer.py --diagnose
```
"""

        try:
            with open('/home/xx/dev/VibePilot_Kit_v2/CLIENT_GUIDE.md', 'w') as f:
                f.write(client_guide)

            self.log("✅ 客户端连接指南已生成")
            return True

        except Exception as e:
            self.log(f"❌ 生成客户端指南失败: {e}", "ERROR")
            return False

    def run_comprehensive_fix(self) -> Dict:
        """运行完整的修复流程"""
        self.log("🚀 开始VPS网络连接综合修复...")
        self.log("="*60)

        # 1. 清理冲突进程
        self.kill_conflicting_processes()
        time.sleep(3)

        # 2. 检查端口冲突
        self.check_port_conflicts()

        # 3. 配置Nginx反向代理
        self.check_nginx_config()

        # 4. 系统优化
        self.optimize_system_settings()

        # 5. 创建启动脚本
        self.create_startup_script()

        # 6. 生成客户端指南
        self.generate_client_config()

        # 7. 启动VibePilot服务
        self.log("🚀 重新启动VibePilot服务...")
        os.system('/usr/local/bin/start_vibepilot.sh')
        time.sleep(5)

        # 8. 测试连接
        connectivity_results = self.test_connectivity()

        # 9. 生成报告
        self.report["connectivity_test"] = connectivity_results
        self.report["recommendations"] = [
            "使用SSH隧道连接以获得最佳稳定性",
            "如果直连有问题，考虑配置WireGuard VPN",
            "监控服务日志: tail -f /var/log/vibepilot.log",
            "定期运行网络诊断工具检查状态"
        ]

        return self.report

    def diagnose_only(self) -> Dict:
        """仅运行诊断，不修复"""
        self.log("🔍 运行网络连接诊断...")

        # 基本诊断
        self.check_port_conflicts()
        connectivity_results = self.test_connectivity()

        self.report["connectivity_test"] = connectivity_results
        return self.report

def main():
    fixer = NetworkFixer()

    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        report = fixer.diagnose_only()
    else:
        report = fixer.run_comprehensive_fix()

    # 输出最终报告
    print("\n" + "="*60)
    print("📊 网络修复报告")
    print("="*60)

    if report["issues_found"]:
        print("\n🔍 发现的问题:")
        for issue in report["issues_found"]:
            print(f"  - {issue}")

    if report["fixes_applied"]:
        print("\n🔧 应用的修复:")
        for fix in report["fixes_applied"]:
            print(f"  ✅ {fix}")

    if "connectivity_test" in report:
        print("\n🌐 连接测试结果:")
        for test, result in report["connectivity_test"].items():
            status = result["status"]
            if "成功" in status:
                extra = f"HTTP {result['code']} ({result['time']})"
            else:
                extra = result.get("error", "")
            print(f"  {status} {test}: {extra}")

    print("\n💡 建议:")
    for rec in report["recommendations"]:
        print(f"  - {rec}")

    # 保存报告
    with open(f'/tmp/network_fix_report_{int(time.time())}.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📝 详细报告已保存到: /tmp/network_fix_report_{int(time.time())}.json")
    print("\n🎉 网络修复完成!")

if __name__ == "__main__":
    main()