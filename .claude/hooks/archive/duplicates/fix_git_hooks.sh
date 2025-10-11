#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Git Hooks一致性修复脚本

echo "🔧 修复Git Hooks执行一致性问题"

# 1. 确保hooks有正确的shebang
for hook in .git/hooks/pre-commit .git/hooks/commit-msg .git/hooks/pre-push; do
    if [ -f "$hook" ]; then
        # 确保第一行是正确的shebang
        if ! head -n1 "$hook" | grep -q "^#!/bin/bash"; then
            echo "修复 $hook 的shebang..."
            sed -i '1s/^/#!/bin/bash\n/' "$hook"
        fi

        # 确保有执行权限
        chmod +x "$hook"
        echo "✅ $hook 已修复"
    fi
done

# 2. 创建hooks诊断脚本
cat > .git/hooks/test-hooks.sh << 'EOF'
#!/bin/bash
echo "=== Git Hooks诊断 ==="
echo "当前目录: $(pwd)"
echo "Git目录: $(git rev-parse --git-dir)"
echo "Claude Enhancer路径: $PERFECT21_HOME"

# 测试每个hook
for hook in pre-commit commit-msg pre-push; do
    if [ -f ".git/hooks/$hook" ]; then
        echo "✅ $hook 存在"
        ls -la ".git/hooks/$hook"
    else
        echo "❌ $hook 不存在"
    fi
done
EOF

chmod +x .git/hooks/test-hooks.sh

# 3. 设置环境变量
echo "export PERFECT21_HOME=$(pwd)" >> ~/.bashrc

echo "✅ Git Hooks一致性问题已修复"
echo "运行 .git/hooks/test-hooks.sh 进行诊断"