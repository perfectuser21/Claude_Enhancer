# Implementation Plan: Anti-Hollow Gate Improvements v8.2

**Feature**: Anti-Hollow Gate Enhancements
**Date**: 2025-10-28
**Impact**: 43 points (MEDIUM)
**Agent Strategy**: 3 Agents (parallel)
**Estimated Duration**: 4.5-5 hours

---

## 📋 Executive Summary

### Objectives

Enhance Anti-Hollow Gate system with 4 P0 improvements to eliminate plan-execution verification gaps:

1. **Stable ID Mapping**: Replace fragile string matching with unique IDs
2. **Evidence Schema Validation**: Enforce required fields per evidence type
3. **Code Block Filtering**: Eliminate false positives from Markdown code examples
4. **Regex Escaping**: Safe handling of special characters in validation

### Success Criteria

- ✅ 100% text-change resilience (ID-based validation)
- ✅ 100% evidence completeness enforcement
- ✅ 0% false positives from code blocks
- ✅ 0% regex escaping failures
- ✅ <1s total validation time (3.5x current acceptable)
- ✅ Backward compatible with v8.1.0 (dual-mode operation)

### Delivery Approach

**3-Agent Parallel Strategy** (based on Impact Assessment):
- **Agent 1**: ID System & Mapping (2-3h)
- **Agent 2**: Evidence & Text Processing (2-2.5h)
- **Agent 3**: Integration & Documentation (1.5-2h)

**Total Time**: 4.5 hours (vs 6 hours sequential, 25% faster)

---

## 🎯 Week 1: Core Infrastructure

**Duration**: 2-3 hours (Agent 1 + Agent 2 parallel)
**Deliverables**: ID mapping system + Evidence validation + Text processing utilities

### Agent 1: Stable ID Mapping System

#### Day 1.1: Schema & Data Structure (45 min)

**Objective**: Define MAPPING.yml structure and ID format

**Tasks**:

1. **Create MAPPING.yml schema definition**
   ```yaml
   # .workflow/PLAN_CHECKLIST_MAPPING.yml
   version: "1.0"
   plan_file: "docs/PLAN_xxx.md"
   checklist_file: "docs/ACCEPTANCE_CHECKLIST_xxx.md"
   mappings:
     - plan_section: "Week 4: KPI Dashboard"
       plan_items:
         - id: PLAN-W4-001
           text: "4 KPI metrics implementation"
       checklist_items:
         - id: CL-W4-005
           text: "4.5 KPI Dashboard压力测试 (1000+ items)"
           required_evidence_type: "stress_test"
   ```

2. **Implement ID generation function**
   ```bash
   # scripts/lib/id_mapping.sh
   generate_plan_id() {
     local week="$1"
     local counter="$2"
     printf "PLAN-W%s-%03d" "$week" "$counter"
   }

   generate_checklist_id() {
     local week="$1"
     local counter="$2"
     printf "CL-W%s-%03d" "$week" "$counter"
   }
   ```

3. **Create ID uniqueness validator**
   ```bash
   validate_id_uniqueness() {
     local mapping_file="$1"
     # Check no duplicate plan IDs
     # Check no duplicate checklist IDs
     # Return 0 if unique, 1 if collision
   }
   ```

**Deliverables**:
- `.workflow/PLAN_CHECKLIST_MAPPING.yml` (schema)
- `scripts/lib/id_mapping.sh` (ID generation)
- Unit tests: `scripts/tests/test_id_generation.sh`

**Testing**:
```bash
# Test ID format
[[ $(generate_plan_id 4 1) == "PLAN-W4-001" ]]
[[ $(generate_checklist_id 4 5) == "CL-W4-005" ]]

# Test collision detection
# Should fail with duplicate IDs
```

**Evidence Required**:
- Test output showing ID format validation
- Collision detection working

---

#### Day 1.2: Mapping Generator (60 min)

**Objective**: Auto-generate MAPPING.yml from existing PLAN.md

**Tasks**:

1. **Create mapping generator script**
   ```bash
   # scripts/generate_mapping.sh
   #!/usr/bin/env bash

   PLAN_FILE="$1"
   OUTPUT_FILE=".workflow/PLAN_CHECKLIST_MAPPING.yml"

   # Parse PLAN.md structure
   # Extract week sections (## Week N:)
   # Extract items within each week
   # Generate sequential IDs
   # Output YAML
   ```

2. **Parse PLAN.md structure**
   - Identify week sections: `## Week N: Title`
   - Extract items: Lines starting with `- ` or numbered lists
   - Assign IDs sequentially per week

3. **Handle edge cases**
   - Sub-items (indented lists)
   - Code blocks (should be ignored)
   - Empty weeks

**Deliverables**:
- `scripts/generate_mapping.sh` (~150 lines)
- Sample MAPPING.yml output

**Testing**:
```bash
# Test with sample PLAN.md
cat > test_plan.md <<'EOF'
## Week 1: Infrastructure
- Item A
- Item B

## Week 2: Features
- Item C
EOF

bash scripts/generate_mapping.sh test_plan.md
# Verify output has correct IDs
```

**Evidence Required**:
- Generated MAPPING.yml matches expected structure
- Handles nested items correctly

---

#### Day 1.3: Checklist ID Integration (45 min)

**Objective**: Update checklist generation to include IDs

**Tasks**:

1. **Modify generate_checklist_from_plan.sh**
   ```bash
   # Add ID comment after checklist item
   echo "- [ ] ${item_text}"
   echo "<!-- id: ${checklist_id}; evidence: -->"
   ```

2. **Read IDs from MAPPING.yml**
   - Use yq to parse mapping file
   - Match checklist items to IDs
   - Insert ID comments

3. **Preserve evidence IDs if already present**
   ```bash
   # If evidence already collected
   if [[ -n "$existing_evidence" ]]; then
     echo "<!-- id: ${checklist_id}; evidence: ${existing_evidence} -->"
   fi
   ```

**Deliverables**:
- Updated `scripts/generate_checklist_from_plan.sh` (+50 lines)

**Testing**:
```bash
# Generate checklist from PLAN with mapping
bash scripts/generate_checklist_from_plan.sh docs/PLAN_test.md
# Verify checklist has <!-- id: CL-W1-001 --> comments
```

**Evidence Required**:
- Checklist output contains ID comments
- Evidence IDs preserved if present

---

#### Day 1.4: ID-Based Validation (30 min)

**Objective**: Update validation to use IDs instead of text

**Tasks**:

1. **Implement lookup_checklist_item_by_id()**
   ```bash
   lookup_checklist_item_by_id() {
     local mapping_file="$1"
     local plan_id="$2"

     # Query MAPPING.yml for checklist items mapped to plan_id
     yq eval ".mappings[] | select(.plan_items[].id == \"$plan_id\") | .checklist_items[].id" "$mapping_file"
   }
   ```

2. **Update validate_plan_execution.sh**
   ```bash
   # Old: grep for item text
   # New: lookup by ID, then check [x] status

   for plan_id in $(yq eval '.mappings[].plan_items[].id' "$MAPPING_FILE"); do
     checklist_ids=$(lookup_checklist_item_by_id "$MAPPING_FILE" "$plan_id")
     for cl_id in $checklist_ids; do
       # Find line with <!-- id: $cl_id -->
       # Check if line has [x]
     done
   done
   ```

3. **Implement dual-mode detection**
   ```bash
   if grep -q '<!-- id: CL-' "$CHECKLIST_FILE"; then
     validate_with_ids  # New ID-based mode
   else
     validate_legacy    # Old text-based mode
   fi
   ```

**Deliverables**:
- Updated `scripts/validate_plan_execution.sh` (+100 lines)

**Testing**:
```bash
# Test ID-based validation
# Modify checklist text, validation should still pass
```

**Evidence Required**:
- Text change doesn't break validation
- Both modes work correctly

---

### Agent 2: Evidence & Text Processing

#### Day 2.1: Evidence Schema Validation (60 min)

**Objective**: Enforce required fields per evidence type using jq

**Tasks**:

1. **Install jq dependency check**
   ```bash
   # scripts/lib/evidence_validation.sh
   check_jq_available() {
     if ! command -v jq &>/dev/null; then
       echo "❌ jq not installed. Install: apt-get install jq / brew install jq"
       return 1
     fi
   }
   ```

2. **Implement validate_evidence_file()**
   ```bash
   validate_evidence_file() {
     local evid_file="$1"
     local schema_file=".evidence/schema.json"

     # Extract type
     local ev_type=$(yq -r '.type // ""' "$evid_file")
     [[ -n "$ev_type" ]] || { echo "❌ Missing type"; return 1; }

     # Get required fields for this type
     local required_fields=$(jq -r --arg t "$ev_type" \
       '.evidence_types[] | select(.type==$t) | .required_fields[]' \
       "$schema_file")

     # Check each required field exists
     while read -r field; do
       yq -e ".$field" "$evid_file" >/dev/null 2>&1 || {
         echo "❌ $evid_file: missing required field '$field'"
         return 1
       }
     done <<< "$required_fields"

     return 0
   }
   ```

3. **Integrate into validate_checklist.sh**
   ```bash
   # After extracting evidence ID from comment
   validate_evidence_file ".evidence/2025W44/${evid}.yml" || exit 1
   ```

**Deliverables**:
- `scripts/lib/evidence_validation.sh` (~100 lines)
- Updated `scripts/evidence/validate_checklist.sh` (+20 lines)

**Testing**:
```bash
# Test valid evidence
cat > .evidence/test/EVID-TEST-001.yml <<EOF
id: EVID-TEST-001
type: functional_test
test_command: "bash test.sh"
exit_code: 0
output_sample: "All tests passed"
EOF
validate_evidence_file .evidence/test/EVID-TEST-001.yml  # Should pass

# Test invalid evidence (missing field)
cat > .evidence/test/EVID-TEST-002.yml <<EOF
id: EVID-TEST-002
type: functional_test
# Missing: test_command, exit_code, output_sample
EOF
validate_evidence_file .evidence/test/EVID-TEST-002.yml  # Should fail
```

**Evidence Required**:
- Valid evidence passes validation
- Invalid evidence fails with clear error message
- Performance: <100ms per file

---

#### Day 2.2: Code Block Filtering (45 min)

**Objective**: Strip Markdown code blocks before keyword detection

**Tasks**:

1. **Implement strip_code_blocks()**
   ```bash
   # scripts/lib/text_processing.sh
   strip_code_blocks() {
     awk '
       BEGIN { in_block = 0 }
       /^```/ {
         in_block = !in_block
         next
       }
       !in_block { print }
     '
   }
   ```

2. **Handle nested code blocks**
   - Track nesting level
   - Only output when level == 0

3. **Integrate into validate_plan_execution.sh**
   ```bash
   # Before keyword detection
   plan_content=$(strip_code_blocks < "$PLAN_FILE")

   # Now search in filtered content
   if echo "$plan_content" | grep -q "Performance benchmarks"; then
     # This won't trigger on code examples
   fi
   ```

**Deliverables**:
- `scripts/lib/text_processing.sh` (strip_code_blocks function, ~30 lines)
- Updated `scripts/validate_plan_execution.sh` (+10 lines)

**Testing**:
```bash
# Test code block removal
cat > test.md <<'EOF'
Real requirement: Performance testing required

Example code:
```bash
echo "Performance testing example"
```

Another requirement here
EOF

filtered=$(strip_code_blocks < test.md)
[[ $(echo "$filtered" | grep -c "Performance") -eq 1 ]]  # Only real requirement
```

**Evidence Required**:
- Code blocks removed correctly
- Non-code content preserved
- Performance: <50ms for 10K line file

---

#### Day 2.3: Regex Escaping (30 min)

**Objective**: Safe handling of special characters in grep patterns

**Tasks**:

1. **Implement re_escape()**
   ```bash
   # scripts/lib/text_processing.sh
   re_escape() {
     sed -e 's/[^^$.*+?()[\]{}|\\]/\\&/g'
   }
   ```

2. **Apply to all user input in grep**
   ```bash
   # Before
   grep "$item_text" file  # ❌ Unsafe

   # After
   grep "$(echo "$item_text" | re_escape)" file  # ✅ Safe
   ```

3. **Update validation scripts**
   - `scripts/validate_plan_execution.sh`
   - `scripts/evidence/validate_checklist.sh`

**Deliverables**:
- `scripts/lib/text_processing.sh` (re_escape function, ~5 lines)
- Updated validation scripts (+15 lines total)

**Testing**:
```bash
# Test special characters
test_strings=(
  "Test (payment) flow"
  "Version 2.0.1"
  "Filter | command"
  "Array [0]"
)

for str in "${test_strings[@]}"; do
  escaped=$(echo "$str" | re_escape)
  echo "Test string" | grep "$escaped"  # Should not error
done
```

**Evidence Required**:
- All special characters escaped correctly
- Grep doesn't fail on any input
- Performance: <1ms per string

---

## 🎯 Week 2: Integration & Testing

**Duration**: 1.5-2 hours (Agent 3)
**Deliverables**: Integrated system + Complete test suite + Documentation

### Agent 3: Integration & Documentation

#### Day 3.1: Pre-commit Hook Integration (30 min)

**Objective**: Integrate all validations into pre-commit hook

**Tasks**:

1. **Update .git/hooks/pre-commit**
   ```bash
   # Source new libraries
   source scripts/lib/id_mapping.sh
   source scripts/lib/evidence_validation.sh
   source scripts/lib/text_processing.sh

   # Run validations
   echo "🔍 Validating ID mapping..."
   bash scripts/validate_mapping_schema.sh || exit 1

   echo "🔍 Validating evidence..."
   bash scripts/evidence/validate_checklist.sh || exit 1

   echo "🔍 Validating plan execution..."
   bash scripts/validate_plan_execution.sh || exit 1
   ```

2. **Performance check**
   - Measure total validation time
   - Must be <2s for pre-commit
   - Optimize if needed

3. **Error message clarity**
   - Each validation failure has clear error
   - Points to specific file and line
   - Suggests fix

**Deliverables**:
- Updated `.git/hooks/pre-commit` (+40 lines)

**Testing**:
```bash
# Test pre-commit hook
# Should run all validations in <2s
time .git/hooks/pre-commit
```

**Evidence Required**:
- All validations execute
- Total time <2s
- Clear error messages

---

#### Day 3.2: Migration Tool (45 min)

**Objective**: Auto-migrate v8.1.0 projects to v8.2

**Tasks**:

1. **Create migration script**
   ```bash
   # scripts/migrate_to_id_system.sh
   #!/usr/bin/env bash

   echo "🔄 Migrating to ID-based system..."

   # Step 1: Find PLAN and CHECKLIST files
   # Step 2: Generate MAPPING.yml
   # Step 3: Update CHECKLIST with ID comments
   # Step 4: Preserve existing evidence references
   # Step 5: Validate migration
   ```

2. **Preserve evidence references**
   ```bash
   # Extract existing evidence IDs from comments
   # Preserve them in new ID-based comments
   # <!-- evidence: EVID-xxx --> → <!-- id: CL-W1-001; evidence: EVID-xxx -->
   ```

3. **Dry-run mode**
   ```bash
   # Show what would change without modifying files
   bash scripts/migrate_to_id_system.sh --dry-run
   ```

**Deliverables**:
- `scripts/migrate_to_id_system.sh` (~200 lines)

**Testing**:
```bash
# Test with v8.1.0 project
cp -r test-project test-project-backup
bash scripts/migrate_to_id_system.sh test-project
# Verify MAPPING.yml created
# Verify CHECKLIST has IDs
# Verify evidence preserved
```

**Evidence Required**:
- v8.1.0 project successfully migrated
- All evidence preserved
- Validation passes after migration

---

#### Day 3.3: Complete Test Suite (45 min)

**Objective**: Comprehensive testing of all improvements

**Tasks**:

1. **Unit tests**
   - `tests/test_id_generation.sh` - ID format & uniqueness
   - `tests/test_evidence_schema.sh` - Schema validation
   - `tests/test_code_block_filter.sh` - Markdown parsing
   - `tests/test_regex_escape.sh` - Special character handling

2. **Integration tests**
   - `tests/test_end_to_end.sh` - PLAN → CHECKLIST → Evidence → Validation
   - `tests/test_text_change_resilience.sh` - Modify text, validation passes
   - `tests/test_dual_mode.sh` - Both legacy and ID modes work

3. **Performance tests**
   - `tests/test_performance.sh` - Validate <1s for typical project
   - Test with 100 items, 50 evidence files
   - Measure each component separately

4. **Regression tests**
   - Existing v8.1.0 evidence still validates
   - No breaking changes in API
   - Performance within 3x baseline

**Deliverables**:
- `scripts/tests/test_suite.sh` (runs all tests)
- Individual test scripts (~50 lines each)

**Testing**:
```bash
# Run complete test suite
bash scripts/tests/test_suite.sh

# Expected output:
# ✅ Unit tests: 15/15 passed
# ✅ Integration tests: 8/8 passed
# ✅ Performance tests: 4/4 passed
# ✅ Regression tests: 5/5 passed
# Total: 32/32 tests passed (100%)
```

**Evidence Required**:
- All tests passing
- Coverage report showing critical paths tested
- Performance benchmarks

---

#### Day 3.4: Documentation (30 min)

**Objective**: Complete user-facing documentation

**Tasks**:

1. **Create docs/ANTI_HOLLOW_GUIDE.md**
   ```markdown
   # Anti-Hollow Gate User Guide

   ## ID-Based Validation
   - What are PLAN IDs and Checklist IDs?
   - How to use MAPPING.yml
   - Migration from v8.1.0

   ## Evidence Schema Validation
   - Required fields per type
   - How to create valid evidence
   - Troubleshooting validation errors

   ## Examples
   - Complete workflow example
   - Code block filtering demo
   - Special character handling
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [8.2.0] - 2025-10-28

   ### Added
   - Stable ID mapping system (PLAN-Wn-nnn, CL-Wn-nnn)
   - Evidence schema strict validation with jq
   - Code block filtering for Markdown
   - Regex escaping for special characters

   ### Changed
   - validate_plan_execution.sh now uses ID-based lookup
   - Dual-mode operation (ID mode + legacy text mode)

   ### Migration
   - Use `scripts/migrate_to_id_system.sh` to upgrade
   - v8.1.0 projects still compatible
   ```

3. **Update CLAUDE.md**
   ```markdown
   ## 🛡️ 规则3: Anti-Hollow Gate System v8.2

   ### New in v8.2:
   - Stable ID mapping (text-change resilient)
   - 100% evidence completeness enforcement
   - 0% false positives from code blocks
   ```

**Deliverables**:
- `docs/ANTI_HOLLOW_GUIDE.md` (~500 lines)
- Updated `CHANGELOG.md` (+30 lines)
- Updated `CLAUDE.md` (+20 lines)

**Evidence Required**:
- Documentation covers all new features
- Examples are accurate and tested
- Migration guide is clear

---

## 📊 Quality Gates

### Phase 3: Testing (Before Phase 4)

**Automated Checks** (Must pass 100%):
- ✅ All unit tests pass (15/15)
- ✅ All integration tests pass (8/8)
- ✅ Performance tests within targets
  - Total validation: <1s
  - ID lookup: <10ms
  - Evidence validation: <100ms/file
  - Code block filtering: <50ms
- ✅ Shellcheck linting: 0 errors, 0 warnings
- ✅ Bash syntax validation: All scripts valid

**Manual Checks** (Agent 3 verifies):
- 🤖 Dual-mode validation works correctly
- 🤖 Migration tool preserves all evidence
- 🤖 Error messages are clear and actionable
- 🤖 Documentation examples are accurate

---

### Phase 4: Review (Before Phase 5)

**Pre-merge Audit** (`scripts/pre_merge_audit.sh`):
- ✅ Configuration completeness (jq installed, hooks registered)
- ✅ Evidence validation (100% compliance)
- ✅ Version consistency (6 files: VERSION, settings.json, manifest.yml, package.json, CHANGELOG.md, SPEC.yaml)
- ✅ No hollow implementations
- ✅ Root documents ≤7
- ✅ Documentation complete

**Manual Review**:
- 🤖 Code follows project patterns
- 🤖 MAPPING.yml schema is correct
- 🤖 Acceptance checklist ≥90% complete
- 🤖 All 4 P0 improvements implemented

---

## 🚨 Risk Mitigation

### Risk 1: jq Not Available

**Likelihood**: Medium
**Impact**: High (blocks evidence validation)

**Mitigation**:
- **Detection**: Pre-commit hook checks jq availability
- **Installation guide**: Add to docs/INSTALLATION.md
  ```bash
  # Debian/Ubuntu
  sudo apt-get install jq

  # macOS
  brew install jq

  # Verify
  jq --version
  ```
- **Fallback**: Basic YAML validation with yq (less strict)
  ```bash
  if ! command -v jq &>/dev/null; then
    echo "⚠️ jq not found, using basic validation"
    validate_evidence_basic  # yq-based, checks type only
  fi
  ```

**Success Criteria**: Installation guide tested on 3 platforms

---

### Risk 2: Performance Degradation

**Likelihood**: Low
**Impact**: Medium (validation >2s annoys users)

**Mitigation**:
- **Benchmark early**: Measure after Agent 1 & 2 complete
- **Optimization pass**: If >1s, optimize:
  - Cache parsed YAML in memory
  - Parallel evidence validation
  - Skip validation if no changes
- **Target**: <1s for typical project (10 evidence files)

**Success Criteria**: Performance test passes with <1s

---

### Risk 3: Migration Tool Breaks Evidence

**Likelihood**: Low
**Impact**: High (data loss)

**Mitigation**:
- **Dry-run mode**: Show changes without applying
- **Backup reminder**: Script warns to backup first
- **Validation step**: Run validation after migration
- **Comprehensive testing**: Test with v8.1.0 projects

**Success Criteria**: 3 test projects migrated successfully

---

### Risk 4: Backward Compatibility Issues

**Likelihood**: Low
**Impact**: Medium (users stuck on v8.1.0)

**Mitigation**:
- **Dual-mode operation**: Support both legacy and ID modes
- **Auto-detection**: Check for ID comments, fall back gracefully
- **Clear migration path**: v8.2 → v8.3 deprecation → v9.0 removal
- **Testing**: Validate v8.1.0 projects work unchanged

**Success Criteria**: v8.1.0 projects validate without modification

---

## 📈 Success Metrics

### Validation Reliability
- **Before v8.2**: Text matching, fragile to changes
- **After v8.2**: ID-based, 100% resilient to text changes

**Test**: Change 10 checklist item texts, validation still passes

---

### Evidence Quality
- **Before v8.2**: Evidence completeness unknown (no field validation)
- **After v8.2**: 100% completeness enforcement (all required fields checked)

**Test**: Create evidence missing field, validation fails

---

### False Positive Rate
- **Before v8.2**: Unknown (code blocks trigger keywords)
- **After v8.2**: 0% (code blocks filtered)

**Test**: PLAN with "performance" in code block doesn't trigger validation

---

### Regex Safety
- **Before v8.2**: Special characters cause grep failures
- **After v8.2**: 0% failures (all chars escaped)

**Test**: 100 items with special chars, all validate successfully

---

## 📦 Deliverables Checklist

### Week 1 (Agent 1 + Agent 2)

**Agent 1 Deliverables**:
- [ ] `.workflow/PLAN_CHECKLIST_MAPPING.yml` - Schema definition
- [ ] `scripts/lib/id_mapping.sh` - ID generation functions
- [ ] `scripts/generate_mapping.sh` - Mapping generator
- [ ] Updated `scripts/generate_checklist_from_plan.sh` - ID integration
- [ ] Updated `scripts/validate_plan_execution.sh` - ID-based validation
- [ ] `scripts/tests/test_id_generation.sh` - Unit tests

**Agent 2 Deliverables**:
- [ ] `scripts/lib/evidence_validation.sh` - Schema validation
- [ ] `scripts/lib/text_processing.sh` - Code block filter, regex escape
- [ ] Updated `scripts/evidence/validate_checklist.sh` - Integration
- [ ] `scripts/tests/test_evidence_schema.sh` - Unit tests
- [ ] `scripts/tests/test_text_processing.sh` - Unit tests

### Week 2 (Agent 3)

**Agent 3 Deliverables**:
- [ ] Updated `.git/hooks/pre-commit` - Integration
- [ ] `scripts/migrate_to_id_system.sh` - Migration tool
- [ ] `scripts/tests/test_suite.sh` - Complete test suite
- [ ] `scripts/tests/test_end_to_end.sh` - Integration test
- [ ] `scripts/tests/test_performance.sh` - Performance benchmark
- [ ] `docs/ANTI_HOLLOW_GUIDE.md` - User guide
- [ ] Updated `CHANGELOG.md` - Release notes
- [ ] Updated `CLAUDE.md` - Documentation

---

## 🎯 Acceptance Criteria

### Must Have (P0)

1. **Stable ID Mapping**
   - ✅ Every plan item has unique ID
   - ✅ Every checklist item has unique ID
   - ✅ MAPPING.yml tracks relationships
   - ✅ Text changes don't break validation
   - ✅ Can trace plan → checklist → evidence chain

2. **Evidence Schema Validation**
   - ✅ Validates all required fields per type
   - ✅ Uses jq for field checking
   - ✅ Clear error for missing fields
   - ✅ Performance: <100ms per file

3. **Code Block Filtering**
   - ✅ Strips ``` blocks before keyword detection
   - ✅ Handles nested blocks
   - ✅ No false positives from code examples
   - ✅ Performance: <50ms for typical PLAN

4. **Regex Escaping**
   - ✅ Escapes all special characters
   - ✅ Works with grep -E and grep -F
   - ✅ Handles edge cases (nested brackets, dots)
   - ✅ Performance: <1ms per string

### Quality Criteria

- ✅ All tests passing (32/32)
- ✅ Performance within targets (<1s total)
- ✅ Backward compatible (v8.1.0 projects work)
- ✅ Documentation complete and accurate
- ✅ No regressions in existing functionality

### Completion Criteria

- ✅ 36/40 acceptance checklist items (90%)
- ✅ Each item has evidence comment
- ✅ All evidence passes schema validation
- ✅ Pre-merge audit passes

---

## 📅 Timeline Summary

```
Day 1 (2.5h):
├─ Agent 1: ID System (parallel)
│  ├─ Schema & data structure (45m)
│  ├─ Mapping generator (60m)
│  ├─ Checklist integration (45m)
│  └─ ID-based validation (30m)
│
└─ Agent 2: Evidence & Text (parallel)
   ├─ Evidence schema validation (60m)
   ├─ Code block filtering (45m)
   └─ Regex escaping (30m)

Day 2 (2h):
└─ Agent 3: Integration
   ├─ Pre-commit hook integration (30m)
   ├─ Migration tool (45m)
   ├─ Complete test suite (45m)
   └─ Documentation (30m)

Total: 4.5 hours (25% faster than sequential)
```

---

## 🔄 Phase Transitions

### Phase 1 → Phase 2
**Trigger**: All Phase 1 docs complete (P1_DISCOVERY, CHECKLIST, IMPACT_ASSESSMENT, PLAN) ✅

**Checkpoint**:
- [ ] Workflow Guardian validates 4 Phase 1 docs present
- [ ] Impact Assessment shows 43 points (MEDIUM)
- [ ] 3-agent strategy approved

**Action**: Launch Agent 1 & Agent 2 in parallel

---

### Phase 2 → Phase 3
**Trigger**: All Agent 1 & Agent 2 deliverables complete

**Checkpoint**:
- [ ] Agent 1 deliverables: 6/6 files
- [ ] Agent 2 deliverables: 5/5 files
- [ ] Initial unit tests passing

**Action**: Launch Agent 3 for integration

---

### Phase 3 → Phase 4
**Trigger**: All automated tests pass ⛔ Quality Gate 1

**Checkpoint**:
- [ ] Unit tests: 15/15 passed
- [ ] Integration tests: 8/8 passed
- [ ] Performance tests: 4/4 passed
- [ ] Shellcheck: 0 errors
- [ ] Bash syntax: All valid

**Action**: Proceed to manual review

---

### Phase 4 → Phase 5
**Trigger**: Manual review complete + Pre-merge audit passes ⛔ Quality Gate 2

**Checkpoint**:
- [ ] Code review complete (REVIEW.md created)
- [ ] Pre-merge audit: 12/12 checks passed
- [ ] Acceptance checklist: ≥90% (36/40)
- [ ] Version consistency: 6/6 files

**Action**: Prepare release

---

### Phase 5 → Phase 6
**Trigger**: Release preparation complete

**Checkpoint**:
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if needed)
- [ ] Git tag created (v8.2.0)
- [ ] Documentation published

**Action**: Request user acceptance

---

### Phase 6 → Phase 7
**Trigger**: User confirms "没问题" (No issues)

**Action**: Final cleanup and prepare merge

---

### Phase 7 → Merge
**Trigger**: User says "merge"

**Checkpoint**:
- [ ] comprehensive_cleanup.sh executed
- [ ] Version consistency verified (6/6 files)
- [ ] Phase consistency verified (7 Phases)
- [ ] Root documents ≤7

**Action**: Create PR and merge to main

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

**Plan Confidence**: 92% (Based on clear requirements, proven agent strategy, historical success with PR #49)
