#!/bin/bash
# Git Worktree Manager - 智能管理并行开发环境

PROJECT_ROOT="${CLAUDE_ENHANCER_HOME:-$(pwd)}"
PROJECT_NAME=$(basename "$PROJECT_ROOT")

# 显示帮助
show_help() {
    echo "🌳 Git Worktree Manager"
    echo ""
    echo "Usage:"
    echo "  create <feature> - Create new worktree for feature"
    echo "  list            - List all worktrees"
    echo "  remove <feature> - Remove worktree"
    echo "  switch <feature> - Switch to worktree directory"
    echo ""
}

# 创建worktree
create_worktree() {
    local feature=$1
    local branch_name="feature/$feature"
    local worktree_dir="../${PROJECT_NAME}-${feature}"

    echo "📦 Creating worktree for: $feature"
    echo "  Directory: $worktree_dir"
    echo "  Branch: $branch_name"

    # 检查分支是否存在
    if git show-ref --verify --quiet "refs/heads/$branch_name"; then
        echo "  Using existing branch: $branch_name"
        git worktree add "$worktree_dir" "$branch_name"
    else
        echo "  Creating new branch: $branch_name"
        git worktree add -b "$branch_name" "$worktree_dir"
    fi

    if [ $? -eq 0 ]; then
        echo "✅ Worktree created successfully!"
        echo ""
        echo "Next steps:"
        echo "  cd $worktree_dir"
        echo "  code .  # Open in VSCode"
        echo ""
        echo "💡 Tip: You can now develop $feature independently!"
    fi
}

# 列出所有worktrees
list_worktrees() {
    echo "🌳 Current worktrees:"
    echo ""
    git worktree list | while read -r line; do
        dir=$(echo "$line" | awk '{print $1}')
        branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')
        feature=$(basename "$dir" | sed "s/${PROJECT_NAME}-//")

        if [[ "$dir" == "$PROJECT_ROOT" ]]; then
            echo "📍 $dir [$branch] (main)"
        else
            echo "   $dir [$branch] (feature: $feature)"
        fi
    done
}

# 删除worktree
remove_worktree() {
    local feature=$1
    local worktree_dir="../${PROJECT_NAME}-${feature}"

    echo "🗑️ Removing worktree: $worktree_dir"
    git worktree remove "$worktree_dir"

    if [ $? -eq 0 ]; then
        echo "✅ Worktree removed successfully!"

        # 询问是否删除分支
        echo ""
        echo "Branch feature/$feature still exists."
        echo "Delete branch? (y/n)"
        read -r response
        if [[ "$response" == "y" ]]; then
            git branch -d "feature/$feature" 2>/dev/null || \
            git branch -D "feature/$feature"
        fi
    fi
}

# 切换到worktree目录
switch_worktree() {
    local feature=$1
    local worktree_dir="../${PROJECT_NAME}-${feature}"

    if [ -d "$worktree_dir" ]; then
        echo "📂 Switching to: $worktree_dir"
        cd "$worktree_dir"
        exec $SHELL
    else
        echo "❌ Worktree not found: $worktree_dir"
        echo "Available worktrees:"
        list_worktrees
    fi
}

# 主逻辑
case "${1:-help}" in
    create)
        create_worktree "$2"
        ;;
    list)
        list_worktrees
        ;;
    remove)
        remove_worktree "$2"
        ;;
    switch)
        switch_worktree "$2"
        ;;
    *)
        show_help
        ;;
esac