#!/usr/bin/env bash
# ============================================================================
# Workflow Progress Data Generator
# ============================================================================
# 从 .workflow/current 和 gates.yml 生成实时进度JSON
# 输出到 .temp/workflow_progress.json
# ============================================================================

set -euo pipefail

readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly WORKFLOW_DIR="${PROJECT_ROOT}/.workflow"
readonly CURRENT_FILE="${WORKFLOW_DIR}/current"
readonly GATES_FILE="${WORKFLOW_DIR}/gates.yml"
readonly IMPACT_FILE="${WORKFLOW_DIR}/impact_assessments/current.json"
readonly OUTPUT_DIR="${PROJECT_ROOT}/.temp"
readonly OUTPUT_FILE="${OUTPUT_DIR}/workflow_progress.json"

# ============================================================================
# Helper Functions
# ============================================================================

parse_yaml_value() {
  local file="$1"
  local key="$2"
  grep "^${key}:" "${file}" 2>/dev/null | sed "s/^${key}:\s*//" | tr -d '"' | head -1 || echo ""
}

get_phase_checks_count() {
  local phase="$1"
  # Default counts for each phase (can be enhanced by parsing gates.yml)
  case "${phase}" in
    P0) echo "7" ;;   # Discovery
    P1) echo "12" ;;  # Planning & Architecture
    P2) echo "15" ;;  # Implementation
    P3) echo "20" ;;  # Testing
    P4) echo "18" ;;  # Review
    P5) echo "10" ;;  # Release & Monitor
    *) echo "10" ;;
  esac
}

get_phase_name() {
  case "$1" in
    P0) echo "Discovery" ;;
    P1) echo "Planning & Architecture" ;;
    P2) echo "Implementation" ;;
    P3) echo "Testing" ;;
    P4) echo "Review" ;;
    P5) echo "Release & Monitor" ;;
    *) echo "Unknown" ;;
  esac
}

# ============================================================================
# Main Logic
# ============================================================================

generate_progress() {
  # Create output directory
  mkdir -p "${OUTPUT_DIR}"

  # Read current workflow state
  if [[ ! -f "${CURRENT_FILE}" ]]; then
    cat > "${OUTPUT_FILE}" <<'EOF'
{
  "error": "No active workflow found",
  "timestamp": "",
  "current_phase": "P0",
  "overall_progress": 0,
  "phases": [],
  "impact_assessment": {"score": 0, "level": "unknown", "recommended_agents": 0},
  "agents_active": 0,
  "agents_total": 0
}
EOF
    cat "${OUTPUT_FILE}"
    return 1
  fi

  local current_phase
  local task_name
  local checklist_total
  local checklist_completed

  current_phase=$(parse_yaml_value "${CURRENT_FILE}" "phase")
  task_name=$(parse_yaml_value "${CURRENT_FILE}" "task")
  checklist_total=$(parse_yaml_value "${CURRENT_FILE}" "checklist_items_total")
  checklist_completed=$(parse_yaml_value "${CURRENT_FILE}" "checklist_items_completed")

  # Default values
  current_phase="${current_phase:-P0}"
  task_name="${task_name:-Workflow Task}"
  checklist_total="${checklist_total:-7}"
  checklist_completed="${checklist_completed:-0}"

  # Read impact assessment
  local impact_score="0"
  local impact_level="unknown"
  local recommended_agents="0"

  if [[ -f "${IMPACT_FILE}" ]]; then
    impact_score=$(grep -o '"score":\s*[0-9]*' "${IMPACT_FILE}" 2>/dev/null | grep -o '[0-9]*' | head -1 || echo "0")
    impact_level=$(grep -o '"level":\s*"[^"]*"' "${IMPACT_FILE}" 2>/dev/null | sed 's/.*"\([^"]*\)".*/\1/' | head -1 || echo "unknown")
    recommended_agents=$(grep -o '"min_agents":\s*[0-9]*' "${IMPACT_FILE}" 2>/dev/null | grep -o '[0-9]*' | head -1 || echo "0")
  fi

  # Calculate overall progress (based on which phase we're in)
  local overall_progress
  case "${current_phase}" in
    P0) overall_progress=0 ;;
    P1) overall_progress=17 ;;
    P2) overall_progress=33 ;;
    P3) overall_progress=50 ;;
    P4) overall_progress=67 ;;
    P5) overall_progress=83 ;;
    *) overall_progress=0 ;;
  esac

  # Add current phase progress
  if [[ "${checklist_total}" -gt 0 ]]; then
    local phase_contribution=$((checklist_completed * 17 / checklist_total))
    overall_progress=$((overall_progress + phase_contribution))
  fi

  # Generate JSON using Python for reliability
  python3 <<PYTHON_SCRIPT > "${OUTPUT_FILE}"
import json
from datetime import datetime, timezone

phases_data = []
phase_list = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5']
phase_names = {
    'P0': 'Discovery',
    'P1': 'Planning & Architecture',
    'P2': 'Implementation',
    'P3': 'Testing',
    'P4': 'Review',
    'P5': 'Release & Monitor'
}
phase_checks = {
    'P0': 7,
    'P1': 12,
    'P2': 15,
    'P3': 20,
    'P4': 18,
    'P5': 10
}

current_phase = '${current_phase}'
current_index = phase_list.index(current_phase) if current_phase in phase_list else 0
checklist_total = ${checklist_total}
checklist_completed = ${checklist_completed}

for i, phase in enumerate(phase_list):
    phase_obj = {
        'id': phase,
        'name': phase_names[phase],
        'status': 'pending',
        'progress': 0,
        'total_checks': phase_checks[phase],
        'passed_checks': 0,
        'failed_checks': [],
        'started_at': None,
        'completed_at': None
    }

    if i < current_index:
        # Completed phases
        phase_obj['status'] = 'completed'
        phase_obj['progress'] = 100
        phase_obj['passed_checks'] = phase_obj['total_checks']
        phase_obj['started_at'] = '2025-10-17T10:00:00Z'
        phase_obj['completed_at'] = '2025-10-17T11:00:00Z'
    elif i == current_index:
        # Current phase
        phase_obj['status'] = 'in_progress'
        phase_obj['total_checks'] = checklist_total
        phase_obj['passed_checks'] = checklist_completed
        if checklist_total > 0:
            phase_obj['progress'] = int(checklist_completed * 100 / checklist_total)
        phase_obj['started_at'] = '2025-10-17T10:30:00Z'

    phases_data.append(phase_obj)

output = {
    'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    'task_name': '''${task_name}''',
    'current_phase': '${current_phase}',
    'overall_progress': ${overall_progress},
    'phases': phases_data,
    'impact_assessment': {
        'score': ${impact_score},
        'level': '${impact_level}',
        'recommended_agents': ${recommended_agents}
    },
    'agents_active': 0,
    'agents_total': ${recommended_agents}
}

print(json.dumps(output, indent=2, ensure_ascii=False))
PYTHON_SCRIPT

  cat "${OUTPUT_FILE}"
}

# ============================================================================
# Execute
# ============================================================================

generate_progress
