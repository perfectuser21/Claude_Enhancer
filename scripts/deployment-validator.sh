#!/bin/bash

# =============================================================================
# Claude Enhancer 5.1 - Deployment Validation Script
# Comprehensive validation of cloud infrastructure deployment
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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
ENVIRONMENT="prod"
REGION="us-east-1"
VALIDATION_RESULTS=()
FAILED_CHECKS=0
PASSED_CHECKS=0

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $*"; }
log_header() { echo -e "${CYAN}[${1}]${NC} $2"; }

# Result tracking
add_result() {
    local status=$1
    local check=$2
    local details=$3

    VALIDATION_RESULTS+=("$status|$check|$details")

    if [ "$status" = "PASS" ]; then
        ((PASSED_CHECKS++))
        log_info "✅ $check"
    else
        ((FAILED_CHECKS++))
        log_error "❌ $check: $details"
    fi
}

# Create reports directory
mkdir -p "$REPORT_DIR"

# =============================================================================
# Infrastructure Validation Functions
# =============================================================================

validate_vpc() {
    log_header "VPC" "Validating VPC infrastructure..."

    local vpc_id=$(aws ec2 describe-vpcs \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-vpc" \
        --query 'Vpcs[0].VpcId' --output text --region "$REGION" 2>/dev/null)

    if [ "$vpc_id" != "None" ] && [ -n "$vpc_id" ]; then
        add_result "PASS" "VPC exists" "$vpc_id"

        # Check subnets
        local subnet_count=$(aws ec2 describe-subnets \
            --filters "Name=vpc-id,Values=$vpc_id" \
            --query 'length(Subnets)' --output text --region "$REGION")

        if [ "$subnet_count" -ge 9 ]; then
            add_result "PASS" "Subnets configured" "$subnet_count subnets found"
        else
            add_result "FAIL" "Insufficient subnets" "Expected 9+, found $subnet_count"
        fi

        # Check NAT gateways
        local nat_count=$(aws ec2 describe-nat-gateways \
            --filter "Name=vpc-id,Values=$vpc_id" "Name=state,Values=available" \
            --query 'length(NatGateways)' --output text --region "$REGION")

        if [ "$nat_count" -ge 1 ]; then
            add_result "PASS" "NAT gateways operational" "$nat_count NAT gateways"
        else
            add_result "FAIL" "No NAT gateways found" ""
        fi

    else
        add_result "FAIL" "VPC not found" ""
    fi
}

validate_ecs_cluster() {
    log_header "ECS" "Validating ECS cluster and services..."

    local cluster_arn=$(aws ecs describe-clusters \
        --clusters "${PROJECT_NAME}-${ENVIRONMENT}-cluster" \
        --query 'clusters[0].clusterArn' --output text --region "$REGION" 2>/dev/null)

    if [ "$cluster_arn" != "None" ] && [ -n "$cluster_arn" ]; then
        add_result "PASS" "ECS cluster exists" "$(basename "$cluster_arn")"

        # Check services
        local services=("auth" "core" "agent")
        for service in "${services[@]}"; do
            local service_name="${PROJECT_NAME}-${ENVIRONMENT}-${service}-service"
            local service_status=$(aws ecs describe-services \
                --cluster "${PROJECT_NAME}-${ENVIRONMENT}-cluster" \
                --services "$service_name" \
                --query 'services[0].status' --output text --region "$REGION" 2>/dev/null)

            if [ "$service_status" = "ACTIVE" ]; then
                local running_count=$(aws ecs describe-services \
                    --cluster "${PROJECT_NAME}-${ENVIRONMENT}-cluster" \
                    --services "$service_name" \
                    --query 'services[0].runningCount' --output text --region "$REGION")
                add_result "PASS" "$service service running" "$running_count tasks"
            else
                add_result "FAIL" "$service service not active" "$service_status"
            fi
        done

    else
        add_result "FAIL" "ECS cluster not found" ""
    fi
}

validate_load_balancer() {
    log_header "ALB" "Validating Application Load Balancer..."

    local alb_arn=$(aws elbv2 describe-load-balancers \
        --names "${PROJECT_NAME}-${ENVIRONMENT}-alb" \
        --query 'LoadBalancers[0].LoadBalancerArn' --output text --region "$REGION" 2>/dev/null)

    if [ "$alb_arn" != "None" ] && [ -n "$alb_arn" ]; then
        add_result "PASS" "Application Load Balancer exists" "$(basename "$alb_arn")"

        # Check target groups
        local target_groups=$(aws elbv2 describe-target-groups \
            --load-balancer-arn "$alb_arn" \
            --query 'length(TargetGroups)' --output text --region "$REGION")

        if [ "$target_groups" -ge 3 ]; then
            add_result "PASS" "Target groups configured" "$target_groups target groups"
        else
            add_result "FAIL" "Insufficient target groups" "Expected 3+, found $target_groups"
        fi

        # Check listeners
        local listeners=$(aws elbv2 describe-listeners \
            --load-balancer-arn "$alb_arn" \
            --query 'length(Listeners)' --output text --region "$REGION")

        if [ "$listeners" -ge 2 ]; then
            add_result "PASS" "ALB listeners configured" "$listeners listeners"
        else
            add_result "FAIL" "Missing ALB listeners" "Expected 2+, found $listeners"
        fi

    else
        add_result "FAIL" "Application Load Balancer not found" ""
    fi
}

validate_database() {
    log_header "RDS" "Validating Aurora PostgreSQL cluster..."

    local cluster_id=$(aws rds describe-db-clusters \
        --db-cluster-identifier "${PROJECT_NAME}-${ENVIRONMENT}-aurora-cluster" \
        --query 'DBClusters[0].DBClusterIdentifier' --output text --region "$REGION" 2>/dev/null)

    if [ "$cluster_id" != "None" ] && [ -n "$cluster_id" ]; then
        local cluster_status=$(aws rds describe-db-clusters \
            --db-cluster-identifier "$cluster_id" \
            --query 'DBClusters[0].Status' --output text --region "$REGION")

        if [ "$cluster_status" = "available" ]; then
            add_result "PASS" "Aurora cluster available" "$cluster_id"

            # Check instances
            local instance_count=$(aws rds describe-db-cluster-members \
                --db-cluster-identifier "$cluster_id" \
                --query 'length(DBClusterMembers)' --output text --region "$REGION")

            if [ "$instance_count" -ge 2 ]; then
                add_result "PASS" "Aurora instances configured" "$instance_count instances"
            else
                add_result "FAIL" "Insufficient Aurora instances" "Expected 2+, found $instance_count"
            fi

        else
            add_result "FAIL" "Aurora cluster not available" "$cluster_status"
        fi

    else
        add_result "FAIL" "Aurora cluster not found" ""
    fi
}

validate_redis() {
    log_header "REDIS" "Validating ElastiCache Redis cluster..."

    local replication_group_id="${PROJECT_NAME}-${ENVIRONMENT}-redis"
    local redis_status=$(aws elasticache describe-replication-groups \
        --replication-group-id "$replication_group_id" \
        --query 'ReplicationGroups[0].Status' --output text --region "$REGION" 2>/dev/null)

    if [ "$redis_status" = "available" ]; then
        add_result "PASS" "Redis cluster available" "$replication_group_id"

        # Check nodes
        local node_count=$(aws elasticache describe-replication-groups \
            --replication-group-id "$replication_group_id" \
            --query 'ReplicationGroups[0].NumCacheClusters' --output text --region "$REGION")

        if [ "$node_count" -ge 2 ]; then
            add_result "PASS" "Redis nodes configured" "$node_count nodes"
        else
            add_result "FAIL" "Insufficient Redis nodes" "Expected 2+, found $node_count"
        fi

    else
        add_result "FAIL" "Redis cluster not available" "$redis_status"
    fi
}

validate_s3_buckets() {
    log_header "S3" "Validating S3 buckets..."

    local bucket_types=("assets" "uploads" "backups" "alb-logs")
    for bucket_type in "${bucket_types[@]}"; do
        local bucket_pattern="${PROJECT_NAME}-${ENVIRONMENT}-${bucket_type}"
        local bucket_exists=$(aws s3api list-buckets \
            --query "Buckets[?contains(Name, '${bucket_pattern}')].Name" \
            --output text --region "$REGION" 2>/dev/null)

        if [ -n "$bucket_exists" ]; then
            add_result "PASS" "S3 bucket exists" "$bucket_type: $bucket_exists"
        else
            add_result "FAIL" "S3 bucket missing" "$bucket_type"
        fi
    done
}

validate_cloudfront() {
    log_header "CDN" "Validating CloudFront distribution..."

    local distribution_id=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?contains(Comment, '${PROJECT_NAME}')].Id" \
        --output text --region "$REGION" 2>/dev/null)

    if [ -n "$distribution_id" ]; then
        local distribution_status=$(aws cloudfront get-distribution \
            --id "$distribution_id" \
            --query 'Distribution.Status' --output text --region "$REGION")

        if [ "$distribution_status" = "Deployed" ]; then
            add_result "PASS" "CloudFront distribution deployed" "$distribution_id"
        else
            add_result "FAIL" "CloudFront distribution not ready" "$distribution_status"
        fi
    else
        add_result "FAIL" "CloudFront distribution not found" ""
    fi
}

# =============================================================================
# Application Health Checks
# =============================================================================

validate_application_health() {
    log_header "HEALTH" "Validating application endpoints..."

    # Get ALB DNS name
    local alb_dns=$(aws elbv2 describe-load-balancers \
        --names "${PROJECT_NAME}-${ENVIRONMENT}-alb" \
        --query 'LoadBalancers[0].DNSName' --output text --region "$REGION" 2>/dev/null)

    if [ "$alb_dns" != "None" ] && [ -n "$alb_dns" ]; then
        # Test health endpoint
        if curl -s -f "http://$alb_dns/health" >/dev/null; then
            add_result "PASS" "Health endpoint responsive" "http://$alb_dns/health"
        else
            add_result "FAIL" "Health endpoint not accessible" "http://$alb_dns/health"
        fi

        # Test API endpoint
        if curl -s -f "http://$alb_dns/api/v1/status" >/dev/null; then
            add_result "PASS" "API endpoint responsive" "http://$alb_dns/api/v1/status"
        else
            add_result "WARN" "API endpoint check failed" "http://$alb_dns/api/v1/status"
        fi

    else
        add_result "FAIL" "Cannot retrieve ALB DNS name" ""
    fi
}

# =============================================================================
# Security Validation
# =============================================================================

validate_security() {
    log_header "SECURITY" "Validating security configuration..."

    # Check security groups
    local sg_count=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=${PROJECT_NAME}-${ENVIRONMENT}-*" \
        --query 'length(SecurityGroups)' --output text --region "$REGION")

    if [ "$sg_count" -ge 4 ]; then
        add_result "PASS" "Security groups configured" "$sg_count security groups"
    else
        add_result "FAIL" "Insufficient security groups" "Expected 4+, found $sg_count"
    fi

    # Check KMS keys
    local kms_keys=$(aws kms list-aliases \
        --query "Aliases[?contains(AliasName, '${PROJECT_NAME}')].AliasName" \
        --output text --region "$REGION")

    if [ -n "$kms_keys" ]; then
        add_result "PASS" "KMS keys configured" "$kms_keys"
    else
        add_result "FAIL" "No KMS keys found" ""
    fi

    # Check SSL certificate
    local cert_arn=$(aws acm list-certificates \
        --query "CertificateSummaryList[?contains(DomainName, '${PROJECT_NAME}')].CertificateArn" \
        --output text --region "$REGION")

    if [ -n "$cert_arn" ]; then
        local cert_status=$(aws acm describe-certificate \
            --certificate-arn "$cert_arn" \
            --query 'Certificate.Status' --output text --region "$REGION")

        if [ "$cert_status" = "ISSUED" ]; then
            add_result "PASS" "SSL certificate valid" "$(basename "$cert_arn")"
        else
            add_result "FAIL" "SSL certificate not valid" "$cert_status"
        fi
    else
        add_result "WARN" "No SSL certificate found" ""
    fi
}

# =============================================================================
# Performance Validation
# =============================================================================

validate_performance() {
    log_header "PERFORMANCE" "Validating performance configuration..."

    # Check auto scaling policies
    local scaling_policies=$(aws application-autoscaling describe-scaling-policies \
        --service-namespace ecs \
        --query 'length(ScalingPolicies)' --output text --region "$REGION" 2>/dev/null)

    if [ "$scaling_policies" -gt 0 ]; then
        add_result "PASS" "Auto scaling policies configured" "$scaling_policies policies"
    else
        add_result "WARN" "No auto scaling policies found" ""
    fi

    # Check CloudWatch alarms
    local alarm_count=$(aws cloudwatch describe-alarms \
        --alarm-name-prefix "${PROJECT_NAME}-${ENVIRONMENT}" \
        --query 'length(MetricAlarms)' --output text --region "$REGION")

    if [ "$alarm_count" -gt 0 ]; then
        add_result "PASS" "CloudWatch alarms configured" "$alarm_count alarms"
    else
        add_result "WARN" "No CloudWatch alarms found" ""
    fi
}

# =============================================================================
# Report Generation
# =============================================================================

generate_report() {
    local report_file="${REPORT_DIR}/deployment_validation_$(date +%Y%m%d_%H%M%S).json"
    local summary_file="${REPORT_DIR}/validation_summary.txt"

    log_header "REPORT" "Generating validation report..."

    # JSON report
    cat > "$report_file" << EOF
{
    "validation_report": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "environment": "$ENVIRONMENT",
        "region": "$REGION",
        "summary": {
            "total_checks": $((PASSED_CHECKS + FAILED_CHECKS)),
            "passed_checks": $PASSED_CHECKS,
            "failed_checks": $FAILED_CHECKS,
            "success_rate": $(echo "scale=2; $PASSED_CHECKS * 100 / ($PASSED_CHECKS + $FAILED_CHECKS)" | bc -l 2>/dev/null || echo "0")
        },
        "results": [
EOF

    local first=true
    for result in "${VALIDATION_RESULTS[@]}"; do
        IFS='|' read -r status check details <<< "$result"

        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$report_file"
        fi

        cat >> "$report_file" << EOF
            {
                "status": "$status",
                "check": "$check",
                "details": "$details"
            }
EOF
    done

    cat >> "$report_file" << EOF
        ]
    }
}
EOF

    # Text summary
    cat > "$summary_file" << EOF
Claude Enhancer 5.1 - Deployment Validation Summary
================================================

Environment: $ENVIRONMENT
Region: $REGION
Timestamp: $(date)

Results:
--------
Total Checks: $((PASSED_CHECKS + FAILED_CHECKS))
Passed: $PASSED_CHECKS
Failed: $FAILED_CHECKS
Success Rate: $(echo "scale=1; $PASSED_CHECKS * 100 / ($PASSED_CHECKS + $FAILED_CHECKS)" | bc -l 2>/dev/null || echo "0")%

Status: $([ $FAILED_CHECKS -eq 0 ] && echo "✅ DEPLOYMENT VALID" || echo "❌ DEPLOYMENT ISSUES DETECTED")

Detailed Results:
----------------
EOF

    for result in "${VALIDATION_RESULTS[@]}"; do
        IFS='|' read -r status check details <<< "$result"
        printf "%-50s %s %s\n" "$check" "$status" "$details" >> "$summary_file"
    done

    log_info "Validation report saved to: $report_file"
    log_info "Summary saved to: $summary_file"
}

# =============================================================================
# Main Execution
# =============================================================================

show_help() {
    cat << EOF
Claude Enhancer 5.1 - Deployment Validation Script

Usage: $0 [OPTIONS]

Options:
  -e, --environment ENV    Environment to validate (dev|staging|prod) [default: prod]
  -r, --region REGION      AWS region [default: us-east-1]
  --skip-health           Skip application health checks
  --quick                 Run only critical infrastructure checks
  -h, --help              Show this help message

Examples:
  $0                      # Validate production environment
  $0 -e staging -r us-west-2  # Validate staging in us-west-2
  $0 --quick              # Quick validation (infrastructure only)

EOF
}

parse_arguments() {
    SKIP_HEALTH=false
    QUICK_MODE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            --skip-health)
                SKIP_HEALTH=true
                shift
                ;;
            --quick)
                QUICK_MODE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

main() {
    parse_arguments "$@"

    echo -e "${CYAN}"
    echo "==============================================="
    echo "  Claude Enhancer 5.1 - Deployment Validator"
    echo "==============================================="
    echo -e "${NC}"
    echo "Environment: $ENVIRONMENT"
    echo "Region: $REGION"
    echo "Time: $(date)"
    echo ""

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        log_error "AWS credentials not configured"
        exit 1
    fi

    # Run validations
    validate_vpc
    validate_ecs_cluster
    validate_load_balancer
    validate_database
    validate_redis
    validate_s3_buckets

    if [ "$QUICK_MODE" = false ]; then
        validate_cloudfront
        validate_security
        validate_performance

        if [ "$SKIP_HEALTH" = false ]; then
            validate_application_health
        fi
    fi

    # Generate report
    generate_report

    # Final summary
    echo ""
    echo -e "${CYAN}===============================================${NC}"
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✅ DEPLOYMENT VALIDATION SUCCESSFUL${NC}"
        echo -e "All $PASSED_CHECKS checks passed!"
    else
        echo -e "${RED}❌ DEPLOYMENT VALIDATION FAILED${NC}"
        echo -e "$FAILED_CHECKS out of $((PASSED_CHECKS + FAILED_CHECKS)) checks failed"
        exit 1
    fi
    echo -e "${CYAN}===============================================${NC}"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi