# VPC and Networking
resource "aws_vpc" "inlets_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "epaper-inlets-vpc"
  })
}

resource "aws_internet_gateway" "inlets_igw" {
  vpc_id = aws_vpc.inlets_vpc.id

  tags = merge(var.tags, {
    Name = "epaper-inlets-igw"
  })
}

resource "aws_subnet" "inlets_public" {
  vpc_id                  = aws_vpc.inlets_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "epaper-inlets-public-subnet"
  })
}

resource "aws_route_table" "inlets_public" {
  vpc_id = aws_vpc.inlets_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.inlets_igw.id
  }

  tags = merge(var.tags, {
    Name = "epaper-inlets-public-rt"
  })
}

resource "aws_route_table_association" "inlets_public" {
  subnet_id      = aws_subnet.inlets_public.id
  route_table_id = aws_route_table.inlets_public.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Endpoints for SSM (optional - allows SSM without internet access)
# Uncomment these if you want to use SSM without requiring internet gateway

# resource "aws_vpc_endpoint" "ssm" {
#   vpc_id              = aws_vpc.inlets_vpc.id
#   service_name        = "com.amazonaws.${var.aws_region}.ssm"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = [aws_subnet.inlets_public.id]
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true
#   tags = merge(var.tags, { Name = "epaper-ssm-endpoint" })
# }

# resource "aws_vpc_endpoint" "ssm_messages" {
#   vpc_id              = aws_vpc.inlets_vpc.id
#   service_name        = "com.amazonaws.${var.aws_region}.ssmmessages"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = [aws_subnet.inlets_public.id]
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true
#   tags = merge(var.tags, { Name = "epaper-ssm-messages-endpoint" })
# }

# resource "aws_vpc_endpoint" "ec2_messages" {
#   vpc_id              = aws_vpc.inlets_vpc.id
#   service_name        = "com.amazonaws.${var.aws_region}.ec2messages"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = [aws_subnet.inlets_public.id]
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true
#   tags = merge(var.tags, { Name = "epaper-ec2-messages-endpoint" })
# }