# Staging Environment Configuration
aws_region = "us-east-1"
environment = "stg"

# EventBridge schedule (hourly)
eventbridge_schedule = "rate(1 hour)"

# SNS notification email (verified)
sns_alert_email = "ja.harr91@gmail.com"


# Project identifier
project_id = "absa-drift"