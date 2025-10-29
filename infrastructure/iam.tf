# IAM role for EC2 instance with SSM access
resource "aws_iam_role" "inlets_server" {
  name = "epaper-inlets-server-role"

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

  tags = var.tags
}

# Attach SSM managed policy for Session Manager
resource "aws_iam_role_policy_attachment" "ssm_managed_instance" {
  role       = aws_iam_role.inlets_server.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach CloudWatch agent policy for logs
resource "aws_iam_role_policy_attachment" "cloudwatch_agent" {
  role       = aws_iam_role.inlets_server.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Instance profile for the EC2 instance
resource "aws_iam_instance_profile" "inlets_server" {
  name = "epaper-inlets-server-profile"
  role = aws_iam_role.inlets_server.name

  tags = var.tags
}