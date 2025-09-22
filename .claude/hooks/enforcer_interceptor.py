#!/usr/bin/env python3
"""
Claude Enhancer Enforcer Interceptor - Claude Code执行拦截器

这个拦截器在Claude Code实际执行任何工具之前运行，
能够真正阻止不符合Claude Enhancer规则的执行，并强制重定向到正确的方案。
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add enforcer to path
sys.path.insert(0, "/home/xx/dev/Claude Enhancer/core/enforcer")
from agent_enforcer import AgentEnforcer, EnforcementMode

# Configure logging
logging.basicConfig(
    level=os.getenv("CLAUDE_ENHANCER_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/claude_enhancer_interceptor.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("claude_enhancer.interceptor")


class ClaudeCodeInterceptor:
    """Claude Code执行拦截器"""

    def __init__(self):
        self.enforcer = AgentEnforcer()
        self.intercept_count = 0
        self.last_result = None

    def intercept_pre_tool_use(self, tool_name: str, tool_input: str) -> Dict[str, Any]:
        """在工具使用前拦截"""
        self.intercept_count += 1

        # 只拦截Task工具调用（Agent执行）
        if tool_name != "Task":
            return {"action": "continue", "status": "passed"}

        logger.info(f"Intercepting Task tool use (attempt #{self.intercept_count})")

        try:
            # 使用强制器检查
            result = self.enforcer.enforce(tool_input)
            self.last_result = result

            if result["status"] == "approved":
                logger.info("✅ Task execution approved")
                return {"action": "continue", "status": "approved", "result": result}

            elif result["status"] == "blocked":
                logger.warning(f"❌ Task execution blocked: {result['message']}")
                return {
                    "action": "block",
                    "status": "blocked",
                    "message": result["message"],
                    "result": result,
                    "exit_with_error": True,
                }

            elif result["status"] == "redirected":
                logger.info(f"🔄 Task execution redirected: {result['message']}")
                return {
                    "action": "redirect",
                    "status": "redirected",
                    "message": result["message"],
                    "new_execution": result["corrected_plan"],
                    "instructions": result["instructions"],
                    "result": result,
                }

            elif result["status"] == "guide":
                logger.info(f"💡 Task execution needs guidance: {result['message']}")
                return {
                    "action": "guide",
                    "status": "guide",
                    "message": result["message"],
                    "guidance": result["guidance"],
                    "template": result["template"],
                    "result": result,
                }

            elif result["status"] == "overridden":
                logger.info(f"🔧 Task execution overridden: {result['message']}")
                return {
                    "action": "override",
                    "status": "overridden",
                    "message": result["message"],
                    "new_execution": result["new_execution"],
                    "auto_execute": result["auto_execute"],
                    "result": result,
                }

        except Exception as e:
            logger.error(f"Error in interceptor: {e}")
            return {"action": "error", "status": "error", "error": str(e)}

        return {"action": "continue", "status": "unknown"}

    def generate_enforcement_message(self, intercept_result: Dict[str, Any]) -> str:
        """生成强制执行消息"""
        if intercept_result["status"] == "blocked":
            return f"""
🚨 Claude Enhancer 强制阻止执行

{intercept_result['message']}

请修正您的方案以符合Claude Enhancer规则：
- 使用至少3个Agent
- 采用并行执行模式
- 使用正确的Agent组合

修正后请重新提交。
"""

        elif intercept_result["status"] == "redirected":
            return f"""
🔄 Claude Enhancer 自动重定向执行

{intercept_result['message']}

已自动修正您的执行方案：

{intercept_result['instructions']}

Claude Enhancer将自动使用修正后的方案执行。
"""

        elif intercept_result["status"] == "guide":
            return f"""
💡 Claude Enhancer 执行指导

{intercept_result['message']}

{intercept_result['guidance']}

请按照指导修正您的方案。
"""

        elif intercept_result["status"] == "overridden":
            return f"""
🔧 Claude Enhancer 自动重写执行

{intercept_result['message']}

已自动重写您的执行方案，将立即执行修正后的版本。
"""

        return f"Claude Enhancer 处理结果: {intercept_result.get('message', '未知状态')}"

    def should_continue_execution(self, intercept_result: Dict[str, Any]) -> bool:
        """判断是否应该继续执行"""
        return intercept_result.get("action") in ["continue", "override"]

    def get_modified_execution(self, intercept_result: Dict[str, Any]) -> Optional[str]:
        """获取修改后的执行计划"""
        if intercept_result.get("status") in ["redirected", "overridden"]:
            return intercept_result.get("new_execution")
        return None


def main():
    """主入口点"""
    # 从环境变量获取工具信息
    tool_name = os.getenv("CLAUDE_TOOL", "Unknown")
    event_type = os.getenv("CLAUDE_EVENT", "Unknown")

    # 读取输入
    if not sys.stdin.isatty():
        tool_input = sys.stdin.read()
    else:
        tool_input = ""

    interceptor = ClaudeCodeInterceptor()

    # 根据事件类型处理
    if event_type == "PreToolUse":
        result = interceptor.intercept_pre_tool_use(tool_name, tool_input)

        # 输出拦截结果
    # print(json.dumps(result, indent=2, ensure_ascii=False))

        # 如果需要阻止执行，返回非零退出码
        if result.get("exit_with_error", False):
            sys.exit(1)

        # 如果需要重定向，输出新的执行计划
        if result.get("action") == "redirect":
            message = interceptor.generate_enforcement_message(result)
    # print("\n" + "=" * 60)
    # print(message)
    # print("=" * 60)

            # 输出修正后的执行计划到特殊文件，供Claude Code读取
            modified_execution = interceptor.get_modified_execution(result)
            if modified_execution:
                with open("/tmp/claude_enhancer_modified_execution.txt", "w") as f:
                    f.write(modified_execution)
    # print(f"\n修正后的执行计划已保存到: /tmp/claude_enhancer_modified_execution.txt")

    elif event_type == "PostToolUse":
        # 后置处理
    # print(f"Claude Enhancer Post-tool processing for {tool_name}")

    else:
        # 其他事件
    # print(f"Claude Enhancer 处理事件: {event_type}")


if __name__ == "__main__":
    main()
