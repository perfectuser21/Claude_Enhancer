# Perfect21性能优化快速参考手册

## 🚀 快速开始

### 立即使用性能优化

```bash
# 一键优化所有性能
python3 main/performance_cli.py optimize

# 查看性能状态
python3 main/performance_cli.py status

# 启动自动优化（后台运行）
python3 main/performance_cli.py auto start
```

## 📋 常用命令

### CLI命令速查

```bash
# 性能优化
python3 main/performance_cli.py optimize                # 全面优化
python3 main/performance_cli.py optimize --memory       # 只优化内存
python3 main/performance_cli.py optimize --cache        # 只优化缓存
python3 main/performance_cli.py optimize --git          # 只优化Git操作

# 性能分析
python3 main/performance_cli.py analyze                 # 生成性能报告
python3 main/performance_cli.py analyze --save report.json  # 保存报告

# 系统监控
python3 main/performance_cli.py status                  # 查看状态
python3 main/performance_cli.py status --detailed       # 详细信息

# 基准测试
python3 main/performance_cli.py benchmark               # 运行测试
python3 main/performance_cli.py benchmark --save results.json  # 保存结果

# 自动优化控制
python3 main/performance_cli.py auto start              # 启动自动优化
python3 main/performance_cli.py auto stop               # 停止自动优化
python3 main/performance_cli.py auto status             # 查看状态
```

## 💻 Python API速查

### 基本用法

```python
import asyncio
from modules.enhanced_performance_optimizer import (
    optimize_agent_execution,
    batch_git_operations,
    optimize_memory,
    get_performance_report,
    optimized_execution,
    start_performance_optimization
)

async def quick_example():
    # 1. 启动自动优化
    start_performance_optimization()

    # 2. 优化Agent执行
    result = await optimize_agent_execution('my-agent', {'key': 'value'})

    # 3. 批量Git操作
    git_ops = [('status', []), ('branch', []), ('log', ['--oneline', '-5'])]
    operation_ids = batch_git_operations(git_ops)

    # 4. 内存优化
    memory_result = await optimize_memory()

    # 5. 获取性能报告
    report = get_performance_report()
    print(f"缓存命中率: {report['cache_stats']['hit_rate']}")

# 运行示例
asyncio.run(quick_example())
```

### 优化上下文使用

```python
async def context_example():
    # 在优化上下文中执行任务
    async with optimized_execution() as optimizer:
        # 这里的代码会自动应用性能优化
        result = await some_heavy_task()

        # 访问优化器的具体功能
        cache_stats = optimizer.cache_system.get_cache_stats()
        memory_stats = optimizer.memory_optimizer.get_memory_stats()

    # 上下文退出时自动清理和优化
```

## 📊 性能监控指标

### 关键指标解读

| 指标 | 含义 | 目标值 | 问题阈值 |
|------|------|--------|---------|
| 缓存命中率 | Agent结果缓存效率 | > 70% | < 50% |
| 内存使用率 | 进程内存占用 | < 80% | > 90% |
| Git批量化率 | Git操作优化效率 | > 60% | < 30% |
| 响应时间P95 | 95%请求响应时间 | < 500ms | > 1000ms |

### 状态颜色说明

- 🟢 **优秀**: 所有指标都在目标范围内
- 🟡 **良好**: 大部分指标正常，有轻微问题
- 🟠 **注意**: 存在性能问题，需要关注
- 🔴 **警告**: 严重性能问题，需要立即处理

## ⚡ 性能优化技巧

### 1. Agent执行优化

```python
# ✅ 推荐：使用优化后的Agent执行
result = await optimize_agent_execution('agent_type', params)

# ❌ 避免：直接调用未优化的Agent
# result = await raw_agent_execution('agent_type', params)
```

### 2. Git操作优化

```python
# ✅ 推荐：批量Git操作
operations = [
    ('status', []),
    ('branch', ['-a']),
    ('log', ['--oneline', '-10'])
]
batch_git_operations(operations)

# ❌ 避免：频繁单独Git调用
# for op in operations:
#     individual_git_call(op)
```

### 3. 内存管理

```python
# ✅ 推荐：使用资源池
with enhanced_performance_optimizer.resource_manager.get_resource('dict') as d:
    d['key'] = 'value'
    # 自动回收到池中

# ❌ 避免：频繁创建大对象
# for i in range(1000):
#     large_dict = {'data': [j for j in range(1000)]}
```

### 4. 缓存策略

```python
# ✅ 推荐：使用缓存装饰器
from modules.performance_cache import cache_function

@cache_function(ttl=300)  # 5分钟缓存
def expensive_operation(param):
    # 耗时操作
    return result

# ✅ 推荐：异步缓存
from modules.performance_cache import async_cache_function

@async_cache_function(ttl=600)  # 10分钟缓存
async def async_expensive_operation(param):
    return result
```

## 🔧 故障排除

### 常见问题解决

#### 1. 缓存命中率低
```bash
# 检查缓存配置
python3 main/performance_cli.py status --detailed

# 清理并重建缓存
python3 main/performance_cli.py optimize --cache
```

#### 2. 内存使用过高
```bash
# 执行内存优化
python3 main/performance_cli.py optimize --memory

# 查看内存使用详情
python3 -c "
from modules.enhanced_performance_optimizer import enhanced_performance_optimizer
print(enhanced_performance_optimizer.memory_optimizer.get_memory_stats())
"
```

#### 3. Git操作缓慢
```bash
# 优化Git操作
python3 main/performance_cli.py optimize --git

# 检查Git缓存状态
python3 -c "
from modules.enhanced_git_cache import get_git_cache_stats
print(get_git_cache_stats())
"
```

#### 4. 性能回归检测
```bash
# 运行基准测试
python3 main/performance_cli.py benchmark

# 如果发现回归，重新建立基线
python3 -c "
from modules.enhanced_performance_optimizer import enhanced_performance_optimizer
for test_name in ['agent_execution', 'cache_performance', 'git_operations']:
    enhanced_performance_optimizer.benchmark_system.establish_baseline(test_name)
"
```

## 📈 性能调优指南

### 根据使用场景调优

#### 1. 高频Agent调用场景
```python
# 增加Agent缓存大小
enhanced_performance_optimizer.cache_system.max_size = 4096

# 延长缓存TTL
enhanced_performance_optimizer.cache_system.ttl = 7200  # 2小时
```

#### 2. 大量Git操作场景
```python
# 减少批量处理间隔
enhanced_performance_optimizer.git_optimizer.batch_interval = 1.0  # 1秒

# 增加批量大小
enhanced_performance_optimizer.git_optimizer.max_batch_size = 100
```

#### 3. 内存敏感场景
```python
# 启用更激进的GC
enhanced_performance_optimizer.memory_optimizer.memory_pressure_threshold = 60.0  # 60%

# 减少资源池大小
for pool_name in enhanced_performance_optimizer.resource_manager.pool_configs:
    enhanced_performance_optimizer.resource_manager.pool_configs[pool_name]['max'] = 50
```

## 🎯 最佳实践

### DO's ✅

1. **启动时就启用自动优化**
   ```bash
   python3 main/performance_cli.py auto start
   ```

2. **定期查看性能报告**
   ```bash
   python3 main/performance_cli.py analyze
   ```

3. **使用优化上下文包装重要操作**
   ```python
   async with optimized_execution():
       await important_task()
   ```

4. **为常用操作启用缓存**
   ```python
   @cache_function(ttl=300)
   def frequently_called_function():
       pass
   ```

### DON'Ts ❌

1. **不要禁用自动优化**
   - 自动优化是后台运行，不会影响正常使用

2. **不要忽略性能警告**
   - 及时处理性能报告中的问题和建议

3. **不要手动管理缓存**
   - 系统会自动处理缓存清理和淘汰

4. **不要在循环中创建大量对象**
   - 使用资源池或预分配对象

## 📞 获取帮助

### 查看详细文档
```bash
python3 main/performance_cli.py --help
python3 main/performance_cli.py optimize --help
python3 main/performance_cli.py analyze --help
```

### 查看性能日志
```bash
# 查看性能优化日志
tail -f ~/.perfect21/logs/performance.log

# 查看错误日志
tail -f ~/.perfect21/logs/error.log
```

### 运行完整测试
```bash
# 运行性能验证测试
python3 tests/performance_validation.py

# 查看演示
python3 scripts/performance_quick_start.py
```

---

💡 **提示**: 大多数优化是自动进行的，你只需要启动自动优化功能，系统就会在后台持续优化性能。