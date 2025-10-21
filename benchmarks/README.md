# Benchmarks Baseline Data

## 📊 目的

此目录存储Claude Enhancer各项指标的基准数据，用于：
1. **阈值调整依据**：基于证据调整gates.yml中的阈值
2. **性能监控基准**：检测性能退化
3. **准确率追踪**：Impact Assessment等自动化工具的准确率演进
4. **质量门禁校准**：确保质量门禁的合理性

## 📁 目录结构

```
benchmarks/
├── impact_assessment/          # Impact Assessment基准数据
│   ├── baseline_v1.0.json     # v1.0 baseline（86.67%准确率）
│   └── samples/               # 验证样本集
├── performance/               # 性能基准
│   ├── hook_execution.json   # Hook执行时间
│   └── script_execution.json # 脚本执行时间
├── quality_metrics/          # 质量指标基准
│   ├── test_coverage.json    # 测试覆盖率历史
│   ├── shellcheck.json       # Shellcheck警告数（Quality Ratchet）
│   └── complexity.json       # 代码复杂度
└── README.md                 # 本文件
```

## 🎯 Impact Assessment Baseline

### baseline_v1.0.json

**版本**: 1.0.0
**日期**: 2025-10-20
**样本数**: 30个验证样本
**准确率**: 86.67% (26/30)
**性能**: <50ms (P95: 45ms)

**阈值定义**:
- Very-high-risk: ≥70分 → 8 agents
- High-risk: 50-69分 → 6 agents
- Medium-risk: 30-49分 → 3 agents
- Low-risk: 0-29分 → 0 agents

**计算公式**:
```
impact_radius = (risk × 5) + (complexity × 3) + (scope × 2)
```

**误差分析**:
- 误报（推荐过多agents）: 2例
- 漏报（推荐过少agents）: 2例

### 如何使用

#### 1. 调整阈值（需要证据）

当发现阈值不合理时：

```bash
# 1. 收集新样本
echo '{
  "task": "新任务描述",
  "scores": {"risk": 7, "complexity": 8, "impact": 6},
  "actual_agents": 5,
  "result": "correct/overestimated/underestimated"
}' >> benchmarks/impact_assessment/samples/new_sample.json

# 2. 重新计算准确率
bash tools/recalculate_ia_accuracy.sh

# 3. 如果准确率提升，更新baseline
cp baseline_v1.0.json baseline_v1.1.json
# 编辑baseline_v1.1.json，调整阈值

# 4. 更新gates.yml中的Impact Assessment配置
# 5. 提交CHANGELOG说明
```

#### 2. 监控准确率演进

```bash
# 查看历史准确率趋势
jq '.validation_samples.accuracy' benchmarks/impact_assessment/baseline_v*.json
```

#### 3. 性能监控

```bash
# 检查Impact Assessment性能是否退化
jq '.performance_metrics.execution_time_ms.p95' baseline_v1.0.json
# 当前: 45ms
# 如果新版本>55ms（+10ms），需要优化
```

## 📈 Quality Ratchet（质量棘轮）

**概念**：质量指标只能改善，不能退化

**示例：Shellcheck警告数**

```json
{
  "version": "6.6.0",
  "baseline": 277,
  "target": 0,
  "rule": "warnings <= baseline",
  "enforcement": "hard",
  "history": [
    {"version": "6.5.0", "warnings": 290},
    {"version": "6.5.1", "warnings": 277},
    {"version": "6.6.0", "warnings": 275}  // ✅ 改善
  ]
}
```

**CI检查**：
```bash
# .github/workflows/lockdown-ci.yml
if [ $warnings -gt 277 ]; then
  echo "❌ Shellcheck warnings increased"
  exit 1
fi
```

## 🔧 工具脚本

### 创建新baseline

```bash
# tools/create_baseline.sh
#!/bin/bash
version="$1"
metric="$2"

mkdir -p benchmarks/$metric
cat > benchmarks/$metric/baseline_v${version}.json <<EOF
{
  "version": "$version",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "data": {}
}
EOF
```

### 比较baseline差异

```bash
# tools/compare_baselines.sh
#!/bin/bash
old_version="$1"
new_version="$2"

diff -u \
  benchmarks/impact_assessment/baseline_v${old_version}.json \
  benchmarks/impact_assessment/baseline_v${new_version}.json
```

## 📚 相关文档

- **PLAN.md**: Task 10 - 基准数据创建计划
- **CHECKS_MAPPING.md**: 可调整阈值说明
- **.workflow/gates.yml**: 当前使用的阈值配置
- **CHANGELOG.md**: 阈值调整历史记录

## 🔄 更新策略

### 何时更新baseline

1. **准确率提升≥5%**：创建新版本baseline
2. **阈值调整**：必须同时更新baseline并说明原因
3. **性能优化≥20%**：更新性能基准
4. **每个major版本**：必须创建新的baseline快照

### 更新流程

1. 收集新样本/数据
2. 验证改进效果
3. 创建新版本baseline（baseline_vX.Y.json）
4. 更新gates.yml配置
5. 提交CHANGELOG说明
6. 保留旧版本baseline（用于回滚）

## ⚠️  注意事项

1. **绝对不要**直接修改baseline文件，始终创建新版本
2. **必须保留**历史baseline文件（至少保留最近3个版本）
3. **阈值调整**必须有数据支持，不能凭感觉
4. **性能退化**必须有合理解释，否则视为bug

---

**维护者**: Claude Enhancer System
**更新频率**: 每次阈值调整或准确率提升时
**最后更新**: 2025-10-20
