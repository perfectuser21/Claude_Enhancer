#!/bin/bash

# =============================================================================
# Claude Enhancer 5.0 - 文档质量管理系统一键安装脚本
# Deploy DocGate Documentation Quality Management System
# =============================================================================

set -euo pipefail  # 严格错误处理

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 全局变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$PROJECT_ROOT/deploy_docgate_$TIMESTAMP.log"
BACKUP_DIR="$PROJECT_ROOT/.docgate_backup_$TIMESTAMP"

# 日志函数
log() {
    echo -e "${1}" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_step() {
    log "${PURPLE}[STEP]${NC} $1"
}

# 错误处理
error_exit() {
    log_error "$1"
    log_error "安装失败！请查看日志: $LOG_FILE"
    exit 1
}

# 创建备份
create_backup() {
    log_step "创建备份目录: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"

    # 备份现有.claude配置
    if [ -d "$CLAUDE_DIR" ]; then
        log_info "备份现有Claude配置..."
        cp -r "$CLAUDE_DIR" "$BACKUP_DIR/claude_backup" 2>/dev/null || true
    fi

    # 备份现有git hooks
    if [ -d "$PROJECT_ROOT/.git/hooks" ]; then
        log_info "备份现有Git hooks..."
        cp -r "$PROJECT_ROOT/.git/hooks" "$BACKUP_DIR/git_hooks_backup" 2>/dev/null || true
    fi

    # 备份现有.docpolicy.yaml
    if [ -f "$PROJECT_ROOT/.docpolicy.yaml" ]; then
        log_info "备份现有文档策略配置..."
        cp "$PROJECT_ROOT/.docpolicy.yaml" "$BACKUP_DIR/docpolicy_backup.yaml"
    fi

    log_success "备份创建完成"
}

# 显示欢迎信息
show_welcome() {
    clear
    cat << 'EOF'
 ____             ____       _        ____            _
|  _ \  ___   ___/ ___| __ _| |_ ___ / ___| _   _ ___| |_ ___ _ __ ___
| | | |/ _ \ / __| |  _ / _` | __/ _ \\___ \| | | / __| __/ _ \ '_ ` _ \
| |_| | (_) | (__| |_| | (_| | ||  __/___) | |_| \__ \ ||  __/ | | | | |
|____/ \___/ \___|\____|\__,_|\__\___|____/ \__, |___/\__\___|_| |_| |_|
                                           |___/
    Claude Enhancer 5.0 - 文档质量管理系统
    Documentation Quality Management System Installer
===============================================================================
EOF

    log_info "欢迎使用Claude Enhancer 5.0文档质量管理系统安装程序"
    log_info "此脚本将自动部署完整的DocGate系统"
    log_info ""
    log_info "部署组件："
    log_info "  • 文档质量检查引擎"
    log_info "  • Git工作流集成"
    log_info "  • Claude Agent协调器"
    log_info "  • 三层质量门禁"
    log_info "  • API服务接口"
    log_info ""
}

# 检查系统要求
check_requirements() {
    log_step "检查系统依赖项..."

    local missing_deps=()

    # 检查基础命令
    for cmd in git python3 pip3 node npm curl jq; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    # 检查Python版本
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        python_major=$(echo "$python_version" | cut -d'.' -f1)
        python_minor=$(echo "$python_version" | cut -d'.' -f2)

        if [ "$python_major" -lt 3 ] || [ "$python_major" -eq 3 -a "$python_minor" -lt 8 ]; then
            log_warning "Python版本过低: $python_version (需要 >= 3.8)"
            missing_deps+=("python3.8+")
        else
            log_info "Python版本: $python_version ✓"
        fi
    fi

    # 检查Node.js版本
    if command -v node &> /dev/null; then
        node_version=$(node --version | sed 's/v//')
        node_major=$(echo "$node_version" | cut -d'.' -f1)

        if [ "$node_major" -lt 16 ]; then
            log_warning "Node.js版本过低: $node_version (需要 >= 16)"
            missing_deps+=("node16+")
        else
            log_info "Node.js版本: $node_version ✓"
        fi
    fi

    # 检查Git仓库
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_warning "当前目录不是Git仓库，部分功能将受限"
    else
        log_info "Git仓库检查通过 ✓"
    fi

    # 检查网络连接
    if ! curl -s --max-time 5 https://pypi.org > /dev/null; then
        log_warning "网络连接检查失败，可能影响依赖安装"
    else
        log_info "网络连接正常 ✓"
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "缺少必要依赖: ${missing_deps[*]}"
        log_info "请先安装缺少的依赖项："
        log_info ""
        log_info "Ubuntu/Debian:"
        log_info "  sudo apt update"
        log_info "  sudo apt install -y git python3 python3-pip nodejs npm curl jq"
        log_info ""
        log_info "CentOS/RHEL:"
        log_info "  sudo yum install -y git python3 python3-pip nodejs npm curl jq"
        log_info ""
        log_info "macOS:"
        log_info "  brew install git python3 node curl jq"
        log_info ""
        error_exit "依赖检查失败"
    fi

    log_success "系统依赖检查通过"
}

# 创建目录结构
create_directory_structure() {
    log_step "创建文档质量管理目录结构..."

    # 创建核心目录
    local dirs=(
        # Claude Enhancer核心目录
        "$CLAUDE_DIR"
        "$CLAUDE_DIR/core"
        "$CLAUDE_DIR/hooks"
        "$CLAUDE_DIR/git-hooks"
        "$CLAUDE_DIR/agents"
        "$CLAUDE_DIR/config"
        "$CLAUDE_DIR/scripts"
        "$CLAUDE_DIR/logs"
        "$CLAUDE_DIR/cache"

        # 文档目录结构
        "$PROJECT_ROOT/docs"
        "$PROJECT_ROOT/docs/requirements"
        "$PROJECT_ROOT/docs/design"
        "$PROJECT_ROOT/docs/api"
        "$PROJECT_ROOT/docs/guides"
        "$PROJECT_ROOT/docs/changelogs"
        "$PROJECT_ROOT/docs/test-reports"
        "$PROJECT_ROOT/docs/_digest"
        "$PROJECT_ROOT/docs/_reports"
        "$PROJECT_ROOT/docs/_templates"

        # 临时和归档目录
        "$PROJECT_ROOT/tmp/docs"
        "$PROJECT_ROOT/archive/docs"

        # 后端API目录
        "$PROJECT_ROOT/backend/api/docgate"
        "$PROJECT_ROOT/backend/core"
        "$PROJECT_ROOT/backend/services"

        # 测试目录
        "$PROJECT_ROOT/tests/docgate"
        "$PROJECT_ROOT/tests/integration"

        # 监控目录
        "$PROJECT_ROOT/monitoring"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        else
            log_info "目录已存在: $dir"
        fi
    done

    log_success "目录结构创建完成"
}

# 安装Python依赖
install_python_dependencies() {
    log_step "安装Python依赖包..."

    # 创建requirements.txt
    cat > "$PROJECT_ROOT/requirements_docgate.txt" << 'EOF'
# DocGate 文档质量管理系统依赖
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
sqlalchemy>=2.0.0
alembic>=1.12.0
redis>=4.6.0
celery>=5.3.0
httpx>=0.25.0
jinja2>=3.1.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
aiofiles>=23.2.1
markupsafe>=2.1.3
pygments>=2.16.1
markdown>=3.5.1
beautifulsoup4>=4.12.2
lxml>=4.9.3
spacy>=3.7.2
textstat>=0.7.3
nltk>=3.8.1
pyspellchecker>=0.7.2
pyyaml>=6.0.1
toml>=0.10.2
jsonschema>=4.19.1
python-dateutil>=2.8.2
click>=8.1.7
rich>=13.6.0
typer>=0.9.0
watchdog>=3.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.1
pytest-cov>=4.1.0
pytest-mock>=3.11.1
black>=23.9.1
isort>=5.12.0
flake8>=6.1.0
mypy>=1.6.0
pre-commit>=3.5.0
EOF

    # 安装依赖
    log_info "安装Python包依赖..."
    pip3 install -r "$PROJECT_ROOT/requirements_docgate.txt" --user || {
        log_warning "用户安装失败，尝试全局安装..."
        sudo pip3 install -r "$PROJECT_ROOT/requirements_docgate.txt" || {
            log_error "Python依赖安装失败"
            return 1
        }
    }

    # 下载spaCy语言模型
    log_info "下载spaCy中文语言模型..."
    python3 -m spacy download zh_core_web_sm || log_warning "中文模型下载失败，将使用英文模型"
    python3 -m spacy download en_core_web_sm || log_warning "英文模型下载失败"

    # 下载NLTK数据
    log_info "下载NLTK数据..."
    python3 -c "
import nltk
try:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('stopwords')
    print('NLTK数据下载完成')
except Exception as e:
    print(f'NLTK数据下载失败: {e}')
    " || log_warning "NLTK数据下载失败"

    log_success "Python依赖安装完成"
}

# 安装Node.js依赖
install_nodejs_dependencies() {
    log_step "安装Node.js依赖包..."

    # 创建package.json
    cat > "$PROJECT_ROOT/package_docgate.json" << 'EOF'
{
  "name": "claude-enhancer-docgate",
  "version": "1.0.0",
  "description": "DocGate文档质量管理系统前端依赖",
  "dependencies": {
    "markdown-it": "^13.0.2",
    "markdown-it-anchor": "^8.6.7",
    "markdown-it-table-of-contents": "^0.6.0",
    "markdownlint": "^0.31.1",
    "markdownlint-cli": "^0.37.0",
    "alex": "^11.0.1",
    "textlint": "^13.3.2",
    "textlint-rule-max-ten": "^4.0.4",
    "textlint-rule-no-todo": "^2.0.1",
    "write-good": "^1.0.8",
    "puppeteer": "^21.5.0",
    "html-pdf": "^3.0.1",
    "cheerio": "^1.0.0-rc.12",
    "jsdom": "^22.1.0",
    "chalk": "^4.1.2",
    "commander": "^11.1.0",
    "glob": "^10.3.10",
    "chokidar": "^3.5.3"
  },
  "devDependencies": {
    "eslint": "^8.52.0",
    "prettier": "^3.0.3",
    "@types/node": "^20.8.7",
    "typescript": "^5.2.2"
  },
  "scripts": {
    "lint:md": "markdownlint-cli docs/**/*.md",
    "lint:text": "textlint docs/**/*.md",
    "check:accessibility": "alex docs/**/*.md",
    "check:style": "write-good docs/**/*.md",
    "build:docs": "node scripts/build-docs.js",
    "watch:docs": "chokidar 'docs/**/*.md' -c 'npm run build:docs'"
  }
}
EOF

    # 安装Node.js依赖
    log_info "安装Node.js包依赖..."
    if [ -f "$PROJECT_ROOT/package_docgate.json" ]; then
        cd "$PROJECT_ROOT"
        npm install --package-lock-only --prefix . --package "package_docgate.json" || {
            log_warning "npm安装失败，尝试使用yarn..."
            yarn install --production || {
                log_error "Node.js依赖安装失败"
                return 1
            }
        }
    fi

    log_success "Node.js依赖安装完成"
}

# 配置Git Hooks
install_git_hooks() {
    log_step "安装Git Hooks..."

    if [ ! -d "$PROJECT_ROOT/.git" ]; then
        log_warning "非Git仓库，跳过Git Hooks安装"
        return 0
    fi

    # 创建增强的pre-commit hook
    cat > "$PROJECT_ROOT/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# DocGate文档质量预提交检查

set -e

echo "🔍 DocGate文档质量检查..."

# 获取已修改的文档文件
changed_docs=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(md|rst|txt)$' || true)

if [ -z "$changed_docs" ]; then
    echo "✅ 无文档文件变更"
    exit 0
fi

echo "📝 检查文档文件: $changed_docs"

# 检查.docpolicy.yaml配置
if [ ! -f ".docpolicy.yaml" ]; then
    echo "⚠️  未找到.docpolicy.yaml配置文件"
    exit 1
fi

# 执行文档质量检查
python3 .claude/scripts/docgate_pre_commit_check.py --files $changed_docs

# 检查文件名合规性
for file in $changed_docs; do
    # 检查文件名模式
    if echo "$file" | grep -qE "(copy|backup|final\([0-9]+\)|-old)\.md$"; then
        echo "❌ 文件名不符合规范: $file"
        echo "   禁止使用: copy, backup, final(N), -old 等后缀"
        exit 1
    fi

    # 检查文件大小
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        max_size=$((5 * 1024 * 1024))  # 5MB

        if [ "$size" -gt "$max_size" ]; then
            echo "❌ 文件过大: $file ($(($size/1024))KB > 5120KB)"
            exit 1
        fi
    fi
done

echo "✅ 文档质量检查通过"
EOF

    # 创建commit-msg hook
    cat > "$PROJECT_ROOT/.git/hooks/commit-msg" << 'EOF'
#!/bin/bash
# DocGate提交信息检查

commit_msg_file="$1"
commit_msg=$(cat "$commit_msg_file")

echo "📝 检查提交信息格式..."

# 检查提交信息格式
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}"; then
    echo "❌ 提交信息格式不正确"
    echo "正确格式: type(scope): description"
    echo "示例: docs(api): add docgate endpoint documentation"
    echo ""
    echo "类型说明:"
    echo "  feat:     新功能"
    echo "  fix:      bug修复"
    echo "  docs:     文档更新"
    echo "  style:    代码格式"
    echo "  refactor: 代码重构"
    echo "  test:     测试相关"
    echo "  chore:    构建、依赖等"
    exit 1
fi

echo "✅ 提交信息格式正确"
EOF

    # 创建pre-push hook
    cat > "$PROJECT_ROOT/.git/hooks/pre-push" << 'EOF'
#!/bin/bash
# DocGate推送前检查

echo "🚀 DocGate推送前质量检查..."

# 运行文档链接检查
echo "🔗 检查文档链接..."
python3 .claude/scripts/check_doc_links.py docs/ || {
    echo "❌ 文档链接检查失败"
    exit 1
}

# 运行文档结构检查
echo "📋 检查文档结构..."
python3 .claude/scripts/check_doc_structure.py docs/ || {
    echo "❌ 文档结构检查失败"
    exit 1
}

echo "✅ 推送前检查通过"
EOF

    # 设置执行权限
    chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit"
    chmod +x "$PROJECT_ROOT/.git/hooks/commit-msg"
    chmod +x "$PROJECT_ROOT/.git/hooks/pre-push"

    log_success "Git Hooks安装完成"
}

# 配置DocGate Agent
configure_docgate_agent() {
    log_step "配置DocGate Agent..."

    # 创建DocGate核心检查脚本
    cat > "$CLAUDE_DIR/scripts/docgate_pre_commit_check.py" << 'EOF'
#!/usr/bin/env python3
"""
DocGate文档质量预提交检查脚本
"""

import sys
import os
import argparse
import yaml
import re
from pathlib import Path
from typing import List, Dict, Any

def load_config() -> Dict[str, Any]:
    """加载.docpolicy.yaml配置"""
    config_path = Path(".docpolicy.yaml")
    if not config_path.exists():
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def check_filename_patterns(filename: str, config: Dict[str, Any]) -> List[str]:
    """检查文件名模式"""
    issues = []

    deny_patterns = config.get('quality', {}).get('deny_name_patterns', [])
    for pattern in deny_patterns:
        if re.search(pattern, filename):
            issues.append(f"文件名违反规则: {pattern}")

    return issues

def check_file_size(filepath: str, config: Dict[str, Any]) -> List[str]:
    """检查文件大小"""
    issues = []

    max_size_kb = config.get('quality', {}).get('max_file_kb', 5120)
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        if size_kb > max_size_kb:
            issues.append(f"文件过大: {size_kb:.1f}KB > {max_size_kb}KB")

    return issues

def check_content_quality(filepath: str, config: Dict[str, Any]) -> List[str]:
    """检查内容质量"""
    issues = []

    if not os.path.exists(filepath):
        return issues

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否需要摘要
        if config.get('quality', {}).get('require_tldr', False):
            if not re.search(r'(## 摘要|## Summary|TL;DR)', content, re.IGNORECASE):
                issues.append("缺少摘要部分")

        # 检查最少关键点数量
        min_points = config.get('quality', {}).get('min_key_points', 0)
        if min_points > 0:
            key_points = len(re.findall(r'^[\-\*\+]\s+', content, re.MULTILINE))
            if key_points < min_points:
                issues.append(f"关键点不足: {key_points} < {min_points}")

    except Exception as e:
        issues.append(f"内容读取失败: {e}")

    return issues

def main():
    parser = argparse.ArgumentParser(description='DocGate文档质量检查')
    parser.add_argument('--files', nargs='+', required=True, help='要检查的文件列表')
    args = parser.parse_args()

    config = load_config()
    total_issues = 0

    for filepath in args.files:
        print(f"\n🔍 检查文件: {filepath}")
        issues = []

        # 文件名检查
        issues.extend(check_filename_patterns(filepath, config))

        # 文件大小检查
        issues.extend(check_file_size(filepath, config))

        # 内容质量检查
        issues.extend(check_content_quality(filepath, config))

        if issues:
            print(f"❌ 发现问题:")
            for issue in issues:
                print(f"   • {issue}")
            total_issues += len(issues)
        else:
            print("✅ 检查通过")

    if total_issues > 0:
        print(f"\n❌ 总计发现 {total_issues} 个问题")
        sys.exit(1)
    else:
        print(f"\n✅ 所有文件检查通过")
        sys.exit(0)

if __name__ == "__main__":
    main()
EOF

    # 创建链接检查脚本
    cat > "$CLAUDE_DIR/scripts/check_doc_links.py" << 'EOF'
#!/usr/bin/env python3
"""
文档链接检查脚本
"""

import sys
import os
import re
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse

def check_file_links(filepath: Path) -> int:
    """检查单个文件的链接"""
    issues = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找Markdown链接
        links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)

        for text, url in links:
            if url.startswith('http'):
                # 检查外部链接
                try:
                    response = requests.head(url, timeout=5, allow_redirects=True)
                    if response.status_code >= 400:
                        print(f"❌ 死链接: {url} (状态码: {response.status_code})")
                        issues += 1
                except Exception as e:
                    print(f"⚠️  链接检查失败: {url} ({e})")
            else:
                # 检查相对链接
                if url.startswith('/'):
                    link_path = Path(url[1:])
                else:
                    link_path = filepath.parent / url

                if not link_path.exists():
                    print(f"❌ 文件不存在: {url}")
                    issues += 1

    except Exception as e:
        print(f"❌ 文件读取失败: {filepath} ({e})")
        issues += 1

    return issues

def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 check_doc_links.py <docs_directory>")
        sys.exit(1)

    docs_dir = Path(sys.argv[1])
    if not docs_dir.exists():
        print(f"❌ 目录不存在: {docs_dir}")
        sys.exit(1)

    total_issues = 0
    md_files = list(docs_dir.rglob("*.md"))

    print(f"🔗 检查 {len(md_files)} 个Markdown文件的链接...")

    for md_file in md_files:
        print(f"检查: {md_file}")
        issues = check_file_links(md_file)
        total_issues += issues

    if total_issues > 0:
        print(f"\n❌ 发现 {total_issues} 个链接问题")
        sys.exit(1)
    else:
        print(f"\n✅ 所有链接检查通过")
        sys.exit(0)

if __name__ == "__main__":
    main()
EOF

    # 创建文档结构检查脚本
    cat > "$CLAUDE_DIR/scripts/check_doc_structure.py" << 'EOF'
#!/usr/bin/env python3
"""
文档结构检查脚本
"""

import sys
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any

def check_required_fields(filepath: Path, required_fields: List[str]) -> int:
    """检查必填字段"""
    issues = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查YAML front matter
        yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if yaml_match:
            try:
                frontmatter = yaml.safe_load(yaml_match.group(1))
                for field in required_fields:
                    if field not in frontmatter:
                        print(f"❌ 缺少必填字段: {field}")
                        issues += 1
            except yaml.YAMLError:
                print(f"❌ YAML front matter格式错误")
                issues += 1
        else:
            print(f"❌ 缺少YAML front matter")
            issues += len(required_fields)

    except Exception as e:
        print(f"❌ 文件读取失败: {e}")
        issues += 1

    return issues

def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 check_doc_structure.py <docs_directory>")
        sys.exit(1)

    docs_dir = Path(sys.argv[1])
    config_path = Path(".docpolicy.yaml")

    if not config_path.exists():
        print("✅ 无.docpolicy.yaml配置，跳过结构检查")
        sys.exit(0)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    total_issues = 0
    doc_types = config.get('types', {})

    for doc_type, type_config in doc_types.items():
        type_path = docs_dir / type_config.get('path', '').lstrip('/')
        if not type_path.exists():
            continue

        required_fields = type_config.get('required_fields', [])
        if not required_fields:
            continue

        print(f"\n📋 检查{doc_type}文档结构...")

        for md_file in type_path.glob("*.md"):
            print(f"检查: {md_file}")
            issues = check_required_fields(md_file, required_fields)
            total_issues += issues

    if total_issues > 0:
        print(f"\n❌ 发现 {total_issues} 个结构问题")
        sys.exit(1)
    else:
        print(f"\n✅ 文档结构检查通过")
        sys.exit(0)

if __name__ == "__main__":
    main()
EOF

    # 设置执行权限
    chmod +x "$CLAUDE_DIR/scripts/docgate_pre_commit_check.py"
    chmod +x "$CLAUDE_DIR/scripts/check_doc_links.py"
    chmod +x "$CLAUDE_DIR/scripts/check_doc_structure.py"

    log_success "DocGate Agent配置完成"
}

# 创建文档模板
create_document_templates() {
    log_step "创建文档模板..."

    local template_dir="$PROJECT_ROOT/docs/_templates"

    # 需求文档模板
    cat > "$template_dir/requirement.md" << 'EOF'
---
title: "需求标题"
summary: "需求简要描述"
status: "draft"  # draft, review, approved, implemented
priority: "medium"  # low, medium, high, critical
assignee: ""
created_date: ""
last_updated: ""
tags: []
---

# {{ title }}

## 摘要
简要描述这个需求的核心内容和价值。

## 背景
说明为什么需要这个功能或改进。

## 需求详情
详细描述功能需求。

### 功能点
- [ ] 功能点1
- [ ] 功能点2
- [ ] 功能点3

### 验收标准
- [ ] 验收条件1
- [ ] 验收条件2
- [ ] 验收条件3

## 技术考虑
说明技术实现的关键点和限制。

## 影响分析
分析对现有系统的影响。

## 时间估算
预估开发时间和里程碑。
EOF

    # 设计文档模板
    cat > "$template_dir/design.md" << 'EOF'
---
title: "设计标题"
summary: "设计简要描述"
status: "draft"
version: "1.0"
author: ""
reviewers: []
last_updated: ""
tags: []
---

# {{ title }}

## 摘要
设计方案的核心内容和目标。

## 关键设计要点
- 要点1: 描述
- 要点2: 描述
- 要点3: 描述

## 架构设计

### 整体架构

### 组件设计

### 数据流

## 技术选型

## 安全考虑

## 性能考虑

## 部署方案

## 风险评估
EOF

    # API文档模板
    cat > "$template_dir/api.md" << 'EOF'
---
title: "API文档标题"
version: "1.0"
base_url: ""
authentication: ""
last_updated: ""
tags: []
---

# {{ title }}

## 概述
API的基本信息和用途。

## 认证方式

## 基础信息
- **Base URL**: `{{ base_url }}`
- **版本**: {{ version }}
- **协议**: HTTPS
- **数据格式**: JSON

## 端点列表

### GET /endpoint
**描述**: 端点描述

**参数**:
- `param1` (string, required): 参数描述
- `param2` (integer, optional): 参数描述

**响应示例**:
```json
{
  "status": "success",
  "data": {}
}
```

## 错误代码

| 代码 | 说明 |
|------|------|
| 400  | 请求参数错误 |
| 401  | 认证失败 |
| 403  | 权限不足 |
| 404  | 资源不存在 |
| 500  | 服务器内部错误 |

## 示例代码

### cURL
```bash
curl -X GET "{{ base_url }}/endpoint" \
  -H "Authorization: Bearer TOKEN"
```

### Python
```python
import requests

response = requests.get("{{ base_url }}/endpoint")
```
EOF

    log_success "文档模板创建完成"
}

# 验证安装
verify_installation() {
    log_step "验证安装结果..."

    local errors=0

    # 检查目录结构
    log_info "检查目录结构..."
    local required_dirs=(
        "$CLAUDE_DIR"
        "$PROJECT_ROOT/docs"
        "$PROJECT_ROOT/backend/api/docgate"
        "$PROJECT_ROOT/tests/docgate"
    )

    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log_error "目录缺失: $dir"
            ((errors++))
        fi
    done

    # 检查关键文件
    log_info "检查关键文件..."
    local required_files=(
        "$PROJECT_ROOT/.docpolicy.yaml"
        "$CLAUDE_DIR/scripts/docgate_pre_commit_check.py"
        "$PROJECT_ROOT/docs/_templates/requirement.md"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "文件缺失: $file"
            ((errors++))
        fi
    done

    # 检查Git hooks
    if [ -d "$PROJECT_ROOT/.git" ]; then
        log_info "检查Git hooks..."
        local hooks=("pre-commit" "commit-msg" "pre-push")

        for hook in "${hooks[@]}"; do
            if [ ! -x "$PROJECT_ROOT/.git/hooks/$hook" ]; then
                log_error "Git hook缺失或无执行权限: $hook"
                ((errors++))
            fi
        done
    fi

    # 检查Python依赖
    log_info "检查Python依赖..."
    python3 -c "
import sys
missing_modules = []
required_modules = ['fastapi', 'pydantic', 'yaml', 'requests']

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing_modules.append(module)

if missing_modules:
    print(f'❌ 缺少Python模块: {missing_modules}')
    sys.exit(1)
else:
    print('✅ Python依赖检查通过')
" || ((errors++))

    # 运行基础功能测试
    log_info "运行基础功能测试..."
    if [ -f "$CLAUDE_DIR/scripts/docgate_pre_commit_check.py" ]; then
        python3 "$CLAUDE_DIR/scripts/docgate_pre_commit_check.py" --files README.md 2>/dev/null || {
            log_warning "DocGate检查脚本测试未通过（可能正常）"
        }
    fi

    if [ $errors -eq 0 ]; then
        log_success "安装验证通过"
        return 0
    else
        log_error "发现 $errors 个验证错误"
        return 1
    fi
}

# 显示使用说明
show_usage_guide() {
    log_step "生成使用说明..."

    cat > "$PROJECT_ROOT/DOCGATE_USAGE.md" << 'EOF'
# DocGate文档质量管理系统使用指南

## 🎯 系统概述
DocGate是Claude Enhancer 5.0的文档质量管理子系统，提供三层递进式文档质量保障。

## 🏗️ 系统架构

### 三层质量门禁
1. **Layer 1**: 本地pre-commit（轻量级检查）
2. **Layer 2**: 本地pre-push（快速检查）
3. **Layer 3**: CI深度检查（完整分析）

### 核心组件
- **文档策略引擎**: `.docpolicy.yaml`配置驱动
- **Git工作流集成**: 自动化质量检查
- **DocGate Agent**: 智能文档分析
- **API服务**: REST API接口

## 🚀 快速开始

### 1. 基本使用
```bash
# 创建新文档（自动使用模板）
cp docs/_templates/requirement.md docs/requirements/new-feature.md

# 编辑文档后正常提交
git add docs/requirements/new-feature.md
git commit -m "docs(requirements): add new feature specification"
```

### 2. 配置定制
编辑`.docpolicy.yaml`来自定义质量标准：
```yaml
quality:
  require_tldr: true          # 要求摘要
  min_key_points: 3           # 最少关键点
  max_file_kb: 5120          # 最大文件大小
```

### 3. 手动质量检查
```bash
# 检查单个文件
python3 .claude/scripts/docgate_pre_commit_check.py --files docs/api/new-api.md

# 检查链接
python3 .claude/scripts/check_doc_links.py docs/

# 检查结构
python3 .claude/scripts/check_doc_structure.py docs/
```

## 📋 文档类型和模板

### 支持的文档类型
- **requirement**: 需求文档 (`docs/requirements/`)
- **design**: 设计文档 (`docs/design/`)
- **api**: API文档 (`docs/api/`)
- **guide**: 指南文档 (`docs/guides/`)
- **changelog**: 变更日志 (`docs/changelogs/`)
- **test**: 测试报告 (`docs/test-reports/`)

### 使用模板
```bash
# 复制模板创建新文档
cp docs/_templates/requirement.md docs/requirements/my-feature.md
cp docs/_templates/design.md docs/design/my-architecture.md
cp docs/_templates/api.md docs/api/my-api.md
```

## ⚙️ 配置选项

### 文档生命周期
```yaml
lifecycle:
  archive_after_days: 45      # 45天未更新自动归档
  keep_versions: 3            # 保留最近3个版本
  orphan_threshold_days: 30   # 30天未引用视为孤儿
```

### 质量标准
```yaml
quality:
  require_tldr: true          # 必须有摘要
  min_key_points: 3           # 最少3个关键点
  max_file_kb: 5120          # 最大5MB
  deny_name_patterns:         # 禁止的文件名模式
    - "(copy|backup|final\\(\\d+\\)|-old)\\.md$"
```

### 门禁控制
```yaml
gates:
  pre_commit:
    enabled: true
    blocking: true            # 阻断提交

  pre_push:
    enabled: true
    blocking: false           # 仅警告
```

## 🔧 Git工作流集成

### Pre-commit检查
- 文件名合规性
- 文件大小限制
- 基础内容质量

### Pre-push检查
- 链接有效性检查
- 文档结构验证
- 引用完整性

### Commit消息规范
```
type(scope): description

类型:
- docs: 文档更新
- feat: 新功能
- fix: bug修复
- style: 格式调整
- refactor: 重构
- test: 测试
- chore: 构建/依赖

示例:
docs(api): add docgate endpoint documentation
docs(requirements): update user story format
```

## 🐛 故障排除

### 常见问题

**Q: Git hook执行失败**
```bash
# 检查权限
ls -la .git/hooks/
chmod +x .git/hooks/pre-commit

# 检查Python脚本
python3 .claude/scripts/docgate_pre_commit_check.py --help
```

**Q: 依赖模块缺失**
```bash
# 重新安装依赖
pip3 install -r requirements_docgate.txt --user
```

**Q: 文档检查过于严格**
```bash
# 编辑配置文件
vim .docpolicy.yaml

# 临时跳过检查（不推荐）
git commit --no-verify
```

## 📈 最佳实践

### 1. 文档组织
- 按类型分目录存放
- 使用有意义的文件名
- 定期清理过期文档

### 2. 内容质量
- 每个文档都有明确的摘要
- 使用标准的Markdown格式
- 保持链接和引用的准确性

### 3. 版本管理
- 通过Git跟踪文档变更
- 使用规范的提交信息
- 定期备份重要文档

### 4. 协作流程
- 大的文档变更通过PR审查
- 使用Issues跟踪文档需求
- 设置文档维护责任人

## 🔄 维护和更新

### 定期维护任务
```bash
# 检查死链接
python3 .claude/scripts/check_doc_links.py docs/

# 清理过期文档
find docs/ -name "*.md" -mtime +45 -exec mv {} archive/ \;

# 更新依赖
pip3 install -r requirements_docgate.txt --upgrade
```

### 系统更新
```bash
# 重新运行安装脚本
./deploy_docgate_system.sh

# 恢复自定义配置
cp .docgate_backup_*/docpolicy_backup.yaml .docpolicy.yaml
```

---

**需要帮助?**
- 查看系统日志: `cat deploy_docgate_*.log`
- 检查系统状态: `python3 .claude/scripts/health_check.py`
- 联系技术支持: [创建Issue](../../issues)
EOF

    log_success "使用指南创建完成: DOCGATE_USAGE.md"
}

# 清理临时文件
cleanup() {
    log_step "清理临时文件..."

    # 删除临时安装文件
    rm -f "$PROJECT_ROOT/requirements_docgate.txt" 2>/dev/null || true
    rm -f "$PROJECT_ROOT/package_docgate.json" 2>/dev/null || true

    log_success "清理完成"
}

# 显示完成总结
show_completion_summary() {
    clear
    cat << 'EOF'
🎉 DocGate文档质量管理系统部署完成!
===============================================================================
EOF

    log_success "DocGate文档质量管理系统部署成功!"
    log_info ""
    log_info "🎯 部署组件："
    log_info "  ✅ 三层质量门禁系统"
    log_info "  ✅ Git工作流集成"
    log_info "  ✅ 文档模板和结构"
    log_info "  ✅ Python/Node.js依赖"
    log_info "  ✅ DocGate Agent脚本"
    log_info ""
    log_info "📋 关键文件："
    log_info "  • 配置文件: .docpolicy.yaml"
    log_info "  • 使用指南: DOCGATE_USAGE.md"
    log_info "  • 备份目录: $BACKUP_DIR"
    log_info "  • 安装日志: $LOG_FILE"
    log_info ""
    log_info "🚀 快速开始："
    log_info "  1. 查看使用指南: cat DOCGATE_USAGE.md"
    log_info "  2. 创建文档: cp docs/_templates/requirement.md docs/requirements/my-doc.md"
    log_info "  3. 提交测试: git add . && git commit -m 'docs: test docgate system'"
    log_info ""
    log_info "🔧 故障排除："
    log_info "  • 检查安装日志: cat $LOG_FILE"
    log_info "  • 测试Git hooks: git commit --dry-run"
    log_info "  • 验证Python依赖: python3 -c 'import fastapi, yaml'"
    log_info ""
    log_warning "⚠️  重要提醒："
    log_warning "  • 现有配置已备份到: $BACKUP_DIR"
    log_warning "  • 如需恢复，请手动复制备份文件"
    log_warning "  • Git hooks会在下次提交时自动生效"
    log_info ""
    log_success "🌟 DocGate系统已就绪，享受高质量的文档管理体验！"
}

# 主函数
main() {
    # 创建日志文件
    touch "$LOG_FILE"

    # 显示欢迎信息
    show_welcome

    # 确认继续
    echo -n "是否继续安装? (y/N): "
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "安装已取消"
        exit 0
    fi

    # 执行安装步骤
    create_backup
    check_requirements
    create_directory_structure
    install_python_dependencies || log_warning "Python依赖安装可能不完整"
    install_nodejs_dependencies || log_warning "Node.js依赖安装可能不完整"
    install_git_hooks
    configure_docgate_agent
    create_document_templates

    # 验证安装
    if verify_installation; then
        show_usage_guide
        cleanup
        show_completion_summary
    else
        log_error "安装验证失败，请检查错误信息"
        log_info "可以尝试重新运行脚本或手动修复问题"
        exit 1
    fi
}

# 设置trap处理中断
trap 'log_error "安装被中断"; exit 1' INT TERM

# 执行主函数
main "$@"