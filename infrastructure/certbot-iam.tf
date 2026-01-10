# IAM user for certbot to automatically update Route53 DNS records
# Required for Let's Encrypt DNS-01 challenge automation

resource "aws_iam_user" "certbot" {
  name = "epaper-certbot"
  path = "/service-accounts/"

  tags = merge(var.tags, {
    Purpose = "LetsEncrypt DNS-01 automation"
  })
}

# Policy allowing certbot to create/delete TXT records for ACME challenges
resource "aws_iam_user_policy" "certbot_route53" {
  name = "Route53ACMEChallenge"
  user = aws_iam_user.certbot.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "route53:ListHostedZones",
          "route53:GetChange"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "route53:ChangeResourceRecordSets"
        ]
        Resource = "arn:aws:route53:::hostedzone/${local.actual_zone.zone_id}"
      }
    ]
  })
}

# Access key for certbot container
resource "aws_iam_access_key" "certbot" {
  user = aws_iam_user.certbot.name
}

# Store credentials in a local file that docker-compose can mount
resource "local_sensitive_file" "certbot_credentials" {
  content = <<-EOT
    [default]
    aws_access_key_id = ${aws_iam_access_key.certbot.id}
    aws_secret_access_key = ${aws_iam_access_key.certbot.secret}
  EOT
  filename        = "${path.module}/../config/certbot-aws-credentials"
  file_permission = "0600"
}
