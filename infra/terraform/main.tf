terraform {
  required_version = ">= 1.8"
  backend "s3" {
    bucket = "tf-state-absa-drift"
    key    = "absa-drift-dev.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current_identity" {}

locals {
  account_id = data.aws_caller_identity.current_identity.account_id
  project_name = "absa-drift"
  environment = var.environment
}

# S3 Buckets for data and models
module "s3_buckets" {
  source = "./modules/s3"
  data_bucket_name = "${var.project_id}-data-${local.environment}"
  model_bucket_name = "${var.project_id}-models-${local.environment}"
}

# ECR Repository for Lambda containers
module "ecr_repository" {
  source = "./modules/ecr"
  repository_name = "${var.project_id}-ml-${local.environment}"
  region = var.aws_region
  account_id = local.account_id
  lambda_functions_path = "../src/lambdas"
}

# Lambda Functions
module "lambda_functions" {
  source = "./modules/lambda"
  extract_function_name = "${var.project_id}-extract-${local.environment}"
  transform_function_name = "${var.project_id}-transform-${local.environment}"
  monitor_function_name = "${var.project_id}-monitor-${local.environment}"
  alert_function_name = "${var.project_id}-alert-${local.environment}"
  lambda_role_name = "${var.project_id}-lambda-role-${local.environment}"
  lambda_policy_name = "${var.project_id}-lambda-policy-${local.environment}"
  extract_image_uri = module.ecr_repository.extract_image_uri
  transform_image_uri = module.ecr_repository.transform_image_uri
  monitor_image_uri = module.ecr_repository.monitor_image_uri
  alert_image_uri = module.ecr_repository.alert_image_uri
  s3_data_bucket = module.s3_buckets.data_bucket_name
  s3_model_bucket = module.s3_buckets.model_bucket_name
  sns_topic_arn = module.sns_notifications.topic_arn
}

# Step Functions Workflow
module "step_functions" {
  source = "./modules/stepfunctions"
  state_machine_name = "${var.project_id}-pipeline-${local.environment}"
  step_functions_role_name = "${var.project_id}-step-functions-role-${local.environment}"
  step_functions_policy_name = "${var.project_id}-step-functions-lambda-policy-${local.environment}"
  lambda_extract_arn = module.lambda_functions.extract_lambda_arn
  lambda_transform_arn = module.lambda_functions.transform_lambda_arn
  lambda_monitor_arn = module.lambda_functions.monitor_lambda_arn
  lambda_alert_arn = module.lambda_functions.alert_lambda_arn
}

# EventBridge for scheduling
module "eventbridge_scheduler" {
  source = "./modules/eventbridge"
  rule_name = "${var.project_id}-schedule-${local.environment}"
  eventbridge_role_name = "${var.project_id}-eventbridge-role-${local.environment}"
  eventbridge_policy_name = "${var.project_id}-eventbridge-policy-${local.environment}"
  step_function_arn = module.step_functions.state_machine_arn
  schedule_expression = var.eventbridge_schedule
}

# SNS for notifications
module "sns_notifications" {
  source = "./modules/sns"
  topic_name = "${var.project_id}-alerts-${local.environment}"
  alert_email = var.sns_alert_email
}


# Outputs for CI/CD
output "ecr_repository_url" {
  value = module.ecr_repository.repository_url
}

output "s3_data_bucket" {
  value = module.s3_buckets.data_bucket_name
}

output "s3_model_bucket" {
  value = module.s3_buckets.model_bucket_name
}

output "step_function_arn" {
  value = module.step_functions.state_machine_arn
}

output "lambda_function_names" {
  value = {
    extract = module.lambda_functions.extract_lambda_name
    transform = module.lambda_functions.transform_lambda_name
    monitor = module.lambda_functions.monitor_lambda_name
    alert = module.lambda_functions.alert_lambda_name
  }
}

