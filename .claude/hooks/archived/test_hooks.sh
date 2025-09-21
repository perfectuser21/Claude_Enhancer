#!/bin/bash
# 测试Claude Enhancer Hooks

echo "测试1: Agent数量不足（应该被阻止）"
echo '{"subagent_type": "backend-architect", "prompt": "设计登录系统"}' | bash claude_enhancer_agent_validator.sh

echo ""
echo "测试2: 正确的Agent组合"
echo '{"function_calls": [
  {"subagent_type": "backend-architect", "prompt": "设计登录系统"},
  {"subagent_type": "security-auditor", "prompt": "审查安全"},
  {"subagent_type": "test-engineer", "prompt": "编写测试"}
]}' | bash claude_enhancer_master.sh
