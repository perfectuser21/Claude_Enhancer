#!/bin/bash
# Perfect21 Hook安装脚本 - 强制Claude Code遵守规则

echo "================================================"
echo "Perfect21 Hook强制系统安装器"
echo "================================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
fi

# 安装目录
PERFECT21_DIR="/home/xx/dev/Perfect21"
HOOKS_DIR="$PERFECT21_DIR/hooks"
CLAUDE_DIR="/root/.claude"

# 创建必要目录
mkdir -p "$PERFECT21_DIR/.perfect21"
mkdir -p "$CLAUDE_DIR/hooks"

# 安装依赖
echo "📦 安装必要依赖..."
pip3 install rich pyyaml &> /dev/null

# 创建Hook配置
echo "🔧 配置Perfect21 Hook..."

cat > "$CLAUDE_DIR/hooks/pre-execution-hook.py" << 'EOF'
#!/usr/bin/env python3
"""
Claude Code执行前Hook - 强制Perfect21规则检查
"""
import sys
import subprocess
import json

def check_perfect21_rules(command):
    """调用Perfect21验证器检查规则"""
    try:
        result = subprocess.run(
            ["python3", "/home/xx/dev/Perfect21/hooks/perfect21_enforcer.py"],
            input=command,
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            # 违规，阻止执行
            print(result.stdout)
            print("\n🚫 执行被Perfect21规则阻止")
            print("📝 请按照上述要求修正后重试")
            return False
        else:
            # 合规，允许执行
            print(result.stdout)
            return True
    except Exception as e:
        print(f"⚠️ Perfect21检查失败: {e}")
        return True  # 检查失败时允许执行，避免阻塞

# 获取命令
if len(sys.argv) > 1:
    command = " ".join(sys.argv[1:])
else:
    command = sys.stdin.read()

# 检查规则
if not check_perfect21_rules(command):
    sys.exit(1)

sys.exit(0)
EOF

chmod +x "$CLAUDE_DIR/hooks/pre-execution-hook.py"

# 创建快捷命令
echo "🔨 创建快捷命令..."

cat > /usr/local/bin/p21-monitor << 'EOF'
#!/bin/bash
python3 /home/xx/dev/Perfect21/hooks/monitor.py $@
EOF
chmod +x /usr/local/bin/p21-monitor

cat > /usr/local/bin/p21-check << 'EOF'
#!/bin/bash
echo "$@" | python3 /home/xx/dev/Perfect21/hooks/perfect21_enforcer.py
EOF
chmod +x /usr/local/bin/p21-check

cat > /usr/local/bin/p21-stats << 'EOF'
#!/bin/bash
python3 /home/xx/dev/Perfect21/hooks/monitor.py stats
EOF
chmod +x /usr/local/bin/p21-stats

# 创建配置文件
echo "📄 创建配置文件..."

cat > "$PERFECT21_DIR/.perfect21/config.yaml" << 'EOF'
# Perfect21 Hook配置
version: "1.0"

enforcement:
  enabled: true
  strict_mode: true  # 严格模式：必须满足所有规则
  min_agents: 3      # 最少Agent数量
  parallel_required: true  # 必须并行执行

monitoring:
  enabled: true
  log_violations: true
  alert_threshold: 80  # 合规率低于此值时告警

rules:
  check_agent_count: true
  check_parallel: true
  check_git_hooks: true
  check_testing: true
EOF

# 显示安装结果
echo ""
echo "✅ Perfect21 Hook系统安装完成！"
echo ""
echo "可用命令:"
echo "  p21-monitor      - 启动监控面板"
echo "  p21-monitor live - 实时监控"
echo "  p21-monitor report - 生成报告"
echo "  p21-stats        - 查看统计"
echo "  p21-check '命令' - 手动检查命令合规性"
echo ""
echo "📊 测试安装:"
python3 "$HOOKS_DIR/perfect21_enforcer.py" << 'TEST'
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">test-agent</parameter>
  </invoke>
</function_calls>
TEST

echo ""
echo "⚠️ 重要提醒:"
echo "1. Hook已配置，将自动验证Claude Code的执行"
echo "2. 违规操作将被阻止，必须修正后才能继续"
echo "3. 使用 p21-monitor 查看合规情况"
echo ""
echo "🎯 下一步:"
echo "1. 运行 p21-monitor 查看监控面板"
echo "2. 让Claude Code执行任务，观察Hook效果"
echo "3. 查看 /home/xx/dev/Perfect21/.perfect21/violations.log 了解违规详情"