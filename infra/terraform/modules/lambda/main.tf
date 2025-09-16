# Extract Lambda Function
resource "aws_lambda_function" "extract_lambda" {
  function_name = var.extract_function_name
  role          = aws_iam_role.lambda_execution_role.arn
  image_uri     = var.extract_image_uri
  package_type  = "Image"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      ENVIRONMENT        = "extract"
      S3_DATA_BUCKET     = var.s3_data_bucket
      S3_MODEL_BUCKET    = var.s3_model_bucket
    }
  }
}

# Transform Lambda Function
resource "aws_lambda_function" "transform_lambda" {
  function_name = var.transform_function_name
  role          = aws_iam_role.lambda_execution_role.arn
  image_uri     = var.transform_image_uri
  package_type  = "Image"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      ENVIRONMENT        = "transform"
      S3_DATA_BUCKET     = var.s3_data_bucket
      S3_MODEL_BUCKET    = var.s3_model_bucket
    }
  }
}

# Monitor Lambda Function
resource "aws_lambda_function" "monitor_lambda" {
  function_name = var.monitor_function_name
  role          = aws_iam_role.lambda_execution_role.arn
  image_uri     = var.monitor_image_uri
  package_type  = "Image"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      ENVIRONMENT        = "monitor"
      S3_DATA_BUCKET     = var.s3_data_bucket
      S3_MODEL_BUCKET    = var.s3_model_bucket
    }
  }
}

# Alert Lambda Function
resource "aws_lambda_function" "alert_lambda" {
  function_name = var.alert_function_name
  role          = aws_iam_role.lambda_execution_role.arn
  image_uri     = var.alert_image_uri
  package_type  = "Image"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      ENVIRONMENT        = "alert"
      S3_DATA_BUCKET     = var.s3_data_bucket
      S3_MODEL_BUCKET    = var.s3_model_bucket
      SNS_TOPIC_ARN      = var.sns_topic_arn
    }
  }
}