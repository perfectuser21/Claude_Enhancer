# DocGate文档质量管理系统 - 测试报告

测试时间: 2025-09-27 20:08:06

## 测试统计

- 总测试数: 12
- 通过数: 10
- 失败数: 2
- 通过率: 83.3%

## 详细结果

| 状态 | 测试项 | 说明 |
|------|--------|------|
| PASS | Config: .docpolicy.yaml | File exists |
| PASS | Config: .git/hooks/pre-commit-docs | File exists |
| PASS | Config: .git/hooks/pre-push-docs | File exists |
| PASS | Config: docs/templates/requirement.md | File exists |
| PASS | Config: docs/templates/design.md | File exists |
| PASS | Config: docs/templates/api.md | File exists |
| FAIL | Hook: test_valid.md | [0;34m📚 Claude Enhancer - Document Quality Check[0m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
| PASS | Hook: test-copy.md | [0;34m📚 Claude Enhancer - Document Quality Check[0m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
| PASS | Hook: test_sensitive.md | [0;34m📚 Claude Enhancer - Document Quality Check[0m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ |
| PASS | Quality: high_quality.md | Expected: high, Got: high |
| PASS | Quality: low_quality.md | Expected: low, Got: low |
| WARN | Performance: pre-commit | 81.67ms |
