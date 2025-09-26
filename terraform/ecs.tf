# =============================================================================
# Claude Enhancer 5.1 ECS服务配置
# 微服务容器化部署
# =============================================================================

# =============================================================================
# ECS集群
# =============================================================================

resource "aws_ecs_cluster" "main" {
  name = "${local.project}-${local.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 1
  }

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-ecs-cluster"
  })
}

# ECS集群容量提供商
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }

  default_capacity_provider_strategy {
    base              = 0
    weight            = var.enable_spot_instances ? 50 : 0
    capacity_provider = "FARGATE_SPOT"
  }
}

# =============================================================================
# CloudWatch日志组
# =============================================================================

resource "aws_cloudwatch_log_group" "ecs_services" {
  for_each = var.ecs_services

  name              = "/ecs/${local.project}-${local.environment}-${each.key}"
  retention_in_days = var.log_retention_days
  kms_key_id       = aws_kms_key.main.arn

  tags = merge(local.common_tags, {
    Name    = "${local.project}-${local.environment}-${each.key}-logs"
    Service = each.key
  })
}

# =============================================================================
# ECR仓库
# =============================================================================

resource "aws_ecr_repository" "services" {
  for_each = var.ecs_services

  name                 = "${local.project}/${each.key}-service"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key        = aws_kms_key.main.arn
  }

  tags = merge(local.common_tags, {
    Name    = "${local.project}-${each.key}-service"
    Service = each.key
  })
}

# ECR生命周期策略
resource "aws_ecr_lifecycle_policy" "services" {
  for_each = aws_ecr_repository.services

  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["prod-"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 5 staging images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["staging-"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Expire untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# =============================================================================
# ECS任务定义
# =============================================================================

resource "aws_ecs_task_definition" "services" {
  for_each = var.ecs_services

  family                   = "${local.project}-${local.environment}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = each.value.cpu
  memory                  = each.value.memory

  execution_role_arn = aws_iam_role.ecs_execution_role.arn
  task_role_arn      = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "${each.key}-service"
      image = "${aws_ecr_repository.services[each.key].repository_url}:latest"

      portMappings = [
        {
          containerPort = each.value.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        for key, value in merge(each.value.environment_variables, {
          AWS_REGION                = var.aws_region
          AWS_DEFAULT_REGION        = var.aws_region
          ENVIRONMENT              = local.environment
          DATABASE_URL             = "postgresql://postgres:${var.db_password == "" ? random_password.db_password[0].result : var.db_password}@${aws_rds_cluster.main.endpoint}:5432/claude_enhancer"
          REDIS_URL                = "redis://:${var.redis_auth_token == "" ? random_password.redis_auth_token[0].result : var.redis_auth_token}@${aws_elasticache_replication_group.main.configuration_endpoint_address}:6379"
          JWT_SECRET_KEY           = aws_secretsmanager_secret_version.jwt_secret.secret_string
          ENCRYPTION_KEY           = aws_secretsmanager_secret_version.encryption_key.secret_string
          S3_ASSETS_BUCKET         = aws_s3_bucket.assets.bucket
          S3_UPLOADS_BUCKET        = aws_s3_bucket.uploads.bucket
          S3_BACKUPS_BUCKET        = aws_s3_bucket.backups.bucket
          KMS_KEY_ID               = aws_kms_key.main.key_id
        }) : {
          name  = key
          value = tostring(value)
        }
      ]

      secrets = [
        {
          name      = "DATABASE_PASSWORD"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        },
        {
          name      = "REDIS_AUTH_TOKEN"
          valueFrom = aws_secretsmanager_secret.redis_token.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_services[each.key].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:${each.value.container_port}${each.value.health_check_path} || exit 1"
        ]
        interval    = each.value.health_check_interval
        timeout     = each.value.health_check_timeout
        retries     = 3
        startPeriod = 60
      }

      essential = true

      # 资源限制
      ulimits = [
        {
          name      = "nofile"
          softLimit = 65536
          hardLimit = 65536
        }
      ]
    }
  ])

  tags = merge(local.common_tags, {
    Name    = "${local.project}-${local.environment}-${each.key}-task"
    Service = each.key
  })
}

# =============================================================================
# ALB目标组
# =============================================================================

resource "aws_lb_target_group" "services" {
  for_each = var.ecs_services

  name        = "${local.project}-${local.environment}-${each.key}-tg"
  port        = each.value.container_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = each.value.health_check_timeout
    interval            = each.value.health_check_interval
    path                = each.value.health_check_path
    matcher             = "200"
    protocol            = "HTTP"
    port                = "traffic-port"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = false
  }

  tags = merge(local.common_tags, {
    Name    = "${local.project}-${local.environment}-${each.key}-tg"
    Service = each.key
  })

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# ALB监听器规则
# =============================================================================

resource "aws_lb_listener_rule" "services" {
  for_each = var.ecs_services

  listener_arn = aws_lb_listener.https.arn
  priority     = 100 + index(keys(var.ecs_services), each.key)

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services[each.key].arn
  }

  condition {
    path_pattern {
      values = [
        each.key == "auth" ? "/api/v1/auth*" :
        each.key == "core" ? "/api/core*" :
        each.key == "agent" ? "/api/agents*" :
        each.key == "workflow" ? "/api/workflow*" :
        "/${each.key}*"
      ]
    }
  }

  tags = merge(local.common_tags, {
    Name    = "${local.project}-${local.environment}-${each.key}-rule"
    Service = each.key
  })
}

# =============================================================================
# ECS服务
# =============================================================================

resource "aws_ecs_service" "services" {
  for_each = var.ecs_services

  name            = "${local.project}-${local.environment}-${each.key}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.services[each.key].arn
  desired_count   = each.value.desired_count
  launch_type     = "FARGATE"

  platform_version = "LATEST"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.services[each.key].arn
    container_name   = "${each.key}-service"
    container_port   = each.value.container_port
  }

  # 部署配置
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  # 服务发现
  service_registries {
    registry_arn = aws_service_discovery_service.services[each.key].arn
  }

  # 启用执行命令
  enable_execute_command = var.environment != "prod"

  tags = merge(local.common_tags, {
    Name    = "${local.project}-${local.environment}-${each.key}-service"
    Service = each.key
  })

  depends_on = [
    aws_lb_listener.https,
    aws_lb_target_group.services
  ]

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# =============================================================================
# 服务发现
# =============================================================================

resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "${local.project}-${local.environment}.local"
  vpc  = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-namespace"
  })
}

resource "aws_service_discovery_service" "services" {
  for_each = var.ecs_services

  name = each.key

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_grace_period_seconds = 30

  tags = merge(local.common_tags, {
    Name    = "${local.project}-${local.environment}-${each.key}-discovery"
    Service = each.key
  })
}

# =============================================================================
# Auto Scaling
# =============================================================================

resource "aws_appautoscaling_target" "ecs_services" {
  for_each = var.ecs_services

  max_capacity       = each.value.max_capacity
  min_capacity       = each.value.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.services[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = merge(local.common_tags, {
    Name    = "${local.project}-${local.environment}-${each.key}-scaling-target"
    Service = each.key
  })
}

# CPU扩展策略
resource "aws_appautoscaling_policy" "ecs_cpu" {
  for_each = var.ecs_services

  name               = "${local.project}-${local.environment}-${each.key}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_services[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_services[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_services[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.auto_scaling_config.cpu_target_percentage
    scale_in_cooldown  = var.auto_scaling_config.scale_in_cooldown
    scale_out_cooldown = var.auto_scaling_config.scale_out_cooldown
  }
}

# 内存扩展策略
resource "aws_appautoscaling_policy" "ecs_memory" {
  for_each = var.ecs_services

  name               = "${local.project}-${local.environment}-${each.key}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_services[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_services[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_services[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = var.auto_scaling_config.memory_target_percentage
    scale_in_cooldown  = var.auto_scaling_config.scale_in_cooldown
    scale_out_cooldown = var.auto_scaling_config.scale_out_cooldown
  }
}

# ALB请求数扩展策略
resource "aws_appautoscaling_policy" "ecs_requests" {
  for_each = var.ecs_services

  name               = "${local.project}-${local.environment}-${each.key}-requests-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_services[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_services[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_services[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label        = "${aws_lb.main.arn_suffix}/${aws_lb_target_group.services[each.key].arn_suffix}"
    }
    target_value       = var.auto_scaling_config.requests_per_target
    scale_in_cooldown  = var.auto_scaling_config.scale_in_cooldown
    scale_out_cooldown = var.auto_scaling_config.scale_out_cooldown
  }
}

# =============================================================================
# Secrets Manager
# =============================================================================

# 数据库密码密钥
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${local.project}-${local.environment}-db-password"
  description             = "Database password for ${local.project} ${local.environment}"
  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-db-password"
    Type = "database-credential"
  })
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password == "" ? random_password.db_password[0].result : var.db_password
}

# Redis认证令牌密钥
resource "aws_secretsmanager_secret" "redis_token" {
  name                    = "${local.project}-${local.environment}-redis-token"
  description             = "Redis auth token for ${local.project} ${local.environment}"
  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-redis-token"
    Type = "cache-credential"
  })
}

resource "aws_secretsmanager_secret_version" "redis_token" {
  secret_id     = aws_secretsmanager_secret.redis_token.id
  secret_string = var.redis_auth_token == "" ? random_password.redis_auth_token[0].result : var.redis_auth_token
}

# JWT密钥
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${local.project}-${local.environment}-jwt-secret"
  description             = "JWT secret key for ${local.project} ${local.environment}"
  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-jwt-secret"
    Type = "application-secret"
  })
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}

# 应用加密密钥
resource "aws_secretsmanager_secret" "encryption_key" {
  name                    = "${local.project}-${local.environment}-encryption-key"
  description             = "Application encryption key for ${local.project} ${local.environment}"
  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-encryption-key"
    Type = "encryption-key"
  })
}

resource "aws_secretsmanager_secret_version" "encryption_key" {
  secret_id     = aws_secretsmanager_secret.encryption_key.id
  secret_string = random_password.encryption_key.result
}

# 随机密码生成
resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "random_password" "encryption_key" {
  length  = 64
  special = false
}

# =============================================================================
# 输出变量
# =============================================================================

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_services" {
  description = "ECS service names"
  value       = { for k, v in aws_ecs_service.services : k => v.name }
}

output "ecr_repositories" {
  description = "ECR repository URLs"
  value       = { for k, v in aws_ecr_repository.services : k => v.repository_url }
}

output "target_groups" {
  description = "ALB target group ARNs"
  value       = { for k, v in aws_lb_target_group.services : k => v.arn }
}

output "service_discovery_namespace" {
  description = "Service discovery namespace"
  value       = aws_service_discovery_private_dns_namespace.main.name
}