#!/bin/bash
# DocGate部署验证测试脚本

set -e

echo "🧪 DocGate部署验证测试"
echo "========================"

# 检查主要文件是否存在
echo "📋 检查关键文件..."

files_to_check=(
    "deploy_docgate_system.sh"
    ".claude/scripts/health_check.py"
    "DEPLOY_README.md"
    ".docpolicy.yaml"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 缺失"
        exit 1
    fi
done

# 检查脚本权限
echo -e "\n🔧 检查脚本权限..."
if [ -x "deploy_docgate_system.sh" ]; then
    echo "✅ deploy_docgate_system.sh 有执行权限"
else
    echo "❌ deploy_docgate_system.sh 无执行权限"
    exit 1
fi

if [ -x ".claude/scripts/health_check.py" ]; then
    echo "✅ health_check.py 有执行权限"
else
    echo "❌ health_check.py 无执行权限"
    exit 1
fi

# 检查脚本语法
echo -e "\n🔍 检查脚本语法..."

# 检查bash脚本语法
if bash -n deploy_docgate_system.sh; then
    echo "✅ deploy_docgate_system.sh 语法正确"
else
    echo "❌ deploy_docgate_system.sh 语法错误"
    exit 1
fi

# 检查Python脚本语法
if python3 -m py_compile .claude/scripts/health_check.py; then
    echo "✅ health_check.py 语法正确"
else
    echo "❌ health_check.py 语法错误"
    exit 1
fi

# 验证配置文件格式
echo -e "\n📄 验证配置文件格式..."
if python3 -c "import yaml; yaml.safe_load(open('.docpolicy.yaml'))" 2>/dev/null; then
    echo "✅ .docpolicy.yaml 格式正确"
else
    echo "❌ .docpolicy.yaml 格式错误"
    exit 1
fi

# 显示文档大小统计
echo -e "\n📊 文档统计信息..."
echo "部署脚本大小: $(wc -l < deploy_docgate_system.sh) 行"
echo "健康检查脚本大小: $(wc -l < .claude/scripts/health_check.py) 行"
echo "配置文件大小: $(wc -l < .docpolicy.yaml) 行"

echo -e "\n✅ 所有验证测试通过！"
echo "🚀 可以安全运行: ./deploy_docgate_system.sh"