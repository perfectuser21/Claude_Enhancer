# =============================================================================
# Terraform Networking Module Outputs
# Output values for use by other modules
# =============================================================================

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "vpc_arn" {
  description = "ARN of the VPC"
  value       = aws_vpc.main.arn
}

# Internet Gateway
output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# Availability Zones
output "availability_zones" {
  description = "List of availability zones used"
  value       = slice(data.aws_availability_zones.available.names, 0, local.az_count)
}

# Public Subnets
output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "public_subnet_cidrs" {
  description = "List of public subnet CIDR blocks"
  value       = aws_subnet.public[*].cidr_block
}

output "public_subnet_arns" {
  description = "List of public subnet ARNs"
  value       = aws_subnet.public[*].arn
}

# Private Subnets
output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks"
  value       = aws_subnet.private[*].cidr_block
}

output "private_subnet_arns" {
  description = "List of private subnet ARNs"
  value       = aws_subnet.private[*].arn
}

# Database Subnets
output "database_subnet_ids" {
  description = "List of database subnet IDs"
  value       = aws_subnet.database[*].id
}

output "database_subnet_cidrs" {
  description = "List of database subnet CIDR blocks"
  value       = aws_subnet.database[*].cidr_block
}

output "database_subnet_arns" {
  description = "List of database subnet ARNs"
  value       = aws_subnet.database[*].arn
}

# NAT Gateways
output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_public_ips" {
  description = "List of NAT Gateway public IPs"
  value       = aws_eip.nat[*].public_ip
}

# Route Tables
output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "List of private route table IDs"
  value       = aws_route_table.private[*].id
}

output "database_route_table_id" {
  description = "ID of the database route table"
  value       = aws_route_table.database.id
}

# VPC Endpoints
output "s3_vpc_endpoint_id" {
  description = "ID of the S3 VPC endpoint"
  value       = var.enable_s3_endpoint ? aws_vpc_endpoint.s3[0].id : null
}

output "ecr_api_vpc_endpoint_id" {
  description = "ID of the ECR API VPC endpoint"
  value       = var.enable_ecr_endpoints ? aws_vpc_endpoint.ecr_api[0].id : null
}

output "ecr_dkr_vpc_endpoint_id" {
  description = "ID of the ECR DKR VPC endpoint"
  value       = var.enable_ecr_endpoints ? aws_vpc_endpoint.ecr_dkr[0].id : null
}

output "vpc_endpoints_security_group_id" {
  description = "Security group ID for VPC endpoints"
  value       = var.enable_ecr_endpoints ? aws_security_group.vpc_endpoints[0].id : null
}

# Flow Logs
output "vpc_flow_log_id" {
  description = "ID of the VPC Flow Log"
  value       = var.enable_flow_logs ? aws_flow_log.vpc[0].id : null
}

output "vpc_flow_log_cloudwatch_log_group_name" {
  description = "Name of the CloudWatch Log Group for VPC Flow Logs"
  value       = var.enable_flow_logs ? aws_cloudwatch_log_group.vpc_flow_logs[0].name : null
}

# Network Configuration Summary
output "network_configuration" {
  description = "Summary of network configuration"
  value = {
    vpc_id                = aws_vpc.main.id
    vpc_cidr              = aws_vpc.main.cidr_block
    availability_zones    = slice(data.aws_availability_zones.available.names, 0, local.az_count)
    public_subnets        = aws_subnet.public[*].cidr_block
    private_subnets       = aws_subnet.private[*].cidr_block
    database_subnets      = aws_subnet.database[*].cidr_block
    nat_gateways_count    = var.single_nat_gateway ? 1 : local.az_count
    flow_logs_enabled     = var.enable_flow_logs
    s3_endpoint_enabled   = var.enable_s3_endpoint
    ecr_endpoints_enabled = var.enable_ecr_endpoints
  }
}

# For use with other AWS services
output "db_subnet_group_subnet_ids" {
  description = "Subnet IDs for database subnet groups"
  value       = aws_subnet.database[*].id
}

output "alb_subnet_ids" {
  description = "Subnet IDs for Application Load Balancer"
  value       = aws_subnet.public[*].id
}

output "ecs_subnet_ids" {
  description = "Subnet IDs for ECS services"
  value       = aws_subnet.private[*].id
}

# Cost optimization information
output "cost_optimization_applied" {
  description = "Cost optimization settings applied"
  value = {
    single_nat_gateway      = var.single_nat_gateway
    nat_gateway_count      = var.single_nat_gateway ? 1 : local.az_count
    estimated_nat_cost_usd = var.single_nat_gateway ? 32 : (32 * local.az_count)
    flow_logs_enabled      = var.enable_flow_logs
    vpc_endpoints_enabled  = var.enable_s3_endpoint || var.enable_ecr_endpoints
  }
}