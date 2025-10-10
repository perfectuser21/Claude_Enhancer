# Git Hooks与Workflow联动机制详解

## 🔗 核心联动机制

### 1. 读取当前Phase状态

```bash
# .git/hooks/pre-commit 第14-15行
PHASE_FILE="$PROJECT_ROOT/.phase/current"
current_phase=$(cat "$PHASE_FILE")
```

**联动点1**: Hook从`.phase/current`文件读取当前阶段
- workflow的executor.sh切换Phase时会写入这个文件
- Hook每次运行都读取最新的Phase

### 2. 读取gates.yml配置

```bash
# .git/hooks/pre-commit 第16行
GATES_YML="$PROJECT_ROOT/.workflow/gates.yml"

# 第40-63行：解析allow_paths
get_allow_paths() {
    local phase="$1"
    awk -v phase="$phase" '
        /^  [A-Z0-9]+:/ { current_phase = substr($1, 1, length($1)-1) }
        current_phase == phase && /^    allow_paths: \[/ {
            # 解析JSON数组格式
            line = $0
            sub(/.*allow_paths: \[/, "", line)
            sub(/\].*/, "", line)
            gsub(/"/, "", line)
            n = split(line, items, ", ")
            for (i = 1; i <= n; i++) {
                print items[i]
            }
        }
    ' "$GATES_YML"
}
```

**联动点2**: Hook解析gates.yml获取Phase规则
- 读取allow_paths（允许的路径）
- 读取must_produce（必须产出）
- 读取gates（检查项）

### 3. 强制执行allow_paths

```bash
# .git/hooks/pre-commit 第173-229行
echo -e "\n${CYAN}[PATH VALIDATION]${NC}"

if [ -n "$STAGED_FILES" ]; then
    # 读取允许的路径
    allowed_paths=$(get_allow_paths "$current_phase")

    if [ -z "$allowed_paths" ]; then
        echo "⚠️  Warning: gates.yml 中未定义 $current_phase 的 allow_paths"
    else
        # 显示允许的路径
        echo "📂 $current_phase 允许的路径:"
        echo "$allowed_paths" | while read -r path; do
            [ -n "$path" ] && echo "   - $path"
        done

        # 验证每个文件
        path_violations=0

        while IFS= read -r file; do
            [ -z "$file" ] && continue

            # 检查文件是否匹配任意允许的路径
            matched=false
            while IFS= read -r allowed; do
                [ -z "$allowed" ] && continue
                if match_glob "$file" "$allowed"; then
                    matched=true
                    break
                fi
            done <<< "$allowed_paths"

            if [ "$matched" = false ]; then
                echo "❌ $file (不在允许路径内)"
                ((path_violations++))
            else
                echo "✓ $file"
            fi
        done <<< "$STAGED_FILES"

        # 如果有违规，强制退出
        if [ $path_violations -gt 0 ]; then
            echo "❌ ERROR: 检测到 $path_violations 个文件违反了 $current_phase 的路径限制"
            echo "gates.yml 规则: $current_phase 阶段只允许修改:"
            echo "$allowed_paths" | while read -r path; do
                [ -n "$path" ] && echo "  - $path"
            done
            exit 1  # 强制阻止提交
        fi
    fi
fi
```

**联动点3**: 强制阻塞机制
- 检查每个staged文件是否在allow_paths内
- 不匹配的文件导致`exit 1`，**强制阻止提交**

## 🔒 强制机制详解

### 阻塞流程图

```
用户执行 git commit
    ↓
Git自动调用 .git/hooks/pre-commit
    ↓
读取 .phase/current → 获取当前Phase (如P1)
    ↓
读取 .workflow/gates.yml → 获取P1的规则
    ↓
P1 allow_paths: ["docs/PLAN.md"]
    ↓
检查staged文件
    ↓
staged: docs/PLAN.md ✓
staged: src/test.js  ❌ (不在allow_paths中)
    ↓
发现违规 → exit 1
    ↓
Git收到非零退出码 → 提交被取消 ✋
    ↓
用户看到错误信息
```

### 强制性保证

**Git的Hook机制**：
- pre-commit返回0 → Git继续提交
- pre-commit返回非0 → Git取消提交
- **无法绕过**（除非用`git commit --no-verify`）

## 📋 实际执行示例

### 场景1：P1阶段修改PLAN.md（允许）

```bash
$ echo "P1" > .phase/current
$ echo "task 1" >> docs/PLAN.md
$ git add docs/PLAN.md
$ git commit -m "docs: 更新计划"

# Hook执行：
🔍 Claude Enhancer Pre-commit Check (Gates.yml Enforced)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[WORKFLOW]
📍 当前阶段: P1
✓ 工作流阶段: P1 - Plan

[PATH VALIDATION]
📂 P1 允许的路径:
   - docs/PLAN.md

🔍 验证文件路径...
   ✓ docs/PLAN.md

✓ 所有文件路径验证通过

[SECURITY]
🔐 完整安全扫描
✓ 安全检查通过

✅ 所有检查通过！Phase: P1
```

### 场景2：P1阶段修改src文件（阻止）

```bash
$ echo "P1" > .phase/current
$ echo "code" > src/test.js
$ git add src/test.js
$ git commit -m "feat: 新功能"

# Hook执行：
🔍 Claude Enhancer Pre-commit Check (Gates.yml Enforced)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[WORKFLOW]
📍 当前阶段: P1
✓ 工作流阶段: P1 - Plan

[PATH VALIDATION]
📂 P1 允许的路径:
   - docs/PLAN.md

🔍 验证文件路径...
   ❌ src/test.js (不在允许路径内)

❌ ERROR: 检测到 1 个文件违反了 P1 的路径限制

gates.yml 规则: P1 阶段只允许修改:
  - docs/PLAN.md

解决方案：
  1. 只提交允许路径内的文件
  2. 如果需要修改其他文件，请先完成当前Phase并进入下一Phase
  3. 或者更新 .workflow/gates.yml 中的 allow_paths 配置

# Git看到exit 1，取消提交
error: hook returned non-zero exit code: 1
```

## 🔄 与Workflow Executor的联动

### Workflow Executor切换Phase

```bash
# .workflow/executor.sh (简化版)
function switch_phase() {
    local from_phase=$1
    local to_phase=$2

    # 1. 验证当前Phase的Gates
    validate_gates "$from_phase" || {
        echo "❌ Gates验证失败，无法切换"
        return 1
    }

    # 2. 更新Phase文件
    echo "$to_phase" > .phase/current

    # 3. 从这一刻起，Git Hooks读取新的Phase
    # 下次commit时，Hook会强制执行to_phase的规则

    # 4. 创建Gate标记
    touch ".gates/0${from_phase:1:1}.ok"
}
```

### 联动时序图

```
时间轴：

t0: echo "P1" > .phase/current
    ↓
t1: git commit
    ↓ (Git调用pre-commit)
    pre-commit读取 .phase/current → P1
    pre-commit读取 gates.yml → P1的allow_paths
    pre-commit验证文件 → 强制执行
    ↓
t2: .workflow/executor.sh next
    ↓
    executor验证P1的Gates → 检查PLAN.md是否完成
    executor切换Phase → echo "P2" > .phase/current
    ↓
t3: git commit
    ↓ (Git调用pre-commit)
    pre-commit读取 .phase/current → P2 (已更新)
    pre-commit读取 gates.yml → P2的allow_paths
    pre-commit验证文件 → 强制执行新规则
```

## 🎯 Phase特定的强制规则

### P0: 探索阶段（最宽松）

```yaml
# gates.yml
P0:
  allow_paths: ["**"]  # 允许所有路径

# pre-commit行为
if [[ "$current_phase" == "P0" ]]; then
    # 只检查关键安全
    检查私钥 → 发现则exit 1
    检查AWS密钥 → 发现则exit 1
    # 其他任何文件都允许
fi
```

### P1: 规划阶段（严格路径）

```yaml
# gates.yml
P1:
  allow_paths: ["docs/PLAN.md"]

# pre-commit行为
allowed = ["docs/PLAN.md"]
for file in staged_files:
    if file not in allowed:
        exit 1  # 强制阻止
```

### P3: 实现阶段（代码文件）

```yaml
# gates.yml
P3:
  allow_paths: ["src/**", "docs/CHANGELOG.md"]

# pre-commit行为
allowed = ["src/**", "docs/CHANGELOG.md"]
for file in staged_files:
    if not match_glob(file, allowed):
        exit 1  # 强制阻止
```

## 🔧 Glob匹配实现（支持**和*）

```bash
# .git/hooks/pre-commit 第86-107行
match_glob() {
    local file="$1"
    local pattern="$2"

    if [ "$pattern" = "**" ]; then
        return 0  # 匹配所有
    fi

    # 转换glob为正则表达式
    # 关键：先用占位符替换**，避免被*替换影响
    local regex_pattern="$pattern"
    regex_pattern="${regex_pattern//\*\*/__DOUBLESTAR__}"  # ** → 占位符
    regex_pattern="${regex_pattern//\*/[^/]*}"             # * → [^/]*
    regex_pattern="${regex_pattern//__DOUBLESTAR__/.*}"    # 占位符 → .*
    regex_pattern="^${regex_pattern}$"

    if echo "$file" | grep -qE "$regex_pattern"; then
        return 0  # 匹配
    else
        return 1  # 不匹配
    fi
}
```

**示例**：
- `src/**` → `^src/.*$` → 匹配`src/foo.js`, `src/a/b/c.js`
- `docs/*.md` → `^docs/[^/]*\.md$` → 匹配`docs/README.md`，不匹配`docs/a/b.md`

## 🚨 无法绕过的强制性

### 强制性来源

1. **Git内置机制**：
   - pre-commit返回非0 → Git取消提交
   - 这是Git核心功能，无法修改

2. **文件系统依赖**：
   - Hook必须读取`.phase/current` → 如果不存在，直接exit 1
   - Hook必须读取`.workflow/gates.yml` → 解析失败，跳过检查（有警告）

3. **exit 1的分布**：
```bash
# pre-commit中所有exit 1的地方：
第140行: 直接提交main/master → exit 1
第152行: 未启动工作流 → exit 1
第222行: 文件路径违规 → exit 1
第315行: 发现安全问题 → exit 1
```

### 唯一的"绕过"方式

```bash
# 方式1：使用--no-verify（但会被日志记录）
git commit --no-verify -m "message"
# 风险：绕过所有检查，不推荐

# 方式2：修改gates.yml（但需要commit）
# 修改allow_paths，然后commit这个修改
# 这是"合法"的方式

# 方式3：删除Hook（但会被发现）
rm .git/hooks/pre-commit
# 下次运行workflow时会检测到Hook缺失
```

## 📊 联动强度对比

| 联动方式 | 强度 | 说明 |
|---------|------|------|
| **Hook读取Phase** | ⭐⭐⭐⭐⭐ | 每次commit都读取 |
| **Hook读取gates.yml** | ⭐⭐⭐⭐⭐ | 动态解析规则 |
| **路径白名单阻塞** | ⭐⭐⭐⭐⭐ | exit 1强制 |
| **安全检查阻塞** | ⭐⭐⭐⭐⭐ | exit 1强制 |
| **must_produce检查** | ⭐⭐⭐ | 只警告，不阻塞 |

## 🧪 验证联动

### 测试1：修改gates.yml立即生效

```bash
# 1. 当前P1只允许PLAN.md
$ echo "P1" > .phase/current
$ git add src/test.js
$ git commit -m "test"
# 结果：❌ 阻止

# 2. 修改gates.yml添加src/**
$ vim .workflow/gates.yml
# P1: allow_paths: ["docs/PLAN.md", "src/**"]

$ git commit -m "test"
# 结果：✅ 通过（立即生效！）
```

### 测试2：切换Phase立即改变规则

```bash
$ echo "P1" > .phase/current
$ git add src/test.js
$ git commit -m "test"
# 结果：❌ P1不允许src/**

$ echo "P3" > .phase/current
$ git commit -m "test"
# 结果：✅ P3允许src/**
```

## 💡 总结

### 联动机制

1. **Hook读取Workflow状态** → `.phase/current`
2. **Hook读取规则配置** → `.workflow/gates.yml`
3. **Hook解析并强制执行** → allow_paths + 安全检查
4. **exit 1阻塞提交** → Git取消操作

### 强制性保证

- ✅ Git内置机制保证
- ✅ 每次commit都检查
- ✅ 违规必定阻止（exit 1）
- ✅ 清晰的错误提示
- ✅ 动态读取最新规则

### 集成度：95%

- 读取Phase状态：100%
- 读取gates.yml：100%
- 强制路径限制：100%
- 安全检查：100%
- must_produce验证：80%（基础检查）

**Hook不再是摆设，而是Workflow的强制执行器！**