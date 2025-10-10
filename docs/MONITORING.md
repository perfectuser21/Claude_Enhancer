# CI/CD Monitoring Guide

**Version**: 1.0.0
**Created**: 2025-10-08

---

## 概述

本指南说明如何监控Claude Enhancer的CI/CD系统健康状况。

---

## 监控指标

### 1. CI成功率
- **目标**: ≥95%
- **测量**: 过去30天的workflow成功率
- **查看**: GitHub Actions → Insights

### 2. CI运行时间
- **目标**: P95 < 8分钟
- **测量**: 95分位数运行时间
- **查看**: GitHub Actions → Timing

### 3. 安全扫描有效性
- **目标**: 100%漏洞检测
- **测量**: 已知漏洞检测率
- **查看**: Security scan job logs

### 4. 代码质量覆盖
- **目标**: >90%文件被检查
- **测量**: Linting覆盖率
- **查看**: Code quality job logs

---

## 告警规则

### Critical告警
- 安全扫描检测率 < 98%
- CI成功率 < 85%

### High告警
- CI成功率 < 90%
- CI运行时间 > 15分钟

### Medium告警
- CI成功率 < 95%
- CI运行时间 > 10分钟

---

## 健康检查

### 每日检查
```bash
# 1. 检查workflow语法
yamllint .github/workflows/ce-gates.yml

# 2. 验证gates_parser可用
bash .workflow/scripts/gates_parser.sh get_allow_paths P1

# 3. 检查必要工具
command -v shellcheck && command -v yq
```

### 每周检查
- 审查过去7天的CI成功率
- 分析失败原因（如有）
- 验证Branch Protection规则有效

### 每月检查
- 审查SLO达标情况
- 更新告警阈值（如需要）
- 审查安全扫描规则

---

## 故障排查

参见 [CI_TROUBLESHOOTING.md](CI_TROUBLESHOOTING.md)

---

## 仪表板

### GitHub Actions
- URL: https://github.com/your-org/your-repo/actions
- 视图: Workflows, Runs, Usage

### 关键指标
- Total runs
- Success rate
- Average duration
- Queue time

---

## 联系方式

- Slack: #ce-alerts
- Email: devops@example.com
- On-call: PagerDuty

---

**最后更新**: 2025-10-08
