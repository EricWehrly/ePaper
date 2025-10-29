# Security Group for Inlets Server
resource "aws_security_group" "inlets_server" {
  name        = "epaper-inlets-server-sg"
  description = "Security group for inlets server"
  # Uses default VPC (no vpc_id needed)

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Inlets control plane (secure)
  # TODO: Verify inlets server port configuration and nginx proxy setup
  # Current setup: inlets server on 8123 (control), nginx proxies 443->8080 (data)
  # Need to confirm: Does inlets expose data tunnel on 8080 or different port?
  # Consider: Route inlets control through nginx WSS proxy on 443 for better security
  ingress {
    from_port   = 8123
    to_port     = 8123
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # This will be secured with the token
  }

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "epaper-inlets-server-sg"
  })
}