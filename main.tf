terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "ml-pipeline-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "eu-west-2"
    encrypt        = true
    dynamodb_table = "ml-pipeline-tfstate-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ml-pipeline-infra"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

module "model_store" {
  source      = "./modules/s3"
  bucket_name = "ml-pipeline-model-store-${var.environment}"
  environment = var.environment
}

module "compute" {
  source          = "./modules/ec2"
  environment     = var.environment
  instance_type   = var.instance_type
  model_bucket_arn = module.model_store.bucket_arn
}
