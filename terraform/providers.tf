terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "general_account"
  region = "us-east-1"

  assume_role {
    role_arn     = "arn:aws:iam::246773436783:role/Route53DNSRecordsManagerFromProduction"
    session_name = "TerraformCrossAccountSession"
  }
}