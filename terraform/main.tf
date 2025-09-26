# =============================================================================
# Claude Enhancer 5.1 云基础设施 - Terraform配置
# AWS多区域高可用架构
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  # State管理 - 使用S3 + DynamoDB
  backend "s3" {
    bucket         = "claude-enhancer-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "claude-enhancer-terraform-locks"
    encrypt        = true
  }
}

# =============================================================================
# 全局变量
# =============================================================================

locals {
  project = "claude-enhancer"
  environment = var.environment
  region = var.aws_region

  # 通用标签
  common_tags = {
    Project     = local.project
    Environment = local.environment
    ManagedBy   = "terraform"
    Owner       = "claude-enhancer-team"
    CostCenter  = "engineering"
    CreatedBy   = "terraform"
    Repository  = "https://github.com/perfect21/claude-enhancer"
  }

  # 网络配置
  vpc_cidr = "10.0.0.0/16"
  availability_zones = ["${local.region}a", "${local.region}b", "${local.region}c"]

  # 子网CIDR
  public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs  = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
  database_subnet_cidrs = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
}

# =============================================================================
# 主要提供商配置
# =============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# 备用区域提供商 (灾备)
provider "aws" {
  alias  = "backup"
  region = var.backup_region

  default_tags {
    tags = local.common_tags
  }
}

# =============================================================================
# 数据源
# =============================================================================

# 当前AWS账户信息
data "aws_caller_identity" "current" {}

# 可用区信息
data "aws_availability_zones" "available" {
  state = "available"
}

# 最新的Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# =============================================================================
# VPC 和网络基础设施
# =============================================================================

# VPC
resource "aws_vpc" "main" {
  cidr_block           = local.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-igw"
  })
}

# 公共子网
resource "aws_subnet" "public" {
  count = length(local.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnet_cidrs[count.index]
  availability_zone       = local.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-public-subnet-${count.index + 1}"
    Type = "public"
    Tier = "web"
  })
}

# 私有子网
resource "aws_subnet" "private" {
  count = length(local.private_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnet_cidrs[count.index]
  availability_zone = local.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-private-subnet-${count.index + 1}"
    Type = "private"
    Tier = "application"
  })
}

# 数据库子网
resource "aws_subnet" "database" {
  count = length(local.database_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.database_subnet_cidrs[count.index]
  availability_zone = local.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-database-subnet-${count.index + 1}"
    Type = "database"
    Tier = "data"
  })
}

# 弹性IP for NAT网关
resource "aws_eip" "nat" {
  count = length(local.private_subnet_cidrs)

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-nat-eip-${count.index + 1}"
  })
}

# NAT网关
resource "aws_nat_gateway" "main" {
  count = length(local.private_subnet_cidrs)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  depends_on    = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-nat-gw-${count.index + 1}"
  })
}

# 路由表 - 公共
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-public-rt"
    Type = "public"
  })
}

# 路由表 - 私有
resource "aws_route_table" "private" {
  count = length(local.private_subnet_cidrs)

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-private-rt-${count.index + 1}"
    Type = "private"
  })
}

# 路由表 - 数据库
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-database-rt"
    Type = "database"
  })
}

# 路由表关联 - 公共
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# 路由表关联 - 私有
resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# 路由表关联 - 数据库
resource "aws_route_table_association" "database" {
  count = length(aws_subnet.database)

  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# =============================================================================
# 安全组
# =============================================================================

# ALB安全组
resource "aws_security_group" "alb" {
  name        = "${local.project}-${local.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-alb-sg"
  })
}

# ECS服务安全组
resource "aws_security_group" "ecs" {
  name        = "${local.project}-${local.environment}-ecs-sg"
  description = "Security group for ECS services"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description     = "Health check"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-ecs-sg"
  })
}

# RDS安全组
resource "aws_security_group" "rds" {
  name        = "${local.project}-${local.environment}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-rds-sg"
  })
}

# Redis安全组
resource "aws_security_group" "redis" {
  name        = "${local.project}-${local.environment}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from ECS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-redis-sg"
  })
}

# =============================================================================
# RDS Aurora PostgreSQL
# =============================================================================

# DB子网组
resource "aws_db_subnet_group" "main" {
  name       = "${local.project}-${local.environment}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-db-subnet-group"
  })
}

# RDS参数组
resource "aws_db_parameter_group" "aurora_postgresql" {
  family = "aurora-postgresql15"
  name   = "${local.project}-${local.environment}-aurora-postgresql-params"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-aurora-postgresql-params"
  })
}

# Aurora集群参数组
resource "aws_rds_cluster_parameter_group" "aurora_postgresql" {
  family = "aurora-postgresql15"
  name   = "${local.project}-${local.environment}-aurora-postgresql-cluster-params"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-aurora-postgresql-cluster-params"
  })
}

# Aurora PostgreSQL集群
resource "aws_rds_cluster" "main" {
  cluster_identifier = "${local.project}-${local.environment}-aurora-cluster"

  engine             = "aurora-postgresql"
  engine_mode        = "provisioned"
  engine_version     = "15.3"
  database_name      = "claude_enhancer"
  master_username    = "postgres"
  master_password    = var.db_password

  backup_retention_period   = 35
  preferred_backup_window   = "07:00-09:00"
  preferred_maintenance_window = "sun:09:00-sun:10:00"

  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.aurora_postgresql.name
  db_subnet_group_name           = aws_db_subnet_group.main.name
  vpc_security_group_ids         = [aws_security_group.rds.id]

  storage_encrypted = true
  kms_key_id       = aws_kms_key.main.arn

  skip_final_snapshot       = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${local.project}-${local.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  copy_tags_to_snapshot = true
  deletion_protection   = var.environment == "prod"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-aurora-cluster"
  })
}

# Aurora实例
resource "aws_rds_cluster_instance" "cluster_instances" {
  count = var.aurora_instance_count

  identifier         = "${local.project}-${local.environment}-aurora-${count.index}"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = var.aurora_instance_class
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  db_parameter_group_name = aws_db_parameter_group.aurora_postgresql.name

  performance_insights_enabled = true
  monitoring_role_arn         = aws_iam_role.rds_enhanced_monitoring.arn
  monitoring_interval         = 60

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-aurora-${count.index}"
  })
}

# =============================================================================
# ElastiCache Redis
# =============================================================================

# Redis子网组
resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.project}-${local.environment}-redis-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-redis-subnet-group"
  })
}

# Redis参数组
resource "aws_elasticache_parameter_group" "redis" {
  family = "redis7"
  name   = "${local.project}-${local.environment}-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-redis-params"
  })
}

# Redis复制组
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${local.project}-${local.environment}-redis"
  description                = "Redis cluster for ${local.project} ${local.environment}"

  port                = 6379
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  node_type           = var.redis_instance_type

  num_cache_clusters = var.redis_num_cache_nodes

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token

  snapshot_retention_limit = 7
  snapshot_window         = "07:00-09:00"
  maintenance_window      = "sun:09:00-sun:10:00"

  auto_minor_version_upgrade = true

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-redis"
  })
}

# =============================================================================
# Application Load Balancer
# =============================================================================

# ALB
resource "aws_lb" "main" {
  name               = "${local.project}-${local.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "prod"
  drop_invalid_header_fields = true

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.bucket
    prefix  = "alb-access-logs"
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-alb"
  })
}

# HTTP监听器 (重定向到HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS监听器
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Service Unavailable"
      status_code  = "503"
    }
  }
}

# =============================================================================
# S3存储桶
# =============================================================================

# ALB访问日志存储桶
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "${local.project}-${local.environment}-alb-logs-${random_id.bucket_suffix.hex}"
  force_destroy = var.environment != "prod"

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-alb-logs"
    Type = "logs"
  })
}

# 应用资产存储桶
resource "aws_s3_bucket" "assets" {
  bucket        = "${local.project}-${local.environment}-assets-${random_id.bucket_suffix.hex}"
  force_destroy = var.environment != "prod"

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-assets"
    Type = "assets"
  })
}

# 用户上传存储桶
resource "aws_s3_bucket" "uploads" {
  bucket        = "${local.project}-${local.environment}-uploads-${random_id.bucket_suffix.hex}"
  force_destroy = var.environment != "prod"

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-uploads"
    Type = "uploads"
  })
}

# 备份存储桶
resource "aws_s3_bucket" "backups" {
  bucket        = "${local.project}-${local.environment}-backups-${random_id.bucket_suffix.hex}"
  force_destroy = var.environment != "prod"

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-backups"
    Type = "backups"
  })
}

# =============================================================================
# KMS密钥
# =============================================================================

# 主KMS密钥
resource "aws_kms_key" "main" {
  description             = "KMS key for ${local.project} ${local.environment}"
  deletion_window_in_days = var.environment == "prod" ? 30 : 7
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-kms-key"
  })
}

# KMS密钥别名
resource "aws_kms_alias" "main" {
  name          = "alias/${local.project}-${local.environment}"
  target_key_id = aws_kms_key.main.key_id
}

# =============================================================================
# 随机资源
# =============================================================================

# 存储桶后缀
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# 数据库密码
resource "random_password" "db_password" {
  count = var.db_password == "" ? 1 : 0

  length  = 32
  special = true
}

# Redis认证令牌
resource "random_password" "redis_auth_token" {
  count = var.redis_auth_token == "" ? 1 : 0

  length  = 64
  special = false
}

# =============================================================================
# IAM角色和策略
# =============================================================================

# RDS Enhanced Monitoring角色
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "${local.project}-${local.environment}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# RDS Enhanced Monitoring策略附加
resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ECS任务执行角色
resource "aws_iam_role" "ecs_execution_role" {
  name = "${local.project}-${local.environment}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# ECS任务执行策略
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS任务角色
resource "aws_iam_role" "ecs_task_role" {
  name = "${local.project}-${local.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# =============================================================================
# SSL证书
# =============================================================================

# SSL证书
resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-ssl-cert"
  })
}

# 证书验证
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Route53验证记录
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

# =============================================================================
# 输出变量
# =============================================================================

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "database_subnet_ids" {
  description = "Database subnet IDs"
  value       = aws_subnet.database[*].id
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "ALB zone ID"
  value       = aws_lb.main.zone_id
}

output "aurora_cluster_endpoint" {
  description = "Aurora cluster endpoint"
  value       = aws_rds_cluster.main.endpoint
}

output "aurora_reader_endpoint" {
  description = "Aurora reader endpoint"
  value       = aws_rds_cluster.main.reader_endpoint
}

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.main.configuration_endpoint_address
}

output "kms_key_id" {
  description = "KMS key ID"
  value       = aws_kms_key.main.key_id
}

output "ecs_security_group_id" {
  description = "ECS security group ID"
  value       = aws_security_group.ecs.id
}

output "s3_buckets" {
  description = "S3 bucket names"
  value = {
    alb_logs = aws_s3_bucket.alb_logs.bucket
    assets   = aws_s3_bucket.assets.bucket
    uploads  = aws_s3_bucket.uploads.bucket
    backups  = aws_s3_bucket.backups.bucket
  }
}