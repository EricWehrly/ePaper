terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.1"
    }
  }  # Uncomment and configure for remote state storage
  # To migrate to remote state, uncomment and update the backend block below.
  # NOTE: We're currently committing local state temporarily. Migrate to S3
  # (with server-side encryption) as soon as practical and then remove
  # the local state files from the repository.
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "epaper/inlets/terraform.tfstate"
  #   region = "us-east-1"
  #   encrypt = true
  # }
}

provider "aws" {
  region = var.aws_region
}