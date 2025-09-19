# Test Command

Run comprehensive tests for $ARGUMENTS.

## Test Strategy

1. **Test Agents** (parallel execution):
   - test-engineer (unit & integration tests)
   - e2e-test-specialist (end-to-end tests)
   - performance-tester (performance tests)
   - security-auditor (security tests)

2. **Test Coverage**:
   - Unit tests for individual functions
   - Integration tests for modules
   - End-to-end tests for workflows
   - Performance benchmarks
   - Security vulnerability scans

3. **Feedback Loop**:
   If tests fail:
   - Return to the original implementation agent
   - Fix the issues identified
   - Re-run tests until they pass
   - Never skip failed tests

## Important Rules
- Test failures MUST trigger feedback loop
- The same agent who wrote the code should fix it
- All tests must pass before marking task complete