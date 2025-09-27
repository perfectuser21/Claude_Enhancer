#!/usr/bin/env python3
"""统一为6-Phase系统"""

import json
import os

print("=== 统一为6-Phase系统 ===")
print("")

# 1. 修改settings.json
settings_file = ".claude/settings.json"
with open(settings_file, "r", encoding="utf-8") as f:
    settings = json.load(f)

# 修改描述
settings["description"] = "自检优化系统，智能错误恢复和性能监控，支持6-Phase开发生命周期"

# 删除P0和P7
if "workflow_phases" in settings["hooks"]:
    phases = settings["hooks"]["workflow_phases"]
    # 删除P0和P7
    if "P0_branch_creation" in phases:
        del phases["P0_branch_creation"]
    if "P7_deployment" in phases:
        del phases["P7_deployment"]

# 删除workflow_config中的P0和P7
if "workflow_config" in settings:
    if "phases" in settings["workflow_config"]:
        phases_config = settings["workflow_config"]["phases"]
        if "P0" in phases_config:
            del phases_config["P0"]
        if "P7" in phases_config:
            del phases_config["P7"]

# 保存
with open(settings_file, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print("✅ settings.json已更新为6-Phase")

# 2. 更新WORKFLOW.md
workflow_file = ".claude/WORKFLOW.md"
if os.path.exists(workflow_file):
    with open(workflow_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换标题
    content = content.replace("8-Phase工作流框架", "6-Phase工作流框架")
    content = content.replace("完整的8个阶段", "完整的6个阶段")

    with open(workflow_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ WORKFLOW.md已更新为6-Phase")

# 3. 确保当前Phase合法
phase_file = ".phase/current"
with open(phase_file, "r") as f:
    current = f.read().strip()

if current not in ["P1", "P2", "P3", "P4", "P5", "P6"]:
    with open(phase_file, "w") as f:
        f.write("P1")
    print("✅ 当前Phase重置为P1")
else:
    print(f"✅ 当前Phase: {current}")

print("")
print("=== 6-Phase系统统一完成 ===")
print("P1: Requirements Analysis")
print("P2: Design Planning")
print("P3: Implementation")
print("P4: Local Testing")
print("P5: Code Commit")
print("P6: Code Review")
