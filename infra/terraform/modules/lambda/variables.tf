variable "extract_function_name" {
  description = "Extract Lambda function name"
  type        = string
}

variable "transform_function_name" {
  description = "Transform Lambda function name"
  type        = string
}

variable "monitor_function_name" {
  description = "Monitor Lambda function name"
  type        = string
}

variable "alert_function_name" {
  description = "Alert Lambda function name"
  type        = string
}

variable "lambda_role_name" {
  description = "Lambda IAM role name"
  type        = string
}

variable "lambda_policy_name" {
  description = "Lambda IAM policy name"
  type        = string
}

variable "extract_image_uri" {
  description = "ECR image URI for extract Lambda"
  type        = string
}

variable "transform_image_uri" {
  description = "ECR image URI for transform Lambda"
  type        = string
}

variable "monitor_image_uri" {
  description = "ECR image URI for monitor Lambda"
  type        = string
}

variable "alert_image_uri" {
  description = "ECR image URI for alert Lambda"
  type        = string
}

variable "s3_data_bucket" {
  description = "S3 bucket name for data storage"
  type        = string
}

variable "s3_model_bucket" {
  description = "S3 bucket name for model storage"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for notifications"
  type        = string
}