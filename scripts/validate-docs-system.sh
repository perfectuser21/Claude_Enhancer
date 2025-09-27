#!/bin/bash

# 📋 Documentation Quality System Validation Script
# 快速验证文档质量检查系统是否正确安装和配置

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 图标定义
CHECK_MARK="✅"
CROSS_MARK="❌"
WARNING="⚠️"
INFO="ℹ️"

log_info() {
    echo -e "${BLUE}${INFO} $1${NC}"
}

log_success() {
    echo -e "${GREEN}${CHECK_MARK} $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

log_error() {
    echo -e "${RED}${CROSS_MARK} $1${NC}"
}

echo -e "${BLUE}📋 Documentation Quality System Validation${NC}"
echo "================================================"

# 检查文件存在性
echo -e "\n${BLUE}1. Checking System Files...${NC}"

files_to_check=(
    ".github/workflows/docs-quality-check.yml"
    ".markdownlint.json"
    ".markdown-link-check.json"
    "scripts/docs-quality-check.sh"
    "docs/DOCS_QUALITY_SYSTEM.md"
)

missing_files=0
for file in "${files_to_check[@]}"; do
    if [[ -f "$file" ]]; then
        log_success "$file exists"
    else
        log_error "$file is missing"
        ((missing_files++))
    fi
done

# 检查脚本权限
echo -e "\n${BLUE}2. Checking Script Permissions...${NC}"

if [[ -x "scripts/docs-quality-check.sh" ]]; then
    log_success "docs-quality-check.sh is executable"
else
    log_error "docs-quality-check.sh is not executable"
    log_info "Fix with: chmod +x scripts/docs-quality-check.sh"
    ((missing_files++))
fi

# 验证YAML语法
echo -e "\n${BLUE}3. Validating YAML Syntax...${NC}"

if command -v python3 >/dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docs-quality-check.yml'))" 2>/dev/null; then
        log_success "GitHub Actions workflow YAML is valid"
    else
        log_error "GitHub Actions workflow YAML has syntax errors"
        ((missing_files++))
    fi
else
    log_warning "Python3 not available, skipping YAML validation"
fi

# 验证JSON配置
echo -e "\n${BLUE}4. Validating JSON Configuration...${NC}"

for json_file in ".markdownlint.json" ".markdown-link-check.json"; do
    if command -v python3 >/dev/null; then
        if python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
            log_success "$json_file is valid JSON"
        else
            log_error "$json_file has JSON syntax errors"
            ((missing_files++))
        fi
    else
        log_warning "Python3 not available, skipping JSON validation for $json_file"
    fi
done

# 检查文档统计
echo -e "\n${BLUE}5. Analyzing Documentation...${NC}"

total_md_files=$(find . -name "*.md" | grep -v node_modules | wc -l)
total_size=$(find . -name "*.md" | grep -v node_modules | xargs du -b 2>/dev/null | awk '{sum += $1} END {print sum}' || echo "0")
total_size_kb=$((total_size / 1024))

log_info "Total Markdown files: $total_md_files"
log_info "Total documentation size: ${total_size_kb}KB"

if [[ $total_md_files -gt 0 ]]; then
    log_success "Documentation files found"
else
    log_warning "No Markdown files found"
fi

# 检查工作流触发条件
echo -e "\n${BLUE}6. Checking Workflow Configuration...${NC}"

if grep -q "paths:" ".github/workflows/docs-quality-check.yml"; then
    log_success "Workflow has path-based triggers configured"
else
    log_warning "Workflow may trigger on all file changes"
fi

if grep -q "concurrency:" ".github/workflows/docs-quality-check.yml"; then
    log_success "Workflow has concurrency control configured"
else
    log_warning "Workflow lacks concurrency control"
fi

# 检查性能配置
echo -e "\n${BLUE}7. Checking Performance Settings...${NC}"

timeout_minutes=$(grep -o "timeout-minutes: [0-9]*" ".github/workflows/docs-quality-check.yml" | head -1 | grep -o "[0-9]*" || echo "unknown")

if [[ "$timeout_minutes" != "unknown" && "$timeout_minutes" -le 5 ]]; then
    log_success "Workflow timeout is within performance target (${timeout_minutes} minutes)"
else
    log_warning "Workflow timeout may be too long or not configured"
fi

# 生成验证报告
echo -e "\n${BLUE}📊 Validation Summary${NC}"
echo "================================"

if [[ $missing_files -eq 0 ]]; then
    log_success "All system files are present and valid"
    echo -e "\n${GREEN}🎉 Documentation Quality System is ready to use!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Install dependencies: npm install -g markdownlint-cli2 markdown-link-check"
    echo "2. Run local check: ./scripts/docs-quality-check.sh"
    echo "3. Push changes to trigger GitHub Actions workflow"
    echo ""
    exit 0
else
    log_error "Found $missing_files issues that need to be resolved"
    echo -e "\n${RED}❌ System validation failed!${NC}"
    echo ""
    echo "Please fix the issues above before using the system."
    echo ""
    exit 1
fi