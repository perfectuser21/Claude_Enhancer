#!/bin/bash
# Claude Enhancer 错误处理Hook
# 提供友好的错误提示和恢复建议（非阻塞）

set -e

# 读取输入
INPUT=$(cat)

# 提取错误信息
ERROR_MSG=$(echo "$INPUT" | grep -oP '"error"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")

if [ -n "$ERROR_MSG" ]; then
    echo "🔧 错误处理助手"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 分析错误类型并提供建议
    case "$ERROR_MSG" in
        *"command not found"*)
            echo "💡 建议: 检查命令是否存在或安装缺失的工具"
            ;;
        *"permission denied"*)
            echo "💡 建议: 检查文件权限或使用sudo"
            ;;
        *"file not found"*)
            echo "💡 建议: 确认文件路径是否正确"
            ;;
        *"timeout"*)
            echo "💡 建议: 增加超时时间或优化性能"
            ;;
        *"connection"*)
            echo "💡 建议: 检查网络连接和API端点"
            ;;
        *)
            echo "💡 建议: 查看详细日志了解错误原因"
            ;;
    esac

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

# 非阻塞，始终返回成功
exit 0