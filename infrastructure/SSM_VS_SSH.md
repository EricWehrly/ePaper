# SSM Session Manager Access

## Overview
This infrastructure uses AWS Systems Manager (SSM) Session Manager for secure server access without traditional SSH keys. SSM provides better security, auditing, and eliminates the need to manage SSH keys.

## What's Configured

### IAM Roles and Policies
- ✅ **AmazonSSMManagedInstanceCore** - Enables SSM Session Manager
- ✅ **CloudWatchAgentServerPolicy** - Enables centralized logging
- ✅ Instance profile attached to EC2 instance

### Security Groups
- ✅ **HTTP/HTTPS (80/443)** - Public access for the web service
- ✅ **Chisel control (8080)** - Public access with authentication
- ✅ **SSH (port 22)** - Optional, restricted by `allowed_ssh_cidrs` if `key_name` is provided

### Instance Configuration
- ✅ **SSM Agent** - Pre-installed on Amazon Linux 2 AMI
- ✅ **IAM instance profile** - Attached for SSM permissions

## SSM Session Manager Benefits

- **No SSH keys to manage** - Uses IAM for authentication
- **Full audit trail** - All session activity logged to CloudWatch
- **No direct network access required** - Works through AWS APIs
- **MFA support** - Can require MFA for session access
- **Port forwarding** - Can tunnel specific ports securely
- **No inbound firewall rules** - Agent initiates outbound connections only

## Connection Commands

### Basic Shell Session
```bash
# Connect to the instance
aws ssm start-session --target INSTANCE_ID --region us-east-1

# Get instance ID from Terraform output  
aws ssm start-session --target $(terraform output -raw chisel_server_instance_id) --region us-east-1
```

### Port Forwarding
```bash
# Forward local port 8080 to remote port 80
aws ssm start-session --target INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["80"],"localPortNumber":["8080"]}' \
  --region us-east-1
```

### Using Terraform Output
```bash
# The ssm_connection output provides the exact command
eval $(terraform output -raw ssm_connection)
```

## Additional SSM Features (Optional)

### Session Logging to S3
Add comprehensive session logging:
```terraform
resource "aws_iam_role_policy" "ssm_s3_logging" {
  name = "SSMSessionLogging"
  role = aws_iam_role.chisel_server.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetEncryptionConfiguration"
        ]
        Resource = "arn:aws:s3:::your-ssm-logs-bucket/*"
      }
    ]
  })
}
```

### Session Manager Preferences
Configure organization-wide session settings:
```terraform
resource "aws_ssm_document" "session_manager_prefs" {
  name          = "SSM-SessionManagerRunShell"
  document_type = "Session"
  document_format = "JSON"

  content = jsonencode({
    schemaVersion = "1.0"
    description   = "Regional settings for Session Manager"
    sessionType   = "Standard_Stream"
    inputs = {
      s3BucketName                = "your-ssm-logs-bucket"
      s3KeyPrefix                 = "session-logs/"
      s3EncryptionEnabled         = true
      cloudWatchLogGroupName      = "/aws/ssm/sessions"
      cloudWatchEncryptionEnabled = true
      idleSessionTimeout          = "20"
      maxSessionDuration          = "60"
      runAsEnabled                = false
      runAsDefaultUser            = "ec2-user"
      shellProfile = {
        linux = "cd /home/ec2-user && exec /bin/bash"
      }
    }
  })
}
```

## SSH Fallback (Optional)

SSH access is available if you provide a `key_name` in `terraform.tfvars`:
```hcl
key_name = "your-aws-key-pair-name"
```

This is useful for:
- Emergency access if SSM is unavailable
- Tools that specifically require SSH (scp, rsync, etc.)
- Development workflows that depend on SSH