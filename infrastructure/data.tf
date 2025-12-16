# Get existing hosted zone (by ID if provided, otherwise by domain name)
data "aws_route53_zone" "main" {
  count   = var.hosted_zone_id != "" ? 1 : 0
  zone_id = var.hosted_zone_id
}

data "aws_route53_zone" "by_name" {
  count = var.hosted_zone_id == "" ? 1 : 0
  name  = local.zone_name
}

# Determine the zone name from domain_name (handle subdomains)
locals {
  # Extract the zone name from domain_name
  # For "epaper.example.com", we want "example.com"
  # For "example.com", we want "example.com"
  domain_parts = split(".", var.domain_name)
  zone_name = length(local.domain_parts) >= 2 ? join(".", slice(local.domain_parts, length(local.domain_parts) - 2, length(local.domain_parts))) : var.domain_name
  
  # Use the appropriate data source
  actual_zone = var.hosted_zone_id != "" ? data.aws_route53_zone.main[0] : data.aws_route53_zone.by_name[0]
}

# Get latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}