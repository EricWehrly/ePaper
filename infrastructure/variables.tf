variable "domain_name" {
  description = "The domain name for the inlets tunnel (e.g., epaper.yourdomain.com)"
  type        = string
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
  description = "EC2 instance type for the inlets server"
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

variable "inlets_token" {
  description = "Authentication token for inlets tunnel (leave empty to auto-generate)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "generate_client_config" {
  description = "Generate inlets client configuration files (.env.inlets) in the project root"
  type        = bool
  default     = false
}

variable "inlets_upstream" {
  description = "Upstream target for inlets client (where your ePaper app runs)"
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