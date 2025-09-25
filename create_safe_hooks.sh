#!/bin/bash
# Claude Enhancer 安全Hook重建脚本
# 创建安全、简洁的Hook替代方案

set -e

HOOKS_DIR="/home/xx/dev/Claude_Enhancer/.claude/hooks"
LOG_FILE="/tmp/safe_hooks_creation_$(date +%Y%m%d_%H%M%S).log"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

create_quality_gate_hook() {
    log "🛡️ 创建质量门禁Hook..."
    
    cat > "$HOOKS_DIR/quality_gate.sh" << 'QUALITY_GATE'
#!/bin/bash
# Claude Enhancer 质量门禁 - 安全的质量检查

set -e

# 读取输入
INPUT=$(cat)

# 检查基本质量标准
check_quality() {
    local task="$1"
    local warnings=()
    local score=100
    
    # 1. 检查任务描述长度
    if [ ${#task} -lt 10 ]; then
        warnings+=("⚠️ 任务描述过短 (${#task}字符)")
        ((score-=10))
    fi
    
    # 2. 检查是否包含基本信息
    if ! echo "$task" | grep -qE "(实现|修复|优化|测试|部署)"; then
        warnings+=("💡 建议包含明确的动作词")
        ((score-=5))
    fi
    
    # 3. 安全检查 - 禁止危险操作
    if echo "$task" | grep -qE "(删除全部|rm -rf|格式化|destroy)"; then
        warnings+=("🚨 检测到潜在危险操作")
        ((score-=50))
    fi
    
    # 输出质量报告
    echo "🎯 质量评分: ${score}/100" >&2
    
    if [ ${#warnings[@]} -gt 0 ]; then
        echo "📋 质量建议:" >&2
        printf "  %s\n" "${warnings[@]}" >&2
    fi
    
    if [ $score -ge 70 ]; then
        echo "✅ 质量检查通过" >&2
        return 0
    else
        echo "⚠️ 质量评分较低，建议优化" >&2
        return 0  # 不阻止执行，只给建议
    fi
}

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")

if [ -n "$TASK_DESC" ]; then
    check_quality "$TASK_DESC"
fi

# 输出原始输入（不修改）
echo "$INPUT"
exit 0
QUALITY_GATE

    chmod +x "$HOOKS_DIR/quality_gate.sh"
    log "✅ 质量门禁Hook创建完成"
}

create_workflow_advisor() {
    log "💼 创建工作流顾问Hook..."
    
    cat > "$HOOKS_DIR/workflow_advisor.sh" << 'WORKFLOW_ADVISOR'
#!/bin/bash
# Claude Enhancer 工作流顾问 - 友好的流程建议

set -e

# 读取输入
INPUT=$(cat)

# 工作流建议
provide_workflow_advice() {
    local task="$1"
    
    echo "💡 Claude Enhancer 工作流建议:" >&2
    echo "═══════════════════════════════════════════" >&2
    
    # 根据任务类型给出建议
    if echo "$task" | grep -qiE "bug|修复|fix"; then
        echo "🔧 Bug修复工作流:" >&2
        echo "  1. 📝 重现问题并记录" >&2  
        echo "  2. 🔍 根因分析" >&2
        echo "  3. 🛠️ 实施修复" >&2
        echo "  4. ✅ 测试验证" >&2
        echo "  5. 📚 更新文档" >&2
        
    elif echo "$task" | grep -qiE "feature|功能|新增"; then
        echo "🚀 新功能开发工作流:" >&2
        echo "  1. 📋 需求分析" >&2
        echo "  2. 🏗️ 架构设计" >&2  
        echo "  3. 💻 功能实现" >&2
        echo "  4. 🧪 测试验证" >&2
        echo "  5. 📖 文档更新" >&2
        echo "  6. 🚀 部署发布" >&2
        
    elif echo "$task" | grep -qiE "优化|性能|performance"; then
        echo "⚡ 性能优化工作流:" >&2
        echo "  1. 📊 性能基准测试" >&2
        echo "  2. 🔍 瓶颈识别" >&2
        echo "  3. 🛠️ 优化实施" >&2
        echo "  4. 📈 效果验证" >&2
        echo "  5. 📝 优化文档" >&2
        
    else
        echo "📋 通用开发工作流:" >&2
        echo "  1. 🎯 明确目标" >&2
        echo "  2. 📝 制定计划" >&2
        echo "  3. 🔨 执行实施" >&2
        echo "  4. ✅ 质量验证" >&2
        echo "  5. 📚 总结改进" >&2
    fi
    
    echo "" >&2
    echo "💎 Max 20X提醒: 质量优先，充分思考" >&2
    echo "═══════════════════════════════════════════" >&2
}

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")

if [ -n "$TASK_DESC" ]; then
    provide_workflow_advice "$TASK_DESC"
fi

# 输出原始输入（不修改）
echo "$INPUT"
exit 0
WORKFLOW_ADVISOR

    chmod +x "$HOOKS_DIR/workflow_advisor.sh"
    log "✅ 工作流顾问Hook创建完成"
}

create_security_checker() {
    log "🔒 创建安全检查Hook..."
    
    cat > "$HOOKS_DIR/security_checker.sh" << 'SECURITY_CHECKER'
#!/bin/bash
# Claude Enhancer 安全检查器 - 检查潜在安全风险

set -e

# 读取输入
INPUT=$(cat)

# 安全检查
check_security() {
    local task="$1"
    local alerts=()
    
    # 检查危险操作
    if echo "$task" | grep -qiE "(rm -rf|删除|格式化|destroy|truncate)"; then
        alerts+=("🚨 检测到危险的删除操作")
    fi
    
    # 检查敏感信息
    if echo "$task" | grep -qiE "(password|secret|key|token|api)"; then
        alerts+=("🔐 注意: 涉及敏感信息，请谨慎处理")
    fi
    
    # 检查网络操作
    if echo "$task" | grep -qiE "(curl|wget|下载|upload|上传)"; then
        alerts+=("🌐 注意: 涉及网络操作，注意安全")
    fi
    
    # 检查权限操作
    if echo "$task" | grep -qiE "(sudo|chmod 777|权限|permission)"; then
        alerts+=("⚠️ 注意: 涉及权限修改，请谨慎")
    fi
    
    # 输出安全提醒
    if [ ${#alerts[@]} -gt 0 ]; then
        echo "🛡️ 安全提醒:" >&2
        printf "  %s\n" "${alerts[@]}" >&2
        echo "" >&2
    else
        echo "🛡️ 安全检查通过" >&2
    fi
}

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")

if [ -n "$TASK_DESC" ]; then
    check_security "$TASK_DESC"
fi

# 输出原始输入（不修改）
echo "$INPUT"
exit 0
SECURITY_CHECKER

    chmod +x "$HOOKS_DIR/security_checker.sh"
    log "✅ 安全检查Hook创建完成"
}

update_hook_installer() {
    log "🔧 更新Hook安装器..."
    
    cat > "$HOOKS_DIR/install.sh" << 'INSTALLER'
#!/bin/bash
# Claude Enhancer 安全Hook安装器

set -e

# 获取项目根目录
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOKS_DIR="$PROJECT_ROOT/.claude/hooks"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Claude Enhancer 安全Hook安装器${NC}"
echo "═══════════════════════════════════════"

# 检查Git仓库
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${YELLOW}⚠️ 不是Git仓库，跳过Git Hook安装${NC}"
    exit 0
fi

# 安装Git Hooks
install_git_hooks() {
    echo "🔗 安装Git Hooks..."
    
    # Pre-commit
    if [ -f "$HOOKS_DIR/simple_pre_commit.sh" ]; then
        ln -sf "$HOOKS_DIR/simple_pre_commit.sh" "$GIT_HOOKS_DIR/pre-commit"
        echo "  ✅ pre-commit hook installed"
    fi
    
    # Commit-msg  
    if [ -f "$HOOKS_DIR/simple_commit_msg.sh" ]; then
        ln -sf "$HOOKS_DIR/simple_commit_msg.sh" "$GIT_HOOKS_DIR/commit-msg"
        echo "  ✅ commit-msg hook installed"
    fi
    
    # Pre-push
    if [ -f "$HOOKS_DIR/simple_pre_push.sh" ]; then
        ln -sf "$HOOKS_DIR/simple_pre_push.sh" "$GIT_HOOKS_DIR/pre-push"
        echo "  ✅ pre-push hook installed"
    fi
}

# 创建Hook配置
create_hook_config() {
    echo "⚙️ 创建Hook配置..."
    
    cat > "$HOOKS_DIR/.hook_config" << 'CONFIG'
# Claude Enhancer Hook配置
HOOKS_ENABLED=true
QUALITY_GATE_ENABLED=true
WORKFLOW_ADVISOR_ENABLED=true
SECURITY_CHECKER_ENABLED=true
CONFIG

    echo "  ✅ Hook配置文件创建完成"
}

# 验证安装
verify_installation() {
    echo "🔍 验证安装..."
    
    local hooks=(
        "branch_helper.sh"
        "smart_agent_selector.sh"
        "quality_gate.sh"
        "workflow_advisor.sh"
        "security_checker.sh"
    )
    
    local installed=0
    for hook in "${hooks[@]}"; do
        if [ -f "$HOOKS_DIR/$hook" ]; then
            echo "  ✅ $hook"
            ((installed++))
        else
            echo "  ❌ $hook (missing)"
        fi
    done
    
    echo ""
    echo -e "${GREEN}📊 安装完成: ${installed}/${#hooks[@]} hooks${NC}"
}

# 执行安装
install_git_hooks
create_hook_config  
verify_installation

echo ""
echo -e "${GREEN}🎉 Claude Enhancer Hook安装完成！${NC}"
echo ""
echo "安全特性:"
echo "  🛡️ 质量门禁 - 代码质量检查"
echo "  💼 工作流顾问 - 流程建议"  
echo "  🔒 安全检查 - 风险提醒"
echo "  🌿 分支辅助 - Git最佳实践"
echo "  🤖 智能选择 - Agent建议"
echo ""
echo "使用方法:"
echo "  - Hook会自动在适当时机运行"
echo "  - 所有建议都是友好提醒，不会阻止操作"
echo "  - 查看日志: /tmp/claude-enhancer_hooks.log"
INSTALLER

    chmod +x "$HOOKS_DIR/install.sh"
    log "✅ Hook安装器更新完成"
}

create_documentation() {
    log "📚 创建Hook文档..."
    
    cat > "$HOOKS_DIR/README.md" << 'DOCUMENTATION'
# Claude Enhancer 安全Hook系统

## 概览

Claude Enhancer使用精简、安全的Hook系统，提供友好的建议和质量保证，而不会干扰用户的正常工作流程。

## 安全原则

- 🛡️ **只读原则**: Hook不修改用户输入
- 💡 **建议原则**: 提供建议而非强制要求  
- 🔍 **透明原则**: 所有操作对用户可见
- 🚀 **性能原则**: 轻量级，不影响执行速度

## Hook列表

### 1. 核心Hook

#### `branch_helper.sh` 🌿
- **功能**: 提醒用户创建feature分支
- **触发**: Git操作时
- **行为**: 友好提醒，不阻止操作

#### `smart_agent_selector.sh` 🤖  
- **功能**: 根据任务复杂度建议Agent组合
- **触发**: 执行任务前
- **行为**: 输出建议信息

### 2. 质量Hook

#### `quality_gate.sh` 🎯
- **功能**: 代码质量评估
- **检查项**: 
  - 任务描述完整性
  - 基本质量标准
  - 潜在危险操作
- **行为**: 评分和建议，不阻止执行

#### `workflow_advisor.sh` 💼
- **功能**: 工作流程建议
- **特点**: 根据任务类型给出最佳实践建议
- **行为**: 输出流程指导

#### `security_checker.sh` 🔒
- **功能**: 安全风险提醒
- **检查项**:
  - 危险操作检测
  - 敏感信息提醒  
  - 权限操作警告
- **行为**: 安全提醒，不阻止操作

### 3. Git Hook

#### `simple_pre_commit.sh` ✅
- **功能**: 提交前代码检查
- **检查项**: 语法、敏感信息、文件大小
- **行为**: 标准Git Hook行为

#### `simple_commit_msg.sh` 📝
- **功能**: 提交信息格式检查
- **检查项**: 提交信息规范
- **行为**: 格式验证

#### `simple_pre_push.sh` 🚀  
- **功能**: 推送前验证
- **检查项**: 基本验证
- **行为**: 推送前检查

## 使用方法

### 安装
```bash
cd /path/to/your/project
./.claude/hooks/install.sh
```

### 配置
编辑 `.claude/hooks/.hook_config` 文件：
```bash
HOOKS_ENABLED=true
QUALITY_GATE_ENABLED=true
WORKFLOW_ADVISOR_ENABLED=true
SECURITY_CHECKER_ENABLED=true
```

### 日志查看
```bash
# Hook执行日志
tail -f /tmp/claude-enhancer_hooks.log

# Agent选择日志
tail -f /tmp/claude_agent_selection.log
```

## 故障排除

### Hook不工作
1. 检查文件权限: `ls -la .claude/hooks/`
2. 检查Git Hook链接: `ls -la .git/hooks/`
3. 重新安装: `.claude/hooks/install.sh`

### 禁用某个Hook
```bash
# 临时禁用
export CLAUDE_ENHANCER_HOOKS_DISABLED=true

# 永久禁用 - 编辑配置文件
vim .claude/hooks/.hook_config
```

## 开发规范

### 新Hook开发
1. 必须遵循只读原则
2. 不得修改用户输入  
3. 提供友好的用户体验
4. 包含适当的错误处理
5. 添加详细的文档

### 代码模板
```bash
#!/bin/bash
# Claude Enhancer Hook Template

set -e

# 读取输入（不修改）
INPUT=$(cat)

# 你的逻辑
your_hook_logic() {
    # 只能读取和分析，不能修改
    echo "Hook advice here" >&2
}

# 执行逻辑
your_hook_logic

# 原样输出输入
echo "$INPUT" 
exit 0
```

## 安全承诺

Claude Enhancer Hook系统承诺：
- ❌ 绝不修改用户输入
- ❌ 绝不阻止合法操作
- ❌ 绝不收集敏感信息
- ❌ 绝不执行危险命令
- ✅ 只提供友好建议
- ✅ 保持完全透明
- ✅ 尊重用户选择

---
*Claude Enhancer - AI-Driven Development for Non-Programmers*
DOCUMENTATION

    log "✅ Hook文档创建完成"
}

main() {
    echo -e "${BLUE}Claude Enhancer 安全Hook重建${NC}"
    echo "═══════════════════════════════════════════"
    
    log "🚀 开始创建安全Hook系统..."
    
    # 创建安全Hook
    create_quality_gate_hook
    create_workflow_advisor
    create_security_checker
    update_hook_installer
    create_documentation
    
    echo ""
    echo -e "${GREEN}✅ 安全Hook系统创建完成！${NC}"
    echo ""
    echo "新创建的安全Hook:"
    echo "  🛡️ quality_gate.sh - 质量门禁"
    echo "  💼 workflow_advisor.sh - 工作流顾问"
    echo "  🔒 security_checker.sh - 安全检查"
    echo "  🔧 install.sh - 更新的安装器"
    echo "  📚 README.md - 完整文档"
    echo ""
    echo "安装方法:"
    echo "  cd $HOOKS_DIR && ./install.sh"
    echo ""
    
    log "✅ 安全Hook重建完成"
}

main "$@"
