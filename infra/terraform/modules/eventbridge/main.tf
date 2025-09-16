# EventBridge Rule for hourly trigger
resource "aws_cloudwatch_event_rule" "hourly_schedule" {
  name                = var.rule_name
  description         = "Trigger ABSA pipeline every hour"
  schedule_expression = var.schedule_expression
}

# EventBridge Target to invoke Step Functions
resource "aws_cloudwatch_event_target" "step_function_target" {
  rule      = aws_cloudwatch_event_rule.hourly_schedule.name
  target_id = "StepFunctionTarget"
  arn       = var.step_function_arn
  role_arn  = aws_iam_role.eventbridge_role.arn

  input = jsonencode({
    test = false
  })
}