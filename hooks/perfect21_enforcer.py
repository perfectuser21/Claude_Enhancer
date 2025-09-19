#!/usr/bin/env python3
"""
Perfect21 Hook执行器 - 强制Claude Code遵守规则
这个Hook会验证Claude Code的行为并阻止违规操作

集成Rule Guardian实现实时监督
"""

import json
import re
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from features.guardian.rule_guardian import get_rule_guardian
    GUARDIAN_AVAILABLE = True
except ImportError:
    GUARDIAN_AVAILABLE = False

class Perfect21Enforcer:
    """Perfect21规则执行器"""

    def __init__(self):
        self.violations_log = Path("/home/xx/dev/Perfect21/.perfect21/violations.log")
        self.violations_log.parent.mkdir(exist_ok=True)

        # 集成Rule Guardian
        self.guardian = get_rule_guardian() if GUARDIAN_AVAILABLE else None

        # 任务类型到Agent组合的映射
        self.task_patterns = {
            "authentication": {
                "keywords": ["登录", "认证", "auth", "用户", "权限", "JWT", "session", "login"],
                "required_agents": ["backend-architect", "security-auditor", "test-engineer",
                                   "api-designer", "database-specialist"],
                "min_agents": 5
            },
            "api_development": {
                "keywords": ["API", "接口", "REST", "GraphQL", "endpoint"],
                "required_agents": ["api-designer", "backend-architect", "test-engineer",
                                   "technical-writer"],
                "min_agents": 4
            },
            "database": {
                "keywords": ["数据库", "database", "schema", "SQL", "MongoDB", "Redis"],
                "required_agents": ["database-specialist", "backend-architect",
                                   "performance-engineer"],
                "min_agents": 3
            },
            "frontend": {
                "keywords": ["前端", "界面", "UI", "React", "Vue", "页面", "组件"],
                "required_agents": ["frontend-specialist", "ux-designer", "test-engineer"],
                "min_agents": 3
            },
            "performance": {
                "keywords": ["性能", "优化", "performance", "速度", "缓存"],
                "required_agents": ["performance-engineer", "backend-architect",
                                   "database-specialist"],
                "min_agents": 3
            },
            "testing": {
                "keywords": ["测试", "test", "TDD", "单元测试", "e2e"],
                "required_agents": ["test-engineer", "e2e-test-specialist", "performance-tester"],
                "min_agents": 3
            },
            "security": {
                "keywords": ["安全", "security", "加密", "漏洞", "OWASP"],
                "required_agents": ["security-auditor", "backend-architect", "devops-engineer"],
                "min_agents": 3
            },
            "deployment": {
                "keywords": ["部署", "deploy", "CI/CD", "Docker", "Kubernetes"],
                "required_agents": ["devops-engineer", "deployment-manager", "monitoring-specialist"],
                "min_agents": 3
            }
        }

        # 默认最少Agent数量
        self.DEFAULT_MIN_AGENTS = 3

    def identify_task_type(self, command: str) -> Optional[str]:
        """识别任务类型"""
        command_lower = command.lower()

        for task_type, config in self.task_patterns.items():
            for keyword in config["keywords"]:
                if keyword.lower() in command_lower:
                    return task_type

        return None

    def extract_agents(self, command: str) -> List[str]:
        """从命令中提取Agent列表"""
        agents = []

        # 查找所有的subagent_type参数
        pattern = r'<parameter\s+name="subagent_type">([^<]+)</parameter>'
        matches = re.findall(pattern, command)
        agents.extend(matches)

        # 备用模式：查找Task调用
        if not agents:
            pattern = r'subagent_type["\']:\s*["\']([^"\']+)["\']'
            matches = re.findall(pattern, command)
            agents.extend(matches)

        return agents

    def check_parallel_execution(self, command: str) -> bool:
        """检查是否是并行执行（在同一个function_calls块中）"""
        # 检查是否有function_calls标签
        if "<function_calls>" not in command:
            return False

        # 计算function_calls块的数量
        calls_count = command.count("<function_calls>")

        # 计算invoke的数量
        invoke_count = command.count("<invoke")

        # 如果只有一个function_calls块但有多个invoke，说明是并行
        if calls_count == 1 and invoke_count > 1:
            return True

        return False

    def validate_command(self, command: str, context: str = "") -> Tuple[bool, str]:
        """
        验证命令是否符合Perfect21规则

        返回: (是否通过, 错误消息)
        """
        # 如果不是Task相关命令，直接通过
        if "Task" not in command and "subagent" not in command.lower():
            return True, ""

        # 1. 提取Agent列表
        agents = self.extract_agents(command)
        agent_count = len(agents)

        # 2. 识别任务类型
        task_context = command + " " + context
        task_type = self.identify_task_type(task_context)

        # 3. 检查Agent数量
        if task_type:
            config = self.task_patterns[task_type]
            min_agents = config["min_agents"]
            required_agents = config["required_agents"]

            if agent_count < min_agents:
                return False, (
                    f"❌ Perfect21规则违规：{task_type}任务需要至少{min_agents}个Agent，"
                    f"你只使用了{agent_count}个。\n"
                    f"必须使用的Agent组合：{', '.join(required_agents)}\n"
                    f"请修正后重试！"
                )

            # 检查是否包含必要的Agent
            missing_agents = []
            for required in required_agents[:min_agents]:  # 至少要前几个核心Agent
                if required not in agents:
                    missing_agents.append(required)

            if missing_agents:
                return False, (
                    f"❌ Perfect21规则违规：{task_type}任务缺少必要的Agent。\n"
                    f"缺少的Agent：{', '.join(missing_agents)}\n"
                    f"当前Agent：{', '.join(agents)}\n"
                    f"请添加缺失的Agent后重试！"
                )
        else:
            # 没有识别出具体任务类型，使用默认规则
            if agent_count < self.DEFAULT_MIN_AGENTS:
                return False, (
                    f"❌ Perfect21规则违规：任何非trivial任务需要至少{self.DEFAULT_MIN_AGENTS}个Agent，"
                    f"你只使用了{agent_count}个。\n"
                    f"请增加Agent数量后重试！"
                )

        # 4. 检查是否并行执行
        if agent_count > 1 and not self.check_parallel_execution(command):
            return False, (
                "❌ Perfect21规则违规：多个Agent必须在同一个<function_calls>块中并行执行。\n"
                "请将所有Agent调用放在同一个消息中！"
            )

        # 5. 记录成功执行
        self.log_validation(True, task_type, agent_count, agents)

        return True, f"✅ Perfect21验证通过：使用{agent_count}个Agent并行执行"

    def log_validation(self, passed: bool, task_type: Optional[str],
                       agent_count: int, agents: List[str]):
        """记录验证结果"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "passed": passed,
            "task_type": task_type or "unknown",
            "agent_count": agent_count,
            "agents": agents
        }

        with open(self.violations_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def log_violation(self, error_msg: str):
        """记录违规行为"""
        violation = {
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "error": error_msg
        }

        with open(self.violations_log, "a") as f:
            f.write(json.dumps(violation) + "\n")

    def get_violation_stats(self) -> Dict:
        """获取违规统计"""
        if not self.violations_log.exists():
            return {"total": 0, "violations": 0, "compliance_rate": 100}

        total = 0
        violations = 0

        with open(self.violations_log, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    total += 1
                    if not entry.get("passed", True):
                        violations += 1
                except:
                    continue

        compliance_rate = ((total - violations) / total * 100) if total > 0 else 100

        return {
            "total": total,
            "violations": violations,
            "compliance_rate": round(compliance_rate, 2)
        }

def main():
    """Hook主函数"""
    # 获取命令行参数或标准输入
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        command = sys.stdin.read()

    # 创建执行器
    enforcer = Perfect21Enforcer()

    # 验证命令
    passed, message = enforcer.validate_command(command)

    # 输出结果
    print(message)

    # 如果验证失败，返回非零退出码阻止执行
    if not passed:
        enforcer.log_violation(message)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()