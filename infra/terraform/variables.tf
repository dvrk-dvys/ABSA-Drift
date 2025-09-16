variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (staging, prod)"
  type        = string
  default     = "dev"
}


variable "eventbridge_schedule" {
  description = "EventBridge hourly trigger"
  type        = string
  default     = "rate(1 hour)"
}

variable "sns_alert_email" {
  description = "Email address for SNS alerts"
  type        = string
  default     = ""
}

variable "project_id" {
  description = "Project identifier for resource naming"
  type        = string
}

