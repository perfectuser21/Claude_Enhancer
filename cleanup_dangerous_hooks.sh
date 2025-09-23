#!/bin/bash
# Perfect21 Hook Security Cleanup Script
# 安全清理脚本 - 移除危险Hook，保留安全核心

set -e

HOOKS_DIR="/home/xx/dev/Perfect21/.claude/hooks"
BACKUP_DIR="/home/xx/dev/Perfect21/.claude/hooks_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="/tmp/hook_cleanup_$(date +%Y%m%d_%H%M%S).log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${BLUE}"
    echo "═══════════════════════════════════════════"
    echo "  Perfect21 Hook Security Cleanup"
    echo "═══════════════════════════════════════════"
    echo -e "${NC}"
}

# 危险Hook列表
DANGEROUS_HOOKS=(
    # 恶意脚本 - CRITICAL
    "misc/input_hijacker.sh"
    "misc/input_destroyer.sh"
    "misc/force_return.sh"
    "misc/infinite_wait.sh"
    "enforcer_interceptor.py"
    "phase_interceptor.py"
    "enforcement_controller.py"
    
    # 高危控制脚本
    "phase_enforcer.py"
    "smart_dispatcher.py"
    "parallel_execution_optimizer.py"
    "performance_optimized_dispatcher.py"
    "ultra_smart_agent_selector.sh"
    "phase_manager.py"
    "resource_monitor.py"
    "optimized_logger.py"
    "performance_test.py"
    
    # 其他可疑脚本
    "enforcer.sh"
    "phase_checker.sh"
    "phase_flow_monitor.sh"
    "dynamic_task_analyzer.sh"
    "agent-summarizer.py"
    "agent-output-collector.py"
    "security_validator.py"
    "smart_doc_loader.sh"
    
    # Misc目录中的危险脚本
    "misc/context-manager.sh"
    "misc/debug-hook.sh"
    "misc/doc-organizer.sh"
    "misc/git-bridge.sh"
    "misc/intelligent_control.sh"
    "misc/max_quality.sh"
    "misc/perfect21_active_control.sh"
    "misc/pre-task.sh"
    "misc/quality-gates.sh"
    "misc/task-type-detector.sh"
    "misc/task_analyzer.sh"
    "misc/task_precheck.sh"
    "misc/validate_agents_wrapper.sh"
    "misc/validate_stub.sh"
    "misc/worktree-manager.sh"
    "misc/workflow_manager.sh"
)

# 安全Hook列表（保留）
SAFE_HOOKS=(
    "branch_helper.sh"
    "smart_agent_selector.sh" 
    "simple_pre_commit.sh"
    "simple_commit_msg.sh"
    "simple_pre_push.sh"
    "install.sh"
)

backup_hooks() {
    log "📦 备份现有Hook目录..."
    if [ -d "$HOOKS_DIR" ]; then
        cp -r "$HOOKS_DIR" "$BACKUP_DIR"
        log "✅ 备份完成: $BACKUP_DIR"
    else
        log "⚠️  Hook目录不存在: $HOOKS_DIR"
        exit 1
    fi
}

remove_dangerous_hooks() {
    log "🔥 开始移除危险Hook..."
    
    local removed_count=0
    local missing_count=0
    
    for hook in "${DANGEROUS_HOOKS[@]}"; do
        local hook_path="$HOOKS_DIR/$hook"
        if [ -f "$hook_path" ]; then
            echo -e "${RED}❌ 移除危险Hook: $hook${NC}"
            rm -f "$hook_path"
            ((removed_count++))
            log "REMOVED: $hook"
        else
            echo -e "${YELLOW}⚠️  Hook不存在: $hook${NC}"
            ((missing_count++))
        fi
    done
    
    log "✅ 危险Hook移除完成: 删除${removed_count}个，缺失${missing_count}个"
}

remove_directories() {
    log "📁 移除危险目录..."
    
    local dirs_to_remove=(
        "$HOOKS_DIR/deprecated"
        "$HOOKS_DIR/archived"
        "$HOOKS_DIR/misc"
    )
    
    for dir in "${dirs_to_remove[@]}"; do
        if [ -d "$dir" ]; then
            echo -e "${RED}🗑️  移除目录: $(basename "$dir")${NC}"
            rm -rf "$dir"
            log "REMOVED_DIR: $dir"
        fi
    done
}

remove_backup_files() {
    log "🧹 清理备份文件..."
    
    # 移除.bak文件
    find "$HOOKS_DIR" -name "*.bak*" -type f -delete 2>/dev/null || true
    
    # 移除.backup文件
    find "$HOOKS_DIR" -name "*.backup*" -type f -delete 2>/dev/null || true
    
    log "✅ 备份文件清理完成"
}

verify_safe_hooks() {
    log "🔍 验证安全Hook保留情况..."
    
    local safe_count=0
    local missing_safe=0
    
    for hook in "${SAFE_HOOKS[@]}"; do
        local hook_path="$HOOKS_DIR/$hook"
        if [ -f "$hook_path" ]; then
            echo -e "${GREEN}✅ 安全Hook保留: $hook${NC}"
            ((safe_count++))
        else
            echo -e "${YELLOW}⚠️  安全Hook缺失: $hook${NC}"
            ((missing_safe++))
        fi
    done
    
    log "✅ 安全Hook验证: 保留${safe_count}个，缺失${missing_safe}个"
}

create_new_hook_config() {
    log "⚙️  创建新的Hook配置..."
    
    cat > "$HOOKS_DIR/config.yaml" << 'HOOK_CONFIG'
# Perfect21 安全Hook配置
# 只保留必要的、安全的Hook

hooks:
  enabled: true
  
  # 安全的核心Hook
  core_hooks:
    - name: "branch_helper"
      script: "branch_helper.sh"
      description: "分支创建提醒"
      type: "advisory"
      
    - name: "smart_agent_selector"
      script: "smart_agent_selector.sh"
      description: "智能Agent选择建议"
      type: "advisory"
      
  # Git标准Hook  
  git_hooks:
    - name: "pre_commit"
      script: "simple_pre_commit.sh"
      description: "代码质量检查"
      type: "validation"
      
    - name: "commit_msg"
      script: "simple_commit_msg.sh"
      description: "提交信息规范"
      type: "validation"
      
    - name: "pre_push"
      script: "simple_pre_push.sh"
      description: "推送前验证"
      type: "validation"

# 安全规则
security:
  # 禁止的Hook行为
  forbidden_actions:
    - "modify_user_input"
    - "block_execution"
    - "hijack_workflow"
    - "infinite_loops"
    - "unauthorized_file_access"
    
  # 允许的Hook类型  
  allowed_types:
    - "advisory"      # 建议性
    - "validation"    # 验证性
    - "notification"  # 通知性

# 审计设置
audit:
  log_file: "/tmp/perfect21_hooks.log"
  log_level: "INFO"
HOOK_CONFIG

    log "✅ 新Hook配置创建完成"
}

create_security_report() {
    log "📊 生成安全报告..."
    
    local report_file="$HOOKS_DIR/SECURITY_CLEANUP_REPORT.md"
    
    cat > "$report_file" << REPORT
# Hook安全清理报告

## 清理概览
- **清理时间**: $(date)
- **备份位置**: $BACKUP_DIR
- **日志文件**: $LOG_FILE

## 移除的危险Hook
$(printf "- %s\n" "${DANGEROUS_HOOKS[@]}")

## 保留的安全Hook
$(printf "- %s\n" "${SAFE_HOOKS[@]}")

## 安全改进
1. ✅ 移除所有恶意和危险Hook脚本
2. ✅ 清理冗余目录和备份文件
3. ✅ 创建安全的Hook配置文件
4. ✅ 建立安全审计机制

## 后续建议
1. 定期审查Hook安全性
2. 建立Hook代码审查流程
3. 监控Hook行为和性能
4. 用户培训和安全意识

---
*安全清理脚本执行完毕*
REPORT

    log "✅ 安全报告生成: $report_file"
}

main() {
    print_header
    
    log "🚀 开始Hook安全清理流程..."
    
    # 检查权限
    if [ ! -w "$HOOKS_DIR" ]; then
        echo -e "${RED}❌ 错误: 没有Hook目录写权限${NC}"
        exit 1
    fi
    
    # 执行清理步骤
    backup_hooks
    remove_dangerous_hooks
    remove_directories
    remove_backup_files
    verify_safe_hooks
    create_new_hook_config
    create_security_report
    
    echo ""
    echo -e "${GREEN}🎉 Hook安全清理完成！${NC}"
    echo ""
    echo -e "${BLUE}📊 清理结果:${NC}"
    echo -e "  📦 备份位置: ${BACKUP_DIR}"
    echo -e "  📝 日志文件: ${LOG_FILE}"
    echo -e "  🔒 安全Hook: ${#SAFE_HOOKS[@]}个"
    echo -e "  🗑️  移除Hook: ${#DANGEROUS_HOOKS[@]}个"
    echo ""
    echo -e "${YELLOW}⚠️  建议:${NC}"
    echo "  1. 检查备份目录确认重要文件"
    echo "  2. 测试保留Hook的功能性"
    echo "  3. 更新相关文档和配置"
    echo ""
    
    log "✅ Hook安全清理流程完成"
}

# 执行主函数
main "$@"
