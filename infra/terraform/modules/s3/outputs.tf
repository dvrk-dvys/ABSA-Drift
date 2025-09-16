output "data_bucket_name" {
  description = "Name of the data bucket"
  value       = aws_s3_bucket.data_bucket.bucket
}

output "data_bucket_arn" {
  description = "ARN of the data bucket"
  value       = aws_s3_bucket.data_bucket.arn
}

output "model_bucket_name" {
  description = "Name of the model bucket"
  value       = aws_s3_bucket.model_bucket.bucket
}

output "model_bucket_arn" {
  description = "ARN of the model bucket"
  value       = aws_s3_bucket.model_bucket.arn
}