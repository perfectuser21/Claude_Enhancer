#!/usr/bin/env bash
# Checklist Generator - Phase 1.3
# Generates ACCEPTANCE_CHECKLIST.md (user), TECHNICAL_CHECKLIST.md (tech), TRACEABILITY.yml

set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

check_deps

# Configuration
USER_REQUEST="${1:-.workflow/user_request.md}"
OUTPUT_DIR=".workflow"
USER_CHECKLIST="$OUTPUT_DIR/ACCEPTANCE_CHECKLIST.md"
TECH_CHECKLIST="$OUTPUT_DIR/TECHNICAL_CHECKLIST.md"
TRACEABILITY="$OUTPUT_DIR/TRACEABILITY.yml"
LOCKFILE="$OUTPUT_DIR/.lock.checklist"

ANALOGY_LIB="${ANALOGY_LIB:-.claude/data/analogy_library.yml}"

# Escape quotes for YAML
escape_yaml() {
    echo "$1" | sed "s/\"/'/g"
}

# Main generation function
generate_checklists() {
    local request_file="$1"

    if [[ ! -f "$request_file" ]]; then
        echo "ERROR: User request file not found: $request_file" >&2
        exit 92
    fi

    # Parse user request (simple keyword extraction)
    local project_name date
    project_name=$(grep -m1 "^# " "$request_file" | sed 's/^# //' || echo "Project")
    date=$(date +%Y-%m-%d)

    # Extract features (lines starting with - or numbers)
    local features
    features=$(grep -E "^[-0-9]" "$request_file" | head -10)

    if [[ -z "$features" ]]; then
        echo "WARN: No features found in request, using placeholder" >&2
        features="Basic functionality"
    fi

    # Generate user checklist
    echo "Generating user checklist..." >&2
    generate_user_checklist "$project_name" "$date" "$features" | out_atomic "$USER_CHECKLIST"

    # Generate technical checklist
    echo "Generating technical checklist..." >&2
    generate_tech_checklist "$project_name" "$date" "$features" | out_atomic "$TECH_CHECKLIST"

    # Generate traceability
    echo "Generating traceability mapping..." >&2
    generate_traceability "$project_name" "$date" "$features" | out_atomic "$TRACEABILITY"

    echo "✓ Checklists generated successfully" >&2
}

generate_user_checklist() {
    local project="$1" date="$2" features="$3"

    cat <<EOF
# Acceptance Checklist - $project

> **项目**：$project
> **创建时间**：$date
> **完成后您将得到**：实现的功能列表

---

## 您将得到的功能

EOF

    local idx=1
    while IFS= read -r feature; do
        # Clean up feature text
        feature=$(echo "$feature" | sed 's/^[-0-9.]\+\s*//')

        local analogy why
        analogy=$(get_analogy "$feature")
        why=$(get_why "$feature")

        local u_id
        u_id=$(gen_id "U" "$idx")

        cat <<EOF

### $idx. $feature <!-- $u_id -->

**您能做什么**：$feature

**就像**：$analogy

**为什么需要**：$why

**怎么验证**：
- ✓ 功能可以正常使用
- ✓ 测试通过

---
EOF
        ((idx++))
    done <<< "$features"

    cat <<EOF


## 完成标准

✅ 上述所有功能都能使用
✅ 测试通过
✅ 文档完整

---

**创建时间**：$date
**验收负责人**：您（项目所有者）
**AI执行者**：Claude Code
EOF
}

generate_tech_checklist() {
    local project="$1" date="$2" features="$3"

    cat <<EOF
# Technical Checklist - $project

> **Project**: $project
> **Created**: $date
> **Tech Stack**: [To be determined]

---

## Core Functionality

EOF

    local idx=1
    local t_idx=1
    while IFS= read -r feature; do
        feature=$(echo "$feature" | sed 's/^[-0-9.]\+\s*//')

        local t_id
        t_id=$(gen_id "T" "$t_idx")

        cat <<EOF

### $idx. $feature
- [ ] Implementation complete <!-- $t_id -->
- [ ] Unit tests written (≥80% coverage)
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Code review approved

EOF
        ((idx++))
        ((t_idx++))
    done <<< "$features"

    cat <<EOF

---

## Quality Gates

### Phase 3 (Testing)
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Performance benchmarks met

### Phase 4 (Review)
- [ ] Code review approved
- [ ] No critical/high vulnerabilities
- [ ] Documentation complete

---

**Created**: $date
**Version**: 1.0.0
EOF
}

generate_traceability() {
    local project="$1" date="$2" features="$3"

    cat <<EOF
version: "1.0"
project:
  name: "$(escape_yaml "$project")"
  created: "$date"

links:
EOF

    local u_idx=1 t_idx=1
    while IFS= read -r feature; do
        local u_id t_id
        u_id=$(gen_id "U" "$u_idx")
        t_id=$(gen_id "T" "$t_idx")

        # Escape the description for YAML
        local desc
        desc=$(escape_yaml "$(echo "$feature" | sed 's/^[-0-9.]\+\s*//')")

        cat <<EOF
  - u: $u_id
    t: [$t_id]
    description: "$desc"
EOF

        ((u_idx++))
        ((t_idx++))
    done <<< "$features"
}

# Execute with file locking
with_lock "$LOCKFILE" generate_checklists "$USER_REQUEST"
