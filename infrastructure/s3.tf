// S3 bucket to cache Let's Encrypt certificates so we don't re-request on every instance replacement
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "letsencrypt" {
  bucket = "epaper-letsencrypt-${replace(var.domain_name, ".", "-")}-${data.aws_caller_identity.current.account_id}"
  acl    = "private"

  versioning {
    enabled = true
  }


  tags = var.tags
}

# Inline policy to allow EC2 instance role to Get/Put the cert bundle
resource "aws_iam_role_policy" "letsencrypt_s3_access" {
  name = "epaper-letsencrypt-s3-access"
  role = aws_iam_role.chisel_server.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        Resource = ["${aws_s3_bucket.letsencrypt.arn}/*"]
      },
      {
        Effect = "Allow",
        Action = [
          "s3:ListBucket"
        ],
        Resource = ["${aws_s3_bucket.letsencrypt.arn}"]
      }
    ]
  })
}
