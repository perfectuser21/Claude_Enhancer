# =============================================================================
# Terraform Networking Module Variables
# Input variables for VPC and networking configuration
# =============================================================================

variable "name_prefix" {
  description = "Name prefix for all resources"
  type        = string
  validation {
    condition     = length(var.name_prefix) <= 20
    error_message = "Name prefix must be 20 characters or less."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid CIDR block."
  }
}

variable "common_tags" {
  description = "Common tags to be applied to all resources"
  type        = map(string)
  default     = {}
}

variable "kubernetes_cluster_tag" {
  description = "Kubernetes cluster tag value for subnets"
  type        = string
  default     = "shared"
  validation {
    condition     = contains(["owned", "shared"], var.kubernetes_cluster_tag)
    error_message = "Kubernetes cluster tag must be either 'owned' or 'shared'."
  }
}

# NAT Gateway Configuration
variable "single_nat_gateway" {
  description = "Use a single NAT gateway for all private subnets (cost optimization)"
  type        = bool
  default     = false
}

# VPC Flow Logs
variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Retention period for VPC flow logs in days"
  type        = number
  default     = 30
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.flow_logs_retention_days)
    error_message = "Flow logs retention days must be a valid CloudWatch Logs retention value."
  }
}

# VPC Endpoints
variable "enable_s3_endpoint" {
  description = "Enable S3 VPC endpoint"
  type        = bool
  default     = true
}

variable "enable_dynamodb_endpoint" {
  description = "Enable DynamoDB VPC endpoint"
  type        = bool
  default     = false
}

variable "enable_ecr_endpoints" {
  description = "Enable ECR VPC endpoints"
  type        = bool
  default     = true
}

# Network ACLs
variable "enable_database_nacl" {
  description = "Enable additional Network ACL for database subnets"
  type        = bool
  default     = false
}

# Environment-specific overrides
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "availability_zone_count" {
  description = "Number of availability zones to use (max 3)"
  type        = number
  default     = 3
  validation {
    condition     = var.availability_zone_count >= 2 && var.availability_zone_count <= 3
    error_message = "Availability zone count must be between 2 and 3."
  }
}

# Cost optimization settings
variable "cost_optimization" {
  description = "Cost optimization configuration"
  type = object({
    single_nat_gateway    = bool
    disable_flow_logs     = bool
    minimal_vpc_endpoints = bool
  })
  default = {
    single_nat_gateway    = false
    disable_flow_logs     = false
    minimal_vpc_endpoints = false
  }
}