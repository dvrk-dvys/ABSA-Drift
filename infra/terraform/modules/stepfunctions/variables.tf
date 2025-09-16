variable "state_machine_name" {
  description = "Step Functions state machine name"
  type        = string
}

variable "step_functions_role_name" {
  description = "Step Functions IAM role name"
  type        = string
}

variable "step_functions_policy_name" {
  description = "Step Functions IAM policy name"
  type        = string
}

variable "lambda_extract_arn" {
  description = "ARN of the extract Lambda function"
  type        = string
}

variable "lambda_transform_arn" {
  description = "ARN of the transform Lambda function"
  type        = string
}

variable "lambda_monitor_arn" {
  description = "ARN of the monitor Lambda function"
  type        = string
}

variable "lambda_alert_arn" {
  description = "ARN of the alert Lambda function"
  type        = string
}