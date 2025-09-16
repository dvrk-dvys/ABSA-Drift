# ABSA Drift Detection - Terraform Infrastructure

This Terraform configuration provisions AWS infrastructure for the ABSA (Aspect-Based Sentiment Analysis) drift detection pipeline.

## Architecture

The infrastructure deploys:
- **4 Lambda Functions**: extract, transform, monitor, alert (containerized)
- **Step Functions**: orchestrates the Lambda pipeline
- **EventBridge**: triggers pipeline hourly
- **S3 Buckets**: data storage and MLflow model artifacts
- **ECR Repository**: stores Lambda container images
- **SNS Topic**: handles notifications
- **RDS PostgreSQL**: database for state tracking and data storage
- **IAM Roles**: proper permissions for all services

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.8 installed
3. S3 bucket for Terraform state (create manually first)

## Quick Start

1. **Create Terraform state bucket manually**:
   ```bash
   aws s3 mb s3://tf-state-absa-drift
   ```

2. **Update backend configuration** in `main.tf`:
   ```hcl
   backend "s3" {
     bucket = "your-terraform-state-bucket"
     key    = "absa-drift-dev.tfstate"
     region = "us-east-1"
   }
   ```

3. **Configure variables** in `environments/dev.tfvars`:
   ```hcl
   sns_alert_email = "your-email@example.com"
   ```

4. **Deploy infrastructure**:
   ```bash
   terraform init
   terraform plan -var-file="environments/dev.tfvars"
   terraform apply -var-file="environments/dev.tfvars"
   ```

## Module Structure

```
modules/
├── ecr/           # Container registry for Lambda images
├── s3/            # Data and model storage buckets
├── lambda/        # 4 Lambda functions with IAM roles
├── stepfunctions/ # Pipeline orchestration
├── eventbridge/   # Hourly scheduling
├── sns/           # Notifications
└── rds/           # PostgreSQL database for state tracking
```

## Next Steps

After infrastructure deployment:

1. **Build and push Lambda containers**:
   ```bash
   # Get ECR login
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build and push each Lambda
   docker build -t absa-drift-dev:extract-latest src/lambdas/extract/
   docker tag absa-drift-dev:extract-latest <ecr-url>:extract-latest
   docker push <ecr-url>:extract-latest
   ```

2. **Upload models to S3** (from MLflow)

3. **Test the pipeline**:
   ```bash
   aws stepfunctions start-execution \
     --state-machine-arn <step-function-arn> \
     --input '{"test": true}'
   ```

## Configuration

Key variables in `variables.tf`:
- `aws_region`: AWS region (default: us-east-1)
- `environment`: Environment name (dev/staging/prod)
- `lambda_timeout`: Lambda timeout in seconds
- `sns_alert_email`: Email for notifications

## Cost Optimization

- Lambda functions use pay-per-invocation
- S3 buckets have intelligent tiering
- RDS uses db.t3.micro (free tier eligible)
- Consider Aurora Serverless for production workloads

## Security

- All S3 buckets block public access
- IAM roles follow least privilege principle
- ECR repositories have lifecycle policies
- Sensitive variables marked as such

## Cleanup

```bash
terraform destroy -var-file="environments/dev.tfvars"
```

**Note**: This will delete all resources including data. Export important data first.