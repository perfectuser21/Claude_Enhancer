# =============================================================================
# Terraform Configuration for Claude Enhancer Claude Enhancer Infrastructure
# Multi-cloud infrastructure as code with AWS EKS primary deployment
# =============================================================================

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "perfect21-terraform-state"
    key            = "claude-enhancer/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "perfect21-terraform-locks"
  }
}

# =============================================================================
# Variables
# =============================================================================

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "cluster_version" {
  description = "Kubernetes cluster version"
  type        = string
  default     = "1.28"
}

variable "node_instance_types" {
  description = "EC2 instance types for worker nodes"
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

variable "min_node_count" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 2
}

variable "max_node_count" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
}

variable "desired_node_count" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring stack"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable automated backup solutions"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "claude-enhancer.perfect21.dev"
}

# =============================================================================
# Local Values
# =============================================================================

locals {
  name_prefix = "claude-enhancer-${var.environment}"

  common_tags = {
    Project     = "Claude Enhancer"
    Application = "Claude-Enhancer"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "DevOps-Team"
  }

  # Environment-specific configurations
  env_config = {
    development = {
      instance_types    = ["t3.small"]
      min_nodes        = 1
      max_nodes        = 3
      desired_nodes    = 2
      db_instance_class = "db.t3.micro"
      redis_node_type   = "cache.t3.micro"
    }
    staging = {
      instance_types    = ["t3.medium"]
      min_nodes        = 2
      max_nodes        = 5
      desired_nodes    = 3
      db_instance_class = "db.t3.small"
      redis_node_type   = "cache.t3.small"
    }
    production = {
      instance_types    = ["t3.large", "t3.xlarge"]
      min_nodes        = 3
      max_nodes        = 15
      desired_nodes    = 5
      db_instance_class = "db.r6g.large"
      redis_node_type   = "cache.r6g.large"
    }
  }
}

# =============================================================================
# Data Sources
# =============================================================================

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# =============================================================================
# VPC and Networking
# =============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
    "kubernetes.io/cluster/${local.name_prefix}" = "shared"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 3

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-${count.index + 1}"
    Type = "public"
    "kubernetes.io/cluster/${local.name_prefix}" = "shared"
    "kubernetes.io/role/elb" = "1"
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 3

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-${count.index + 1}"
    Type = "private"
    "kubernetes.io/cluster/${local.name_prefix}" = "owned"
    "kubernetes.io/role/internal-elb" = "1"
  })
}

# NAT Gateways
resource "aws_eip" "nat" {
  count = 3

  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-eip-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  count = 3

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt"
  })
}

resource "aws_route_table" "private" {
  count = 3

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-rt-${count.index + 1}"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = 3

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = 3

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# =============================================================================
# EKS Cluster
# =============================================================================

resource "aws_iam_role" "cluster" {
  name = "${local.name_prefix}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "cluster_amazon_eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}

resource "aws_eks_cluster" "main" {
  name     = local.name_prefix
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  # Enable logging
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Encryption
  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }

  tags = local.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.cluster_amazon_eks_cluster_policy,
    aws_cloudwatch_log_group.cluster
  ]
}

# =============================================================================
# EKS Node Groups
# =============================================================================

resource "aws_iam_role" "node_group" {
  name = "${local.name_prefix}-node-group-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "node_group_amazon_eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_amazon_eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_amazon_ec2_container_registry_read_only" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_group.name
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${local.name_prefix}-node-group"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = local.env_config[var.environment].instance_types
  capacity_type  = "ON_DEMAND"

  scaling_config {
    desired_size = local.env_config[var.environment].desired_nodes
    max_size     = local.env_config[var.environment].max_nodes
    min_size     = local.env_config[var.environment].min_nodes
  }

  update_config {
    max_unavailable = 1
  }

  # User data for additional configuration
  launch_template {
    id      = aws_launch_template.node_group.id
    version = "$Latest"
  }

  tags = local.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.node_group_amazon_eks_worker_node_policy,
    aws_iam_role_policy_attachment.node_group_amazon_eks_cni_policy,
    aws_iam_role_policy_attachment.node_group_amazon_ec2_container_registry_read_only,
  ]
}

# =============================================================================
# Launch Template for Node Group
# =============================================================================

resource "aws_launch_template" "node_group" {
  name_prefix = "${local.name_prefix}-node-"

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 50
      volume_type           = "gp3"
      iops                  = 3000
      throughput            = 125
      encrypted             = true
      kms_key_id            = aws_kms_key.ebs.arn
      delete_on_termination = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(local.common_tags, {
      Name = "${local.name_prefix}-node"
    })
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    cluster_name = aws_eks_cluster.main.name
  }))
}

# =============================================================================
# KMS Keys
# =============================================================================

resource "aws_kms_key" "eks" {
  description             = "EKS encryption key for ${local.name_prefix}"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-eks-key"
  })
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${local.name_prefix}-eks"
  target_key_id = aws_kms_key.eks.key_id
}

resource "aws_kms_key" "ebs" {
  description             = "EBS encryption key for ${local.name_prefix}"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ebs-key"
  })
}

resource "aws_kms_alias" "ebs" {
  name          = "alias/${local.name_prefix}-ebs"
  target_key_id = aws_kms_key.ebs.key_id
}

# =============================================================================
# CloudWatch Log Groups
# =============================================================================

resource "aws_cloudwatch_log_group" "cluster" {
  name              = "/aws/eks/${local.name_prefix}/cluster"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.eks.arn

  tags = local.common_tags
}

# =============================================================================
# Outputs
# =============================================================================

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

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