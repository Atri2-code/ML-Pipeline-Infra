resource "aws_s3_bucket" "model_store" {
  bucket        = var.bucket_name
  force_destroy = var.environment != "production"
}

resource "aws_s3_bucket_versioning" "model_store" {
  bucket = aws_s3_bucket.model_store.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "model_store" {
  bucket = aws_s3_bucket.model_store.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "model_store" {
  bucket = aws_s3_bucket.model_store.id
  rule {
    id     = "archive-old-models"
    status = "Enabled"
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "model_store" {
  bucket                  = aws_s3_bucket.model_store.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

variable "bucket_name" { type = string }
variable "environment" { type = string }

output "bucket_name" { value = aws_s3_bucket.model_store.bucket }
output "bucket_arn"  { value = aws_s3_bucket.model_store.arn }
