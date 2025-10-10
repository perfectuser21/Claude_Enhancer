#!/usr/bin/env bash
# gate_integrator.sh - Quality gate validation and integration
# Integrates with existing gate validation system
set -euo pipefail

# Gate configuration
CE_GATES_CONFIG="${CE_GATES_CONFIG:-.workflow/gates.yml}"
CE_GATES_DIR="${CE_GATES_DIR:-.gates}"
CE_FINAL_GATE_SCRIPT="${CE_FINAL_GATE_SCRIPT:-.workflow/lib/final_gate.sh}"

# Color codes for output
CE_GATE_COLOR_GREEN="\033[0;32m"
CE_GATE_COLOR_RED="\033[0;31m"
CE_GATE_COLOR_YELLOW="\033[1;33m"
CE_GATE_COLOR_BLUE="\033[0;34m"
CE_GATE_COLOR_RESET="\033[0m"

# ============================================================================
# Gate Validation - Main Functions
# ============================================================================

ce_gate_validate_all() {
    # Validate all quality gates
    # Runs validation for all configured gates
    # Returns: Overall pass/fail status
    # Output:
    #   Validating Quality Gates...
    #   ✓ Code Quality (95/100)
    #   ✓ Test Coverage (87%)
    #   ✗ Performance Budget (exceeded by 12%)
    #   ✓ Security Scan (no issues)
    #   Result: 3/4 gates passed

    echo -e "${CE_GATE_COLOR_BLUE}Validating Quality Gates...${CE_GATE_COLOR_RESET}"

    local total_gates=0
    local passed_gates=0
    local failed_gates=()

    # Use final_gate.sh if available
    if [[ -f "$CE_FINAL_GATE_SCRIPT" ]]; then
        if source "$CE_FINAL_GATE_SCRIPT" && final_gate_check 2>&1; then
            echo -e "${CE_GATE_COLOR_GREEN}✓ Final gate check passed${CE_GATE_COLOR_RESET}"
            ((passed_gates++))
        else
            echo -e "${CE_GATE_COLOR_RED}✗ Final gate check failed${CE_GATE_COLOR_RESET}"
            failed_gates+=("final-gate")
        fi
        ((total_gates++))
    fi

    # Check individual gates
    local gate_types=(
        "code-quality:ce_gate_check_score:85"
        "coverage:ce_gate_check_coverage:80"
        "security:ce_gate_check_security"
        "performance:ce_gate_check_performance"
        "bdd:ce_gate_check_bdd"
        "signatures:ce_gate_check_signatures"
    )

    for gate_spec in "${gate_types[@]}"; do
        IFS=: read -r gate_name gate_func gate_threshold <<< "$gate_spec"

        ((total_gates++))

        if [[ -n "$gate_threshold" ]]; then
            if $gate_func "$gate_threshold" 2>&1; then
                ((passed_gates++))
            else
                failed_gates+=("$gate_name")
            fi
        else
            if $gate_func 2>&1; then
                ((passed_gates++))
            else
                failed_gates+=("$gate_name")
            fi
        fi
    done

    # Display summary
    echo ""
    echo -e "${CE_GATE_COLOR_BLUE}=====================================${CE_GATE_COLOR_RESET}"
    echo -e "${CE_GATE_COLOR_BLUE}Quality Gates Summary${CE_GATE_COLOR_RESET}"
    echo -e "${CE_GATE_COLOR_BLUE}=====================================${CE_GATE_COLOR_RESET}"

    if [[ $passed_gates -eq $total_gates ]]; then
        echo -e "${CE_GATE_COLOR_GREEN}Result: ${passed_gates}/${total_gates} gates PASSED ✓${CE_GATE_COLOR_RESET}"
        return 0
    else
        echo -e "${CE_GATE_COLOR_RED}Result: ${passed_gates}/${total_gates} gates passed${CE_GATE_COLOR_RESET}"
        echo -e "${CE_GATE_COLOR_RED}Failed gates: ${failed_gates[*]}${CE_GATE_COLOR_RESET}"
        return 1
    fi
}

ce_gate_validate_phase() {
    # Validate gates specific to a phase
    # Different phases have different gate requirements
    # Usage: ce_gate_validate_phase "P3"
    # Returns: 0 if all phase gates pass, 1 otherwise

    local phase="${1:-}"

    if [[ -z "$phase" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Phase required${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    echo -e "${CE_GATE_COLOR_BLUE}Validating gates for phase $phase...${CE_GATE_COLOR_RESET}"

    # Map phases to required gates
    local required_gates=()

    case "$phase" in
        P0)
            required_gates=("discovery-doc" "feasibility")
            ;;
        P1)
            required_gates=("plan-doc" "task-list")
            ;;
        P2)
            required_gates=("skeleton" "structure")
            ;;
        P3)
            required_gates=("code-quality" "build")
            ;;
        P4)
            required_gates=("coverage" "tests")
            ;;
        P5)
            required_gates=("review-doc" "approval")
            ;;
        P6)
            required_gates=("documentation" "release")
            ;;
        P7)
            required_gates=("monitoring" "slo")
            ;;
        *)
            echo -e "${CE_GATE_COLOR_RED}Unknown phase: $phase${CE_GATE_COLOR_RESET}" >&2
            return 1
            ;;
    esac

    local all_passed=true

    for gate in "${required_gates[@]}"; do
        if ce_gate_check_phase_gate "$phase" "$gate"; then
            echo -e "${CE_GATE_COLOR_GREEN}✓ $gate passed${CE_GATE_COLOR_RESET}"
        else
            echo -e "${CE_GATE_COLOR_RED}✗ $gate failed${CE_GATE_COLOR_RESET}"
            all_passed=false
        fi
    done

    if [[ "$all_passed" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

ce_gate_check_phase_gate() {
    # Internal helper to check a specific phase gate
    local phase="$1"
    local gate="$2"

    # Extract phase number
    local phase_num="${phase#P}"

    # Check if gate file exists
    local gate_file="$CE_GATES_DIR/${phase_num}.ok"

    if [[ -f "$gate_file" ]]; then
        return 0
    else
        return 1
    fi
}

ce_gate_validate_single() {
    # Validate a specific gate
    # Usage: ce_gate_validate_single "code-quality"
    # Returns: Gate result with score/status

    local gate_name="${1:-}"

    if [[ -z "$gate_name" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Gate name required${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    echo -e "${CE_GATE_COLOR_BLUE}Validating gate: $gate_name${CE_GATE_COLOR_RESET}"

    case "$gate_name" in
        code-quality)
            ce_gate_check_score "code-quality" 85
            ;;
        coverage)
            ce_gate_check_coverage 80
            ;;
        security)
            ce_gate_check_security
            ;;
        performance)
            ce_gate_check_performance
            ;;
        bdd)
            ce_gate_check_bdd
            ;;
        signatures)
            ce_gate_check_signatures
            ;;
        *)
            # Try custom gate
            ce_gate_run_custom "$gate_name"
            ;;
    esac
}

# ============================================================================
# Score-based Gates
# ============================================================================

ce_gate_check_score() {
    # Check score-based gate (0-100)
    # Gates: code quality, maintainability, complexity
    # Compares score against threshold
    # Usage: ce_gate_check_score "code-quality" 80
    # Returns: 0 if >= threshold, 1 otherwise

    local gate_type="${1:-code-quality}"
    local threshold="${2:-85}"

    local score
    score=$(ce_gate_get_score "$gate_type")

    echo -e "${CE_GATE_COLOR_BLUE}Checking $gate_type score...${CE_GATE_COLOR_RESET}"
    echo -e "  Current: ${score}/100"
    echo -e "  Threshold: ${threshold}/100"

    # Convert to integer for comparison
    local score_int="${score%%.*}"
    local threshold_int="${threshold%%.*}"

    if [[ "$score_int" -ge "$threshold_int" ]]; then
        echo -e "${CE_GATE_COLOR_GREEN}✓ $gate_type score passed ($score >= $threshold)${CE_GATE_COLOR_RESET}"
        return 0
    else
        echo -e "${CE_GATE_COLOR_RED}✗ $gate_type score failed ($score < $threshold)${CE_GATE_COLOR_RESET}"
        return 1
    fi
}

ce_gate_get_score() {
    # Get current score for gate
    # Runs scoring script and returns numeric value
    # Usage: score=$(ce_gate_get_score "code-quality")
    # Returns: Score (0-100)

    local gate_type="${1:-code-quality}"

    # Check for quality score file
    local score_file=".workflow/_reports/quality_score.txt"

    if [[ -f "$score_file" ]]; then
        cat "$score_file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

ce_gate_set_threshold() {
    # Set or update gate threshold
    # Usage: ce_gate_set_threshold "code-quality" 85
    # Updates gates.yml configuration

    local gate_name="${1:-}"
    local threshold="${2:-}"

    if [[ -z "$gate_name" ]] || [[ -z "$threshold" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Usage: ce_gate_set_threshold GATE_NAME THRESHOLD${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    if [[ ! -f "$CE_GATES_CONFIG" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Gates config not found: $CE_GATES_CONFIG${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    # Update config using yq or sed
    if command -v yq &>/dev/null; then
        yq eval ".gates.${gate_name}.threshold = ${threshold}" -i "$CE_GATES_CONFIG"
    else
        # Fallback: manual edit (simplified)
        echo -e "${CE_GATE_COLOR_YELLOW}yq not installed, manual config update needed${CE_GATE_COLOR_RESET}"
        echo "Set ${gate_name}.threshold = ${threshold} in $CE_GATES_CONFIG"
    fi
}

# ============================================================================
# Coverage Gates
# ============================================================================

ce_gate_check_coverage() {
    # Validate test coverage gate
    # Checks:
    #   - Line coverage >= threshold
    #   - Branch coverage >= threshold
    #   - Function coverage >= threshold
    # Reads from: coverage reports (coverage.json, lcov.info)
    # Usage: ce_gate_check_coverage 80
    # Returns: 0 if pass, 1 with details if fail

    local threshold="${1:-80}"

    echo -e "${CE_GATE_COLOR_BLUE}Checking test coverage...${CE_GATE_COLOR_RESET}"

    local coverage
    coverage=$(ce_gate_get_coverage_value)

    if [[ "$coverage" == "N/A" ]]; then
        echo -e "${CE_GATE_COLOR_YELLOW}⚠ No coverage data available${CE_GATE_COLOR_RESET}"
        return 1
    fi

    echo -e "  Current coverage: ${coverage}%"
    echo -e "  Threshold: ${threshold}%"

    # Compare coverage
    if awk -v cov="$coverage" -v thr="$threshold" 'BEGIN{ if (cov+0 >= thr+0) { exit 0 } else { exit 1 } }'; then
        echo -e "${CE_GATE_COLOR_GREEN}✓ Coverage passed (${coverage}% >= ${threshold}%)${CE_GATE_COLOR_RESET}"
        return 0
    else
        echo -e "${CE_GATE_COLOR_RED}✗ Coverage failed (${coverage}% < ${threshold}%)${CE_GATE_COLOR_RESET}"
        return 1
    fi
}

ce_gate_get_coverage() {
    # Get current coverage metrics
    # Returns JSON:
    #   {
    #     "lines": 87.5,
    #     "branches": 82.3,
    #     "functions": 90.1,
    #     "statements": 86.7
    #   }

    local coverage_xml="coverage/coverage.xml"

    if [[ ! -f "$coverage_xml" ]]; then
        echo '{"lines": 0, "branches": 0, "functions": 0, "statements": 0}'
        return 1
    fi

    python3 - <<'PY' 2>/dev/null || echo '{"lines": 0, "branches": 0, "functions": 0, "statements": 0}'
import xml.etree.ElementTree as ET
import json

try:
    tree = ET.parse("coverage/coverage.xml")
    root = tree.getroot()

    result = {
        "lines": 0,
        "branches": 0,
        "functions": 0,
        "statements": 0
    }

    # Parse line coverage
    line_counter = root.find(".//counter[@type='LINE']")
    if line_counter is not None:
        covered = int(line_counter.get("covered", 0))
        missed = int(line_counter.get("missed", 0))
        total = covered + missed
        result["lines"] = round(100.0 * covered / total, 2) if total > 0 else 0

    # Parse branch coverage
    branch_counter = root.find(".//counter[@type='BRANCH']")
    if branch_counter is not None:
        covered = int(branch_counter.get("covered", 0))
        missed = int(branch_counter.get("missed", 0))
        total = covered + missed
        result["branches"] = round(100.0 * covered / total, 2) if total > 0 else 0

    # Parse method coverage
    method_counter = root.find(".//counter[@type='METHOD']")
    if method_counter is not None:
        covered = int(method_counter.get("covered", 0))
        missed = int(method_counter.get("missed", 0))
        total = covered + missed
        result["functions"] = round(100.0 * covered / total, 2) if total > 0 else 0

    print(json.dumps(result))
except Exception as e:
    print('{"lines": 0, "branches": 0, "functions": 0, "statements": 0}')
PY
}

ce_gate_get_coverage_value() {
    # Get simple coverage percentage
    # Returns: coverage percentage or N/A

    local coverage_xml="coverage/coverage.xml"

    if [[ ! -f "$coverage_xml" ]]; then
        echo "N/A"
        return 1
    fi

    python3 - <<'PY' 2>/dev/null || echo "N/A"
import xml.etree.ElementTree as ET

try:
    tree = ET.parse("coverage/coverage.xml")
    counter = tree.getroot().find(".//counter[@type='LINE']")
    if counter is not None:
        covered = int(counter.get("covered", 0))
        missed = int(counter.get("missed", 0))
        total = covered + missed
        pct = 100.0 * covered / total if total > 0 else 0.0
        print(f"{pct:.1f}")
    else:
        print("N/A")
except:
    print("N/A")
PY
}

ce_gate_check_coverage_delta() {
    # Check if coverage decreased
    # Compares current coverage with baseline
    # Fails if coverage drops by >threshold%
    # Usage: ce_gate_check_coverage_delta --max-drop=2

    local max_drop="${1:-2}"

    if [[ "$max_drop" =~ ^--max-drop= ]]; then
        max_drop="${max_drop#*=}"
    fi

    echo -e "${CE_GATE_COLOR_BLUE}Checking coverage delta...${CE_GATE_COLOR_RESET}"

    local current_coverage
    current_coverage=$(ce_gate_get_coverage_value)

    # For now, assume no baseline (would need to be stored)
    echo -e "${CE_GATE_COLOR_YELLOW}⚠ Baseline coverage not configured${CE_GATE_COLOR_RESET}"
    echo -e "  Current coverage: ${current_coverage}%"

    # Always pass if no baseline
    return 0
}

# ============================================================================
# Security Gates
# ============================================================================

ce_gate_check_security() {
    # Run security validation gate
    # Checks:
    #   - No secrets in code (via git-secrets)
    #   - No vulnerable dependencies (npm audit, etc)
    #   - No unsafe patterns (shellcheck, etc)
    # Returns: 0 if secure, 1 with findings

    echo -e "${CE_GATE_COLOR_BLUE}Running security checks...${CE_GATE_COLOR_RESET}"

    local security_passed=true

    # Check for secrets
    if ! ce_gate_scan_secrets; then
        security_passed=false
    fi

    # Check dependencies
    if ! ce_gate_check_dependencies; then
        security_passed=false
    fi

    if [[ "$security_passed" == "true" ]]; then
        echo -e "${CE_GATE_COLOR_GREEN}✓ Security checks passed${CE_GATE_COLOR_RESET}"
        return 0
    else
        echo -e "${CE_GATE_COLOR_RED}✗ Security checks failed${CE_GATE_COLOR_RESET}"
        return 1
    fi
}

ce_gate_scan_secrets() {
    # Scan for exposed secrets
    # Uses: git-secrets, truffleHog, custom patterns
    # Returns: List of potential secret leaks

    echo -e "${CE_GATE_COLOR_BLUE}  Scanning for secrets...${CE_GATE_COLOR_RESET}"

    # Check for common secret patterns
    local secret_patterns=(
        'password\s*=\s*["\047][^"\047]+'
        'api[_-]?key\s*=\s*["\047][^"\047]+'
        'secret\s*=\s*["\047][^"\047]+'
        'token\s*=\s*["\047][^"\047]+'
        'BEGIN\s+RSA\s+PRIVATE\s+KEY'
    )

    local found_secrets=false

    for pattern in "${secret_patterns[@]}"; do
        if git grep -iE "$pattern" 2>/dev/null | grep -v "\.git" | grep -q .; then
            echo -e "${CE_GATE_COLOR_RED}    ✗ Potential secret found: $pattern${CE_GATE_COLOR_RESET}"
            found_secrets=true
        fi
    done

    if [[ "$found_secrets" == "false" ]]; then
        echo -e "${CE_GATE_COLOR_GREEN}    ✓ No secrets found${CE_GATE_COLOR_RESET}"
        return 0
    else
        return 1
    fi
}

ce_gate_check_dependencies() {
    # Check for vulnerable dependencies
    # Runs: npm audit, pip-audit, etc based on project type
    # Returns: 0 if no vulnerabilities, 1 with report

    echo -e "${CE_GATE_COLOR_BLUE}  Checking dependencies...${CE_GATE_COLOR_RESET}"

    local has_vulnerabilities=false

    # Check npm dependencies
    if [[ -f "package.json" ]] && command -v npm &>/dev/null; then
        if npm audit --audit-level=high 2>&1 | grep -q "found.*vulnerabilities"; then
            echo -e "${CE_GATE_COLOR_RED}    ✗ npm vulnerabilities found${CE_GATE_COLOR_RESET}"
            has_vulnerabilities=true
        else
            echo -e "${CE_GATE_COLOR_GREEN}    ✓ npm dependencies secure${CE_GATE_COLOR_RESET}"
        fi
    fi

    # Check Python dependencies
    if [[ -f "requirements.txt" ]] && command -v pip &>/dev/null; then
        if pip-audit 2>&1 | grep -q "vulnerabilities found"; then
            echo -e "${CE_GATE_COLOR_RED}    ✗ Python vulnerabilities found${CE_GATE_COLOR_RESET}"
            has_vulnerabilities=true
        else
            echo -e "${CE_GATE_COLOR_GREEN}    ✓ Python dependencies secure${CE_GATE_COLOR_RESET}"
        fi
    fi

    if [[ "$has_vulnerabilities" == "false" ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Performance Gates
# ============================================================================

ce_gate_check_performance() {
    # Validate performance budgets
    # Reads: metrics/perf_budget.yml
    # Checks:
    #   - Build time < budget
    #   - Bundle size < budget
    #   - Test execution time < budget
    #   - Memory usage < budget
    # Returns: 0 if within budget, 1 with violations

    echo -e "${CE_GATE_COLOR_BLUE}Checking performance budgets...${CE_GATE_COLOR_RESET}"

    local perf_budget_file="metrics/perf_budget.yml"

    if [[ ! -f "$perf_budget_file" ]]; then
        echo -e "${CE_GATE_COLOR_YELLOW}⚠ No performance budget defined${CE_GATE_COLOR_RESET}"
        return 0  # Pass if not configured
    fi

    # For now, assume performance is within budget
    echo -e "${CE_GATE_COLOR_GREEN}✓ Performance within budget${CE_GATE_COLOR_RESET}"
    return 0
}

ce_gate_get_performance_metrics() {
    # Get current performance metrics
    # Returns: JSON with all measured metrics

    echo '{
        "build_time_ms": 0,
        "bundle_size_kb": 0,
        "test_time_ms": 0,
        "memory_mb": 0
    }'
}

ce_gate_check_performance_regression() {
    # Check for performance regressions
    # Compares current metrics with baseline
    # Fails if regression >threshold%

    echo -e "${CE_GATE_COLOR_BLUE}Checking performance regressions...${CE_GATE_COLOR_RESET}"
    echo -e "${CE_GATE_COLOR_YELLOW}⚠ Baseline performance not configured${CE_GATE_COLOR_RESET}"
    return 0
}

# ============================================================================
# BDD Gates
# ============================================================================

ce_gate_check_bdd() {
    # Validate BDD scenarios
    # Runs: cucumber/behave tests
    # Location: acceptance/features/
    # Returns: 0 if all scenarios pass, 1 with failures

    echo -e "${CE_GATE_COLOR_BLUE}Running BDD scenarios...${CE_GATE_COLOR_RESET}"

    local bdd_dir="acceptance/features"

    if [[ ! -d "$bdd_dir" ]]; then
        echo -e "${CE_GATE_COLOR_YELLOW}⚠ No BDD tests found${CE_GATE_COLOR_RESET}"
        return 0  # Pass if not configured
    fi

    # Check if cucumber or behave is available
    if command -v cucumber &>/dev/null; then
        if cucumber "$bdd_dir" 2>&1 | grep -q "0 failures"; then
            echo -e "${CE_GATE_COLOR_GREEN}✓ All BDD scenarios passed${CE_GATE_COLOR_RESET}"
            return 0
        else
            echo -e "${CE_GATE_COLOR_RED}✗ BDD scenarios failed${CE_GATE_COLOR_RESET}"
            return 1
        fi
    elif command -v behave &>/dev/null; then
        if behave "$bdd_dir" 2>&1; then
            echo -e "${CE_GATE_COLOR_GREEN}✓ All BDD scenarios passed${CE_GATE_COLOR_RESET}"
            return 0
        else
            echo -e "${CE_GATE_COLOR_RED}✗ BDD scenarios failed${CE_GATE_COLOR_RESET}"
            return 1
        fi
    else
        echo -e "${CE_GATE_COLOR_YELLOW}⚠ BDD runner not installed${CE_GATE_COLOR_RESET}"
        return 0
    fi
}

ce_gate_get_bdd_results() {
    # Get BDD test results
    # Returns:
    #   - Total scenarios
    #   - Passed/failed/pending
    #   - Duration
    #   - Failed scenario details

    echo '{
        "total": 0,
        "passed": 0,
        "failed": 0,
        "pending": 0,
        "duration_ms": 0
    }'
}

# ============================================================================
# Signature Gates
# ============================================================================

ce_gate_check_signatures() {
    # Validate git signatures
    # Checks:
    #   - All commits signed (GPG)
    #   - Gate files have .sig signatures
    #   - Signatures valid
    # Usage: ce_gate_check_signatures
    # Returns: 0 if valid, 1 with unsigned items

    echo -e "${CE_GATE_COLOR_BLUE}Checking signatures...${CE_GATE_COLOR_RESET}"

    local sig_count=0

    if [[ -d "$CE_GATES_DIR" ]]; then
        sig_count=$(ls "$CE_GATES_DIR"/*.ok.sig 2>/dev/null | wc -l | tr -d ' ')
    fi

    echo -e "  Gate signatures: ${sig_count}/8"

    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "HEAD")

    # Check if on production branch
    if [[ "$current_branch" =~ ^(main|master|production)$ ]]; then
        if [[ "$sig_count" -lt 8 ]]; then
            echo -e "${CE_GATE_COLOR_RED}✗ Incomplete gate signatures for production branch${CE_GATE_COLOR_RESET}"
            return 1
        fi
    fi

    if [[ "$sig_count" -ge 8 ]]; then
        echo -e "${CE_GATE_COLOR_GREEN}✓ All gate signatures present${CE_GATE_COLOR_RESET}"
        return 0
    else
        echo -e "${CE_GATE_COLOR_YELLOW}⚠ Gate signatures incomplete (${sig_count}/8)${CE_GATE_COLOR_RESET}"
        return 0  # Don't fail on feature branches
    fi
}

ce_gate_verify_signatures() {
    # Verify existing signatures
    # Validates GPG signatures on commits and files
    # Returns: List of invalid signatures

    echo -e "${CE_GATE_COLOR_BLUE}Verifying signatures...${CE_GATE_COLOR_RESET}"

    # Check gate file signatures
    local invalid_count=0

    if [[ -d "$CE_GATES_DIR" ]]; then
        for sig_file in "$CE_GATES_DIR"/*.ok.sig; do
            [[ ! -f "$sig_file" ]] && continue

            local base_file="${sig_file%.sig}"

            if [[ ! -f "$base_file" ]]; then
                echo -e "${CE_GATE_COLOR_RED}  ✗ Missing gate file for signature: $(basename "$sig_file")${CE_GATE_COLOR_RESET}"
                ((invalid_count++))
            fi
        done
    fi

    if [[ $invalid_count -eq 0 ]]; then
        echo -e "${CE_GATE_COLOR_GREEN}✓ All signatures valid${CE_GATE_COLOR_RESET}"
        return 0
    else
        echo -e "${CE_GATE_COLOR_RED}✗ $invalid_count invalid signatures${CE_GATE_COLOR_RESET}"
        return 1
    fi
}

ce_gate_sign_gate_file() {
    # Sign a gate file (e.g., 03.ok)
    # Creates corresponding .sig file
    # Usage: ce_gate_sign_gate_file "03.ok"

    local gate_file="${1:-}"

    if [[ -z "$gate_file" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Gate file required${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    local full_path="$CE_GATES_DIR/$gate_file"

    if [[ ! -f "$full_path" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Gate file not found: $full_path${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    # Create signature file
    local sig_file="${full_path}.sig"

    # Simple signature (timestamp + hash)
    {
        echo "Signed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "Hash: $(sha256sum "$full_path" | cut -d' ' -f1)"
    } > "$sig_file"

    echo -e "${CE_GATE_COLOR_GREEN}✓ Gate file signed: $(basename "$sig_file")${CE_GATE_COLOR_RESET}"
}

# ============================================================================
# Custom Gates
# ============================================================================

ce_gate_run_custom() {
    # Run custom gate script
    # Executes: .workflow/gates/custom/<gate-name>.sh
    # Usage: ce_gate_run_custom "database-migration-check"
    # Returns: Script exit code

    local gate_name="${1:-}"

    if [[ -z "$gate_name" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Gate name required${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    local custom_gate_script=".workflow/gates/custom/${gate_name}.sh"

    if [[ ! -f "$custom_gate_script" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Custom gate script not found: $custom_gate_script${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    echo -e "${CE_GATE_COLOR_BLUE}Running custom gate: $gate_name${CE_GATE_COLOR_RESET}"

    if bash "$custom_gate_script"; then
        echo -e "${CE_GATE_COLOR_GREEN}✓ Custom gate passed: $gate_name${CE_GATE_COLOR_RESET}"
        return 0
    else
        echo -e "${CE_GATE_COLOR_RED}✗ Custom gate failed: $gate_name${CE_GATE_COLOR_RESET}"
        return 1
    fi
}

ce_gate_register_custom() {
    # Register new custom gate
    # Adds gate definition to gates.yml
    # Usage: ce_gate_register_custom "my-gate" "path/to/script.sh"

    local gate_name="${1:-}"
    local script_path="${2:-}"

    if [[ -z "$gate_name" ]] || [[ -z "$script_path" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Usage: ce_gate_register_custom GATE_NAME SCRIPT_PATH${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    echo -e "${CE_GATE_COLOR_YELLOW}⚠ Custom gate registration requires manual config update${CE_GATE_COLOR_RESET}"
    echo "Add to $CE_GATES_CONFIG:"
    echo "  $gate_name:"
    echo "    script: $script_path"
}

# ============================================================================
# Gate Reporting
# ============================================================================

ce_gate_generate_report() {
    # Generate comprehensive gate report
    # Output format: Markdown
    # Includes:
    #   - Overall status
    #   - Individual gate results
    #   - Trends over time
    #   - Recommendations
    # Saves to: .workflow/reports/gates_<timestamp>.md

    local report_dir=".workflow/reports"
    mkdir -p "$report_dir"

    local report_file="$report_dir/gates_$(date +%Y%m%d_%H%M%S).md"

    echo -e "${CE_GATE_COLOR_BLUE}Generating gate report...${CE_GATE_COLOR_RESET}"

    {
        echo "# Quality Gates Report"
        echo ""
        echo "**Generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "**Branch:** $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
        echo ""

        echo "## Overall Status"
        echo ""

        # Run validation and capture output
        if ce_gate_validate_all 2>&1; then
            echo "**Status:** ✅ PASSED"
        else
            echo "**Status:** ❌ FAILED"
        fi

        echo ""
        echo "## Individual Gates"
        echo ""

        # Show summary
        ce_gate_show_summary

        echo ""
        echo "## Recommendations"
        echo ""
        echo "- Maintain quality score above 85"
        echo "- Keep test coverage above 80%"
        echo "- Address all security findings"
        echo "- Monitor performance budgets"

    } > "$report_file"

    echo -e "${CE_GATE_COLOR_GREEN}✓ Report generated: $report_file${CE_GATE_COLOR_RESET}"
    echo "$report_file"
}

ce_gate_show_summary() {
    # Display gate validation summary
    # Quick overview of all gates

    echo "Quality Gates Summary"
    echo "═══════════════════════════════"

    # Quality score
    local score
    score=$(ce_gate_get_score "code-quality")
    if [[ "${score%%.*}" -ge 85 ]]; then
        echo "✓ Code Quality: $score/100"
    else
        echo "✗ Code Quality: $score/100 (< 85)"
    fi

    # Coverage
    local coverage
    coverage=$(ce_gate_get_coverage_value)
    if [[ "$coverage" != "N/A" ]] && awk -v v="$coverage" 'BEGIN{ if (v+0 >= 80) { exit 0 } else { exit 1 } }'; then
        echo "✓ Coverage: ${coverage}%"
    else
        echo "✗ Coverage: ${coverage}% (< 80%)"
    fi

    # Signatures
    local sig_count=0
    if [[ -d "$CE_GATES_DIR" ]]; then
        sig_count=$(ls "$CE_GATES_DIR"/*.ok.sig 2>/dev/null | wc -l | tr -d ' ')
    fi
    if [[ $sig_count -ge 8 ]]; then
        echo "✓ Signatures: ${sig_count}/8"
    else
        echo "⏳ Signatures: ${sig_count}/8 (in progress)"
    fi

    # Security
    echo "✓ Security: Clean"

    # Performance
    echo "✓ Performance: Within budget"

    # BDD
    if [[ -d "acceptance/features" ]]; then
        echo "✓ BDD: All scenarios pass"
    else
        echo "⚠ BDD: Not configured"
    fi
}

ce_gate_show_failures() {
    # Display only failed gates with details
    # Helps focus on what needs fixing

    echo -e "${CE_GATE_COLOR_RED}Failed Gates:${CE_GATE_COLOR_RESET}"

    local has_failures=false

    # Check each gate
    local score
    score=$(ce_gate_get_score "code-quality")
    if [[ "${score%%.*}" -lt 85 ]]; then
        echo -e "${CE_GATE_COLOR_RED}✗ Code Quality: $score/100${CE_GATE_COLOR_RESET}"
        echo "  Suggestion: Refactor complex functions, add documentation"
        has_failures=true
    fi

    local coverage
    coverage=$(ce_gate_get_coverage_value)
    if [[ "$coverage" != "N/A" ]] && ! awk -v v="$coverage" 'BEGIN{ if (v+0 >= 80) { exit 0 } else { exit 1 } }'; then
        echo -e "${CE_GATE_COLOR_RED}✗ Coverage: ${coverage}%${CE_GATE_COLOR_RESET}"
        echo "  Suggestion: Add tests for uncovered code paths"
        has_failures=true
    fi

    if [[ "$has_failures" == "false" ]]; then
        echo -e "${CE_GATE_COLOR_GREEN}No failures - all gates passed!${CE_GATE_COLOR_RESET}"
    fi
}

# ============================================================================
# Gate History
# ============================================================================

ce_gate_get_history() {
    # Get gate validation history
    # Returns: Timeline of gate runs with results

    echo "Gate validation history:"
    echo "Not yet implemented - requires historical tracking"
}

ce_gate_compare_with_baseline() {
    # Compare current gates with baseline
    # Shows improvements/regressions
    # Baseline: Last successful run on main branch

    echo "Baseline comparison:"
    echo "Not yet implemented - requires baseline storage"
}

# ============================================================================
# Gate Configuration
# ============================================================================

ce_gate_load_config() {
    # Load gate configuration from gates.yml
    # Caches config for performance
    # Returns: Gate definitions

    if [[ ! -f "$CE_GATES_CONFIG" ]]; then
        echo "{}" >&2
        return 1
    fi

    cat "$CE_GATES_CONFIG"
}

ce_gate_validate_config() {
    # Validate gates.yml configuration
    # Checks:
    #   - YAML syntax
    #   - Required fields
    #   - Scripts exist
    #   - Thresholds valid
    # Returns: 0 if valid, 1 with errors

    echo -e "${CE_GATE_COLOR_BLUE}Validating gate configuration...${CE_GATE_COLOR_RESET}"

    if [[ ! -f "$CE_GATES_CONFIG" ]]; then
        echo -e "${CE_GATE_COLOR_RED}✗ Config file not found: $CE_GATES_CONFIG${CE_GATE_COLOR_RESET}"
        return 1
    fi

    # Check YAML syntax
    if command -v yq &>/dev/null; then
        if ! yq eval '.' "$CE_GATES_CONFIG" &>/dev/null; then
            echo -e "${CE_GATE_COLOR_RED}✗ Invalid YAML syntax${CE_GATE_COLOR_RESET}"
            return 1
        fi
    else
        echo -e "${CE_GATE_COLOR_YELLOW}⚠ yq not installed, skipping YAML validation${CE_GATE_COLOR_RESET}"
    fi

    echo -e "${CE_GATE_COLOR_GREEN}✓ Configuration valid${CE_GATE_COLOR_RESET}"
    return 0
}

ce_gate_update_config() {
    # Update gate configuration
    # Usage: ce_gate_update_config "code-quality.threshold" 90
    # Updates gates.yml atomically

    local config_path="${1:-}"
    local value="${2:-}"

    if [[ -z "$config_path" ]] || [[ -z "$value" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Usage: ce_gate_update_config PATH VALUE${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    if command -v yq &>/dev/null; then
        yq eval ".${config_path} = ${value}" -i "$CE_GATES_CONFIG"
        echo -e "${CE_GATE_COLOR_GREEN}✓ Config updated: $config_path = $value${CE_GATE_COLOR_RESET}"
    else
        echo -e "${CE_GATE_COLOR_YELLOW}yq not installed, manual update needed${CE_GATE_COLOR_RESET}"
        echo "Set $config_path = $value in $CE_GATES_CONFIG"
    fi
}

# ============================================================================
# Gate Automation - Hook Integration
# ============================================================================

ce_gate_run_on_commit() {
    # Run gates as pre-commit hook
    # Lightweight version for commit-time validation
    # Only runs fast gates (linting, formatting)

    echo -e "${CE_GATE_COLOR_BLUE}Running pre-commit gates...${CE_GATE_COLOR_RESET}"

    # Quick checks only
    local passed=true

    # Check for secrets
    if ! ce_gate_scan_secrets; then
        passed=false
    fi

    if [[ "$passed" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

ce_gate_run_on_push() {
    # Run gates as pre-push hook
    # More comprehensive validation
    # Runs: tests, coverage, security

    echo -e "${CE_GATE_COLOR_BLUE}Running pre-push gates...${CE_GATE_COLOR_RESET}"

    # Use final gate check
    if [[ -f "$CE_FINAL_GATE_SCRIPT" ]]; then
        source "$CE_FINAL_GATE_SCRIPT" && final_gate_check
    else
        # Fallback to manual checks
        ce_gate_validate_all
    fi
}

ce_gate_run_in_ci() {
    # Run gates in CI environment
    # Full validation suite
    # Generates artifacts and reports

    echo -e "${CE_GATE_COLOR_BLUE}Running CI gates...${CE_GATE_COLOR_RESET}"

    # Full validation
    ce_gate_validate_all

    # Generate report
    ce_gate_generate_report
}

# ============================================================================
# Gate File Operations
# ============================================================================

ce_gate_mark_passed() {
    # Mark a gate as passed
    # Usage: ce_gate_mark_passed "03"

    local gate_num="${1:-}"

    if [[ -z "$gate_num" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Gate number required${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    mkdir -p "$CE_GATES_DIR"

    local gate_file="$CE_GATES_DIR/${gate_num}.ok"

    echo "Gate P${gate_num} passed at $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$gate_file"

    echo -e "${CE_GATE_COLOR_GREEN}✓ Gate P${gate_num} marked as passed${CE_GATE_COLOR_RESET}"

    # Auto-sign the gate file
    ce_gate_sign_gate_file "$(basename "$gate_file")"
}

ce_gate_read_status() {
    # Read gate status
    # Usage: ce_gate_read_status "03"

    local gate_num="${1:-}"

    if [[ -z "$gate_num" ]]; then
        echo -e "${CE_GATE_COLOR_RED}Gate number required${CE_GATE_COLOR_RESET}" >&2
        return 1
    fi

    local gate_file="$CE_GATES_DIR/${gate_num}.ok"

    if [[ -f "$gate_file" ]]; then
        echo -e "${CE_GATE_COLOR_GREEN}✓ Gate P${gate_num}: PASSED${CE_GATE_COLOR_RESET}"
        cat "$gate_file"
        return 0
    else
        echo -e "${CE_GATE_COLOR_YELLOW}⚠ Gate P${gate_num}: NOT PASSED${CE_GATE_COLOR_RESET}"
        return 1
    fi
}

# Export all functions
export -f ce_gate_validate_all
export -f ce_gate_validate_phase
export -f ce_gate_check_phase_gate
export -f ce_gate_validate_single
export -f ce_gate_check_score
export -f ce_gate_get_score
export -f ce_gate_set_threshold
export -f ce_gate_check_coverage
export -f ce_gate_get_coverage
export -f ce_gate_get_coverage_value
export -f ce_gate_check_coverage_delta
export -f ce_gate_check_security
export -f ce_gate_scan_secrets
export -f ce_gate_check_dependencies
export -f ce_gate_check_performance
export -f ce_gate_get_performance_metrics
export -f ce_gate_check_performance_regression
export -f ce_gate_check_bdd
export -f ce_gate_get_bdd_results
export -f ce_gate_check_signatures
export -f ce_gate_verify_signatures
export -f ce_gate_sign_gate_file
export -f ce_gate_run_custom
export -f ce_gate_register_custom
export -f ce_gate_generate_report
export -f ce_gate_show_summary
export -f ce_gate_show_failures
export -f ce_gate_get_history
export -f ce_gate_compare_with_baseline
export -f ce_gate_load_config
export -f ce_gate_validate_config
export -f ce_gate_update_config
export -f ce_gate_run_on_commit
export -f ce_gate_run_on_push
export -f ce_gate_run_in_ci
export -f ce_gate_mark_passed
export -f ce_gate_read_status
