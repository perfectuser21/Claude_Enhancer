# Parallel Execution Command

Execute multiple agents in parallel for complex tasks.

## Usage
When you need to $ARGUMENTS, select at least 3-5 relevant agents and execute them in parallel using a single function_calls block.

## Agent Selection Guide

### For Authentication/Login Tasks
- backend-architect (API design)
- security-auditor (security review)
- test-engineer (test coverage)
- api-designer (endpoint design)
- database-specialist (data schema)

### For API Development
- api-designer (API specification)
- backend-architect (architecture)
- test-engineer (testing strategy)
- technical-writer (documentation)

### For Database Tasks
- database-specialist (schema design)
- backend-architect (integration)
- performance-engineer (optimization)

### For Frontend Tasks
- frontend-specialist (UI implementation)
- ux-designer (user experience)
- test-engineer (component testing)

### For Testing Tasks
- test-engineer (unit tests)
- e2e-test-specialist (integration tests)
- performance-tester (load testing)

## Execution Pattern
Always use parallel execution in a single message:
```xml
<function_calls>
  <invoke name="Task">...</invoke>
  <invoke name="Task">...</invoke>
  <invoke name="Task">...</invoke>
</function_calls>
```

Remember: Never execute agents sequentially when they can work in parallel!