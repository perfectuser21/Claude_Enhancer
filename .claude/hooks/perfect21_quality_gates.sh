#!/bin/bash
# Perfect21 Quality Gates
# 代码质量、测试、安全等质量门检查

set -e

# 读取输入
INPUT=$(cat)

# 质量检查配置
MIN_TEST_COVERAGE=80
MAX_COMPLEXITY=10
MAX_DUPLICATE=5

# 检测操作类型
detect_operation() {
    local input="$1"

    # Git操作检测
    if echo "$input" | grep -qiE "git (commit|push|merge)"; then
        echo "git_operation"
        return
    fi

    # 代码编辑检测
    if echo "$input" | grep -qiE "Edit|Write|MultiEdit"; then
        echo "code_edit"
        return
    fi

    # 测试执行检测
    if echo "$input" | grep -qiE "test|pytest|jest|mocha|npm test"; then
        echo "test_run"
        return
    fi

    # 构建检测
    if echo "$input" | grep -qiE "build|compile|npm run build|make"; then
        echo "build"
        return
    fi

    echo "general"
}

OPERATION=$(detect_operation "$INPUT")

# Git提交前检查
check_git_commit() {
    echo "🔍 Perfect21 Git提交前质量检查" >&2
    echo "═══════════════════════════════════════════" >&2

    # 检查是否有未运行的测试
    if echo "$INPUT" | grep -qiE "git commit" && ! echo "$INPUT" | grep -qiE "test|lint"; then
        echo "" >&2
        echo "⚠️ 警告：提交前未运行测试" >&2
        echo "" >&2
        echo "📋 建议的检查清单：" >&2
        echo "  □ 运行单元测试 (npm test / pytest)" >&2
        echo "  □ 运行lint检查 (npm run lint / flake8)" >&2
        echo "  □ 检查类型 (npm run typecheck / mypy)" >&2
        echo "  □ 运行安全扫描" >&2
        echo "" >&2
        echo "💡 提示：配置pre-commit hooks可自动执行这些检查" >&2
        echo "" >&2
    fi

    # 检查提交消息格式
    if echo "$INPUT" | grep -qiE "git commit"; then
        COMMIT_MSG=$(echo "$INPUT" | grep -oP '(feat|fix|docs|test|refactor|perf|chore|style):' || echo "")
        if [ -z "$COMMIT_MSG" ]; then
            echo "" >&2
            echo "📝 提交消息格式提醒：" >&2
            echo "  使用标准前缀: feat|fix|docs|test|refactor|perf|chore" >&2
            echo "  例: feat: 添加用户登录功能" >&2
            echo "" >&2
        fi
    fi

    echo "═══════════════════════════════════════════" >&2
}

# 代码编辑后检查
check_code_edit() {
    # 检测编辑的文件类型
    FILE_PATH=$(echo "$INPUT" | grep -oP '"file_path"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1)

    if [ -n "$FILE_PATH" ]; then
        FILE_EXT="${FILE_PATH##*.}"

        echo "📝 Perfect21 代码质量提醒" >&2
        echo "═══════════════════════════════════════════" >&2
        echo "" >&2
        echo "✏️ 编辑文件: $(basename $FILE_PATH)" >&2
        echo "" >&2

        case "$FILE_EXT" in
            js|ts|jsx|tsx)
                echo "JavaScript/TypeScript 最佳实践：" >&2
                echo "  • 使用const/let代替var" >&2
                echo "  • 优先使用async/await" >&2
                echo "  • 添加类型注解(TypeScript)" >&2
                echo "  • 处理错误情况" >&2
                ;;
            py)
                echo "Python 最佳实践：" >&2
                echo "  • 遵循PEP 8规范" >&2
                echo "  • 使用类型提示" >&2
                echo "  • 编写docstring" >&2
                echo "  • 处理异常" >&2
                ;;
            go)
                echo "Go 最佳实践：" >&2
                echo "  • 处理所有错误" >&2
                echo "  • 使用defer清理资源" >&2
                echo "  • 避免全局变量" >&2
                echo "  • 编写测试" >&2
                ;;
            *)
                echo "通用最佳实践：" >&2
                echo "  • 保持代码简洁" >&2
                echo "  • 添加必要注释" >&2
                echo "  • 遵循项目规范" >&2
                ;;
        esac

        echo "" >&2
        echo "🔧 编辑后建议运行：" >&2
        echo "  • 格式化代码 (prettier/black/gofmt)" >&2
        echo "  • 运行lint检查" >&2
        echo "  • 运行相关测试" >&2
        echo "" >&2
        echo "═══════════════════════════════════════════" >&2
    fi
}

# 测试执行检查
check_test_run() {
    echo "🧪 Perfect21 测试执行监控" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2
    echo "📊 测试质量标准：" >&2
    echo "  • 最低覆盖率: ${MIN_TEST_COVERAGE}%" >&2
    echo "  • 所有测试必须通过" >&2
    echo "  • 包含单元测试和集成测试" >&2
    echo "" >&2

    # 检查是否有失败处理
    if echo "$INPUT" | grep -qiE "test.*fail|fail.*test"; then
        echo "⚠️ 测试失败处理建议：" >&2
        echo "  1. 分析失败原因" >&2
        echo "  2. 修复代码或测试" >&2
        echo "  3. 重新运行验证" >&2
        echo "  4. 确保CI/CD通过" >&2
        echo "" >&2
    fi

    echo "═══════════════════════════════════════════" >&2
}

# 构建检查
check_build() {
    echo "🔨 Perfect21 构建质量检查" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2
    echo "📋 构建检查清单：" >&2
    echo "  □ 无编译错误" >&2
    echo "  □ 无类型错误" >&2
    echo "  □ 依赖版本锁定" >&2
    echo "  □ 构建产物优化" >&2
    echo "" >&2

    if echo "$INPUT" | grep -qiE "warning"; then
        echo "⚠️ 发现警告，建议处理以保持代码质量" >&2
        echo "" >&2
    fi

    echo "═══════════════════════════════════════════" >&2
}

# 安全检查提醒
security_check() {
    # 检测敏感操作
    if echo "$INPUT" | grep -qiE "password|secret|token|key|credential|api.?key"; then
        echo "🔒 Perfect21 安全提醒" >&2
        echo "═══════════════════════════════════════════" >&2
        echo "" >&2
        echo "⚠️ 检测到可能的敏感信息操作" >&2
        echo "" >&2
        echo "安全检查清单：" >&2
        echo "  ✓ 不要硬编码密码或密钥" >&2
        echo "  ✓ 使用环境变量存储敏感信息" >&2
        echo "  ✓ 密码必须加密存储" >&2
        echo "  ✓ 敏感日志需要脱敏" >&2
        echo "  ✓ API密钥不要提交到代码库" >&2
        echo "" >&2
        echo "═══════════════════════════════════════════" >&2
    fi
}

# 根据操作类型执行相应检查
case "$OPERATION" in
    git_operation)
        check_git_commit
        ;;
    code_edit)
        check_code_edit
        ;;
    test_run)
        check_test_run
        ;;
    build)
        check_build
        ;;
esac

# 始终执行安全检查
security_check

# 记录质量检查
LOG_FILE="/tmp/perfect21_quality_log.txt"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Operation: $OPERATION" >> "$LOG_FILE"

# 输出原始内容
echo "$INPUT"
exit 0