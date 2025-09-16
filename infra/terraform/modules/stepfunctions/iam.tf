# IAM Role for Step Functions
resource "aws_iam_role" "step_functions_role" {
  name = var.step_functions_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

# Policy to invoke Lambda functions
resource "aws_iam_role_policy" "step_functions_lambda_policy" {
  name = var.step_functions_policy_name
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          var.lambda_extract_arn,
          var.lambda_transform_arn,
          var.lambda_monitor_arn,
          var.lambda_alert_arn
        ]
      }
    ]
  })
}