# Dashboard v2 Data Completion - Technical Discovery

**版本**: v7.2.1
**分支**: feature/dashboard-v2-data-completion
**创建日期**: 2025-10-23
**Phase**: 1.3 - Technical Discovery

---

## 🎯 任务概述

**目标**: 完善Dashboard v2的数据解析能力，填充capabilities和decisions数组，实现完整的CE能力展示和学习系统展示。

**现状**:
- ✅ Dashboard基础框架完成（dashboard.py 674行）
- ✅ API端点正常工作（/api/health, /api/capabilities, /api/learning, /api/projects）
- ✅ Features解析完成（12个features: F001-F012）
- ❌ Capabilities数组为空（需要解析CAPABILITY_MATRIX.md）
- ❌ Decisions数组为空（需要解析.claude/DECISIONS.md）
- ⚠️ Feature-Checkpoint映射缺失（related_checkpoints为空）

---

## 📊 数据源分析

### 1. CAPABILITY_MATRIX.md 分析

**文件位置**: `docs/CAPABILITY_MATRIX.md`

**格式特征**:
```markdown
## 🔍 能力详细矩阵

### C0: 强制新分支
**能力描述**: 禁止直接提交到 main/master 分支...

| 验证维度 | 详细信息 |
|---------|---------|
| **本地验证** | `pre-commit` hook L135-141 |
| **CI验证** | `.github/workflows/ce-gates.yml` Layer 1 (L27-51) |
| **验证逻辑** | ```bash ... ``` |
| **失败表现** | 本地: `❌ ERROR: ...` |
| **修复动作** | 1. 创建 feature 分支... |
| **测试脚本** | `test/test_phase_gates.sh` |
| **绕过风险** | ⚠️ 使用 `--no-verify` 可绕过... |
```

**解析策略**:
1. 使用正则提取每个能力块（C0-C9）
2. 模式: `^### (C\d+): (.+)$` - 匹配能力ID和名称
3. 提取 "能力描述" 后的文本
4. 解析表格中的验证维度（本地验证、CI验证、失败表现、修复动作）
5. 提取绕过风险信息

**数据结构**（目标）:
```python
{
    "id": "C0",
    "name": "强制新分支",
    "type": "基础防护",
    "level": "Critical",
    "description": "禁止直接提交到 main/master 分支...",
    "local_verification": "pre-commit hook L135-141",
    "ci_verification": ".github/workflows/ce-gates.yml Layer 1",
    "failure_pattern": "❌ ERROR: 禁止直接提交到...",
    "fix_action": "1. 创建 feature 分支...",
    "bypass_risk": "使用 --no-verify 可绕过..."
}
```

---

### 2. DECISIONS.md 分析

**文件位置**: `.claude/DECISIONS.md`

**格式特征**:
```markdown
### 2025-10-13: 系统定位明确
**决策**: 这是专业级个人工具，不是企业级系统
**原因**:
- 用户是编程小白，个人使用
- 不涉及团队协作
- 避免过度设计和复杂化

**禁止操作**：
- ❌ 添加团队协作功能
- ❌ 添加多用户权限管理

**允许操作**：
- ✅ 使用"专业级"、"个人工具"术语
- ✅ 优化单用户体验

**影响范围**: 所有文档、代码注释、配置文件
```

**解析策略**:
1. 使用正则匹配每个决策条目：`^### (\d{4}-\d{2}-\d{2}): (.+)$`
2. 提取决策内容（"**决策**:" 后的文本）
3. 提取原因列表（"**原因**:" 下的 bullet points）
4. 提取禁止操作列表（"**禁止操作**:" 下的 ❌ 项）
5. 提取允许操作列表（"**允许操作**:" 下的 ✅ 项）
6. 提取影响范围（"**影响范围**:" 后的文本）

**数据结构**（目标）:
```python
{
    "date": "2025-10-13",
    "title": "系统定位明确",
    "decision": "这是专业级个人工具，不是企业级系统",
    "reasons": [
        "用户是编程小白，个人使用",
        "不涉及团队协作",
        ...
    ],
    "forbidden_actions": [
        "添加团队协作功能",
        "添加多用户权限管理",
        ...
    ],
    "allowed_actions": [
        "使用'专业级'、'个人工具'术语",
        "优化单用户体验",
        ...
    ],
    "affected_scope": "所有文档、代码注释、配置文件"
}
```

---

### 3. CHECKS_INDEX.json 分析

**文件位置**: `docs/CHECKS_INDEX.json`

**格式特征**:
```json
{
  "version": "6.6.0",
  "total_min": 97,
  "by_phase": {
    "P1": 33,
    "P2": 15,
    "P3": 15,
    "P4": 10,
    "P5": 15,
    "P6": 5,
    "P7": 4
  },
  "ids": [
    "PD_S001",
    "PD_S002",
    ...
  ]
}
```

**使用目的**:
- 提供97个checkpoints的完整列表
- 用于建立Feature-Checkpoint映射关系
- 显示每个Phase的checkpoint数量统计

**解析策略**:
1. 直接JSON解析
2. 提取 `ids` 数组获取所有checkpoint ID
3. 使用 `by_phase` 统计显示Phase分布

---

## 🔧 技术实现方案

### 方案1: 扩展parsers.py（推荐）

**优点**:
- ✅ 符合现有架构
- ✅ 复用cache系统
- ✅ 保持代码一致性

**实现步骤**:
1. 在 `parsers.py` 添加 `CapabilityMatrixParser` 类
2. 在 `parsers.py` 添加 `DecisionParser` 类
3. 添加正则表达式匹配逻辑
4. 集成到 `dashboard.py` 的 `/api/capabilities` 和 `/api/learning` 端点

**代码结构**:
```python
class CapabilityMatrixParser:
    def __init__(self, project_root: Path):
        self.matrix_file = project_root / "docs" / "CAPABILITY_MATRIX.md"

    def parse_capabilities(self) -> List[Capability]:
        """解析C0-C9能力"""
        capabilities = []
        content = self.matrix_file.read_text()

        # 正则匹配: ### C0: 强制新分支
        pattern = r'### (C\d+): (.+?)\n'
        matches = re.finditer(pattern, content)

        for match in matches:
            cap_id = match.group(1)
            cap_name = match.group(2)
            # 提取详细信息...
            capabilities.append(Capability(...))

        return capabilities

class DecisionParser:
    def __init__(self, project_root: Path):
        self.decisions_file = project_root / ".claude" / "DECISIONS.md"

    def parse_decisions(self) -> List[Decision]:
        """解析历史决策"""
        decisions = []
        content = self.decisions_file.read_text()

        # 正则匹配: ### 2025-10-13: 系统定位明确
        pattern = r'### (\d{4}-\d{2}-\d{2}): (.+?)\n'
        matches = re.finditer(pattern, content)

        for match in matches:
            date = match.group(1)
            title = match.group(2)
            # 提取详细信息...
            decisions.append(Decision(...))

        return decisions
```

---

### 方案2: 创建独立解析模块

**优点**:
- 模块化更好
- 可单独测试

**缺点**:
- ❌ 增加文件数量
- ❌ 与现有架构不一致

**不推荐使用**

---

## 🎨 Feature-Checkpoint映射策略

**目标**: 建立F001-F012与97个checkpoints的关联

**映射逻辑**（基于语义关联）:

```python
FEATURE_CHECKPOINT_MAP = {
    "F001": {  # Branch Protection
        "checkpoints": ["PD_S001", "P1_001", "P4_015"],  # 分支保护相关检查点
        "related_capabilities": ["C0", "C1"]
    },
    "F002": {  # 7-Phase Workflow
        "checkpoints": ["P1_001", "P1_002", ..., "P7_004"],  # 全流程检查点
        "related_capabilities": ["C1", "C2"]
    },
    # ... F003-F012
}
```

**实现方式**:
1. **手动映射**（推荐）- 基于文档分析手动建立精确映射
2. **关键词匹配** - 使用关键词自动推断（容易误判）

**存储位置**: `tools/feature_mapping.py` 或嵌入 `parsers.py`

---

## 📈 性能考虑

**缓存策略**:
- ✅ Capabilities: 60秒TTL（很少变化）
- ✅ Decisions: 60秒TTL（偶尔添加）
- ✅ Feature-Checkpoint映射: 静态数据（无需TTL）

**解析性能**:
- CAPABILITY_MATRIX.md: ~15KB，预计解析时间 <50ms
- DECISIONS.md: ~5KB，预计解析时间 <20ms
- 总API响应时间: <100ms（缓存命中时 <10ms）

**文件监控**:
使用现有的 `mtime` 机制检测文件变化

---

## 🧪 测试策略

**单元测试**（推荐添加）:
```bash
# test/test_dashboard_v2_parsers.py
def test_capability_parser():
    parser = CapabilityMatrixParser(PROJECT_ROOT)
    caps = parser.parse_capabilities()
    assert len(caps) >= 10  # C0-C9
    assert caps[0].id == "C0"
    assert caps[0].level == "Critical"

def test_decision_parser():
    parser = DecisionParser(PROJECT_ROOT)
    decisions = parser.parse_decisions()
    assert len(decisions) > 0
    assert "2025-10-13" in [d.date for d in decisions]
```

**集成测试**:
```bash
# test/test_dashboard_v2.sh
curl http://localhost:7777/api/capabilities | jq '.capabilities | length'
# 预期: >= 10

curl http://localhost:7777/api/learning | jq '.decisions | length'
# 预期: > 0
```

---

## 🚨 风险与挑战

### 风险1: Markdown解析不稳定
**描述**: Markdown格式可能不一致，导致解析失败
**缓解措施**:
- 使用宽松的正则表达式
- 添加错误处理和默认值
- 记录解析失败的行号

### 风险2: 性能问题
**描述**: 每次请求都解析Markdown可能较慢
**缓解措施**:
- ✅ 使用缓存系统（已有）
- ✅ 监控文件mtime，仅在变化时重新解析

### 风险3: Feature-Checkpoint映射不准确
**描述**: 手动映射可能遗漏或错误
**缓解措施**:
- 提供"未映射"的显示选项
- 允许后续迭代更新映射

---

## 📋 数据模型定义

**需要在 `data_models.py` 添加**:

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class Capability:
    """CE能力数据模型"""
    id: str  # C0-C9
    name: str
    type: str  # 基础防护、流程控制等
    level: str  # Critical, High, Medium
    description: str
    local_verification: str
    ci_verification: str
    failure_pattern: str
    fix_action: str
    bypass_risk: Optional[str] = None

@dataclass(frozen=True)
class Decision:
    """历史决策数据模型"""
    date: str  # YYYY-MM-DD
    title: str
    decision: str
    reasons: List[str]
    forbidden_actions: List[str]
    allowed_actions: List[str]
    affected_scope: str
    related_files: Optional[List[str]] = None
```

---

## 📦 交付清单

Phase 2（Implementation）需要完成：

1. **代码修改**:
   - [ ] `tools/data_models.py` - 添加Capability和Decision数据类
   - [ ] `tools/parsers.py` - 添加CapabilityMatrixParser类
   - [ ] `tools/parsers.py` - 添加DecisionParser类
   - [ ] `tools/parsers.py` 或独立文件 - 添加Feature-Checkpoint映射
   - [ ] `tools/dashboard.py` - 集成新解析器到API端点

2. **测试**:
   - [ ] `test/test_dashboard_v2_parsers.py` - 添加单元测试
   - [ ] `test/test_dashboard_v2.sh` - 更新集成测试

3. **文档**:
   - [ ] 更新 `docs/DASHBOARD_GUIDE.md`（如有）

---

## 🔄 与现有系统的集成点

**集成点1: cache.py**
```python
# 添加新的缓存函数
@cache_with_ttl(ttl=60)
def get_capabilities():
    parser = CapabilityMatrixParser(PROJECT_ROOT)
    return parser.parse_capabilities()

@cache_with_ttl(ttl=60)
def get_decisions():
    parser = DecisionParser(PROJECT_ROOT)
    return parser.parse_decisions()
```

**集成点2: dashboard.py**
```python
def serve_capabilities(self):
    caps = get_capabilities()  # 使用缓存
    features = get_features()

    return {
        "core_stats": {...},
        "capabilities": [asdict(c) for c in caps],  # 新增！
        "features": features
    }

def serve_learning(self):
    decisions = get_decisions()  # 使用缓存

    return {
        "decisions": [asdict(d) for d in decisions],  # 新增！
        "statistics": {
            "total_decisions": len(decisions),
            "memory_cache_size": ...
        }
    }
```

---

## 📊 估算工作量

| 任务 | 预计时间 | 复杂度 |
|------|---------|--------|
| 添加数据模型 | 15分钟 | 低 |
| CapabilityMatrixParser | 45分钟 | 中 |
| DecisionParser | 30分钟 | 中 |
| Feature-Checkpoint映射 | 30分钟 | 低 |
| 集成到dashboard.py | 20分钟 | 低 |
| 单元测试 | 30分钟 | 中 |
| 集成测试 | 15分钟 | 低 |
| **总计** | **3.25小时** | **中等** |

---

## ✅ Phase 1.3 完成标志

- [x] 分析了3个数据源（CAPABILITY_MATRIX.md, DECISIONS.md, CHECKS_INDEX.json）
- [x] 确定了解析策略（正则表达式 + JSON）
- [x] 设计了数据模型（Capability, Decision）
- [x] 制定了集成方案（扩展parsers.py）
- [x] 评估了性能和风险
- [x] 创建了详细的技术发现文档

**下一步**: Phase 1.4 Impact Assessment（影响评估）
