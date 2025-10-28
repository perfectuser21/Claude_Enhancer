# Acceptance Checklist: Anti-Hollow Gate Improvements

**Feature**: Anti-Hollow Gate v8.2 Enhancements
**Date**: 2025-10-28
**Branch**: feature/anti-hollow-improvements

---

## 📋 Overview

This checklist defines the acceptance criteria for the 4 P0 improvements to Anti-Hollow Gate system. Each item must be completed with evidence before the feature can be considered complete.

**Completion Target**: ≥90% (36/40 items)

---

## 🎯 P0-1: Stable ID Mapping System

### 1.1 Core Infrastructure

- [ ] 1.1.1 Create PLAN_CHECKLIST_MAPPING.yml schema definition
  - Format: version, plan_file, checklist_file, mappings array
  - Each mapping has: plan_section, plan_items (id, text), checklist_items (id, text, required_evidence_type)

- [ ] 1.1.2 Implement ID generation function
  - Format: PLAN-W{week}-{nnn} and CL-W{week}-{nnn}
  - Sequential numbering per week
  - Uniqueness validation

- [ ] 1.1.3 Create mapping file generator script
  - Parse PLAN.md sections
  - Generate unique IDs for each item
  - Output valid MAPPING.yml

- [ ] 1.1.4 Update checklist generation to include IDs
  - Modify scripts/generate_checklist_from_plan.sh
  - Add ID comments: `<!-- id: CL-W4-005; evidence: EVID-xxx -->`
  - Preserve human-readable text

### 1.2 Validation Integration

- [ ] 1.2.1 Update validate_plan_execution.sh to use IDs
  - Read MAPPING.yml instead of text matching
  - Lookup items by ID, not text
  - Fall back to text matching for legacy format

- [ ] 1.2.2 Implement dual-mode validation
  - Detect if checklist has IDs
  - Use ID mode if available
  - Use legacy text mode otherwise

- [ ] 1.2.3 Add ID uniqueness validator
  - Check no duplicate IDs in mapping file
  - Validate ID format (regex)
  - Clear error messages

### 1.3 Testing & Evidence

- [ ] 1.3.1 Unit test: ID generation
  - Test sequential numbering
  - Test format validation
  - Test collision detection

- [ ] 1.3.2 Integration test: Text change resilience
  - Create PLAN → CHECKLIST with IDs
  - Modify checklist text
  - Validation still passes via ID

- [ ] 1.3.3 Performance test: ID lookup
  - Measure YAML parsing time
  - Target: <10ms per lookup
  - Test with 100+ items

---

## 🎯 P0-2: Strict Evidence Schema Validation

### 2.1 Schema Enforcement

- [ ] 2.1.1 Install and verify jq availability
  - Add to setup/installation docs
  - Check in pre-commit hook
  - Fallback strategy if missing

- [ ] 2.1.2 Implement validate_evidence_file() function
  - Extract type field from YAML
  - Lookup required fields from schema.json
  - Validate all required fields present

- [ ] 2.1.3 Integrate into validate_checklist.sh
  - Call validate_evidence_file() for each evidence
  - Aggregate errors
  - Return clear error messages

### 2.2 Required Fields Validation

- [ ] 2.2.1 Validate functional_test type
  - Required: test_command, exit_code, output_sample
  - Check each field exists and non-empty
  - Error if missing

- [ ] 2.2.2 Validate performance_test type
  - Required: test_command, execution_time, baseline
  - Check numeric fields are valid numbers
  - Error if missing

- [ ] 2.2.3 Validate stress_test type
  - Required: test_command, scale, result
  - Validate scale is numeric
  - Error if missing

- [ ] 2.2.4 Validate benchmark type
  - Required: test_command, comparison, result
  - Validate comparison structure
  - Error if missing

### 2.3 Testing & Evidence

- [ ] 2.3.1 Unit test: Schema validation
  - Test each evidence type
  - Test missing required fields
  - Test invalid type enum

- [ ] 2.3.2 Integration test: Complete evidence
  - Create valid evidence file
  - Validation passes
  - Performance: <100ms

- [ ] 2.3.3 Integration test: Incomplete evidence
  - Create evidence missing field
  - Validation fails with clear error
  - Error message shows missing field name

---

## 🎯 P0-3: Code Block Filtering

### 3.1 Implementation

- [ ] 3.1.1 Implement strip_code_blocks() function
  - AWK-based parser
  - Handles ``` fenced blocks
  - Preserves non-code content

- [ ] 3.1.2 Handle nested code blocks
  - Test triple-backtick in code block
  - Correct parsing with nesting
  - No false removal

- [ ] 3.1.3 Integrate into validate_plan_execution.sh
  - Filter PLAN.md before keyword detection
  - Apply to all text-based validation
  - Preserve original file

### 3.2 Testing & Evidence

- [ ] 3.2.1 Unit test: Simple code block
  - Input: Text with single ``` block
  - Output: Block removed, text preserved
  - Verification

- [ ] 3.2.2 Unit test: Multiple code blocks
  - Input: Multiple ``` blocks
  - Output: All blocks removed
  - Text between blocks preserved

- [ ] 3.2.3 Integration test: False positive elimination
  - PLAN with "performance" in code block
  - Keyword detection doesn't trigger
  - Real "performance" text still detected

- [ ] 3.2.4 Performance test: Large PLAN.md
  - Input: 10,000 line PLAN
  - Execution time: <50ms
  - Memory usage: acceptable

---

## 🎯 P0-4: Regex Escaping

### 4.1 Implementation

- [ ] 4.1.1 Implement re_escape() function
  - Escape regex special chars: ^$.*+?()[]{}|\
  - Use sed for replacement
  - Handle edge cases

- [ ] 4.1.2 Apply to all grep operations
  - Update validate_plan_execution.sh
  - Update validate_checklist.sh
  - Escape user input before grep

- [ ] 4.1.3 Handle both grep -E and grep -F
  - Test with extended regex mode
  - Test with fixed string mode
  - Consistent behavior

### 4.2 Testing & Evidence

- [ ] 4.2.1 Unit test: Special characters
  - Test: "Test (payment) $99.99 [confirmed]"
  - Escaped correctly
  - Grep matches literal string

- [ ] 4.2.2 Unit test: Edge cases
  - Test nested brackets: "[[foo]]"
  - Test dots: "version.2.0"
  - Test pipes: "cmd | filter"

- [ ] 4.2.3 Integration test: Real checklist items
  - Items with parentheses validate
  - Items with dots validate
  - No grep errors

- [ ] 4.2.4 Performance test: Escaping speed
  - 100 strings escaped
  - Time: <100ms total (<1ms each)
  - No memory leaks

---

## 🔧 Integration & Documentation

### 5.1 System Integration

- [ ] 5.1.1 Update pre-commit hook
  - Include all new validations
  - Performance: <2s total
  - Clear error messages

- [ ] 5.1.2 Create migration tool
  - scripts/migrate_to_id_system.sh
  - Auto-generate IDs for existing projects
  - Preserve evidence references

- [ ] 5.1.3 Update CI/CD workflows
  - Add jq installation step
  - Run enhanced validations
  - Fail on validation errors

### 5.2 Documentation

- [ ] 5.2.1 Create usage guide
  - docs/ANTI_HOLLOW_GUIDE.md
  - Explain ID system
  - Evidence validation examples

- [ ] 5.2.2 Update CHANGELOG.md
  - List all 4 P0 improvements
  - Breaking changes (if any)
  - Migration instructions

- [ ] 5.2.3 Update CLAUDE.md
  - Add new validation rules
  - Update workflow examples
  - Link to guide

### 5.3 Testing & Quality

- [ ] 5.3.1 Run complete test suite
  - All unit tests pass
  - All integration tests pass
  - All stress tests pass

- [ ] 5.3.2 Performance benchmark
  - Before: ~200ms validation
  - After: <700ms validation
  - Within 3.5x target

- [ ] 5.3.3 Backward compatibility test
  - v8.1.0 projects still work
  - Legacy mode functions correctly
  - Migration tool tested

---

## 📊 Success Metrics

### Validation Reliability
- [ ] ID-based matching: 100% reliable with text changes
- [ ] Evidence validation: 100% completeness enforcement
- [ ] Code block filtering: 0% false positives
- [ ] Regex escaping: 0% special character failures

### Performance
- [ ] Total validation time: <1s for typical project
- [ ] ID lookup: <10ms per item
- [ ] Evidence validation: <100ms per file
- [ ] Code block filtering: <50ms per PLAN

### Quality
- [ ] All existing evidence files still validate
- [ ] No regression in existing functionality
- [ ] Clear error messages for all failures
- [ ] Documentation complete and accurate

---

## 🎯 Completion Criteria

**Minimum Requirements**:
- ✅ 36/40 items completed (90%)
- ✅ All P0 core functionality implemented
- ✅ All tests passing
- ✅ Performance within targets
- ✅ Documentation complete

**Evidence Requirements**:
- Each completed item must have evidence comment
- Evidence must pass schema validation
- Evidence ID format: EVID-YYYYWWW-NNN

**Example**:
```markdown
- [x] 1.1.1 Create PLAN_CHECKLIST_MAPPING.yml schema definition
<!-- id: CL-AH-001; evidence: EVID-2025W44-020 -->
```

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
