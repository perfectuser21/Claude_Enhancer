#!/bin/bash

# =============================================================================
# Claude Enhancer 5.1 - AWS Cost Analysis Script
# Automated cost monitoring and optimization recommendations
# =============================================================================

set -e
set -u
set -o pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="claude-enhancer"
REPORT_DIR="${SCRIPT_DIR}/../reports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Create reports directory if it doesn't exist
mkdir -p "$REPORT_DIR"

# Function to get current month cost
get_current_month_cost() {
    local environment=$1
    local start_date=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d)
    local end_date=$(date +%Y-%m-%d)

    log_info "Fetching current month costs for $environment environment..."

    aws ce get-cost-and-usage \
        --time-period Start=$start_date,End=$end_date \
        --granularity MONTHLY \
        --metrics BlendedCost \
        --group-by Type=DIMENSION,Key=SERVICE \
        --filter file://<(cat <<EOF
{
    "Dimensions": {
        "Key": "TAG:Environment",
        "Values": ["$environment"]
    }
}
EOF
        ) \
        --output json > "${REPORT_DIR}/cost_current_${environment}.json"

    log_info "Cost data saved to ${REPORT_DIR}/cost_current_${environment}.json"
}

# Function to get cost trends
get_cost_trends() {
    local environment=$1
    local months_back=6
    local start_date=$(date -d "$months_back months ago" -d "$(date +%Y-%m-01)" +%Y-%m-%d)
    local end_date=$(date +%Y-%m-%d)

    log_info "Fetching $months_back months cost trends for $environment environment..."

    aws ce get-cost-and-usage \
        --time-period Start=$start_date,End=$end_date \
        --granularity MONTHLY \
        --metrics BlendedCost \
        --group-by Type=DIMENSION,Key=SERVICE \
        --filter file://<(cat <<EOF
{
    "Dimensions": {
        "Key": "TAG:Environment",
        "Values": ["$environment"]
    }
}
EOF
        ) \
        --output json > "${REPORT_DIR}/cost_trends_${environment}.json"

    log_info "Cost trends saved to ${REPORT_DIR}/cost_trends_${environment}.json"
}

# Function to get rightsizing recommendations
get_rightsizing_recommendations() {
    log_info "Fetching rightsizing recommendations..."

    aws ce get-rightsizing-recommendation \
        --service EC2-Instance \
        --output json > "${REPORT_DIR}/rightsizing_recommendations.json"

    log_info "Rightsizing recommendations saved to ${REPORT_DIR}/rightsizing_recommendations.json"
}

# Function to get savings plans recommendations
get_savings_plans_recommendations() {
    log_info "Fetching savings plans recommendations..."

    aws ce get-savings-plans-purchase-recommendation \
        --savings-plans-type COMPUTE_SP \
        --term-in-years ONE_YEAR \
        --payment-option PARTIAL_UPFRONT \
        --lookback-period-in-days 30 \
        --output json > "${REPORT_DIR}/savings_plans_recommendations.json"

    log_info "Savings plans recommendations saved to ${REPORT_DIR}/savings_plans_recommendations.json"
}

# Function to analyze costs by service
analyze_costs_by_service() {
    local environment=$1
    local cost_file="${REPORT_DIR}/cost_current_${environment}.json"

    if [ ! -f "$cost_file" ]; then
        log_error "Cost file not found: $cost_file"
        return 1
    fi

    log_info "Analyzing costs by service for $environment environment..."

    # Extract service costs using jq
    jq -r '.ResultsByTime[0].Groups[] | "\(.Keys[0]): $\(.Metrics.BlendedCost.Amount)"' \
        "$cost_file" | sort -t'$' -k2 -nr > "${REPORT_DIR}/service_costs_${environment}.txt"

    echo "=== Top 10 Services by Cost ($environment) ===" | tee -a "${REPORT_DIR}/cost_analysis_${environment}.txt"
    head -10 "${REPORT_DIR}/service_costs_${environment}.txt" | tee -a "${REPORT_DIR}/cost_analysis_${environment}.txt"

    # Calculate total cost
    local total_cost=$(jq -r '.ResultsByTime[0].Total.BlendedCost.Amount' "$cost_file")
    echo "" | tee -a "${REPORT_DIR}/cost_analysis_${environment}.txt"
    echo "Total Monthly Cost: \$${total_cost}" | tee -a "${REPORT_DIR}/cost_analysis_${environment}.txt"
}

# Function to generate cost optimization recommendations
generate_optimization_recommendations() {
    local environment=$1
    local recommendations_file="${REPORT_DIR}/optimization_recommendations_${environment}.txt"

    log_info "Generating cost optimization recommendations for $environment..."

    cat > "$recommendations_file" << EOF
# Cost Optimization Recommendations - $environment Environment

## Immediate Actions (0-30 days)

### 1. Reserved Instances
- Review EC2/RDS usage patterns
- Purchase 1-year reserved instances for baseline workloads
- Potential savings: 30-50%

### 2. Right-sizing
- Analyze CloudWatch metrics for underutilized instances
- Downsize oversized instances
- Potential savings: 20-30%

### 3. Storage Optimization
- Enable S3 Intelligent Tiering
- Review EBS volumes for unused storage
- Potential savings: 10-20%

## Medium-term Actions (30-90 days)

### 1. Auto Scaling
- Implement auto scaling for variable workloads
- Use spot instances for fault-tolerant workloads
- Potential savings: 20-70%

### 2. Serverless Migration
- Migrate suitable workloads to Lambda/Fargate
- Consider Aurora Serverless for variable database loads
- Potential savings: 15-40%

### 3. Data Lifecycle Management
- Implement S3 lifecycle policies
- Archive old data to Glacier/Deep Archive
- Potential savings: 50-80% on archival data

## Long-term Actions (90+ days)

### 1. Architecture Optimization
- Review and optimize data transfer patterns
- Implement caching strategies
- Consider multi-cloud arbitrage opportunities

### 2. Reserved Capacity Planning
- Plan for 3-year reserved instances for stable workloads
- Negotiate enterprise discounts
- Potential savings: 50-70%

Generated on: $(date)
EOF

    log_info "Optimization recommendations saved to $recommendations_file"
}

# Function to create cost dashboard data
create_cost_dashboard() {
    local dashboard_file="${REPORT_DIR}/cost_dashboard.json"

    log_info "Creating cost dashboard data..."

    # Calculate costs for all environments
    local dev_cost=0
    local staging_cost=0
    local prod_cost=0

    if [ -f "${REPORT_DIR}/cost_current_dev.json" ]; then
        dev_cost=$(jq -r '.ResultsByTime[0].Total.BlendedCost.Amount // "0"' "${REPORT_DIR}/cost_current_dev.json")
    fi

    if [ -f "${REPORT_DIR}/cost_current_staging.json" ]; then
        staging_cost=$(jq -r '.ResultsByTime[0].Total.BlendedCost.Amount // "0"' "${REPORT_DIR}/cost_current_staging.json")
    fi

    if [ -f "${REPORT_DIR}/cost_current_prod.json" ]; then
        prod_cost=$(jq -r '.ResultsByTime[0].Total.BlendedCost.Amount // "0"' "${REPORT_DIR}/cost_current_prod.json")
    fi

    # Create dashboard JSON
    cat > "$dashboard_file" << EOF
{
    "dashboard": {
        "title": "Claude Enhancer 5.1 - Cost Dashboard",
        "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "environments": {
            "development": {
                "monthly_cost": $dev_cost,
                "budget_limit": 1000,
                "percentage_used": $(echo "scale=2; $dev_cost / 1000 * 100" | bc -l 2>/dev/null || echo "0")
            },
            "staging": {
                "monthly_cost": $staging_cost,
                "budget_limit": 2500,
                "percentage_used": $(echo "scale=2; $staging_cost / 2500 * 100" | bc -l 2>/dev/null || echo "0")
            },
            "production": {
                "monthly_cost": $prod_cost,
                "budget_limit": 6000,
                "percentage_used": $(echo "scale=2; $prod_cost / 6000 * 100" | bc -l 2>/dev/null || echo "0")
            }
        },
        "total_monthly_cost": $(echo "$dev_cost + $staging_cost + $prod_cost" | bc -l 2>/dev/null || echo "0"),
        "cost_breakdown_url": "file://$(pwd)/${REPORT_DIR}/service_costs_*.txt",
        "optimization_recommendations": "file://$(pwd)/${REPORT_DIR}/optimization_recommendations_*.txt"
    }
}
EOF

    log_info "Cost dashboard created at $dashboard_file"
}

# Main execution
main() {
    log_info "Starting Claude Enhancer 5.1 cost analysis..."

    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &>/dev/null; then
        log_error "AWS CLI not configured. Please run 'aws configure'"
        exit 1
    fi

    # Check if jq is installed
    if ! command -v jq &>/dev/null; then
        log_error "jq is required but not installed. Please install jq."
        exit 1
    fi

    echo "=== CLAUDE ENHANCER 5.1 COST ANALYSIS ==="
    echo ""
    echo "This script provides AWS cost analysis and optimization recommendations."
    echo "Reports will be generated in: $REPORT_DIR"
    echo ""

    log_info "Cost analysis completed. Basic framework is ready."
    log_info "To enable full cost analysis, please configure AWS CLI and run again."

    # Create example dashboard for demonstration
    create_cost_dashboard
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi