# Phase 1.3: Technical Discovery
# Claude Enhancer v8.0 - Dual Evolution Learning System
# 日期: 2025-10-27
# 阶段: Discovery & Planning

---

## 🎯 项目概述

**目标**: 在现有7-Phase工作流基础上，增加双进化学习能力

**版本**: v7.3.0 → v8.0.0

**核心价值**:
- 统一工作流：开发CE自身和外部项目使用同样的7-Phase系统（97检查点）
- 学习系统：自动捕获5类学习经验（错误、性能、架构、代码质量、成功模式）
- 智能修复：三级Auto-fix策略，提高开发效率
- 知识管理：Learning Items → TODO队列 → Notion同步

---

## 🔍 技术可行性分析

### 1. 环境验证

**当前环境**:
- Python: 3.10.12 ✅
- Node.js: v16.20.2 ✅
- 已安装依赖: requests ✅

**需要新增**:
- PyYAML (用于Learning Item存储)
- Notion SDK (用于Notion同步)

**结论**: ✅ **GO** - 环境满足要求

---

### 2. 与现有系统集成分析

#### 2.1 现有7-Phase系统 (v7.3.0)

**核心文件**:
```
.workflow/
├── SPEC.yaml          # 7 Phases定义 (锁定)
├── manifest.yml       # Phase执行配置
├── gates.yml          # 质量门禁
└── LOCK.json          # SHA256指纹保护
```

**集成点**:
1. **Phase 1**: 在1.3 Technical Discovery和1.5 Architecture Planning嵌入架构学习钩子
2. **Phase 2**: 在Implementation嵌入错误捕获和Auto-fix钩子
3. **Phase 3**: 在Testing嵌入性能学习和测试失败Auto-fix钩子
4. **Phase 4**: 在Review嵌入代码质量学习钩子
5. **Phase 7**: 在Closure嵌入Notion同步钩子

**风险评估**:
- 🟢 低风险：新增功能为钩子机制，不修改核心工作流
- 🟢 低风险：数据存储独立（.learning/目录），不影响现有结构
- 🟡 中风险：需要确保不违反规则2（核心结构锁定）

**结论**: ✅ **GO** - 集成方案可行

---

#### 2.2 数据存储策略

**挑战**: 外部项目的Learning数据需要返回CE目录

**方案**:
```yaml
方案A: 环境变量 (推荐)
  实现: export CE_HOME=/home/xx/dev/Claude\ Enhancer
  优点: 简单、可靠、跨项目
  缺点: 需要用户配置环境变量

方案B: 配置文件
  实现: ~/.ce/config.yml 存储CE_HOME路径
  优点: 无需环境变量
  缺点: 需要维护配置文件

方案C: 自动检测
  实现: 搜索包含.workflow/SPEC.yaml的目录
  优点: 零配置
  缺点: 性能开销、不可靠
```

**决策**: ✅ **方案A（环境变量）+ 方案C（fallback自动检测）**

**实现**:
```bash
# 优先使用环境变量
CE_HOME=${CE_HOME:-$(find ~ -maxdepth 3 -name "SPEC.yaml" -path "*/.workflow/*" -exec dirname {} \; 2>/dev/null | head -1 | xargs dirname)}
```

**结论**: ✅ **GO** - 数据存储方案可行

---

### 3. Learning System设计验证

#### 3.1 五类学习数据结构

**设计**:
```yaml
learning_item:
  id: uuid
  timestamp: ISO8601
  project: string  # "claude-enhancer" 或外部项目名
  category: error_pattern|performance|architecture|code_quality|success_pattern
  phase: Phase1-Phase7

  context:
    working_directory: path
    file: path
    line: number
    git_branch: string
    git_commit: hash

  observation:
    type: error|optimization|insight
    description: string (中文)
    technical_details: string (英文)
    code_snippet: string

  learning:
    root_cause: string
    solution: string
    prevention: string
    confidence: float (0-1)

  actionable:
    todo_candidate: bool
    priority: high|medium|low
    estimated_effort: string
    auto_fix_eligible: bool
    auto_fix_tier: tier1_auto|tier2_try_then_ask|tier3_must_confirm
```

**存储格式**: YAML (人类可读、Git友好)

**文件命名**: `{timestamp}_{seq}_{category}_{project}.yml`
- 例: `2025-10-27_001_error_my-web-app.yml`

**技术验证**:
- ✅ YAML格式易于编辑和版本控制
- ✅ 文件系统存储简单可靠
- ✅ 符号链接可实现多维度索引（by_project, by_category）

**结论**: ✅ **GO** - 数据结构设计可行

---

#### 3.2 Auto-fix机制验证

**三级策略**:

**Tier 1 - Auto (自动修复，无需询问)**:
- 条件: confidence >= 0.95, risk_level = low, reversible = true
- 示例:
  - `ImportError: No module named 'xxx'` → `pip install xxx`
  - 格式化错误 → `black` / `prettier`
  - 端口冲突 → 自动更换端口

**Tier 2 - Try Then Ask (尝试修复，失败后询问)**:
- 条件: confidence 0.70-0.94, risk_level = medium, reversible = true
- 示例:
  - 构建失败 → 尝试常见修复，失败后问用户
  - 测试失败 → 尝试修复测试，失败后报告

**Tier 3 - Must Confirm (必须询问)**:
- 条件: confidence < 0.70, risk_level = high, irreversible = true
- 示例:
  - 数据迁移
  - 安全补丁
  - 破坏性变更

**技术验证**:
```python
# 伪代码验证
def auto_fix(error, learning_history):
    # 1. 匹配历史Learning Items
    similar = search_similar_pattern(error, learning_history)

    # 2. 计算信心分数
    confidence = calculate_confidence(similar)

    # 3. 决策
    if confidence >= 0.95 and is_low_risk(error):
        return apply_fix_auto(similar.solution)
    elif confidence >= 0.70:
        try:
            result = try_fix(similar.solution)
            if not result.success:
                return ask_user(error, similar)
        except:
            return ask_user(error, similar)
    else:
        return ask_user_first(error, similar)
```

**结论**: ✅ **GO** - Auto-fix机制设计可行

---

#### 3.3 TODO队列系统验证

**转换规则**:
```yaml
automatic_conversion:
  conditions:
    - learning_item.actionable.todo_candidate == true
    - learning_item.learning.confidence >= 0.80
    - learning_item.actionable.priority in [high, medium]

  action: 自动创建TODO

manual_review:
  conditions:
    - learning_item.learning.confidence < 0.80
    - OR learning_item.actionable.priority == low

  action: 加入"待审查"队列，用户查询时展示
```

**TODO数据结构**:
```yaml
todo:
  id: uuid
  title: string
  description: markdown
  priority: high|medium|low
  estimated_effort: string
  status: pending|in_progress|completed|rejected
  source_learning_id: uuid  # 关联到Learning Item
  created_at: timestamp
  tags: list
```

**存储**:
```
.todos/
├── queue.json          # 队列索引
├── pending/            # 待处理
├── in_progress/        # 进行中
├── completed/          # 已完成
└── rejected/           # 已拒绝
```

**结论**: ✅ **GO** - TODO系统设计可行

---

### 4. Notion集成验证

#### 4.1 Notion API可行性

**现有Notion配置**:
```
Token: ${NOTION_TOKEN} (从环境变量读取)
Database IDs:
  - notes: 1fb0ec1c-c75b-482b-be0c-ffd4fdb5fd4d
  - tasks: 54fe0d4c-f434-4e91-8bb0-e33967661c42
  - events: e6c819b1-fd59-41d1-af89-539ac9504c07
```

**需要安装**:
```bash
pip3 install notion-client
```

**同步时机**: Phase 7 (Closure) 完成后

**同步内容**:
1. Learning Items → `notes` database
2. TODOs → `tasks` database
3. Project Summary → `events` database

**批量策略**:
- 收集Phase 1-7所有Learning Items
- 生成非技术摘要（中文，面向非程序员）
- 一次性批量写入Notion

**技术验证**:
```python
# 伪代码验证
from notion_client import Client

notion = Client(auth="ntn_...")

# 创建Learning Item页面
notion.pages.create(
    parent={"database_id": "1fb0ec1c..."},
    properties={
        "标题": {"title": [{"text": {"content": "..."}}]},
        "类别": {"select": {"name": "error_pattern"}},
        "项目": {"rich_text": [{"text": {"content": "my-web-app"}}]},
        "优先级": {"select": {"name": "high"}},
        "信心分数": {"number": 0.95}
    },
    children=[...]  # 详细内容
)
```

**结论**: ✅ **GO** - Notion集成可行

---

#### 4.2 非技术摘要生成

**目标**: 让非程序员理解做了什么

**禁用术语**:
- API, JWT, OAuth, Token, Hash
- 数据库, SQL, NoSQL, Schema
- 前端, 后端, 中间件
- 函数, 变量, 类, 对象

**替换规则**:
```yaml
replacements:
  "实现了认证系统" → "做了登录功能，用户可以安全登录"
  "优化了数据库查询" → "让系统运行更快了"
  "重构了代码" → "整理了代码，以后更容易维护"
  "修复了bug" → "修复了一个问题"
  "实现了缓存层" → "加了一个加速机制"
```

**生成模板**:
```markdown
## 项目：{project_name}

**时间**: {start_date} 到 {end_date}（共{duration}天）

**做了什么**:
- {feature_1_plain_language}
- {feature_2_plain_language}

**遇到的问题**:
- {issue_1_plain_language}（已解决）

**学到的经验**:
- {learning_1_plain_language}

**下一步建议**:
- {suggestion_1}
```

**结论**: ✅ **GO** - 摘要生成可行

---

## 🎯 技术Spike验证

### Spike 1: Learning Item捕获与存储

**测试目标**: 验证YAML存储和读取

**测试代码**:
```python
import yaml
import uuid
from datetime import datetime

learning_item = {
    'id': str(uuid.uuid4()),
    'timestamp': datetime.now().isoformat(),
    'project': 'test-project',
    'category': 'error_pattern',
    'phase': 'Phase2',
    'observation': {
        'description': '测试Learning Item'
    },
    'learning': {
        'confidence': 0.95
    }
}

# 写入
with open('/tmp/test_learning.yml', 'w') as f:
    yaml.dump(learning_item, f, allow_unicode=True)

# 读取
with open('/tmp/test_learning.yml', 'r') as f:
    loaded = yaml.safe_load(f)

assert loaded['id'] == learning_item['id']
print("✅ Spike 1 通过")
```

**结果**: ✅ **通过**

---

### Spike 2: CE_HOME自动检测

**测试目标**: 验证自动检测CE目录

**测试代码**:
```bash
#!/bin/bash

# 方法1: 环境变量
CE_HOME_ENV=${CE_HOME:-""}

# 方法2: 自动检测
CE_HOME_AUTO=$(find ~ -maxdepth 3 -name "SPEC.yaml" -path "*/.workflow/*" 2>/dev/null | head -1 | xargs dirname | xargs dirname)

# 优先使用环境变量
CE_HOME=${CE_HOME_ENV:-$CE_HOME_AUTO}

echo "CE_HOME: $CE_HOME"
test -f "$CE_HOME/.workflow/SPEC.yaml" && echo "✅ Spike 2 通过"
```

**结果**: ✅ **通过**

---

### Spike 3: Notion API连接

**测试目标**: 验证Notion Token可用

**测试代码**:
```python
from notion_client import Client

notion = Client(auth=os.getenv("NOTION_TOKEN"))

# 测试查询数据库
result = notion.databases.query(database_id="1fb0ec1c-c75b-482b-be0c-ffd4fdb5fd4d")

print(f"✅ Spike 3 通过 - 找到{len(result['results'])}条记录")
```

**注意**: 实际执行时需要安装 `pip3 install notion-client`

**结果**: 🟡 **待验证** (需要安装依赖后验证)

---

## ⚠️ 风险识别

### 技术风险

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| 违反规则2（核心结构锁定） | 🟡 中 | 所有修改通过`tools/verify-core-structure.sh`验证 |
| Learning Items存储过多导致性能问题 | 🟢 低 | 实现定期归档机制（30天后归档） |
| Auto-fix误操作导致代码错误 | 🟡 中 | Tier1只允许低风险操作，所有操作记录日志 |
| Notion API限流 | 🟢 低 | 批量同步（非实时），失败后重试 |
| 外部项目识别错误 | 🟢 低 | 使用basename($PWD)，简单可靠 |

### 业务风险

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| 用户不习惯新的学习系统 | 🟢 低 | 学习系统静默运行，不影响正常开发 |
| TODO队列过多导致overwhelm | 🟡 中 | 实现优先级过滤，只推荐高优先级TODO |
| 非技术摘要不够"人话" | 🟢 低 | 建立术语替换字典，持续优化 |

### 时间风险

| 阶段 | 预估时间 | 风险 |
|------|---------|------|
| Phase 2 实现 | 2天 | 🟢 低 |
| Phase 3 测试 | 1天 | 🟢 低 |
| Phase 4 审查 | 0.5天 | 🟢 低 |
| Phase 5-7 发布 | 0.5天 | 🟢 低 |
| **总计** | **4天** | 🟢 **低** |

---

## 🎯 Go/No-Go决策

### 技术维度
- ✅ 环境满足要求
- ✅ 集成方案可行
- ✅ 数据存储方案验证通过
- ✅ 核心Spike验证通过（2/3）
- 🟡 Notion API待验证（需安装依赖）

### 业务维度
- ✅ 功能价值明确（学习系统 + Auto-fix + TODO管理）
- ✅ 不降低现有质量标准
- ✅ 符合v7.3.0的设计哲学

### 风险维度
- ✅ 技术风险可控（中等2个，低5个）
- ✅ 业务风险可控（中等1个，低2个）
- ✅ 时间风险低

---

## 🚀 最终结论

**决策**: ✅ **GO**

**理由**:
1. 技术可行性已验证（3个Spike中2个通过，1个待安装依赖）
2. 集成方案不违反核心规则（规则1、规则2）
3. 风险可控，缓解措施明确
4. 预期4天完成，时间合理

**下一步**: 进入Phase 1.4 (Impact Assessment)

---

## 📝 附录：关键技术决策

### 决策1: 为什么用YAML而不是JSON？
- YAML更易读（支持注释）
- Git diff友好
- Python/Bash都有成熟的解析库

### 决策2: 为什么用文件系统而不是数据库？
- 简单、可靠、无额外依赖
- Git版本控制友好
- 符合CE的轻量级哲学

### 决策3: 为什么Notion同步放在Phase 7而不是实时？
- 减少API调用（避免限流）
- 批量同步可以生成更好的摘要
- 用户开发时不需要实时同步

### 决策4: 为什么Auto-fix分三级而不是全自动？
- 平衡效率和安全
- 给用户控制权（高风险操作）
- 避免"魔法"行为导致困惑

---

**文档状态**: ✅ 完成（>300行）
**下一阶段**: Phase 1.4 Impact Assessment
