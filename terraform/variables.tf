# =============================================================================
# Claude Enhancer 5.1 Terraform变量定义
# =============================================================================

# =============================================================================
# 基础配置变量
# =============================================================================

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "backup_region" {
  description = "AWS backup region for disaster recovery"
  type        = string
  default     = "us-west-2"
}

variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\\.[a-z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid domain format."
  }
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID for the domain"
  type        = string
}

# =============================================================================
# 数据库配置变量
# =============================================================================

variable "aurora_instance_class" {
  description = "Aurora PostgreSQL instance class"
  type        = string
  default     = "db.r6g.large"

  validation {
    condition = can(regex("^db\\.(r6g|r5|r4)\\.(large|xlarge|2xlarge|4xlarge|8xlarge|12xlarge|16xlarge|24xlarge)$", var.aurora_instance_class))
    error_message = "Aurora instance class must be a valid RDS instance type."
  }
}

variable "aurora_instance_count" {
  description = "Number of Aurora instances (1 writer + N readers)"
  type        = number
  default     = 3

  validation {
    condition     = var.aurora_instance_count >= 1 && var.aurora_instance_count <= 15
    error_message = "Aurora instance count must be between 1 and 15."
  }
}

variable "db_password" {
  description = "Master password for the Aurora database (leave empty for auto-generated)"
  type        = string
  default     = ""
  sensitive   = true

  validation {
    condition     = var.db_password == "" || length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters long."
  }
}

# =============================================================================
# Redis配置变量
# =============================================================================

variable "redis_instance_type" {
  description = "ElastiCache Redis instance type"
  type        = string
  default     = "cache.r7g.large"

  validation {
    condition = can(regex("^cache\\.(r7g|r6g|r5|r4)\\.(micro|small|medium|large|xlarge|2xlarge|4xlarge|8xlarge|12xlarge|16xlarge|24xlarge)$", var.redis_instance_type))
    error_message = "Redis instance type must be a valid ElastiCache instance type."
  }
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in the Redis replication group"
  type        = number
  default     = 3

  validation {
    condition     = var.redis_num_cache_nodes >= 1 && var.redis_num_cache_nodes <= 20
    error_message = "Redis cache nodes count must be between 1 and 20."
  }
}

variable "redis_auth_token" {
  description = "Auth token for Redis (leave empty for auto-generated)"
  type        = string
  default     = ""
  sensitive   = true

  validation {
    condition     = var.redis_auth_token == "" || length(var.redis_auth_token) >= 16
    error_message = "Redis auth token must be at least 16 characters long."
  }
}

# =============================================================================
# ECS配置变量
# =============================================================================

variable "ecs_services" {
  description = "ECS service configurations"
  type = map(object({
    cpu                      = number
    memory                   = number
    desired_count           = number
    min_capacity            = number
    max_capacity            = number
    container_port          = number
    health_check_path       = string
    health_check_timeout    = number
    health_check_interval   = number
    environment_variables   = map(string)
  }))

  default = {
    auth = {
      cpu                   = 1024
      memory                = 2048
      desired_count        = 2
      min_capacity         = 2
      max_capacity         = 10
      container_port       = 8080
      health_check_path    = "/api/v1/health"
      health_check_timeout = 5
      health_check_interval = 30
      environment_variables = {
        SERVICE_NAME = "auth-service"
        LOG_LEVEL   = "INFO"
      }
    }

    core = {
      cpu                   = 2048
      memory                = 4096
      desired_count        = 3
      min_capacity         = 3
      max_capacity         = 15
      container_port       = 8080
      health_check_path    = "/api/health"
      health_check_timeout = 5
      health_check_interval = 30
      environment_variables = {
        SERVICE_NAME = "core-service"
        LOG_LEVEL   = "INFO"
      }
    }

    agent = {
      cpu                   = 4096
      memory                = 8192
      desired_count        = 2
      min_capacity         = 2
      max_capacity         = 8
      container_port       = 8080
      health_check_path    = "/agents/health"
      health_check_timeout = 10
      health_check_interval = 30
      environment_variables = {
        SERVICE_NAME = "agent-service"
        LOG_LEVEL   = "INFO"
      }
    }

    workflow = {
      cpu                   = 1024
      memory                = 2048
      desired_count        = 2
      min_capacity         = 2
      max_capacity         = 6
      container_port       = 8080
      health_check_path    = "/workflow/status"
      health_check_timeout = 5
      health_check_interval = 30
      environment_variables = {
        SERVICE_NAME = "workflow-service"
        LOG_LEVEL   = "INFO"
      }
    }
  }
}

# =============================================================================
# 自动扩展配置
# =============================================================================

variable "auto_scaling_config" {
  description = "Auto scaling configuration for ECS services"
  type = object({
    cpu_target_percentage    = number
    memory_target_percentage = number
    requests_per_target     = number
    scale_out_cooldown      = number
    scale_in_cooldown       = number
  })

  default = {
    cpu_target_percentage    = 70
    memory_target_percentage = 80
    requests_per_target     = 100
    scale_out_cooldown      = 300
    scale_in_cooldown       = 600
  }
}

# =============================================================================
# 安全配置变量
# =============================================================================

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]

  validation {
    condition = alltrue([
      for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All CIDR blocks must be valid."
  }
}

variable "enable_waf" {
  description = "Enable AWS WAF for the application"
  type        = bool
  default     = true
}

variable "waf_rules" {
  description = "WAF rules configuration"
  type = object({
    enable_rate_limiting    = bool
    rate_limit_requests    = number
    rate_limit_window      = number
    enable_geo_blocking    = bool
    blocked_countries      = list(string)
    enable_sql_injection   = bool
    enable_xss_protection  = bool
  })

  default = {
    enable_rate_limiting   = true
    rate_limit_requests   = 2000
    rate_limit_window     = 300
    enable_geo_blocking   = true
    blocked_countries     = ["CN", "RU", "KP"]
    enable_sql_injection  = true
    enable_xss_protection = true
  }
}

# =============================================================================
# 监控配置变量
# =============================================================================

variable "enable_monitoring" {
  description = "Enable enhanced monitoring and logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch logs retention period in days"
  type        = number
  default     = 30

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "alert_sns_topic_arn" {
  description = "SNS topic ARN for alerts (optional)"
  type        = string
  default     = ""
}

# =============================================================================
# 备份和灾备配置
# =============================================================================

variable "backup_retention_days" {
  description = "Database backup retention period in days"
  type        = number
  default     = 35

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 35
    error_message = "Backup retention days must be between 1 and 35."
  }
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = true
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for databases"
  type        = bool
  default     = true
}

variable "snapshot_window" {
  description = "Preferred backup window (format: HH:MM-HH:MM)"
  type        = string
  default     = "07:00-09:00"

  validation {
    condition = can(regex("^([01]?[0-9]|2[0-3]):[0-5][0-9]-([01]?[0-9]|2[0-3]):[0-5][0-9]$", var.snapshot_window))
    error_message = "Snapshot window must be in HH:MM-HH:MM format."
  }
}

variable "maintenance_window" {
  description = "Preferred maintenance window (format: ddd:HH:MM-ddd:HH:MM)"
  type        = string
  default     = "sun:09:00-sun:10:00"

  validation {
    condition = can(regex("^(mon|tue|wed|thu|fri|sat|sun):[0-2][0-9]:[0-5][0-9]-(mon|tue|wed|thu|fri|sat|sun):[0-2][0-9]:[0-5][0-9]$", var.maintenance_window))
    error_message = "Maintenance window must be in ddd:HH:MM-ddd:HH:MM format."
  }
}

# =============================================================================
# CDN配置变量
# =============================================================================

variable "enable_cdn" {
  description = "Enable CloudFront CDN"
  type        = bool
  default     = true
}

variable "cdn_config" {
  description = "CloudFront CDN configuration"
  type = object({
    price_class                = string
    default_cache_ttl         = number
    max_cache_ttl             = number
    enable_compression        = bool
    enable_http2              = bool
    enable_ipv6               = bool
    viewer_protocol_policy    = string
  })

  default = {
    price_class             = "PriceClass_All"
    default_cache_ttl      = 86400
    max_cache_ttl          = 31536000
    enable_compression     = true
    enable_http2           = true
    enable_ipv6            = true
    viewer_protocol_policy = "redirect-to-https"
  }

  validation {
    condition = contains([
      "PriceClass_100", "PriceClass_200", "PriceClass_All"
    ], var.cdn_config.price_class)
    error_message = "CDN price class must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }

  validation {
    condition = contains([
      "allow-all", "redirect-to-https", "https-only"
    ], var.cdn_config.viewer_protocol_policy)
    error_message = "Viewer protocol policy must be allow-all, redirect-to-https, or https-only."
  }
}

# =============================================================================
# 成本优化配置
# =============================================================================

variable "enable_spot_instances" {
  description = "Enable spot instances for non-critical workloads"
  type        = bool
  default     = false
}

variable "enable_scheduled_scaling" {
  description = "Enable scheduled scaling for predictable workloads"
  type        = bool
  default     = false
}

variable "scaling_schedule" {
  description = "Scaling schedule configuration"
  type = map(object({
    min_capacity         = number
    max_capacity         = number
    desired_capacity     = number
    recurrence          = string
    timezone            = string
  }))

  default = {
    business_hours = {
      min_capacity     = 4
      max_capacity     = 20
      desired_capacity = 6
      recurrence      = "0 9 * * MON-FRI"
      timezone        = "UTC"
    }
    off_hours = {
      min_capacity     = 2
      max_capacity     = 10
      desired_capacity = 3
      recurrence      = "0 18 * * MON-FRI"
      timezone        = "UTC"
    }
  }
}

# =============================================================================
# 开发和调试配置
# =============================================================================

variable "enable_debug_mode" {
  description = "Enable debug mode (only for non-prod environments)"
  type        = bool
  default     = false
}

variable "enable_bastion_host" {
  description = "Enable bastion host for secure access"
  type        = bool
  default     = false
}

variable "bastion_instance_type" {
  description = "EC2 instance type for bastion host"
  type        = string
  default     = "t3.micro"
}

variable "enable_vpn_access" {
  description = "Enable VPN access for remote development"
  type        = bool
  default     = false
}

# =============================================================================
# 标签配置
# =============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "cost_center" {
  description = "Cost center for billing and resource allocation"
  type        = string
  default     = "engineering"
}

variable "owner" {
  description = "Resource owner or team responsible"
  type        = string
  default     = "claude-enhancer-team"
}

variable "business_unit" {
  description = "Business unit owning these resources"
  type        = string
  default     = "product"
}

# =============================================================================
# 环境特定覆盖
# =============================================================================

variable "environment_overrides" {
  description = "Environment-specific configuration overrides"
  type        = map(any)
  default     = {}
}