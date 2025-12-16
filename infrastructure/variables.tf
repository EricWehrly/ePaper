variable "domain_name" {
  description = "The domain name for the Chisel tunnel (e.g., epaper.yourdomain.com)"
  type        = string
  validation {
    condition     = length(regexall("[A-Za-z0-9.-]+\\.[A-Za-z]{2,}", var.domain_name)) > 0
    error_message = "domain_name must be a valid domain (e.g., epaper.example.com)"
  }
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID for the domain (leave empty to auto-discover from domain_name)"
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type for the Chisel server"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "AWS key pair name for EC2 SSH access (optional - SSM Session Manager is also available)"
  type        = string
  default     = null
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH to the instance"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict this to your IP ranges for security
}

variable "chisel_auth" {
  description = "Authentication credential for Chisel tunnel (leave empty to auto-generate)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "generate_client_config" {
  description = "Generate Chisel client configuration files (.env.chisel) in the project root"
  type        = bool
  default     = false
}

variable "enable_certbot_staging" {
  description = "Use Let's Encrypt staging environment to avoid hitting production rate limits while testing"
  type        = bool
  default     = true
}

variable "use_letsencrypt_s3" {
  description = "Enable S3 caching for Let's Encrypt certificates (recommended to avoid rate limits)"
  type        = bool
  default     = true
}

variable "chisel_upstream" {
  description = "Upstream target for Chisel client (where your ePaper app runs)"
  type        = string
  default     = "http://epaper-display:80"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "ePaper"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}