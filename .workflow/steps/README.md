# Workflow Steps Tracking System

## Purpose
Track the 11-step workflow progress with detailed status for each step.

## Structure
```
.workflow/steps/
├── current               # Current active step
├── step_01_discussion    # Step 1: Pre-Discussion
├── step_02_branch        # Step 2: Branch Check (Phase -1)
├── step_03_phase0        # Step 3: Phase 0 - Discovery
├── step_04_impact        # Step 4: Impact Radius Assessment
├── step_05_phase1        # Step 5: Phase 1 - Planning & Architecture
├── step_06_phase2        # Step 6: Phase 2 - Implementation
├── step_07_phase3        # Step 7: Phase 3 - Testing
├── step_08_phase4        # Step 8: Phase 4 - Review
├── step_09_phase5        # Step 9: Phase 5 - Release & Monitor
├── step_10_acceptance    # Step 10: Acceptance Report
├── step_11_cleanup       # Step 11: Cleanup & Merge
└── history               # Step transition history
```

## Status Values
- `pending`: Not started
- `in_progress`: Currently working on
- `completed`: Finished successfully
- `blocked`: Blocked by dependency
- `skipped`: Intentionally skipped (with reason)

## Update Mechanism
Each hook is responsible for updating its corresponding step status:
- `requirement_clarification.sh` → `step_01_discussion`
- `branch_helper.sh` → `step_02_branch`
- Phase completion hooks → `step_03` to `step_09`
- Cleanup hooks → `step_11_cleanup`

## Usage
```bash
# Check current step
cat .workflow/steps/current

# Check specific step status
cat .workflow/steps/step_03_phase0

# View history
cat .workflow/steps/history
```

## Lifecycle
1. Step marked as `in_progress` when started
2. Status updated during execution
3. Marked as `completed` when validation passes
4. History updated with timestamp
5. `current` updated to next step
