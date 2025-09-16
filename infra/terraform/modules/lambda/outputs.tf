output "extract_lambda_arn" {
  description = "ARN of the extract lambda function"
  value       = aws_lambda_function.extract_lambda.arn
}

output "extract_lambda_name" {
  description = "Name of the extract lambda function"
  value       = aws_lambda_function.extract_lambda.function_name
}

output "transform_lambda_arn" {
  description = "ARN of the transform lambda function"
  value       = aws_lambda_function.transform_lambda.arn
}

output "transform_lambda_name" {
  description = "Name of the transform lambda function"
  value       = aws_lambda_function.transform_lambda.function_name
}

output "monitor_lambda_arn" {
  description = "ARN of the monitor lambda function"
  value       = aws_lambda_function.monitor_lambda.arn
}

output "monitor_lambda_name" {
  description = "Name of the monitor lambda function"
  value       = aws_lambda_function.monitor_lambda.function_name
}

output "alert_lambda_arn" {
  description = "ARN of the alert lambda function"
  value       = aws_lambda_function.alert_lambda.arn
}

output "alert_lambda_name" {
  description = "Name of the alert lambda function"
  value       = aws_lambda_function.alert_lambda.function_name
}