# 📊 输出长度控制策略

## 问题分析
Agent输出可能超过32000 token限制，导致任务中断。

## 解决方案

### 方案1：Agent指令优化（推荐）
在调用Agent时明确限制输出长度：

```python
# ✅ 正确：明确要求简洁输出
<invoke name="Task">
  <parameter name="prompt">
    分析认证系统需求。

    输出要求：
    - 最多500字总结
    - 列出5-10个关键点
    - 不要详细代码示例
    - 只输出核心结论
  </parameter>
</invoke>

# ❌ 错误：没有输出限制
<invoke name="Task">
  <parameter name="prompt">
    设计完整的认证系统，包括所有细节。
  </parameter>
</invoke>
```

### 方案2：分阶段执行
将大任务分解成多个小任务：

```python
# 不是一次要求全部
# 而是分步骤
Step 1: 只要求架构设计概要（500字）
Step 2: 只要求核心API列表（10个端点）
Step 3: 只要求关键代码片段（3个函数）
```

### 方案3：使用文件输出
让Agent将详细内容写入文件，只返回摘要：

```python
<parameter name="prompt">
  设计认证系统架构。

  要求：
  1. 详细设计写入 /docs/auth_design.md
  2. 只返回200字的执行摘要
  3. 列出创建的文件路径
</parameter>
```

### 方案4：输出格式控制

```python
# 使用结构化输出
输出格式：
- 任务：[20字以内]
- 状态：[完成/失败]
- 关键结果：[3-5个要点，每个20字]
- 文件：[创建的文件列表]
- 下一步：[50字以内]
```

### 方案5：环境变量配置
```bash
# 设置更大的输出限制（如果需要）
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=50000

# 或在任务中动态控制
export AGENT_OUTPUT_LIMIT=1000
```

## 实施建议

### 立即采用：
1. **所有Agent调用都加输出限制**
   ```
   输出要求：
   - 摘要：200字以内
   - 详细内容：写入文件
   - 只返回核心信息
   ```

2. **使用分页思维**
   - 获取列表时：只要前10个
   - 生成代码时：只要核心函数
   - 写文档时：只要大纲

3. **监控输出长度**
   ```python
   if len(output) > 30000:
       # 截断并提示
       return output[:30000] + "\n... [输出过长已截断]"
   ```

## 标准Agent调用模板

```xml
<invoke name="Task">
  <parameter name="subagent_type">backend-architect</parameter>
  <parameter name="prompt">
    任务：设计用户认证模块

    输出要求：
    1. 摘要（100字）说明设计方案
    2. 列出5个核心组件名称
    3. 创建详细设计文档到 /docs/auth_design.md
    4. 返回总字数不超过500字

    注意：详细代码和文档写入文件，不要在输出中包含
  </parameter>
</invoke>
```

## 紧急处理

如果遇到输出过长：
1. 立即中断当前Agent
2. 重新调用，加上输出限制
3. 要求只返回摘要
4. 详细内容写入文件