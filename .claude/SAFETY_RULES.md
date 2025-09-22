# 🛡️ 安全规则 - 防止危险操作

## 🔴 绝对禁止自动执行的操作

### 1. 生产部署
```bash
# ❌ 绝对不要自动执行
git push origin main --force
kubectl apply -f production.yaml
docker push prod-image

# ✅ 正确做法
echo "部署命令已准备："
echo "git push origin main"
echo "请人工确认后执行"
```

### 2. 数据库危险操作
```sql
-- ❌ 绝对不要自动执行
DROP DATABASE production;
DELETE FROM users;
TRUNCATE TABLE orders;

-- ✅ 正确做法
-- 生成SQL但不执行
-- 要求用户确认
```

### 3. 文件系统危险操作
```bash
# ❌ 绝对不要自动执行
rm -rf /
rm -rf ~
rm -rf .git

# ✅ 正确做法
# 只删除项目内的临时文件
rm /tmp/test_*.tmp
```

## ⚠️ 需要用户确认的操作

### Phase 7 部署相关
- 推送到main分支
- 触发CI/CD
- 修改生产配置
- 数据库迁移

### 示例代码
```python
def phase_7_deploy():
    print("📋 部署准备完成，需要执行以下操作：")
    print("1. git push origin main")
    print("2. 触发部署流水线")
    print("")
    print("⚠️ 这些操作会影响生产环境")
    print("请手动执行或明确指示我执行")

    # 不自动执行，等待用户确认
    # if user_confirms:
    #     execute_deployment()
```

## ✅ 可以自动执行的安全操作

### Phase 0-6 的所有操作
- 创建feature分支
- 编写代码
- 运行测试
- 提交到feature分支
- 创建PR

### 安全原则
1. **只在feature分支工作**
2. **不修改main/master分支**
3. **不执行删除操作（除了明确的临时文件）**
4. **不修改生产配置**
5. **不自动触发部署**

## 🔍 检查机制

每次执行前检查：
```python
def is_safe_operation(command):
    dangerous_patterns = [
        "rm -rf",
        "DROP DATABASE",
        "DELETE FROM",
        "push.*main",
        "push.*master",
        "--force",
        "kubectl.*production",
        "docker push"
    ]

    for pattern in dangerous_patterns:
        if pattern in command:
            return False, "危险操作，需要用户确认"

    return True, "安全操作"
```

## 💡 最佳实践

1. **生成命令但不执行**
   ```python
   print("建议的部署命令：")
   print("sh deploy.sh --env=staging")
   # 不自动执行
   ```

2. **使用staging环境测试**
   ```bash
   # 自动部署到staging可以
   git push origin feature/xxx

   # 但不自动部署到production
   # git push origin main  # 需要用户确认
   ```

3. **明确告知风险**
   ```
   ⚠️ 警告：此操作将影响生产环境
   - 影响用户数：10000+
   - 数据库变更：是
   - 需要回滚计划：是

   确定要继续吗？
   ```