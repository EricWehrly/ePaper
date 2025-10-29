# Generate secure inlets token if not provided
resource "random_password" "inlets_token" {
  count   = var.inlets_token == "" ? 1 : 0
  length  = 64
  special = false
}

# Create user data script for inlets server setup
locals {
  # Use provided token or generate one
  actual_inlets_token = var.inlets_token != "" ? var.inlets_token : random_password.inlets_token[0].result
  
  user_data = base64encode(templatefile("${path.module}/templates/inlets-server-init.sh", {
    inlets_token = local.actual_inlets_token
    domain_name  = var.domain_name
  }))
}

# EC2 Instance for Inlets Server
resource "aws_instance" "inlets_server" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  subnet_id              = aws_subnet.inlets_public.id
  vpc_security_group_ids = [aws_security_group.inlets_server.id]
  iam_instance_profile   = aws_iam_instance_profile.inlets_server.name
  
  user_data = local.user_data

  tags = merge(var.tags, {
    Name = "epaper-inlets-server"
  })

  # Ensure we have a new instance if user data changes
  user_data_replace_on_change = true
}# Elastic IP for stable public IP
resource "aws_eip" "inlets_server" {
  instance = aws_instance.inlets_server.id
  domain   = "vpc"

  tags = merge(var.tags, {
    Name = "epaper-inlets-server-eip"
  })

  depends_on = [aws_internet_gateway.inlets_igw]
}

# Generate inlets client configuration (optional)
resource "local_file" "inlets_client_env" {
  count = var.generate_client_config ? 1 : 0
  
  filename = "${path.module}/.env.inlets"
  content = templatefile("${path.module}/templates/env.inlets.tpl", {
    domain_name  = var.domain_name
    inlets_token = local.actual_inlets_token
    upstream     = var.inlets_upstream
  })
  
  file_permission = "0600"  # Secure permissions for sensitive file
}