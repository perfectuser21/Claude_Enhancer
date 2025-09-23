# Claude Enhancer 性能优化使用指南

## 🚀 快速开始

### 立即使用高性能版本
```bash
# 替换原有清理脚本
.claude/scripts/hyper_performance_cleanup.sh

# 带详细输出
.claude/scripts/hyper_performance_cleanup.sh --verbose

# 干运行模式（预览操作）
.claude/scripts/hyper_performance_cleanup.sh --dry-run
```

## 📊 性能测试和验证

### 1. 快速验证
```bash
# 简单的性能验证
./quick_performance_validation.sh
```

### 2. 详细性能测试
```bash
# 运行完整性能测试套件
.claude/scripts/performance_test_suite.sh

# 输出位置
# - 测试结果: /tmp/perfect21_perf_results.json
# - 分析报告: /tmp/perfect21_performance_analysis.md
```

### 3. 实时性能监控
```bash
# 启动连续监控
.claude/scripts/realtime_performance_monitor.sh --continuous

# 单次测试特定脚本
.claude/scripts/realtime_performance_monitor.sh --single cleanup.sh

# 仅显示当前仪表板
.claude/scripts/realtime_performance_monitor.sh --dashboard
```

### 4. 全面基准测试
```bash
# 运行综合基准测试
.claude/scripts/benchmark_runner.sh

# 输出位置
# - 结果: /tmp/perfect21_benchmark_suite/results/
# - 报告: /tmp/perfect21_benchmark_suite/reports/
```

## ⚙️ 性能调优参数

### 环境变量配置
```bash
# 调整并行任务数（默认：CPU核心数）
export PARALLEL_JOBS=8

# 调整批处理大小（默认：500）
export BATCH_SIZE=1000

# 设置内存限制（默认：512MB）
export MAX_MEMORY_MB=1024

# 启用详细日志
export VERBOSE=true

# 运行脚本
.claude/scripts/hyper_performance_cleanup.sh
```

### 针对不同场景的优化
```bash
# 小项目（<100文件）
PARALLEL_JOBS=2 BATCH_SIZE=100 .claude/scripts/hyper_performance_cleanup.sh

# 中型项目（100-500文件）
PARALLEL_JOBS=4 BATCH_SIZE=500 .claude/scripts/hyper_performance_cleanup.sh

# 大型项目（>500文件）
PARALLEL_JOBS=8 BATCH_SIZE=1000 .claude/scripts/hyper_performance_cleanup.sh

# 超大项目（>1000文件）
PARALLEL_JOBS=12 BATCH_SIZE=1500 .claude/scripts/hyper_performance_cleanup.sh
```

## 📈 性能监控和分析

### 监控指标说明
```
执行时间目标:
- 小型项目: <100ms
- 中型项目: <250ms
- 大型项目: <500ms
- 超大项目: <750ms

资源使用目标:
- CPU利用率: >80%
- 内存使用: <512MB
- 成功率: >95%
```

### 性能数据位置
```bash
# 实时监控日志
/tmp/perfect21_performance.log

# 基准测试结果
/tmp/perfect21_benchmark_suite/

# 性能分析报告
/tmp/perfect21_performance_analysis.md
```

## 🔧 故障排除

### 常见问题和解决方案

#### 1. 脚本执行缓慢
```bash
# 检查并行度设置
echo "当前并行任务数: $PARALLEL_JOBS"
echo "系统CPU核心数: $(nproc)"

# 优化建议
export PARALLEL_JOBS=$(nproc)
export BATCH_SIZE=500
```

#### 2. 内存使用过高
```bash
# 监控内存使用
ps -o pid,ppid,rss,cmd -p $$

# 减少内存使用
export MAX_MEMORY_MB=256
export BATCH_SIZE=100
```

#### 3. 权限问题
```bash
# 确保脚本有执行权限
chmod +x .claude/scripts/*.sh

# 检查目录权限
ls -la .claude/scripts/
```

#### 4. 依赖缺失
```bash
# 检查必要的命令
command -v find || echo "需要 find 命令"
command -v xargs || echo "需要 xargs 命令"
command -v awk || echo "需要 awk 命令"

# 检查Bash版本（推荐5.0+）
echo "Bash版本: $BASH_VERSION"
```

## 📊 性能对比

### 脚本版本对比
| 版本 | 目标时间 | 特性 | 适用场景 |
|------|----------|------|----------|
| cleanup.sh | 基准 | 原始版本 | 兼容性需求 |
| ultra_optimized_cleanup.sh | 2-3x提升 | 部分优化 | 渐进式升级 |
| hyper_performance_cleanup.sh | 5-10x提升 | 全面优化 | 生产环境 |

### 性能提升预期
```
数据集规模 -> 性能提升倍数:
- 小型(60文件)    -> 3-5x
- 中型(200文件)   -> 5-7x
- 大型(400文件)   -> 7-10x
- 超大(800文件)   -> 10-15x
```

## 🎯 最佳实践

### 1. 选择合适的版本
```bash
# 开发环境：使用hyper-performance版本
.claude/scripts/hyper_performance_cleanup.sh

# CI/CD环境：添加性能验证
.claude/scripts/performance_test_suite.sh

# 生产环境：启用监控
.claude/scripts/realtime_performance_monitor.sh --continuous
```

### 2. 定期性能检查
```bash
# 每周运行基准测试
crontab -e
# 添加: 0 2 * * 1 /path/to/benchmark_runner.sh

# 监控性能趋势
tail -f /tmp/perfect21_performance.log
```

### 3. 自定义优化
```bash
# 创建项目特定配置
cat > .performance_config << EOF
PARALLEL_JOBS=6
BATCH_SIZE=750
MAX_MEMORY_MB=768
EOF

# 使用配置
source .performance_config
.claude/scripts/hyper_performance_cleanup.sh
```

## 🔄 持续优化

### 定期评估
1. **每月**: 运行完整基准测试
2. **每季度**: 评估性能趋势
3. **每半年**: 考虑参数调优

### 性能回归检测
```bash
# 建立性能基线
.claude/scripts/benchmark_runner.sh > baseline_performance.txt

# 定期对比
.claude/scripts/benchmark_runner.sh > current_performance.txt
diff baseline_performance.txt current_performance.txt
```

### 扩展和自定义
```bash
# 添加自定义清理规则
# 编辑 hyper_performance_cleanup.sh
# 在 hyper_scan 函数中添加新的文件模式

# 自定义监控指标
# 编辑 realtime_performance_monitor.sh
# 添加项目特定的性能指标
```

## 📞 支持和反馈

### 性能问题报告
1. 运行诊断脚本收集信息
2. 包含系统信息（CPU、内存、Bash版本）
3. 提供性能测试结果
4. 描述预期vs实际性能

### 获取帮助
```bash
# 查看脚本帮助
.claude/scripts/realtime_performance_monitor.sh --help
.claude/scripts/performance_test_suite.sh --help

# 查看详细配置选项
grep -n "^#" .claude/scripts/hyper_performance_cleanup.sh
```

---

## ✅ 检查清单

使用前确认：
- [ ] 脚本具有执行权限
- [ ] 系统有足够的可用内存
- [ ] 了解当前项目规模
- [ ] 选择合适的性能参数
- [ ] 建立性能监控

性能优化后验证：
- [ ] 执行时间符合预期
- [ ] 资源使用在合理范围
- [ ] 清理效果正确
- [ ] 无错误或警告
- [ ] 性能数据已记录

---

**记住**: 性能优化是一个持续的过程。定期监控、测试和调优，以确保最佳性能表现。

*更新时间: 2024年*