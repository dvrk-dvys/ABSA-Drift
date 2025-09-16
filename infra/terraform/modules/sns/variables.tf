variable "topic_name" {
  description = "SNS topic name"
  type        = string
}

variable "alert_email" {
  description = "Email address for SNS alerts"
  type        = string
  default     = ""
}