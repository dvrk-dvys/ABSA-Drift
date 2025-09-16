variable "rule_name" {
  description = "EventBridge rule name"
  type        = string
}

variable "eventbridge_role_name" {
  description = "EventBridge IAM role name"
  type        = string
}

variable "eventbridge_policy_name" {
  description = "EventBridge IAM policy name"
  type        = string
}

variable "step_function_arn" {
  description = "ARN of the Step Functions state machine to trigger"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge schedule expression"
  type        = string
  default     = "rate(1 hour)"
}