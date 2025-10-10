# Coverage Quick Start Guide
**For Developers - Get Started in 2 Minutes**

## What Is This?

Your code now has a **quality gate**: you must have **80% test coverage** to pass CI. This guide shows you how to check coverage locally before pushing.

## Quick Commands

### Before Committing Code

```bash
# Quick check (2 minutes)
./scripts/verify_coverage_local.sh
```

**What it does**:
- Runs all tests with coverage
- Shows coverage percentages
- Fails if below 80%

**Example Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Local Coverage Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Checking JavaScript Coverage...
  JavaScript Coverage: 85.32%
  ✓ Above threshold 80%

Step 2: Checking Python Coverage...
  ✓ Python coverage above 80%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Coverage Verification PASSED
```

### Deep Dive (When You Need Details)

```bash
# Full report with HTML output
./scripts/coverage_check.sh
```

**What it does**:
- Generates all report formats
- Creates interactive HTML reports
- Shows exactly which lines are untested

**Then open**:
```bash
# JavaScript report
open coverage/lcov-report/index.html

# Python report
open coverage/htmlcov-python/index.html
```

### Just JavaScript

```bash
npm run test:coverage
```

### Just Python

```bash
pytest --cov=src --cov-report=html
open coverage/htmlcov-python/index.html
```

## Reading the HTML Report

### JavaScript Report

![Coverage Report Example]
```
File                | Stmts | Branch | Funcs | Lines | Uncovered Lines
------------------------------------------------------------------------------
src/api/routes.js   | 85.2% | 78.5%  | 82.1% | 85.2% | 45-52, 67-71
src/core/db.js      | 91.3% | 88.2%  | 90.0% | 91.3% | 23, 45
```

**Click on a file** → See code with highlights:
- 🟢 Green = Covered
- 🔴 Red = Not covered
- 🟡 Yellow = Partial (branches)

### What to Do If Lines Are Red

1. **Find the red lines** - These weren't tested
2. **Add a test** - Write test that executes those lines
3. **Re-run coverage** - Verify lines turn green
4. **Commit** - Now you can push

## Understanding Coverage Metrics

### Statements (Most Important)
> Individual code statements that were run

**Example**:
```javascript
const x = 1;          // Statement
const y = 2;          // Statement
return x + y;         // Statement
```

**80% statements** = 80% of these lines ran during tests

### Branches (Conditional Logic)
> How many if/else paths were tested

**Example**:
```javascript
if (user.isAdmin) {      // 2 branches
  return admin();        // Branch 1
} else {
  return user();         // Branch 2
}
```

**80% branches** = Tested 4 out of 5 if/else paths

### Functions
> How many functions were called

**Example**:
```javascript
function add(a, b) { return a + b; }  // Function 1
function sub(a, b) { return a - b; }  // Function 2
```

**80% functions** = Called 8 out of 10 functions

### Lines
> Physical lines executed

Similar to statements, but counts actual file lines.

## Common Scenarios

### Scenario 1: Coverage Below 80%

**Problem**:
```
❌ Coverage 75.2% is below threshold 80%
```

**Solution**:
1. Open HTML report
2. Find files with low coverage (red)
3. Add tests for uncovered lines
4. Re-run until ≥80%

### Scenario 2: Which Files Need Tests?

**Command**:
```bash
npm run test:coverage -- --verbose
```

**Look for**:
```
src/new-feature.js    | 45.2%  ← Add tests here!
src/api/endpoint.js   | 92.1%  ← Good coverage
```

### Scenario 3: I Only Changed One File

**Problem**: Don't want to test everything

**Solution**: Differential coverage (coming soon)

**Workaround**: Run full coverage, it's fast
```bash
./scripts/verify_coverage_local.sh  # ~2 min
```

### Scenario 4: CI Failed But Local Passed

**Problem**: Different environments

**Solution**: Match CI versions
```bash
# Use same Node version as CI
nvm use 18

# Use same Python version as CI
pyenv local 3.9

# Re-run
./scripts/verify_coverage_local.sh
```

## CI Behavior

### What CI Does Automatically

1. **On every push** to main/develop/feature branches:
   - Runs all tests
   - Generates coverage reports
   - Checks if ≥80%

2. **On every PR**:
   - Comments with coverage status
   - Shows coverage percentage
   - Uploads HTML reports as artifacts

3. **If coverage fails**:
   - ❌ Red X on commit
   - PR cannot be merged
   - Download artifacts to see details

### Viewing CI Coverage Reports

1. Go to **GitHub Actions** tab
2. Click on the failing workflow
3. Click **Summary**
4. Scroll to **Coverage Report Summary**
5. Download **coverage-javascript** or **coverage-python** artifact
6. Unzip and open `index.html`

## Best Practices

### Write Tests BEFORE Coding (TDD)

```bash
# 1. Write test (it will fail)
npm test

# 2. Write code to make it pass
npm test

# 3. Check coverage
npm run test:coverage
```

### Aim for 90%+

**Thresholds**:
- **Minimum**: 80% (CI enforced)
- **Good**: 85%
- **Excellent**: 90%+

### Test the Important Stuff First

**Priority**:
1. **API endpoints** (85% threshold)
2. **Core modules** (90% threshold)
3. **Business logic**
4. **UI components** (80% threshold)

### Don't Test Just for Coverage

**Bad**:
```javascript
test('calls function', () => {
  myFunction(); // Just calling it
});
```

**Good**:
```javascript
test('returns correct value for valid input', () => {
  expect(myFunction(5)).toBe(10);
});

test('throws error for invalid input', () => {
  expect(() => myFunction(-1)).toThrow();
});
```

## Troubleshooting

### Coverage command not found

```bash
# Install dependencies
npm install
pip install -r requirements.txt
```

### Coverage is 0%

```bash
# Check if tests exist
npm test  # Should pass
pytest    # Should pass

# Then run coverage
npm run test:coverage
```

### Can't open HTML report

```bash
# Use full path
open "$(pwd)/coverage/lcov-report/index.html"
```

### Coverage dropped after refactor

**Solution**: Add tests for new code paths
```bash
# See what's missing
./scripts/coverage_check.sh

# Open HTML report
open coverage/lcov-report/index.html

# Find red lines, add tests
```

## Cheat Sheet

| Task | Command |
|------|---------|
| Quick check | `./scripts/verify_coverage_local.sh` |
| Full report | `./scripts/coverage_check.sh` |
| JS only | `npm run test:coverage` |
| Python only | `pytest --cov=src --cov-report=html` |
| Open JS report | `open coverage/lcov-report/index.html` |
| Open Python report | `open coverage/htmlcov-python/index.html` |
| See what's tested | `npm test -- --verbose` |
| Run one test file | `npm test -- path/to/test.js` |

## Questions?

**Q: Why 80%?**
A: Industry standard for production-grade code. Catches most bugs while remaining achievable.

**Q: Can I skip coverage for a file?**
A: Yes, but only for non-critical code (scripts, tooling). Edit `jest.config.js` or `.coveragerc`.

**Q: Coverage passing but tests fail?**
A: Coverage ≠ test success. You need BOTH:
- Tests pass (functionality works)
- Coverage ≥80% (code is tested)

**Q: How do I test async code?**
A: Use `async/await` in tests:
```javascript
test('async function', async () => {
  const result = await myAsyncFunc();
  expect(result).toBe(expected);
});
```

**Q: What about mocks?**
A: Mocking is counted as coverage. Mock external dependencies, test your code.

---

**Need more details?** See [COVERAGE_IMPLEMENTATION_REPORT.md](./COVERAGE_IMPLEMENTATION_REPORT.md)

**Having issues?** Check troubleshooting section above or open an issue.
