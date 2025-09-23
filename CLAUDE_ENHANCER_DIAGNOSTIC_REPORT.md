# Claude Enhancer 诊断报告

生成时间: 2025-09-23 17:44:36

## 系统统计

- 总文件数: 344
- 脚本文件数: 185
- 备份文件数: 0
- 废弃文件数: 0
- 配置文件数: 41
- Hook脚本数: 9
- 文档文件数: 164

## 发现的问题

### 配置错误

- .claude/config/migration_mapping.yaml: while parsing a block mapping
  in ".claude/config/migration_mapping.yaml", line 10, column 5
expected <block end>, but found '<scalar>'
  in ".claude/config/migration_mapping.yaml", line 12, column 15

### 配置冲突

- 键'version'在21个文件中重复
- 键'project'在11个文件中重复
- 键'description'在20个文件中重复
- 键'hooks'在23个文件中重复
- 键'security'在7个文件中重复
- 键'environment'在14个文件中重复
- 键'custom_rules'在10个文件中重复
- 键'execution_modes'在7个文件中重复
- 键'metadata'在3个文件中重复
- 键'system'在6个文件中重复
- 键'workflow'在6个文件中重复
- 键'agents'在6个文件中重复
- 键'task_types'在16个文件中重复
- 键'quality_gates'在9个文件中重复
- 键'environments'在3个文件中重复
- 键'logging'在12个文件中重复
- 键'performance'在9个文件中重复
- 键'integrations'在9个文件中重复
- 键'notifications'在9个文件中重复
- 键'whitelist'在12个文件中重复
- 键'schema'在3个文件中重复
- 键'compatibility'在3个文件中重复
- 键'features'在5个文件中重复
- 键'rules'在3个文件中重复
- 键'error_handling'在3个文件中重复
- 键'extends'在3个文件中重复
- 键'environment_variables'在3个文件中重复

### 性能问题

- .claude/scripts/cleanup.sh 执行超时
- .claude/scripts/ultra_optimized_cleanup.sh 执行时间过长: 1.26秒

### 文档问题

- docs/enterprise_auth_backend_architecture.md 过大: 96.3KB
- docs/authentication_system_architecture.md 过大: 59.7KB
- .claude/agents/specialized/game-developer.md 过大: 59.1KB
- .claude/agents/specialized/fintech-specialist.md 过大: 53.4KB
- .claude/agents/specialized/embedded-engineer.md 过大: 49.8KB
- .claude/agents/specialized/healthcare-dev.md 过大: 50.1KB
- .claude/agents/specialized/ecommerce-expert.md 过大: 54.3KB

### 文档重复

- WORKFLOW.md 在多处重复: ['WORKFLOW.md', '.claude/WORKFLOW.md']
- README.md 在多处重复: ['README.md', 'frontend/auth/README.md', 'test/auth/README.md', '.claude/README.md', '.claude/features/standard/smart_document_loading/README.md', '.claude/ARCHITECTURE/README.md', 'backend/tests/README.md']
- PERFORMANCE_OPTIMIZATION_SUMMARY.md 在多处重复: ['PERFORMANCE_OPTIMIZATION_SUMMARY.md', '.claude/PERFORMANCE_OPTIMIZATION_SUMMARY.md']
- backend-engineer.md 在多处重复: ['.trash/20250923_174410/agents_backup_20250914_224521/backend-engineer.md', '.claude/agents/backend-engineer.md', '.claude/agents/development/backend-engineer.md']
- spec-architect.md 在多处重复: ['.trash/20250923_174410/agents_backup_20250914_224521/spec-architect.md', '.claude/agents/spec-architect.md']
- orchestrator.md 在多处重复: ['.trash/20250923_174410/agents_backup_20250914_224521/orchestrator.md', '.claude/agents/orchestrator.md']
- frontend-engineer.md 在多处重复: ['.trash/20250923_174410/agents_backup_20250914_224521/frontend-engineer.md', '.claude/agents/frontend-engineer.md']
- README_WORKFLOW.md 在多处重复: ['.claude/hooks_backup_20250923_172415/README_WORKFLOW.md', '.claude/hooks_backup_20250923_172419/README_WORKFLOW.md', '.claude/hooks/README_WORKFLOW.md']

