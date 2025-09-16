# Production Environment Configuration
aws_region = "us-east-1"
environment = "prod"

# EventBridge schedule (hourly)
eventbridge_schedule = "rate(1 hour)"

# SNS notification email (to be configured)
sns_alert_email = "ja.harr91@gmail.com"


# Project identifier
project_id = "absa-drift"