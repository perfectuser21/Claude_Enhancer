#!/bin/bash
# Claude Enhancer - Per-Phase Guidance System
# Version: 1.0.0
# Purpose: Provide proactive guidance for each Phase of the workflow
# Usage: Can be called standalone or integrated into PrePrompt hook

set -euo pipefail

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PHASE_FILE="$PROJECT_ROOT/.phase/current"

# Get current phase
get_current_phase() {
  if [[ -f "$PHASE_FILE" ]]; then
    cat "$PHASE_FILE" | tr -d '[:space:]'
  else
    echo "None"
  fi
}

# Show guidance for Phase 1
show_phase1_guidance() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  📋 Phase 1: Discovery & Planning                          ║
╚═══════════════════════════════════════════════════════════════╝
🎯 Goal: Understand problem + Create comprehensive plan
✅ Allowed: Read code, Create P1_DISCOVERY/CHECKLIST/PLAN, Impact Assessment
❌ Restricted: NO code implementation, NO testing, NO commits yet
💡 Activities: Branch Check → Requirements → Discovery → Assessment → Planning
📊 Complete: 3 docs + user confirms "start Phase 2" + .phase/phase1_confirmed
🚀 Next: Wait for user confirmation → Phase 2
EOF
}

# Show guidance for Phase 2
show_phase2_guidance() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  🔧 Phase 2: Implementation                                 ║
╚═══════════════════════════════════════════════════════════════╝
🎯 Goal: Implement core functionality
✅ Allowed: Write/edit code, Make commits (feat:/fix:), Apply Impact Assessment (0/3/6 agents)
❌ Restricted: Modify kernel files (needs rfc/*), Write to main branch, Skip Phase 1 docs
💡 Activities: Implement per PLAN.md, Create validation scripts, Configure hooks
🚀 Parallel: High potential (4/4), 3.6x speedup, See docs/PARALLEL_SUBAGENT_STRATEGY.md
📊 Complete: Core features done, Code standards met, Proper commit messages
🚀 Next: Phase 3 (Testing & Validation)
EOF
}

# Show guidance for Phase 3
show_phase3_guidance() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  🧪 Phase 3: Testing - Quality Gate 1 🔒                   ║
╚═══════════════════════════════════════════════════════════════╝
🎯 Goal: Ensure code quality and functionality
✅ Allowed: Run static_checks.sh, Run tests, Fix bugs immediately, Optimize, Refactor
❌ Restricted: Skip failed checks, Lower thresholds, Proceed with failures
💡 Activities: bash scripts/static_checks.sh, Syntax (bash -n), Shellcheck, Complexity (<150L), Performance (<2s), Coverage (≥70%)
🔒 Hard Blocks: Static check failure, Syntax errors, Performance issues → Must fix
📊 Complete: All checks pass, Coverage ≥70%, No errors/warnings, Performance OK
🚀 Next: Phase 4 (Code Review)
EOF
}

# Show guidance for Phase 4
show_phase4_guidance() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  👁️  Phase 4: Review - Quality Gate 2 🔒                   ║
╚═══════════════════════════════════════════════════════════════╝
🎯 Goal: Comprehensive code review + Pre-merge audit
✅ Allowed: Run pre_merge_audit.sh, Manual review, Fix issues, Update docs, Create REVIEW.md
❌ Restricted: Skip critical issues, Proceed with version mismatch, Incomplete docs
💡 Activities: bash scripts/pre_merge_audit.sh (12 checks), Review logic, Verify consistency, Check Phase 1 checklist (≥90%), Version consistency (6 files)
🔒 Hard Blocks: Critical issues, Version mismatch, Checklist <90% → Must fix
📊 Complete: pre_merge_audit.sh passes (12/12), REVIEW.md created, No critical issues, Version OK
🚀 Next: Phase 5 (Release Preparation)
EOF
}

# Show guidance for Phase 5
show_phase5_guidance() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  📦 Phase 5: Release Preparation                            ║
╚═══════════════════════════════════════════════════════════════╝
🎯 Goal: Prepare for release + Update documentation
✅ Allowed: Update VERSION, Update CHANGELOG/README, Configure monitoring
❌ Restricted: Discover bugs (Phase 3-4), Major code changes (Phase 2), Skip version increment
💡 Activities: bash scripts/bump_version.sh, Update 6 files (VERSION, settings.json, manifest.yml, package.json, CHANGELOG.md, SPEC.yaml), Update release docs
🔒 Hard Blocks: Version not incremented, 6 files inconsistent → Must fix
📊 Complete: VERSION incremented, All 6 files consistent, CHANGELOG updated, Docs complete
🚀 Next: Phase 6 (Acceptance Testing)
EOF
}

# Show guidance for Phase 6
show_phase6_guidance() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  ✅ Phase 6: Acceptance Testing                             ║
╚═══════════════════════════════════════════════════════════════╝
🎯 Goal: Verify against Phase 1 checklist + User confirmation
✅ Allowed: Verify ACCEPTANCE_CHECKLIST.md, Run acceptance tests, Create ACCEPTANCE_REPORT.md
❌ Restricted: Proceed without user confirmation, Skip checklist items, Ignore failures
💡 Activities: Check each item in Phase 1 ACCEPTANCE_CHECKLIST.md, Run E2E tests, Generate report, Present to user, Wait for "没问题"
📊 Complete: ACCEPTANCE_REPORT.md created, All critical items verified, User confirms
🚀 Next: Phase 7 (Final Cleanup)
EOF
}

# Show guidance for Phase 7
show_phase7_guidance() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  🧹 Phase 7: Final Cleanup & Merge Preparation              ║
╚═══════════════════════════════════════════════════════════════╝
🎯 Goal: Comprehensive cleanup + Version verification + Ready to merge
✅ Allowed: Run comprehensive_cleanup.sh, Run check_version_consistency.sh, Clean .temp/, Remove old versions, Prepare PR
❌ Restricted: Create PR before Phase 7 complete, Skip cleanup, Leave version inconsistency
💡 Activities: bash scripts/comprehensive_cleanup.sh aggressive, bash scripts/check_version_consistency.sh, Verify git clean, Verify .temp/<10MB, Verify root docs ≤7
🔒 Hard Blocks: Version inconsistency, Unclean git status, Phase ≠ Phase7 → Must fix
📊 Complete: All cleanup done, Version verified (6/6), Git clean, User says "merge"
🚀 Next: Create PR → CI → Merge → Tag → Release
EOF
}

# Show guidance for no phase
show_no_phase_guidance() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  ⚠️  No Active Phase Detected                              ║
╚═══════════════════════════════════════════════════════════════╝
🎯 You should be in a workflow phase!
💡 To start: (1) git checkout -b feature/task, (2) echo "Phase1" > .phase/current, (3) Create P1_DISCOVERY/CHECKLIST/PLAN
📋 Resuming: Check branch (git rev-parse --abbrev-ref HEAD), Check phase (cat .phase/current), Review phase docs
EOF
}

# Main function
main() {
  local current_phase
  current_phase=$(get_current_phase)

  case "$current_phase" in
    "Phase1")
      show_phase1_guidance
      ;;
    "Phase2")
      show_phase2_guidance
      ;;
    "Phase3")
      show_phase3_guidance
      ;;
    "Phase4")
      show_phase4_guidance
      ;;
    "Phase5")
      show_phase5_guidance
      ;;
    "Phase6")
      show_phase6_guidance
      ;;
    "Phase7")
      show_phase7_guidance
      ;;
    "None"|*)
      show_no_phase_guidance
      ;;
  esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi

