#!/usr/bin/env python3
"""
简化的5阶段执行拦截器
直接生成正确的多Agent并行调用指令
"""

import json
import os
import sys

# 阶段状态文件
STATE_FILE = "/home/xx/dev/Claude Enhancer/.claude_enhancer/current_phase.txt"


def get_current_phase():
    """获取当前阶段"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return int(f.read().strip())
    return 0


def set_current_phase(phase):
    """设置当前阶段"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(str(phase))


def main():
    """主函数"""
    if len(sys.argv) < 2:
        sys.exit(0)

    command = sys.argv[1]

    if command == "check":
        # 检查是否应该进入5阶段
        current_phase = get_current_phase()

        if current_phase == 0:
            # 开始第一阶段
            # print("\n⚨⚨⚨ CLAUDE_ENHANCER 5阶段执行启动 ⚨⚨⚨")
            # print("\n请使用以下3个agents并行执行需求分析：")
            # print("- requirements-analyst")
            # print("- business-analyst")
            # print("- project-manager")
            set_current_phase(1)
            sys.exit(1)  # 返回1表示需要介入

        elif current_phase == 1:
            # 进入第二阶段
            # print("\n✅ 阶段1完成！")
            # print("\n📊 阶段2/5: 架构设计")
            # print("请使用以下4个agents并行执行：")
            # print("- api-designer")
            # print("- backend-architect")
            # print("- database-specialist")
            # print("- frontend-specialist")
            set_current_phase(2)
            sys.exit(1)

        elif current_phase == 2:
            # 进入第三阶段
            # print("\n✅ 阶段2完成！")
            # print("\n💻 阶段3/5: 实现开发")
            # print("请使用以下5个agents并行执行：")
            # print("- fullstack-engineer")
            # print("- backend-architect")
            # print("- frontend-specialist")
            # print("- database-specialist")
            # print("- test-engineer")
            set_current_phase(3)
            sys.exit(1)

        elif current_phase == 3:
            # 进入第四阶段
            # print("\n✅ 阶段3完成！")
            # print("\n🧪 阶段4/5: 测试验证")
            # print("请使用以下4个agents并行执行：")
            # print("- test-engineer")
            # print("- e2e-test-specialist")
            # print("- performance-tester")
            # print("- security-auditor")
            set_current_phase(4)
            sys.exit(1)

        elif current_phase == 4:
            # 进入第五阶段
            # print("\n✅ 阶段4完成！")
            # print("\n🚀 阶段5/5: 部署上线")
            # print("请使用以下3个agents顺序执行：")
            # print("- devops-engineer")
            # print("- monitoring-specialist")
            # print("- technical-writer")
            set_current_phase(5)
            sys.exit(1)

        elif current_phase == 5:
            # 所有阶段完成
            # print("\n🎉 所有5个阶段完成！")
            set_current_phase(0)  # 重置
            sys.exit(0)

    elif command == "reset":
        # 重置阶段
        set_current_phase(0)
        # print("阶段已重置")
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
