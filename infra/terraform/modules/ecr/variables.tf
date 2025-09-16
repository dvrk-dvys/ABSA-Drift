variable "repository_name" {
  description = "ECR repository name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "lambda_functions_path" {
  description = "Path to Lambda functions directory"
  type        = string
}

variable "ecr_image_tag" {
  description = "ECR image tag"
  type        = string
  default     = "latest"
}