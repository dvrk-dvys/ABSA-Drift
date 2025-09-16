resource "aws_s3_bucket" "data_bucket" {
  bucket = var.data_bucket_name
}

resource "aws_s3_bucket_public_access_block" "data_bucket_pab" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "data_bucket_acl_ownership" {
  bucket = aws_s3_bucket.data_bucket.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "data_bucket_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.data_bucket_acl_ownership,
    aws_s3_bucket_public_access_block.data_bucket_pab,
  ]

  bucket = aws_s3_bucket.data_bucket.id
  acl    = "private"
}

resource "aws_s3_bucket" "model_bucket" {
  bucket = var.model_bucket_name
}

resource "aws_s3_bucket_public_access_block" "model_bucket_pab" {
  bucket = aws_s3_bucket.model_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "model_bucket_acl_ownership" {
  bucket = aws_s3_bucket.model_bucket.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "model_bucket_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.model_bucket_acl_ownership,
    aws_s3_bucket_public_access_block.model_bucket_pab,
  ]

  bucket = aws_s3_bucket.model_bucket.id
  acl    = "private"
}