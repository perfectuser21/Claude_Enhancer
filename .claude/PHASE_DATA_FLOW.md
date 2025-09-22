# 📊 Phase间数据传递机制

## 问题
各个Phase产生的数据如何传递给后续Phase？

## 解决方案

### 1. TodoWrite作为状态管理器
```python
todos = [
    {
        "content": "Phase 1: 需求分析",
        "status": "completed",
        "activeForm": "分析需求",
        "output": {  # 存储输出数据
            "task_type": "authentication",
            "complexity": "high",
            "required_agents": 5
        }
    }
]

# Phase 3读取Phase 1的输出
task_type = todos[1]["output"]["task_type"]
```

### 2. 临时文件存储
```bash
# Phase 1输出
echo "{\"task_type\": \"authentication\"}" > /tmp/phase1_output.json

# Phase 3读取
TASK_TYPE=$(jq -r '.task_type' /tmp/phase1_output.json)
```

### 3. 直接在代码注释中传递
```python
# Phase 1分析结果：
# - 任务类型：authentication
# - 需要5个Agent
# - 影响文件：auth.py, user.py

# Phase 3使用这些信息
```

## 推荐方式

**使用TodoWrite的output字段**，因为：
- 持久化存储
- 可视化展示
- 易于追踪

## 数据流示例

```
Phase 0 → 输出：branch_name
    ↓
Phase 1 → 输出：task_type, complexity
    ↓
Phase 2 → 输出：architecture_design, api_spec
    ↓
Phase 3 → 输出：implemented_files
    ↓
Phase 4 → 输出：test_results
    ↓
Phase 5 → 输出：commit_hash
    ↓
Phase 6 → 输出：review_feedback
    ↓
Phase 7 → 输出：deployment_status
```