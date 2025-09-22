# 🧹 Claude Enhancer 文件清理策略

## 🎯 目标
防止开发过程中产生垃圾文件，并自动清理临时文件

## 📋 垃圾文件类型识别

### 1. Python缓存文件
```
*.pyc
*.pyo
__pycache__/
*.py[cod]
*$py.class
```

### 2. 备份和临时文件
```
*.bak
*.backup
*.old
*.tmp
*.temp
*.swp
*~
.DS_Store
Thumbs.db
```

### 3. 测试文件
```
test_*.txt
test_*.md
*_test_output.*
test_results/
```

### 4. 错误创建的API代码
```
backend/api/routes/*_routes.py (除了必要的)
backend/models/todo_*.py
backend/schemas/todo_*.py
database/*todo*.sql
test/*todo*.py
```

## 🔧 清理脚本

### 即时清理脚本
```bash
#!/bin/bash
# cleanup.sh - 立即清理所有垃圾文件

echo "🧹 开始清理垃圾文件..."

# Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# 备份文件
find . -type f -name "*.bak" -delete 2>/dev/null
find . -type f -name "*.backup" -delete 2>/dev/null
find . -type f -name "*.old" -delete 2>/dev/null

# 临时文件
find . -type f -name "*.tmp" -delete 2>/dev/null
find . -type f -name "*.temp" -delete 2>/dev/null
find . -type f -name "*.swp" -delete 2>/dev/null
find . -type f -name "*~" -delete 2>/dev/null

# 系统文件
find . -type f -name ".DS_Store" -delete 2>/dev/null
find . -type f -name "Thumbs.db" -delete 2>/dev/null

echo "✅ 清理完成！"
```

### 安全清理脚本（需确认）
```bash
#!/bin/bash
# safe_cleanup.sh - 列出文件并确认后清理

echo "🔍 扫描垃圾文件..."

# 收集所有垃圾文件
FILES_TO_DELETE=$(find . \
    \( -name "*.pyc" -o -name "*.pyo" -o -name "__pycache__" \
    -o -name "*.bak" -o -name "*.backup" -o -name "*.old" \
    -o -name "*.tmp" -o -name "*.temp" -o -name "*.swp" \
    -o -name "*~" -o -name ".DS_Store" -o -name "Thumbs.db" \) \
    -not -path "./.git/*" 2>/dev/null)

if [ -z "$FILES_TO_DELETE" ]; then
    echo "✅ 没有垃圾文件需要清理"
    exit 0
fi

echo "📋 发现以下垃圾文件："
echo "$FILES_TO_DELETE" | head -20
TOTAL=$(echo "$FILES_TO_DELETE" | wc -l)
echo "共 $TOTAL 个文件"

read -p "确认删除？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "$FILES_TO_DELETE" | xargs rm -rf
    echo "✅ 清理完成！"
else
    echo "❌ 取消清理"
fi
```

## 🚀 自动化清理机制

### 1. Git Hooks集成
在`.git/hooks/post-commit`中添加：
```bash
#!/bin/bash
# 每次提交后自动清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
```

### 2. .gitignore优化
确保`.gitignore`包含：
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.pyc
*.pyo

# Backup files
*.bak
*.backup
*.old
*~

# Temporary files
*.tmp
*.temp
*.swp
.DS_Store
Thumbs.db

# Test outputs
test_*.txt
test_*.md
test_results/
test_output/

# IDE
.vscode/
.idea/
*.sublime-*

# Logs
*.log
logs/
```

### 3. Phase 5后自动清理
在Phase 5（代码提交）时自动执行：
```bash
# 提交前清理
cleanup_before_commit() {
    echo "🧹 提交前清理..."

    # 清理Python缓存
    find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null

    # 清理备份文件
    find . -name "*.bak" -delete 2>/dev/null

    # 清理临时文件
    find . -name "*.tmp" -delete 2>/dev/null
}
```

## 📊 清理报告生成

### 定期清理报告
```bash
#!/bin/bash
# cleanup_report.sh - 生成清理报告

echo "📊 垃圾文件报告"
echo "================"
echo ""

echo "Python缓存："
find . -name "*.pyc" -o -name "__pycache__" | wc -l

echo "备份文件："
find . -name "*.bak" -o -name "*.backup" | wc -l

echo "临时文件："
find . -name "*.tmp" -o -name "*.temp" | wc -l

echo "测试文件："
find . -name "test_*.txt" -o -name "test_*.md" | wc -l

echo ""
echo "磁盘占用："
du -sh . 2>/dev/null
```

## 🛡️ 预防措施

### 1. 开发规范
- 不创建不必要的测试文件
- 测试输出使用内存或临时目录
- 及时清理开发过程产物

### 2. Agent提示
在Agent任务中添加：
```yaml
cleanup_reminder: |
  完成任务后请：
  1. 删除测试文件
  2. 清理临时输出
  3. 移除调试日志
```

### 3. CI/CD集成
```yaml
# .github/workflows/cleanup.yml
name: Cleanup
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # 每周清理

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run cleanup
        run: |
          ./cleanup.sh
          git add -A
          git diff --staged --quiet || git commit -m "🧹 Auto cleanup"
          git push
```

## 💡 最佳实践

### 1. 实时清理
- Phase 3后：清理测试输出
- Phase 5前：清理缓存文件
- Phase 7后：清理部署临时文件

### 2. 文件命名
- 临时文件加`.tmp`后缀
- 测试文件放`test_output/`
- 备份使用版本控制而非`.bak`

### 3. 监控提醒
```python
# 文件监控脚本
import os
import time

def check_garbage_files():
    """检查垃圾文件数量"""
    patterns = ['*.pyc', '*.bak', '*.tmp']
    total = 0

    for pattern in patterns:
        # 使用glob查找
        files = glob.glob(f'**/{pattern}', recursive=True)
        total += len(files)

    if total > 50:
        print(f"⚠️ 垃圾文件过多({total})，建议清理")
        return False
    return True
```

## 🔄 定期维护

### 每日清理
```bash
# 添加到crontab
0 2 * * * cd /path/to/project && ./cleanup.sh
```

### 每周深度清理
```bash
# 深度清理包括日志和缓存
0 3 * * 0 cd /path/to/project && ./deep_cleanup.sh
```

### 月度存档
```bash
# 存档旧文件而非删除
0 4 1 * * cd /path/to/project && ./archive_old_files.sh
```

---

**记住**：预防胜于清理，良好的开发习惯能减少90%的垃圾文件！