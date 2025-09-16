# Step Functions State Machine
resource "aws_sfn_state_machine" "absa_pipeline" {
  name     = var.state_machine_name
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "ABSA Drift Detection Pipeline - Cascade of extract -> transform -> monitor -> alert"
    StartAt = "ExtractLambda"
    States = {
      ExtractLambda = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.lambda_extract_arn
          "Payload.$"  = "$"
        }
        ResultPath = "$.extract_result"
        Next       = "TransformLambda"
      }
      TransformLambda = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.lambda_transform_arn
          Payload = {
            "bucket.$" = "$.extract_result.Payload.bucket"
            "key.$"    = "$.extract_result.Payload.key"
            "test.$"   = "$.test"
          }
        }
        ResultPath = "$.transform_result"
        Next       = "MonitorLambda"
      }
      MonitorLambda = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.lambda_monitor_arn
          Payload = {
            "bucket.$"          = "$.transform_result.Payload.bucket"
            drift_threshold     = 0.2
            min_cluster_size    = 1
            "test.$"           = "$.test"
          }
        }
        ResultPath = "$.monitor_result"
        Next       = "AlertLambda"
      }
      AlertLambda = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.lambda_alert_arn
          Payload = {
            "status.$"          = "$.monitor_result.Payload.status"
            "drift_detected.$"  = "$.monitor_result.Payload.drift_detected"
            "alert_message.$"   = "$.monitor_result.Payload.alert_message"
            "total_clusters.$"  = "$.monitor_result.Payload.total_clusters"
            "test.$"           = "$.test"
          }
        }
        ResultPath = "$.alert_result"
        End        = true
      }
    }
  })
}