#!/bin/bash
# Quality Enforcer - 确保高质量输出

INPUT=$(cat)

echo "🎯 Quality Mode: Comprehensive Analysis Required" >&2
echo "" >&2

# 检测任务类型并强制质量流程
if echo "$INPUT" | grep -qi "implement\|create\|build\|develop"; then
    echo "📋 Mandatory Quality Process:" >&2
    echo "" >&2
    echo "1️⃣ Requirements Analysis (必须)" >&2
    echo "   - User needs clarification" >&2
    echo "   - Success criteria definition" >&2
    echo "" >&2
    echo "2️⃣ Architecture Design (必须)" >&2
    echo "   - System design" >&2
    echo "   - Technology selection" >&2
    echo "   - Security considerations" >&2
    echo "" >&2
    echo "3️⃣ Implementation (必须)" >&2
    echo "   - Code quality" >&2
    echo "   - Error handling" >&2
    echo "   - Performance optimization" >&2
    echo "" >&2
    echo "4️⃣ Testing (必须)" >&2
    echo "   - Unit tests" >&2
    echo "   - Integration tests" >&2
    echo "   - Edge cases" >&2
    echo "" >&2
    echo "5️⃣ Documentation (必须)" >&2
    echo "   - Code comments" >&2
    echo "   - User guide" >&2
    echo "   - API documentation" >&2
    echo "" >&2
    echo "⚡ Minimum Required Agents: 5" >&2
    echo "   - architect + developer + tester + security + documenter" >&2
    echo "" >&2
fi

# 对简单查询也要求完整性
if echo "$INPUT" | grep -qi "what\|how\|why\|explain"; then
    echo "📚 For best explanation, using multiple perspectives:" >&2
    echo "   - Technical explanation" >&2
    echo "   - Practical examples" >&2
    echo "   - Common pitfalls" >&2
    echo "   - Best practices" >&2
    echo "" >&2
fi

echo "$INPUT"