# Claude Enhancer v2.0 架构重构测试计划

**测试工程师**: Test Engineer Professional
**版本**: v2.0
**日期**: 2025-10-14
**状态**: 设计完成
**分支**: feature/architecture-v2.0

---

## 📋 执行摘要

本测试计划为 Claude Enhancer v2.0 架构重构提供全面的测试策略，确保从当前架构平滑迁移到四层分层架构（L0-L3）。测试覆盖迁移正确性、锁定机制、Feature系统、Hook增强、兼容性和性能等6个关键领域。

### 🎯 测试目标

- ✅ **迁移正确性**: 验证所有核心文件正确迁移到新架构
- ✅ **锁定机制**: 确保core/文件不可修改，Hash验证工作
- ✅ **Feature系统**: 验证enable/disable机制和依赖管理
- ✅ **Hook增强**: 测试5层检测机制，杜绝"继续"绕过
- ✅ **兼容性**: 确保旧命令和workflow继续工作
- ✅ **性能**: 验证启动时间和锁定检查不影响性能

---

## 🏗️ 架构v2.0概述

### 四层架构 (L0-L3)

```
┌─────────────────────────────────────────────┐
│        L3: Features (60%+) - 特性层         │ ← 快速变化
│    basic/ | standard/ | advanced/           │
├─────────────────────────────────────────────┤
│        L2: Services (20%) - 服务层          │ ← 中速变化
│    validation/ | formatting/ | analysis/    │
├─────────────────────────────────────────────┤
│       L1: Framework (15%) - 框架层          │ ← 缓慢变化
│    workflow/ | strategies/ | hooks/         │
├─────────────────────────────────────────────┤
│         L0: Core (5%) - 内核层              │ ← 极少变化
│    engine.py | orchestrator.py | config.yaml│
└─────────────────────────────────────────────┘
```

### 关键变更

1. **core/ → 最小化内核**：只保留engine.py, orchestrator.py, loader.py, config.yaml
2. **main/ → framework/**：重命名为框架层
3. **modules/ → services/**：重命名为服务层
4. **features/ → 三级分类**：basic/, standard/, advanced/
5. **锁定机制**：core/文件通过Hash验证锁定
6. **Feature系统**：支持enable/disable功能
7. **Hook增强**：5层检测机制防止绕过

---

## 📊 测试范围矩阵

| 测试类型 | 测试场景 | 优先级 | 预计耗时 | 自动化 |
|---------|---------|--------|---------|--------|
| **1. 迁移正确性测试** | | | | |
| 1.1 核心文件迁移 | 4个核心文件 | P0 | 10min | ✅ |
| 1.2 文件内容完整性 | Hash验证 | P0 | 5min | ✅ |
| 1.3 软链接验证 | 兼容性链接 | P1 | 5min | ✅ |
| **2. 锁定机制测试** | | | | |
| 2.1 修改core/阻止 | Pre-commit hook | P0 | 15min | ✅ |
| 2.2 Hash验证 | SHA256校验 | P0 | 10min | ✅ |
| 2.3 Git hook触发 | Pre-commit触发 | P0 | 10min | ✅ |
| 2.4 Claude hook触发 | PreToolUse触发 | P0 | 10min | ✅ |
| **3. Feature系统测试** | | | | |
| 3.1 Enable/Disable | 功能开关 | P0 | 20min | ✅ |
| 3.2 功能加载 | 禁用不加载 | P0 | 15min | ✅ |
| 3.3 依赖检查 | 依赖验证 | P1 | 15min | ✅ |
| **4. Hook增强测试** | | | | |
| 4.1 "继续"绕过防护 | 5层检测 | P0 | 20min | ✅ |
| 4.2 Phase状态检查 | 状态验证 | P0 | 15min | ✅ |
| 4.3 分支状态检查 | 分支验证 | P0 | 15min | ✅ |
| 4.4 5层检测全覆盖 | 完整测试 | P0 | 30min | ✅ |
| **5. 兼容性测试** | | | | |
| 5.1 旧命令支持 | 向后兼容 | P0 | 20min | ✅ |
| 5.2 Workflow兼容 | P0-P7流程 | P0 | 30min | ✅ |
| 5.3 配置兼容 | 配置迁移 | P1 | 15min | ✅ |
| **6. 性能测试** | | | | |
| 6.1 启动时间 | <200ms | P0 | 15min | ✅ |
| 6.2 锁定检查性能 | <50ms | P0 | 15min | ✅ |
| 6.3 Commit性能 | <3s | P1 | 10min | ✅ |

**总计**: 18个测试场景 | 预计总耗时: 4-5小时

---

## 🧪 详细测试策略

## 1. 迁移正确性测试 (Migration Correctness Tests)

### 1.1 核心文件迁移测试

**目标**: 验证4个核心文件成功迁移到core/目录

**测试用例**:

```bash
# Test Case 1.1.1: 核心文件存在性检查
test_core_files_exist() {
    local core_files=(
        ".claude/core/engine.py"
        ".claude/core/orchestrator.py"
        ".claude/core/loader.py"
        ".claude/core/config.yaml"
    )

    for file in "${core_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo "❌ FAIL: Core file missing: $file"
            return 1
        fi
    done

    echo "✅ PASS: All 4 core files exist"
    return 0
}

# Test Case 1.1.2: 旧位置文件已删除
test_old_locations_removed() {
    local old_files=(
        ".claude/engine.py"
        ".claude/orchestrator.py"
    )

    for file in "${old_files[@]}"; do
        if [ -f "$file" ]; then
            echo "❌ FAIL: Old file still exists: $file"
            return 1
        fi
    done

    echo "✅ PASS: Old files removed"
    return 0
}

# Test Case 1.1.3: 核心文件行数检查（防止空文件）
test_core_files_not_empty() {
    local min_lines=50  # 核心文件至少50行

    if [ $(wc -l < .claude/core/engine.py) -lt $min_lines ]; then
        echo "❌ FAIL: engine.py too small"
        return 1
    fi

    if [ $(wc -l < .claude/core/orchestrator.py) -lt $min_lines ]; then
        echo "❌ FAIL: orchestrator.py too small"
        return 1
    fi

    echo "✅ PASS: Core files have sufficient content"
    return 0
}
```

**预期结果**:
- ✅ 4个核心文件存在于 `.claude/core/`
- ✅ 旧位置文件已删除或移动
- ✅ 文件内容完整（不是空文件）

---

### 1.2 文件内容完整性测试

**目标**: 验证迁移过程中文件内容未损坏

**测试用例**:

```bash
# Test Case 1.2.1: Hash完整性验证
test_file_integrity() {
    # 迁移前生成Hash（应该已存在）
    local hash_file=".claude/core/.integrity.sha256"

    if [ ! -f "$hash_file" ]; then
        echo "❌ FAIL: Integrity hash file missing"
        return 1
    fi

    # 验证Hash
    cd .claude/core
    if ! sha256sum -c .integrity.sha256 --quiet; then
        echo "❌ FAIL: Hash verification failed"
        return 1
    fi

    echo "✅ PASS: File integrity verified"
    return 0
}

# Test Case 1.2.2: Python语法检查
test_python_syntax() {
    for pyfile in .claude/core/*.py; do
        if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
            echo "❌ FAIL: Python syntax error in $pyfile"
            return 1
        fi
    done

    echo "✅ PASS: All Python files have valid syntax"
    return 0
}

# Test Case 1.2.3: YAML语法检查
test_yaml_syntax() {
    if ! python3 -c "import yaml; yaml.safe_load(open('.claude/core/config.yaml'))" 2>/dev/null; then
        echo "❌ FAIL: YAML syntax error in config.yaml"
        return 1
    fi

    echo "✅ PASS: YAML file has valid syntax"
    return 0
}
```

**预期结果**:
- ✅ SHA256 Hash验证通过
- ✅ Python文件语法正确
- ✅ YAML文件语法正确

---

### 1.3 软链接验证测试

**目标**: 验证兼容性软链接正常工作

**测试用例**:

```bash
# Test Case 1.3.1: 软链接存在性
test_symlinks_exist() {
    local symlinks=(
        ".claude/engine.py:.claude/core/engine.py"
        ".claude/orchestrator.py:.claude/core/orchestrator.py"
    )

    for link in "${symlinks[@]}"; do
        IFS=':' read -r link_path target <<< "$link"

        if [ ! -L "$link_path" ]; then
            echo "❌ FAIL: Symlink missing: $link_path"
            return 1
        fi

        if [ "$(readlink -f $link_path)" != "$(readlink -f $target)" ]; then
            echo "❌ FAIL: Symlink points to wrong target: $link_path"
            return 1
        fi
    done

    echo "✅ PASS: All symlinks exist and point to correct targets"
    return 0
}

# Test Case 1.3.2: 通过软链接访问文件
test_symlink_access() {
    # 通过旧路径访问（软链接）
    if ! python3 -c "import sys; sys.path.insert(0, '.claude'); import engine" 2>/dev/null; then
        echo "❌ FAIL: Cannot import engine via symlink"
        return 1
    fi

    echo "✅ PASS: Symlink access works"
    return 0
}

# Test Case 1.3.3: 软链接在Git中的状态
test_symlink_git_status() {
    # 软链接应该被Git追踪
    if ! git ls-files --error-unmatch .claude/engine.py 2>/dev/null; then
        echo "❌ FAIL: Symlink not tracked by Git"
        return 1
    fi

    echo "✅ PASS: Symlinks tracked by Git"
    return 0
}
```

**预期结果**:
- ✅ 软链接存在并指向正确目标
- ✅ 通过软链接可以访问文件
- ✅ 软链接被Git正确追踪

---

## 2. 锁定机制测试 (Locking Mechanism Tests)

### 2.1 修改core/文件阻止测试

**目标**: 验证尝试修改core/文件时被Pre-commit hook阻止

**测试用例**:

```bash
# Test Case 2.1.1: 直接修改core/文件被阻止
test_direct_modification_blocked() {
    # 尝试修改engine.py
    echo "# Test modification" >> .claude/core/engine.py
    git add .claude/core/engine.py

    # 尝试提交（应该被阻止）
    if git commit -m "test: try to modify core file" 2>&1 | grep -q "BLOCKED"; then
        echo "✅ PASS: Core file modification blocked"
        # 恢复修改
        git reset HEAD .claude/core/engine.py
        git checkout -- .claude/core/engine.py
        return 0
    else
        echo "❌ FAIL: Core file modification NOT blocked"
        git reset HEAD .claude/core/engine.py
        git checkout -- .claude/core/engine.py
        return 1
    fi
}

# Test Case 2.1.2: 批量修改core/文件被阻止
test_batch_modification_blocked() {
    # 修改多个core文件
    echo "# Test 1" >> .claude/core/engine.py
    echo "# Test 2" >> .claude/core/orchestrator.py
    git add .claude/core/

    if git commit -m "test: try to modify multiple core files" 2>&1 | grep -q "BLOCKED"; then
        echo "✅ PASS: Batch core file modification blocked"
        git reset HEAD .claude/core/
        git checkout -- .claude/core/
        return 0
    else
        echo "❌ FAIL: Batch modification NOT blocked"
        git reset HEAD .claude/core/
        git checkout -- .claude/core/
        return 1
    fi
}

# Test Case 2.1.3: 删除core/文件被阻止
test_deletion_blocked() {
    git rm .claude/core/engine.py

    if git commit -m "test: try to delete core file" 2>&1 | grep -q "BLOCKED"; then
        echo "✅ PASS: Core file deletion blocked"
        git reset HEAD .claude/core/engine.py
        git checkout -- .claude/core/engine.py
        return 0
    else
        echo "❌ FAIL: Core file deletion NOT blocked"
        git reset HEAD .claude/core/engine.py
        git checkout -- .claude/core/engine.py
        return 1
    fi
}
```

**预期结果**:
- ✅ 直接修改core/文件被pre-commit hook阻止
- ✅ 批量修改core/文件被阻止
- ✅ 删除core/文件被阻止
- ✅ 错误消息清晰明确

---

### 2.2 Hash验证测试

**目标**: 验证SHA256 Hash验证机制工作正常

**测试用例**:

```bash
# Test Case 2.2.1: Hash生成
test_hash_generation() {
    cd .claude/core

    # 生成Hash
    if ! sha256sum *.py config.yaml > .integrity.sha256; then
        echo "❌ FAIL: Hash generation failed"
        return 1
    fi

    # 验证文件存在
    if [ ! -f .integrity.sha256 ]; then
        echo "❌ FAIL: Hash file not created"
        return 1
    fi

    echo "✅ PASS: Hash generated successfully"
    return 0
}

# Test Case 2.2.2: Hash验证通过
test_hash_verification_pass() {
    cd .claude/core

    if ! sha256sum -c .integrity.sha256 --quiet; then
        echo "❌ FAIL: Hash verification failed (should pass)"
        return 1
    fi

    echo "✅ PASS: Hash verification passed"
    return 0
}

# Test Case 2.2.3: Hash验证失败（模拟篡改）
test_hash_verification_fail() {
    cd .claude/core

    # 备份原文件
    cp engine.py engine.py.backup

    # 篡改文件
    echo "# Tampered" >> engine.py

    # Hash验证应该失败
    if sha256sum -c .integrity.sha256 --quiet 2>/dev/null; then
        echo "❌ FAIL: Hash verification passed (should fail)"
        mv engine.py.backup engine.py
        return 1
    else
        echo "✅ PASS: Hash verification failed (detected tampering)"
        mv engine.py.backup engine.py
        return 0
    fi
}
```

**预期结果**:
- ✅ Hash文件成功生成
- ✅ 未修改时Hash验证通过
- ✅ 文件被篡改时Hash验证失败

---

### 2.3 Git Hook触发测试

**目标**: 验证Pre-commit hook在提交时正确触发

**测试用例**:

```bash
# Test Case 2.3.1: Pre-commit hook存在
test_precommit_hook_exists() {
    if [ ! -f .git/hooks/pre-commit ]; then
        echo "❌ FAIL: Pre-commit hook not installed"
        return 1
    fi

    if [ ! -x .git/hooks/pre-commit ]; then
        echo "❌ FAIL: Pre-commit hook not executable"
        return 1
    fi

    echo "✅ PASS: Pre-commit hook installed"
    return 0
}

# Test Case 2.3.2: Hook包含core/保护逻辑
test_hook_contains_protection() {
    if ! grep -q "core/" .git/hooks/pre-commit; then
        echo "❌ FAIL: Hook doesn't contain core/ protection"
        return 1
    fi

    if ! grep -q "integrity" .git/hooks/pre-commit; then
        echo "❌ FAIL: Hook doesn't contain integrity check"
        return 1
    fi

    echo "✅ PASS: Hook contains protection logic"
    return 0
}

# Test Case 2.3.3: Hook在正常提交时不阻止
test_hook_allows_normal_commit() {
    # 修改非core/文件
    echo "# Test" >> .claude/tests/test_example.py
    git add .claude/tests/test_example.py

    if ! git commit -m "test: normal commit" 2>/dev/null; then
        echo "❌ FAIL: Hook blocked normal commit"
        git reset HEAD .claude/tests/test_example.py
        git checkout -- .claude/tests/test_example.py
        return 1
    fi

    echo "✅ PASS: Hook allows normal commits"
    # 撤销提交
    git reset --soft HEAD~1
    git reset HEAD .claude/tests/test_example.py
    git checkout -- .claude/tests/test_example.py
    return 0
}
```

**预期结果**:
- ✅ Pre-commit hook已安装且可执行
- ✅ Hook包含core/保护和integrity检查逻辑
- ✅ Hook不阻止正常提交（非core/文件）

---

### 2.4 Claude Hook触发测试

**目标**: 验证Claude的PreToolUse hook阻止修改core/文件

**测试用例**:

```python
# Test Case 2.4.1: PreToolUse hook存在
def test_claude_hook_exists():
    hook_path = ".claude/hooks/pre_tool_use.sh"

    if not os.path.exists(hook_path):
        print("❌ FAIL: Claude PreToolUse hook not found")
        return False

    if not os.access(hook_path, os.X_OK):
        print("❌ FAIL: Claude hook not executable")
        return False

    print("✅ PASS: Claude PreToolUse hook exists")
    return True

# Test Case 2.4.2: Hook检测Write工具调用core/
def test_hook_detects_core_write():
    import subprocess

    # 模拟Claude调用Write工具修改core/文件
    env = os.environ.copy()
    env['TOOL_NAME'] = 'Write'
    env['FILE_PATH'] = '.claude/core/engine.py'

    result = subprocess.run(
        ['.claude/hooks/pre_tool_use.sh'],
        env=env,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("❌ FAIL: Hook didn't block Write to core/")
        return False

    if "BLOCKED" not in result.stdout:
        print("❌ FAIL: Hook didn't show BLOCKED message")
        return False

    print("✅ PASS: Hook blocked Write to core/")
    return True

# Test Case 2.4.3: Hook允许修改非core/文件
def test_hook_allows_non_core_write():
    import subprocess

    env = os.environ.copy()
    env['TOOL_NAME'] = 'Write'
    env['FILE_PATH'] = '.claude/features/test.py'

    result = subprocess.run(
        ['.claude/hooks/pre_tool_use.sh'],
        env=env,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ FAIL: Hook blocked write to features/")
        return False

    print("✅ PASS: Hook allows write to non-core files")
    return True
```

**预期结果**:
- ✅ Claude PreToolUse hook存在且可执行
- ✅ Hook阻止Claude Write工具修改core/文件
- ✅ Hook允许修改其他文件

---

## 3. Feature系统测试 (Feature System Tests)

### 3.1 Enable/Disable功能测试

**目标**: 验证Feature开关机制正常工作

**测试用例**:

```bash
# Test Case 3.1.1: Feature配置文件存在
test_feature_config_exists() {
    if [ ! -f .claude/features/config.yaml ]; then
        echo "❌ FAIL: Feature config file missing"
        return 1
    fi

    echo "✅ PASS: Feature config exists"
    return 0
}

# Test Case 3.1.2: 禁用Feature
test_disable_feature() {
    # 禁用某个feature
    python3 - <<EOF
import yaml
with open('.claude/features/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['features']['example_feature']['enabled'] = False

with open('.claude/features/config.yaml', 'w') as f:
    yaml.dump(config, f)

print("Feature disabled")
EOF

    # 验证配置
    if ! python3 -c "import yaml; c = yaml.safe_load(open('.claude/features/config.yaml')); assert c['features']['example_feature']['enabled'] == False"; then
        echo "❌ FAIL: Failed to disable feature"
        return 1
    fi

    echo "✅ PASS: Feature disabled successfully"
    return 0
}

# Test Case 3.1.3: 启用Feature
test_enable_feature() {
    python3 - <<EOF
import yaml
with open('.claude/features/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

config['features']['example_feature']['enabled'] = True

with open('.claude/features/config.yaml', 'w') as f:
    yaml.dump(config, f)

print("Feature enabled")
EOF

    if ! python3 -c "import yaml; c = yaml.safe_load(open('.claude/features/config.yaml')); assert c['features']['example_feature']['enabled'] == True"; then
        echo "❌ FAIL: Failed to enable feature"
        return 1
    fi

    echo "✅ PASS: Feature enabled successfully"
    return 0
}
```

**预期结果**:
- ✅ Feature配置文件存在且语法正确
- ✅ 可以通过配置禁用Feature
- ✅ 可以通过配置启用Feature

---

### 3.2 功能加载测试

**目标**: 验证禁用的Feature不会被加载

**测试用例**:

```python
# Test Case 3.2.1: 禁用Feature不加载
def test_disabled_feature_not_loaded():
    import sys
    sys.path.insert(0, '.claude')
    from core import loader

    # 禁用test_feature
    import yaml
    with open('.claude/features/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    config['features']['test_feature'] = {'enabled': False}

    with open('.claude/features/config.yaml', 'w') as f:
        yaml.dump(config, f)

    # 加载features
    features = loader.load_features()

    if 'test_feature' in features:
        print("❌ FAIL: Disabled feature was loaded")
        return False

    print("✅ PASS: Disabled feature not loaded")
    return True

# Test Case 3.2.2: 启用Feature正常加载
def test_enabled_feature_loaded():
    import sys
    sys.path.insert(0, '.claude')
    from core import loader

    # 启用test_feature
    import yaml
    with open('.claude/features/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    config['features']['test_feature'] = {'enabled': True}

    with open('.claude/features/config.yaml', 'w') as f:
        yaml.dump(config, f)

    # 加载features
    features = loader.load_features()

    if 'test_feature' not in features:
        print("❌ FAIL: Enabled feature was not loaded")
        return False

    print("✅ PASS: Enabled feature loaded")
    return True

# Test Case 3.2.3: 加载性能测试
def test_feature_loading_performance():
    import sys
    import time
    sys.path.insert(0, '.claude')
    from core import loader

    start = time.perf_counter()
    features = loader.load_features()
    elapsed = time.perf_counter() - start

    # 加载时间应小于100ms
    if elapsed > 0.1:
        print(f"❌ FAIL: Feature loading too slow: {elapsed*1000:.2f}ms")
        return False

    print(f"✅ PASS: Feature loading fast: {elapsed*1000:.2f}ms")
    return True
```

**预期结果**:
- ✅ 禁用的Feature不会被加载到内存
- ✅ 启用的Feature正常加载
- ✅ Feature加载时间<100ms

---

### 3.3 依赖检查测试

**目标**: 验证Feature依赖关系正确处理

**测试用例**:

```python
# Test Case 3.3.1: 检测缺失依赖
def test_missing_dependency_detection():
    import sys
    sys.path.insert(0, '.claude')
    from core import loader

    # 创建有依赖的feature配置
    import yaml
    config = {
        'features': {
            'feature_a': {
                'enabled': True,
                'depends_on': ['feature_b']  # feature_b不存在
            }
        }
    }

    with open('.claude/features/config.yaml', 'w') as f:
        yaml.dump(config, f)

    try:
        features = loader.load_features()
        print("❌ FAIL: Missing dependency not detected")
        return False
    except loader.DependencyError:
        print("✅ PASS: Missing dependency detected")
        return True

# Test Case 3.3.2: 检测循环依赖
def test_circular_dependency_detection():
    import sys
    sys.path.insert(0, '.claude')
    from core import loader

    # 创建循环依赖
    config = {
        'features': {
            'feature_a': {
                'enabled': True,
                'depends_on': ['feature_b']
            },
            'feature_b': {
                'enabled': True,
                'depends_on': ['feature_a']  # 循环依赖
            }
        }
    }

    with open('.claude/features/config.yaml', 'w') as f:
        yaml.dump(config, f)

    try:
        features = loader.load_features()
        print("❌ FAIL: Circular dependency not detected")
        return False
    except loader.CircularDependencyError:
        print("✅ PASS: Circular dependency detected")
        return True

# Test Case 3.3.3: 依赖顺序加载
def test_dependency_order():
    import sys
    sys.path.insert(0, '.claude')
    from core import loader

    config = {
        'features': {
            'feature_a': {
                'enabled': True,
                'depends_on': ['feature_b']
            },
            'feature_b': {
                'enabled': True,
                'depends_on': []
            }
        }
    }

    with open('.claude/features/config.yaml', 'w') as f:
        yaml.dump(config, f)

    features = loader.load_features()
    load_order = list(features.keys())

    # feature_b应该在feature_a之前加载
    if load_order.index('feature_b') > load_order.index('feature_a'):
        print("❌ FAIL: Dependencies not loaded in order")
        return False

    print("✅ PASS: Dependencies loaded in correct order")
    return True
```

**预期结果**:
- ✅ 缺失依赖被检测并报错
- ✅ 循环依赖被检测并报错
- ✅ Feature按依赖顺序加载

---

## 4. Hook增强测试 (Hook Enhancement Tests)

### 4.1 "继续"绕过防护测试

**目标**: 验证5层检测机制防止用户使用"继续"绕过workflow

**测试场景**:

```bash
# Test Case 4.1.1: 检测"继续"关键词
test_detect_continue_keyword() {
    # 模拟用户输入"继续"
    export USER_INPUT="继续"

    # 调用hook
    if .claude/hooks/workflow_guard.sh 2>&1 | grep -q "BLOCKED.*继续"; then
        echo "✅ PASS: '继续' keyword detected and blocked"
        return 0
    else
        echo "❌ FAIL: '继续' keyword not blocked"
        return 1
    fi
}

# Test Case 4.1.2: 检测"continue"关键词
test_detect_continue_english() {
    export USER_INPUT="continue with the task"

    if .claude/hooks/workflow_guard.sh 2>&1 | grep -q "BLOCKED"; then
        echo "✅ PASS: 'continue' keyword detected and blocked"
        return 0
    else
        echo "❌ FAIL: 'continue' keyword not blocked"
        return 1
    fi
}

# Test Case 4.1.3: 检测其他绕过词（"跳过"、"skip"等）
test_detect_bypass_keywords() {
    local bypass_words=("跳过" "skip" "忽略" "ignore" "直接" "直接做")

    for word in "${bypass_words[@]}"; do
        export USER_INPUT="$word this step"

        if ! .claude/hooks/workflow_guard.sh 2>&1 | grep -q "BLOCKED"; then
            echo "❌ FAIL: Bypass word '$word' not blocked"
            return 1
        fi
    done

    echo "✅ PASS: All bypass keywords detected and blocked"
    return 0
}

# Test Case 4.1.4: 允许正常的"continue"用法（如循环）
test_allow_legitimate_continue() {
    export USER_INPUT="Use continue statement in loop"
    export CONTEXT="code_discussion"

    if .claude/hooks/workflow_guard.sh 2>&1 | grep -q "BLOCKED"; then
        echo "❌ FAIL: Legitimate 'continue' blocked"
        return 1
    else
        echo "✅ PASS: Legitimate 'continue' allowed"
        return 0
    fi
}
```

**5层检测机制**:

```
Layer 1: 关键词检测（继续、continue、跳过、skip、忽略、ignore）
    ↓
Layer 2: 上下文分析（是否在执行模式？是否在Phase中？）
    ↓
Layer 3: Phase状态检查（当前Phase是否完成？）
    ↓
Layer 4: 历史记录检查（是否连续使用"继续"？）
    ↓
Layer 5: 智能判断（AI是否理解任务？是否有PLAN.md？）
```

**预期结果**:
- ✅ "继续"、"continue"等绕过词被检测
- ✅ 5层检测全部通过才允许继续
- ✅ 正常代码讨论中的"continue"不被误判

---

### 4.2 Phase状态检查测试

**目标**: 验证Hook检查Phase状态，防止跳过Phase

**测试用例**:

```bash
# Test Case 4.2.1: P1未完成不能进入P2
test_phase_order_enforcement() {
    # 设置当前Phase为P0（未完成P1）
    echo '{"current_phase": "P0", "p1_complete": false}' > .workflow/state.json

    # 尝试进入P2
    export NEXT_PHASE="P2"

    if .claude/hooks/phase_guard.sh 2>&1 | grep -q "BLOCKED.*P1.*not.*complete"; then
        echo "✅ PASS: Phase order enforced"
        return 0
    else
        echo "❌ FAIL: Phase order not enforced"
        return 1
    fi
}

# Test Case 4.2.2: Phase完成标记检查
test_phase_completion_marker() {
    # 检查PLAN.md是否存在（P1完成标记）
    rm -f docs/PLAN.md
    echo '{"current_phase": "P1", "p1_complete": true}' > .workflow/state.json

    if .claude/hooks/phase_guard.sh 2>&1 | grep -q "WARNING.*PLAN.md.*missing"; then
        echo "✅ PASS: Phase completion marker checked"
        return 0
    else
        echo "❌ FAIL: Phase completion marker not checked"
        return 1
    fi
}

# Test Case 4.2.3: Phase状态回溯检测
test_phase_rollback_detection() {
    # 从P3回到P1（可疑行为）
    echo '{"current_phase": "P3", "history": ["P1", "P2", "P3"]}' > .workflow/state.json

    export NEXT_PHASE="P1"

    if .claude/hooks/phase_guard.sh 2>&1 | grep -q "WARNING.*rollback"; then
        echo "✅ PASS: Phase rollback detected"
        return 0
    else
        echo "❌ FAIL: Phase rollback not detected"
        return 1
    fi
}
```

**预期结果**:
- ✅ Phase必须按顺序执行（P0→P1→P2→...）
- ✅ 每个Phase的完成标记被检查
- ✅ 异常的Phase回溯被检测并告警

---

### 4.3 分支状态检查测试

**目标**: 验证Hook检查分支状态（参考规则0）

**测试用例**:

```bash
# Test Case 4.3.1: main分支禁止直接开发
test_main_branch_protection() {
    # 切换到main分支
    git checkout main 2>/dev/null || git checkout -b main

    # 尝试修改文件
    echo "# test" >> test_file.txt
    git add test_file.txt

    if git commit -m "test" 2>&1 | grep -q "BLOCKED.*main"; then
        echo "✅ PASS: Main branch protected"
        git reset HEAD test_file.txt
        rm test_file.txt
        return 0
    else
        echo "❌ FAIL: Main branch not protected"
        git reset HEAD test_file.txt
        rm test_file.txt
        return 1
    fi
}

# Test Case 4.3.2: Feature分支主题匹配检查
test_feature_branch_topic_match() {
    # 在feature/user-auth分支上开发支付功能（不匹配）
    git checkout -b feature/user-auth 2>/dev/null

    export TASK_DESCRIPTION="实现支付系统"

    if .claude/hooks/branch_helper.sh 2>&1 | grep -q "WARNING.*topic.*mismatch"; then
        echo "✅ PASS: Branch topic mismatch detected"
        git checkout feature/architecture-v2.0
        git branch -D feature/user-auth
        return 0
    else
        echo "❌ FAIL: Branch topic mismatch not detected"
        git checkout feature/architecture-v2.0
        git branch -D feature/user-auth
        return 1
    fi
}

# Test Case 4.3.3: 建议创建新分支
test_suggest_new_branch() {
    git checkout main

    export TASK_DESCRIPTION="新功能：实时通知系统"

    if .claude/hooks/branch_helper.sh 2>&1 | grep -q "SUGGEST.*feature/real-time-notification"; then
        echo "✅ PASS: New branch suggested"
        return 0
    else
        echo "❌ FAIL: New branch not suggested"
        return 1
    fi
}
```

**预期结果**:
- ✅ main/master分支禁止直接开发
- ✅ Feature分支主题与任务不匹配时告警
- ✅ 新任务建议创建新分支

---

### 4.4 5层检测全覆盖测试

**目标**: 验证5层检测机制全部工作

**综合测试场景**:

```bash
# Test Case 4.4.1: 全部5层都触发
test_all_5_layers_trigger() {
    local test_case="用户说'继续'且在main分支且P1未完成且无PLAN.md且连续3次使用'继续'"

    # 设置环境
    git checkout main
    export USER_INPUT="继续"
    echo '{"current_phase": "P1", "p1_complete": false, "continue_count": 3}' > .workflow/state.json
    rm -f docs/PLAN.md

    # 运行hook
    local output=$(.claude/hooks/comprehensive_guard.sh 2>&1)

    # 检查所有5层是否触发
    local layers_triggered=0

    echo "$output" | grep -q "Layer 1.*BLOCKED.*keyword" && layers_triggered=$((layers_triggered + 1))
    echo "$output" | grep -q "Layer 2.*BLOCKED.*main.*branch" && layers_triggered=$((layers_triggered + 1))
    echo "$output" | grep -q "Layer 3.*BLOCKED.*P1.*incomplete" && layers_triggered=$((layers_triggered + 1))
    echo "$output" | grep -q "Layer 4.*BLOCKED.*continue.*repeated" && layers_triggered=$((layers_triggered + 1))
    echo "$output" | grep -q "Layer 5.*BLOCKED.*PLAN.md.*missing" && layers_triggered=$((layers_triggered + 1))

    if [ $layers_triggered -eq 5 ]; then
        echo "✅ PASS: All 5 layers triggered"
        git checkout feature/architecture-v2.0
        return 0
    else
        echo "❌ FAIL: Only $layers_triggered/5 layers triggered"
        git checkout feature/architecture-v2.0
        return 1
    fi
}

# Test Case 4.4.2: 正常流程所有层都通过
test_all_5_layers_pass() {
    # 设置正常环境
    git checkout -b feature/new-feature
    export USER_INPUT="开始实现用户认证功能"
    echo '{"current_phase": "P1", "p1_complete": true}' > .workflow/state.json
    echo "# PLAN" > docs/PLAN.md

    local output=$(.claude/hooks/comprehensive_guard.sh 2>&1)

    if echo "$output" | grep -q "BLOCKED"; then
        echo "❌ FAIL: Normal flow blocked"
        git checkout feature/architecture-v2.0
        git branch -D feature/new-feature
        return 1
    else
        echo "✅ PASS: All 5 layers passed for normal flow"
        git checkout feature/architecture-v2.0
        git branch -D feature/new-feature
        return 0
    fi
}

# Test Case 4.4.3: 性能测试（5层检测<50ms）
test_5_layer_performance() {
    local start=$(date +%s%N)

    .claude/hooks/comprehensive_guard.sh >/dev/null 2>&1

    local end=$(date +%s%N)
    local elapsed=$(( (end - start) / 1000000 ))  # 转换为毫秒

    if [ $elapsed -gt 50 ]; then
        echo "❌ FAIL: 5-layer check too slow: ${elapsed}ms"
        return 1
    else
        echo "✅ PASS: 5-layer check fast: ${elapsed}ms"
        return 0
    fi
}
```

**预期结果**:
- ✅ 5层检测全部触发并正确工作
- ✅ 正常流程不被误判
- ✅ 5层检测总耗时<50ms

---

## 5. 兼容性测试 (Compatibility Tests)

### 5.1 旧命令支持测试

**目标**: 确保旧的命令和导入语句继续工作

**测试用例**:

```python
# Test Case 5.1.1: 旧的import路径仍然工作
def test_legacy_import_works():
    import sys
    sys.path.insert(0, '.claude')

    try:
        # 旧路径（通过软链接）
        import engine
        import orchestrator

        print("✅ PASS: Legacy imports work via symlinks")
        return True
    except ImportError as e:
        print(f"❌ FAIL: Legacy import failed: {e}")
        return False

# Test Case 5.1.2: 旧的配置路径仍然工作
def test_legacy_config_path():
    import os

    # 旧路径应该通过软链接指向新路径
    if not os.path.exists('.claude/config.yaml'):
        print("❌ FAIL: Legacy config path not available")
        return False

    # 应该指向core/config.yaml
    if os.path.islink('.claude/config.yaml'):
        target = os.readlink('.claude/config.yaml')
        if 'core/config.yaml' in target:
            print("✅ PASS: Legacy config path redirects correctly")
            return True

    print("❌ FAIL: Legacy config path not a symlink to core/")
    return False

# Test Case 5.1.3: 旧的CLI命令仍然工作
def test_legacy_cli_commands():
    import subprocess

    # 测试旧命令（如果有wrapper脚本）
    old_commands = [
        '.claude/run_workflow.sh',
        '.claude/select_agents.sh'
    ]

    for cmd in old_commands:
        if os.path.exists(cmd):
            result = subprocess.run([cmd, '--help'], capture_output=True)
            if result.returncode != 0:
                print(f"❌ FAIL: Legacy command failed: {cmd}")
                return False

    print("✅ PASS: Legacy CLI commands work")
    return True
```

**预期结果**:
- ✅ 旧的import语句通过软链接继续工作
- ✅ 旧的配置文件路径通过软链接可访问
- ✅ 旧的CLI命令通过wrapper脚本继续工作

---

### 5.2 Workflow兼容性测试

**目标**: 确保P0-P7 workflow流程不受影响

**测试用例**:

```bash
# Test Case 5.2.1: P0-P7 workflow可以完整执行
test_full_workflow_execution() {
    # 创建测试分支
    git checkout -b test/workflow-compat

    # 执行完整workflow（模拟）
    local phases=("P0" "P1" "P2" "P3" "P4" "P5" "P6" "P7")

    for phase in "${phases[@]}"; do
        if ! .workflow/executor.sh --phase "$phase" --dry-run 2>/dev/null; then
            echo "❌ FAIL: Phase $phase execution failed"
            git checkout feature/architecture-v2.0
            git branch -D test/workflow-compat
            return 1
        fi
    done

    echo "✅ PASS: Full P0-P7 workflow executed successfully"
    git checkout feature/architecture-v2.0
    git branch -D test/workflow-compat
    return 0
}

# Test Case 5.2.2: Workflow状态文件格式兼容
test_workflow_state_format() {
    # 检查旧格式状态文件是否能读取
    cat > .workflow/state.json.old <<EOF
{
    "current_phase": "P3",
    "phases_completed": ["P0", "P1", "P2"]
}
EOF

    # 尝试读取
    if ! python3 -c "import json; s = json.load(open('.workflow/state.json.old')); assert 'current_phase' in s"; then
        echo "❌ FAIL: Old state format not compatible"
        return 1
    fi

    echo "✅ PASS: Old workflow state format compatible"
    rm .workflow/state.json.old
    return 0
}

# Test Case 5.2.3: Agent选择逻辑兼容
test_agent_selection_compatibility() {
    # 测试旧的Agent选择方式
    export TASK_DESCRIPTION="实现用户认证"

    # 调用Agent选择器
    local agents=$(.claude/hooks/smart_agent_selector.sh)

    # 应该返回至少4个Agent
    local agent_count=$(echo "$agents" | jq '. | length')

    if [ "$agent_count" -lt 4 ]; then
        echo "❌ FAIL: Agent selection returned too few agents: $agent_count"
        return 1
    fi

    echo "✅ PASS: Agent selection compatible, returned $agent_count agents"
    return 0
}
```

**预期结果**:
- ✅ P0-P7 workflow完整执行无错误
- ✅ 旧的workflow状态文件格式仍然可读
- ✅ Agent选择逻辑返回正确数量的Agents

---

### 5.3 配置兼容性测试

**目标**: 确保旧的配置文件可以迁移或兼容

**测试用例**:

```python
# Test Case 5.3.1: 旧配置文件自动迁移
def test_config_migration():
    import yaml
    import os

    # 创建旧格式配置
    old_config = {
        'system': {
            'version': '1.0',
            'core': {
                'engine': 'lazy_orchestrator'
            }
        }
    }

    with open('.claude/config.yaml.old', 'w') as f:
        yaml.dump(old_config, f)

    # 运行迁移工具
    import subprocess
    result = subprocess.run(
        ['python3', '.claude/config/migration_tool.py',
         '--input', '.claude/config.yaml.old',
         '--output', '.claude/core/config.yaml.new'],
        capture_output=True
    )

    if result.returncode != 0:
        print("❌ FAIL: Config migration failed")
        return False

    # 验证新配置
    with open('.claude/core/config.yaml.new', 'r') as f:
        new_config = yaml.safe_load(f)

    if 'core' not in new_config or 'framework' not in new_config:
        print("❌ FAIL: New config format incorrect")
        return False

    print("✅ PASS: Config migrated successfully")
    os.remove('.claude/config.yaml.old')
    os.remove('.claude/core/config.yaml.new')
    return True

# Test Case 5.3.2: 配置向后兼容
def test_config_backward_compatibility():
    import yaml

    # 新配置应该包含旧字段的映射
    with open('.claude/core/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 检查兼容性映射
    if 'compatibility' not in config:
        print("⚠️  WARNING: No compatibility section in config")

    # 检查关键配置项
    required_keys = ['core', 'framework', 'services', 'features']
    for key in required_keys:
        if key not in config:
            print(f"❌ FAIL: Missing required config key: {key}")
            return False

    print("✅ PASS: Config has backward compatibility")
    return True

# Test Case 5.3.3: 环境变量兼容
def test_environment_variable_compatibility():
    import os

    # 旧环境变量应该仍然被识别
    old_env_vars = {
        'CLAUDE_ENHANCER_ROOT': '.claude',
        'CLAUDE_CONFIG_PATH': '.claude/config.yaml'
    }

    for var, value in old_env_vars.items():
        os.environ[var] = value

    # 验证能被读取
    import sys
    sys.path.insert(0, '.claude/core')
    try:
        import loader
        # loader应该能读取旧环境变量
        print("✅ PASS: Old environment variables compatible")
        return True
    except Exception as e:
        print(f"❌ FAIL: Environment variable compatibility issue: {e}")
        return False
```

**预期结果**:
- ✅ 旧配置文件可以自动迁移到新格式
- ✅ 新配置保持向后兼容性
- ✅ 旧的环境变量仍然被识别

---

## 6. 性能测试 (Performance Tests)

### 6.1 启动时间测试

**目标**: 确保系统启动时间<200ms

**测试用例**:

```python
# Test Case 6.1.1: 冷启动时间
def test_cold_start_time():
    import subprocess
    import time

    # 清除缓存
    subprocess.run(['rm', '-rf', '.claude/cache/*'], shell=True)
    subprocess.run(['rm', '-rf', '.claude/__pycache__'], shell=True)
    subprocess.run(['rm', '-rf', '.claude/core/__pycache__'], shell=True)

    # 测量冷启动时间
    start = time.perf_counter()

    result = subprocess.run(
        ['python3', '-c', 'import sys; sys.path.insert(0, ".claude/core"); from lazy_orchestrator import LazyOrchestrator; o = LazyOrchestrator()'],
        capture_output=True
    )

    elapsed = (time.perf_counter() - start) * 1000  # 转换为毫秒

    if result.returncode != 0:
        print(f"❌ FAIL: Import failed: {result.stderr.decode()}")
        return False

    if elapsed > 200:
        print(f"❌ FAIL: Cold start too slow: {elapsed:.2f}ms")
        return False

    print(f"✅ PASS: Cold start time: {elapsed:.2f}ms")
    return True

# Test Case 6.1.2: 热启动时间
def test_warm_start_time():
    import time
    import sys
    sys.path.insert(0, '.claude/core')

    # 第一次加载（预热）
    from lazy_orchestrator import LazyOrchestrator
    _ = LazyOrchestrator()

    # 测量热启动时间
    start = time.perf_counter()
    orchestrator = LazyOrchestrator()
    elapsed = (time.perf_counter() - start) * 1000

    # 热启动应该更快，<100ms
    if elapsed > 100:
        print(f"❌ FAIL: Warm start too slow: {elapsed:.2f}ms")
        return False

    print(f"✅ PASS: Warm start time: {elapsed:.2f}ms")
    return True

# Test Case 6.1.3: Feature加载时间
def test_feature_loading_time():
    import time
    import sys
    sys.path.insert(0, '.claude/core')
    from loader import load_features

    start = time.perf_counter()
    features = load_features()
    elapsed = (time.perf_counter() - start) * 1000

    # Feature加载应该<100ms
    if elapsed > 100:
        print(f"❌ FAIL: Feature loading too slow: {elapsed:.2f}ms")
        return False

    print(f"✅ PASS: Feature loading time: {elapsed:.2f}ms, loaded {len(features)} features")
    return True
```

**性能基准**:
- 冷启动时间: <200ms
- 热启动时间: <100ms
- Feature加载: <100ms

**预期结果**:
- ✅ 冷启动时间符合基准
- ✅ 热启动时间更快
- ✅ Feature加载不影响性能

---

### 6.2 锁定检查性能测试

**目标**: 确保锁定检查不拖慢commit流程

**测试用例**:

```bash
# Test Case 6.2.1: Hash验证性能
test_hash_verification_performance() {
    cd .claude/core

    local iterations=100
    local total_time=0

    for i in $(seq 1 $iterations); do
        local start=$(date +%s%N)
        sha256sum -c .integrity.sha256 --quiet >/dev/null 2>&1
        local end=$(date +%s%N)

        local elapsed=$(( (end - start) / 1000000 ))  # 毫秒
        total_time=$((total_time + elapsed))
    done

    local avg_time=$((total_time / iterations))

    if [ $avg_time -gt 50 ]; then
        echo "❌ FAIL: Hash verification too slow: ${avg_time}ms average"
        return 1
    else
        echo "✅ PASS: Hash verification fast: ${avg_time}ms average"
        return 0
    fi
}

# Test Case 6.2.2: Pre-commit hook性能
test_precommit_hook_performance() {
    # 创建测试提交
    echo "# test" >> .claude/tests/test_perf.py
    git add .claude/tests/test_perf.py

    # 测量hook执行时间
    local start=$(date +%s%N)

    # 运行hook（不实际提交）
    .git/hooks/pre-commit >/dev/null 2>&1
    local hook_result=$?

    local end=$(date +%s%N)
    local elapsed=$(( (end - start) / 1000000 ))

    # 清理
    git reset HEAD .claude/tests/test_perf.py
    git checkout -- .claude/tests/test_perf.py

    # Hook执行应该<3秒
    if [ $elapsed -gt 3000 ]; then
        echo "❌ FAIL: Pre-commit hook too slow: ${elapsed}ms"
        return 1
    else
        echo "✅ PASS: Pre-commit hook fast: ${elapsed}ms"
        return 0
    fi
}

# Test Case 6.2.3: Claude hook性能
test_claude_hook_performance() {
    export TOOL_NAME="Write"
    export FILE_PATH=".claude/features/test.py"

    local start=$(date +%s%N)
    .claude/hooks/pre_tool_use.sh >/dev/null 2>&1
    local end=$(date +%s%N)

    local elapsed=$(( (end - start) / 1000000 ))

    # Claude hook应该<100ms
    if [ $elapsed -gt 100 ]; then
        echo "❌ FAIL: Claude hook too slow: ${elapsed}ms"
        return 1
    else
        echo "✅ PASS: Claude hook fast: ${elapsed}ms"
        return 0
    fi
}
```

**性能基准**:
- Hash验证: <50ms
- Pre-commit hook: <3s
- Claude hook: <100ms

**预期结果**:
- ✅ Hash验证快速（<50ms）
- ✅ Pre-commit hook不阻塞工作流
- ✅ Claude hook响应迅速

---

### 6.3 Commit性能测试

**目标**: 确保整个commit流程（包括所有检查）<3秒

**测试用例**:

```bash
# Test Case 6.3.1: 正常commit性能
test_normal_commit_performance() {
    # 创建测试文件
    echo "def test(): pass" > .claude/tests/test_commit_perf.py
    git add .claude/tests/test_commit_perf.py

    # 测量完整commit时间
    local start=$(date +%s%N)

    if ! git commit -m "test: commit performance test" >/dev/null 2>&1; then
        echo "❌ FAIL: Commit failed"
        return 1
    fi

    local end=$(date +%s%N)
    local elapsed=$(( (end - start) / 1000000 ))

    # 撤销commit
    git reset --soft HEAD~1
    git reset HEAD .claude/tests/test_commit_perf.py
    rm .claude/tests/test_commit_perf.py

    # Commit应该<3秒
    if [ $elapsed -gt 3000 ]; then
        echo "❌ FAIL: Commit too slow: ${elapsed}ms"
        return 1
    else
        echo "✅ PASS: Commit fast: ${elapsed}ms"
        return 0
    fi
}

# Test Case 6.3.2: 大量文件commit性能
test_bulk_commit_performance() {
    # 创建10个文件
    for i in $(seq 1 10); do
        echo "def test_$i(): pass" > .claude/tests/test_bulk_$i.py
        git add .claude/tests/test_bulk_$i.py
    done

    local start=$(date +%s%N)
    git commit -m "test: bulk commit" >/dev/null 2>&1
    local end=$(date +%s%N)
    local elapsed=$(( (end - start) / 1000000 ))

    # 撤销
    git reset --soft HEAD~1
    git reset HEAD .claude/tests/test_bulk_*.py
    rm .claude/tests/test_bulk_*.py

    # 大量文件commit应该<5秒
    if [ $elapsed -gt 5000 ]; then
        echo "❌ FAIL: Bulk commit too slow: ${elapsed}ms"
        return 1
    else
        echo "✅ PASS: Bulk commit fast: ${elapsed}ms"
        return 0
    fi
}

# Test Case 6.3.3: Commit with hooks disabled性能对比
test_commit_without_hooks() {
    echo "def test(): pass" > .claude/tests/test_no_hooks.py
    git add .claude/tests/test_no_hooks.py

    # 禁用hooks
    local start=$(date +%s%N)
    git commit --no-verify -m "test: no hooks" >/dev/null 2>&1
    local end=$(date +%s%N)
    local no_hooks_time=$(( (end - start) / 1000000 ))

    # 撤销
    git reset --soft HEAD~1
    git reset HEAD .claude/tests/test_no_hooks.py

    # 启用hooks
    git add .claude/tests/test_no_hooks.py
    start=$(date +%s%N)
    git commit -m "test: with hooks" >/dev/null 2>&1
    end=$(date +%s%N)
    local with_hooks_time=$(( (end - start) / 1000000 ))

    # 撤销
    git reset --soft HEAD~1
    git reset HEAD .claude/tests/test_no_hooks.py
    rm .claude/tests/test_no_hooks.py

    # 计算hooks开销
    local overhead=$((with_hooks_time - no_hooks_time))

    echo "📊 Commit performance:"
    echo "   Without hooks: ${no_hooks_time}ms"
    echo "   With hooks: ${with_hooks_time}ms"
    echo "   Overhead: ${overhead}ms"

    # Hooks开销应该<1秒
    if [ $overhead -gt 1000 ]; then
        echo "❌ FAIL: Hooks overhead too high: ${overhead}ms"
        return 1
    else
        echo "✅ PASS: Hooks overhead acceptable: ${overhead}ms"
        return 0
    fi
}
```

**性能基准**:
- 正常commit: <3s
- 批量文件commit: <5s
- Hooks开销: <1s

**预期结果**:
- ✅ Commit流程快速完成
- ✅ 大量文件不显著影响性能
- ✅ Hooks开销可接受

---

## 📊 测试执行计划

### 测试阶段

```
Phase 1: 迁移验证 (30min)
├─ 1.1 核心文件迁移测试 (10min)
├─ 1.2 文件完整性测试 (10min)
└─ 1.3 软链接验证测试 (10min)

Phase 2: 锁定机制验证 (50min)
├─ 2.1 修改阻止测试 (15min)
├─ 2.2 Hash验证测试 (15min)
├─ 2.3 Git hook测试 (10min)
└─ 2.4 Claude hook测试 (10min)

Phase 3: Feature系统验证 (50min)
├─ 3.1 Enable/Disable测试 (20min)
├─ 3.2 功能加载测试 (15min)
└─ 3.3 依赖检查测试 (15min)

Phase 4: Hook增强验证 (70min)
├─ 4.1 "继续"绕过防护 (20min)
├─ 4.2 Phase状态检查 (15min)
├─ 4.3 分支状态检查 (15min)
└─ 4.4 5层检测全覆盖 (20min)

Phase 5: 兼容性验证 (50min)
├─ 5.1 旧命令支持测试 (20min)
├─ 5.2 Workflow兼容测试 (20min)
└─ 5.3 配置兼容测试 (10min)

Phase 6: 性能验证 (40min)
├─ 6.1 启动时间测试 (15min)
├─ 6.2 锁定检查性能 (15min)
└─ 6.3 Commit性能测试 (10min)

总计: 290分钟 (~5小时)
```

### 执行策略

1. **串行执行**（默认）:
   ```bash
   ./test/架构v2.0/run_all_tests.sh
   ```

2. **并行执行**（快速模式）:
   ```bash
   ./test/架构v2.0/run_all_tests.sh --parallel
   ```
   预计耗时: ~2小时

3. **按阶段执行**:
   ```bash
   ./test/架构v2.0/run_tests.sh --phase migration
   ./test/架构v2.0/run_tests.sh --phase locking
   # ... 依次执行
   ```

---

## 📈 测试数据和预期结果

### 测试数据准备

```bash
test/架构v2.0/
├── data/
│   ├── sample_core_files/        # 测试用核心文件
│   ├── sample_features/          # 测试用Feature
│   ├── sample_configs/           # 测试用配置
│   └── integrity_hashes/         # 测试用Hash文件
├── fixtures/
│   ├── mock_workflow_state.json  # Mock workflow状态
│   ├── mock_git_status.txt       # Mock git状态
│   └── mock_user_inputs.txt      # Mock用户输入
└── expected/
    ├── migration_results.json    # 预期迁移结果
    ├── locking_behaviors.json    # 预期锁定行为
    └── performance_benchmarks.json # 预期性能指标
```

### 预期结果总览

| 测试类别 | 总用例数 | 预期通过率 | 关键指标 |
|---------|---------|-----------|---------|
| 迁移正确性 | 9 | 100% | 4个核心文件迁移成功 |
| 锁定机制 | 12 | 100% | core/文件100%保护 |
| Feature系统 | 9 | 100% | Enable/Disable工作 |
| Hook增强 | 12 | 100% | 5层检测全覆盖 |
| 兼容性 | 9 | 100% | 旧命令100%兼容 |
| 性能 | 9 | 100% | 启动<200ms, Commit<3s |
| **总计** | **60** | **100%** | **零回归** |

---

## 🚀 快速开始

### 安装依赖

```bash
# Python依赖
pip install pytest pytest-cov pyyaml psutil

# Bash测试框架
brew install bats-core  # macOS
apt-get install bats    # Ubuntu
```

### 运行测试

```bash
# 1. 快速验证（核心测试，15分钟）
./test/架构v2.0/quick_test.sh

# 2. 完整测试套件（5小时）
./test/架构v2.0/run_all_tests.sh

# 3. 生成测试报告
./test/架构v2.0/run_all_tests.sh --report

# 4. CI模式（并行执行，2小时）
./test/架构v2.0/run_all_tests.sh --ci
```

### 查看测试报告

```bash
# HTML报告
open test/架构v2.0/reports/test_report.html

# Markdown报告
cat test/架构v2.0/reports/test_report.md

# JSON结果
jq . test/架构v2.0/reports/test_results.json
```

---

## ✅ 验收标准

### 必须达成 (P0)

- [ ] 所有60个测试用例通过率100%
- [ ] 4个核心文件成功迁移到core/
- [ ] 锁定机制100%阻止修改core/
- [ ] 5层检测机制全部工作
- [ ] 旧命令100%兼容
- [ ] 启动时间<200ms
- [ ] Commit时间<3s

### 建议达成 (P1)

- [ ] 测试覆盖率>90%
- [ ] 性能无退化（与v1.0对比）
- [ ] 文档完整性100%
- [ ] CI集成完成

### 可选优化 (P2)

- [ ] 性能提升>10%
- [ ] 测试执行时间<2小时（并行）
- [ ] 自动化回归测试

---

## 📞 联系与支持

**测试工程师**: Test Engineer Professional
**分支**: feature/architecture-v2.0
**文档版本**: v1.0
**最后更新**: 2025-10-14

---

*本测试计划遵循Test Engineer专业标准，确保架构v2.0迁移的零回归和高质量交付。*
