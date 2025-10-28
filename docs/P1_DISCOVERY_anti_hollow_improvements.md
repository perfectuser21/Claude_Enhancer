# Phase 1 Discovery: Anti-Hollow Gate Improvements

**Date**: 2025-10-28
**Feature**: Anti-Hollow improvements
**Status**: Phase 1.2 - Technical Discovery

---

## 📋 Executive Summary

**Context**: PR #49 implemented Anti-Hollow Gate v8.1.0 baseline, establishing the foundation with Evidence System, Auto-Fix v2, KPI Dashboard, and Skills Framework. Post-implementation review and user feedback identified critical improvements needed to strengthen the validation mechanism and prevent hollow implementations more reliably.

**Goal**: Enhance Anti-Hollow Gate system with 4 P0 improvements to eliminate plan-execution verification gaps and strengthen evidence-based validation.

**Problem**: Current implementation has fragile string matching, inadequate evidence schema validation, false keyword triggers, and unsafe regex operations.

**Solution**: Implement stable ID mapping, strict schema validation, code block filtering, and regex escaping to create a robust validation system.

---

## 🎯 Problem Statement

### Current Pain Points

#### 1. **Fragile String Matching** (P0 - Critical)
**Problem**: Plan-to-Checklist mapping relies on plain text string matching
```bash
# Current fragile approach
if grep -q "Performance benchmarks" "$PLAN_FILE"; then
  # Expects exact match in checklist
  grep "Performance benchmarks" "$CHECKLIST_FILE"
fi
```

**Impact**:
- Minor text changes break validation (e.g., "Performance benchmarks" → "Performance testing")
- Cannot track item evolution across iterations
- Difficult to trace which plan item maps to which checklist item

**Evidence**:
- User review feedback (.temp/solution_refinement.md:5-36)
- Historical issues with text-based matching in workflow_guardian.sh

#### 2. **Inadequate Evidence Schema Validation** (P0 - Critical)
**Problem**: Only checks evidence file existence, not required fields
```bash
# Current weak validation
if [[ -f ".evidence/2025W44/${evid}.yml" ]]; then
  echo "✓ Evidence exists"
fi
# ❌ Doesn't check if 'test_command', 'exit_code', 'output_sample' exist
```

**Impact**:
- Can mark items complete with incomplete evidence
- No enforcement of evidence type requirements
- Cannot validate evidence quality

**Evidence**:
- .temp/solution_refinement.md:38-68 (schema validation proposal)
- Evidence schema defined in .evidence/schema.json but not enforced

#### 3. **False Keyword Triggers** (P0 - Important)
**Problem**: Markdown code blocks in PLAN.md trigger keyword detection
```markdown
# PLAN.md example
## Week 4: Performance Testing
```bash
# Example command
bash scripts/performance_benchmark.sh
```

# ❌ Above code block triggers "performance" keyword falsely
```

**Impact**:
- Code examples cause false positives in validation
- Cannot distinguish between actual requirements and examples
- Validation becomes unreliable

**Evidence**:
- .temp/solution_refinement.md:72-94 (code block filtering proposal)

#### 4. **Unsafe Regex Operations** (P0 - Critical)
**Problem**: Special characters in checklist items break grep
```bash
# Problematic item
"Test payment flow (Stripe integration)"

# Current code
grep "Test payment flow (Stripe integration)" # ❌ Fails, () are regex chars
```

**Impact**:
- Items with parentheses, dots, brackets fail validation
- Grep errors cause false negatives
- Validation script crashes

**Evidence**:
- .temp/solution_refinement.md:96-114 (regex escaping proposal)

---

## 🔍 Root Cause Analysis

### Why These Problems Exist

**Root Cause 1: No Stable Identifiers**
- Original design relied on human-readable text
- No unique ID system for tracking items
- Text changes invalidate mappings

**Root Cause 2: Weak Contract Enforcement**
- Evidence schema exists (.evidence/schema.json) but not validated
- Trust-based system without technical enforcement
- No required field validation

**Root Cause 3: Naive Text Processing**
- Simple grep/awk without Markdown awareness
- No distinction between content and code
- Treats all text as potential validation targets

**Root Cause 4: Unescaped User Input**
- Direct use of plan/checklist text in regex
- No sanitization of special characters
- Assumes input is regex-safe

---

## 🎯 Success Criteria

### P0 Improvements (Must Have)

#### 1. Stable ID Mapping System
**Criteria**:
- ✅ Every plan item has unique ID (format: PLAN-W{week}-{nnn})
- ✅ Every checklist item has unique ID (format: CL-W{week}-{nnn})
- ✅ Mapping file tracks relationships (.workflow/PLAN_CHECKLIST_MAPPING.yml)
- ✅ Text changes don't break validation
- ✅ Can trace plan → checklist → evidence chain

**Validation**:
```bash
# Test: Change checklist text without breaking validation
# Before: "- [x] 4.5 KPI Dashboard压力测试 (1000+ items)"
# After:  "- [x] 4.5 Stress test KPI Dashboard with 1000+ items"
# Result: Validation still passes via ID mapping
```

#### 2. Strict Evidence Schema Validation
**Criteria**:
- ✅ Validates all required fields per evidence type
- ✅ Uses jq for YAML field validation
- ✅ Returns clear error for missing fields
- ✅ Checks evidence type enum validity
- ✅ Performance: <100ms per evidence file

**Validation**:
```bash
# Test: Create evidence missing required field
cat > .evidence/2025W44/EVID-2025W44-999.yml <<EOF
id: EVID-2025W44-999
type: functional_test
description: "Test case"
# Missing: test_command, exit_code, output_sample
EOF

# Expected: Validation fails with clear error
bash scripts/evidence/validate_checklist.sh
# Output: "❌ EVID-2025W44-999: missing required field 'test_command'"
```

#### 3. Code Block Filtering
**Criteria**:
- ✅ Strips Markdown code blocks before keyword detection
- ✅ Handles nested code blocks
- ✅ Preserves non-code content
- ✅ No false positives from code examples
- ✅ Performance: <50ms for typical PLAN.md

**Validation**:
```bash
# Test: PLAN with code block containing keyword
cat > test_plan.md <<'EOF'
## Requirements
User must complete performance testing

## Example
```bash
echo "performance testing example"
```
EOF

# Code block should not trigger "performance testing" detection
plan_text=$(strip_code_blocks < test_plan.md)
[[ $(echo "$plan_text" | grep -c "performance testing") -eq 1 ]] # Only real requirement
```

#### 4. Regex Escaping
**Criteria**:
- ✅ Escapes all regex special characters
- ✅ Works with grep -E and grep -F patterns
- ✅ Handles edge cases (nested brackets, dots)
- ✅ Clear function interface (re_escape)
- ✅ Performance: <1ms per string

**Validation**:
```bash
# Test: Item with special characters
item="Test payment (Stripe) $99.99 [confirmed]"
escaped=$(echo "$item" | re_escape)
# Should match literal string, not regex
grep -E "^- \\[x\\] $(echo "$item" | re_escape)" checklist.md
```

---

## 📊 Technical Feasibility

### Dependencies

**New Dependencies**:
- `jq` - JSON/YAML query tool (for evidence validation)
  - Already used in project? **No**
  - Installation: `apt-get install jq` (Debian/Ubuntu), `brew install jq` (macOS)
  - Size: ~1.5MB
  - Risk: Low (stable, widely used)

**Existing Dependencies** (no changes):
- `yq` - YAML processing
- `bash 4+` - Shell scripting
- `grep`, `sed`, `awk` - Text processing

### Implementation Complexity

| Improvement | Complexity | Effort | Risk |
|-------------|-----------|--------|------|
| Stable ID Mapping | Medium | 2-3h | Low |
| Schema Validation | Low | 1h | Low (if jq installed) |
| Code Block Filter | Low | 1h | Very Low |
| Regex Escaping | Very Low | 30m | Very Low |

**Total Estimated Effort**: 4.5-5.5 hours

### Performance Impact

**Expected Performance**:
- ID mapping lookup: <10ms (YAML parsing with yq)
- Schema validation: <100ms per evidence file
- Code block filtering: <50ms per PLAN.md
- Regex escaping: <1ms per string

**Total validation overhead**: <500ms for typical project (10 evidence files)

**Baseline**: Current validation takes ~200ms
**After improvements**: ~700ms (3.5x slower but still <1s, acceptable)

---

## 🏗️ Proposed Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│         Anti-Hollow Gate v8.2 (Enhanced)                │
└─────────────────────────────────────────────────────────┘
              │
              ├─ Layer 1: Plan-to-Checklist Mapping
              │  ├─ .workflow/PLAN_CHECKLIST_MAPPING.yml
              │  │  └─ Stable IDs: PLAN-W4-001 ↔ CL-W4-005
              │  └─ scripts/generate_checklist_from_plan.sh
              │
              ├─ Layer 2: Evidence Schema Validation
              │  ├─ .evidence/schema.json (type definitions)
              │  ├─ scripts/evidence/validate_checklist.sh
              │  └─ validate_evidence_file() with jq
              │
              ├─ Layer 3: Safe Text Processing
              │  ├─ strip_code_blocks() - Filter Markdown
              │  ├─ re_escape() - Escape regex chars
              │  └─ scripts/validate_plan_execution.sh
              │
              └─ Integration: Pre-commit Hook
                 └─ .git/hooks/pre-commit
                    └─ All validations before commit
```

### Data Flow

```
1. Plan Creation (Phase 1.5)
   PLAN.md created
      ↓
   generate_checklist_from_plan.sh
      ↓
   PLAN_CHECKLIST_MAPPING.yml + CHECKLIST.md (with IDs)

2. Checklist Completion (Phase 3+)
   Developer marks: [x] CL-W4-005
      ↓
   Evidence collected: EVID-2025W44-015
      ↓
   Checklist comment: <!-- id: CL-W4-005; evidence: EVID-2025W44-015 -->

3. Validation (Pre-commit)
   Read MAPPING.yml
      ↓
   For each plan_item:
      ├─ Find mapped checklist_item by ID
      ├─ Check [x] status
      ├─ Extract evidence ID from comment
      ├─ validate_evidence_file(EVID-2025W44-015)
      │  ├─ Check file exists
      │  ├─ Validate type field
      │  └─ Validate required fields (jq)
      └─ ✅ Pass or ❌ Fail with clear error
```

### File Structure Changes

**New Files**:
```
.workflow/
└── PLAN_CHECKLIST_MAPPING.yml    # NEW: ID mapping registry

scripts/
├── validate_mapping_schema.sh     # NEW: Mapping file validation
└── lib/
    ├── text_processing.sh         # NEW: strip_code_blocks, re_escape
    └── evidence_validation.sh     # NEW: validate_evidence_file
```

**Modified Files**:
```
scripts/generate_checklist_from_plan.sh   # Add ID generation
scripts/evidence/validate_checklist.sh    # Add schema validation
scripts/validate_plan_execution.sh        # Add code block filtering
```

---

## 🧪 Testing Strategy

### Test Levels

#### 1. Unit Tests (scripts/tests/)
**Coverage**:
- `test_stable_id_generation.sh` - ID format validation
- `test_evidence_schema.sh` - Schema validation with jq
- `test_code_block_filter.sh` - Markdown parsing
- `test_regex_escape.sh` - Special character handling

#### 2. Integration Tests
**Scenarios**:
- End-to-end: Plan → Checklist → Evidence → Validation
- Text change resilience: Modify checklist text, validation still passes
- Invalid evidence detection: Missing fields caught
- Code block false positive: Examples don't trigger validation

#### 3. Regression Tests
**Baseline**: v8.1.0 behavior preserved
- Existing evidence files still validate
- Current PLAN/CHECKLIST format compatible
- No performance regression (within 3x)

#### 4. Stress Tests
**Scale Tests**:
- 100+ plan items with IDs
- 50+ evidence files validation
- Large PLAN.md (10,000 lines) with code blocks
- Performance target: <5s for 100 items

---

## 📝 Migration Plan

### Backward Compatibility

**Strategy**: Dual-mode operation

```bash
# Detect legacy format (no IDs)
if ! grep -q "<!-- id: CL-" "$CHECKLIST_FILE"; then
  # Legacy mode: Use text matching (current behavior)
  validate_legacy_checklist
else
  # New mode: Use ID mapping
  validate_with_id_mapping
fi
```

**Migration Path**:
1. v8.1.0 → v8.2.0: Both modes supported
2. v8.3.0: Deprecation warning for legacy format
3. v9.0.0: Legacy mode removed (breaking change)

### Existing Projects

**Auto-migration tool**:
```bash
# scripts/migrate_to_id_system.sh
# - Scans existing PLAN.md and CHECKLIST.md
# - Generates MAPPING.yml with IDs
# - Updates checklist comments with IDs
# - Preserves existing evidence references
```

---

## 🚨 Risk Analysis

### Technical Risks

#### Risk 1: jq Dependency
**Probability**: Medium
**Impact**: High (blocks schema validation)
**Mitigation**:
- Check jq availability in setup script
- Provide installation instructions
- Fallback: Basic YAML validation with yq (less strict)

#### Risk 2: ID Collision
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Sequential numbering per week (W4-001, W4-002...)
- Validation script checks uniqueness
- Clear error if collision detected

#### Risk 3: Performance Degradation
**Probability**: Low
**Impact**: Low (validation <5s acceptable)
**Mitigation**:
- Benchmark before/after
- Cache parsed YAML in memory
- Parallel evidence validation if needed

### Process Risks

#### Risk 4: User Adoption Resistance
**Probability**: Low (personal project)
**Impact**: Medium
**Mitigation**:
- Auto-migration tool for existing projects
- Clear documentation and examples
- Backward compatibility in v8.2.0

---

## 📚 Reference Materials

### User Feedback
- `.temp/solution_refinement.md` - Complete refinement plan with P0/P1/P2 priorities
- User's professional review (message #14 in context) - 10 detailed suggestions

### Current Implementation
- `scripts/evidence/collect.sh` - Evidence collection (287 lines)
- `scripts/evidence/validate_checklist.sh` - Current validation (218 lines)
- `.evidence/schema.json` - Evidence type definitions (114 lines)

### Proposed Improvements
- `.temp/anti_hollow_solution.md` - Original complete solution
- User decisions: 60% adoption rate (P0: 100%, P1: 60%, P2: 0%)

---

## 🎯 Next Steps (Phase 1.3-1.5)

### Phase 1.3: Create Acceptance Checklist
**Define completion criteria for each P0 improvement**

### Phase 1.4: Impact Assessment
**Calculate impact radius and agent strategy**

### Phase 1.5: Create Implementation Plan
**Detailed week-by-week plan with testing requirements**

---

## 📊 Metrics & Success Indicators

### Validation Reliability
- **Before**: Text matching fragility = High
- **After**: ID-based matching fragility = Zero

### Evidence Quality
- **Before**: Evidence completeness = Unknown (no validation)
- **After**: Evidence completeness = 100% (required fields enforced)

### False Positive Rate
- **Before**: Code block false positives = Unknown
- **After**: Code block false positives = 0%

### Regex Safety
- **Before**: Special character failures = Frequent
- **After**: Special character failures = 0%

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
