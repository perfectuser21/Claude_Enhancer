# 代码优先政策

## 强制规则：70%代码 + 30%文档

### ❌ 禁止的行为
1. 创建纯文档任务（除非用户明确要求）
2. 生成README/GUIDE等文档（除非必要）
3. 过度设计而不实现

### ✅ 强制要求
1. **每个Agent必须产出可运行代码**
2. **文档只在以下情况生成**：
   - API文档（自动从代码生成）
   - 测试报告（测试执行后生成）
   - 必要的配置说明

### 代码实现检查清单
每个Phase结束前必须确认：
- [ ] 生成了实际可运行的代码？
- [ ] 代码有对应的测试？
- [ ] 配置文件完整？
- [ ] 可以立即运行？

### Agent输出要求
```yaml
backend-architect:
  ❌ 不要: 10页架构文档
  ✅ 要: app.py + models.py + 简短注释

api-designer:
  ❌ 不要: 详细的API规范文档
  ✅ 要: routes.py + 自动生成的OpenAPI

test-engineer:
  ❌ 不要: 测试策略文档
  ✅ 要: test_*.py 可运行测试文件

technical-writer:
  ❌ 不要: 独立文档文件
  ✅ 要: 代码内注释 + docstring
```

## 执行示例

### 错误示例 ❌
```python
# 生成了设计文档
"""
这个系统将包含以下组件：
1. 用户认证模块
2. 数据处理模块
3. API接口模块
...10页设计文档...
"""
```

### 正确示例 ✅
```python
# auth.py - 实际可运行的认证模块
from fastapi import FastAPI, Depends, HTTPException
from jose import JWTError, jwt

app = FastAPI()

@app.post("/login")
async def login(username: str, password: str):
    """用户登录接口"""
    # 实际的认证逻辑
    if verify_password(password, user.password_hash):
        return {"access_token": create_jwt_token(username)}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# 可以立即运行：python auth.py
```

## 度量标准
- 代码行数 / 总行数 > 70%
- 可执行文件 / 总文件 > 80%
- 测试覆盖率 > 80%
- 文档仅限必要说明