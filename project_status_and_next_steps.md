# ABSA-Drift Project Status & Next Steps

## Current Implementation Status

### ✅ **COMPLETED** 
1. **Model Training Pipeline** - `src/training/train_model.py`
   - Multi-output XGBoost regressor working
   - MLflow experiment tracking configured 
   - Models saved to S3: `s3://absa-drift-models/mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/`
   
2. **Model Inference** - `src/training/test_inference.py`
   - Successfully loads models from MLflow
   - Predictions working with 3 outputs: sentiment_score, engagement_score, implicitness_degree
   
3. **Data Pipeline** - `src/utils/data_utils.py`
   - PostgreSQL data loading working
   - Feature engineering with BERT embeddings working
   - Target creation pipeline complete

4. **Project Structure**
   - Complete directory structure following plan
   - MLflow server configured with S3 backend

### ❌ **MISSING/TODO**
1. **Lambda Functions** (ALL EMPTY - Priority 1)
   - `src/lambdas/extract/` - needs implementation
   - `src/lambdas/transform/` - needs model loading from S3
   - `src/lambdas/monitor/` - needs drift detection
   - `src/lambdas/alert/` - needs SNS notifications

2. **Infrastructure** (Priority 2)
   - Terraform modules not implemented
   - No Dockerfiles for Lambda containers
   - No ECR repositories configured

3. **Orchestration** (Priority 3)
   - Step Functions state machine not created
   - EventBridge scheduling not configured
   - SAM template needs real AWS integration

## Updated Architecture (No LocalStack)

### Model Flow
```
MLflow Training → S3 Model Storage → Lambda Transform Function
                                         ↓
                                    Model Predictions
```

**S3 Model Path**: `s3://absa-drift-models/mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/`

**Key Files in S3**:
- `model.pkl` (500.3 KB) - The trained XGBoost model
- `MLmodel` (46.8 KB) - MLflow model metadata
- `requirements.txt` - Model dependencies
- `conda.yaml` - Environment specification

### Lambda Integration Strategy
1. **Transform Lambda** downloads model from S3 to `/tmp` on startup
2. Uses `mlflow.pyfunc.load_model()` with S3 URIs
3. No LocalStack - direct AWS S3 integration

## Step-by-Step Next Actions

### Phase 1: Lambda Functions (Days 1-2)

#### Step 1: Implement Extract Lambda
```bash
# Create files needed:
touch src/lambdas/extract/lambda_function.py
touch src/lambdas/extract/s3_utils.py  
touch src/lambdas/extract/Dockerfile
touch src/lambdas/extract/requirements.txt
```

**Implementation**: Read hourly CSV files from S3, validate schema, pass to transform

#### Step 2: Implement Transform Lambda (CRITICAL)
```bash  
# Create files needed:
touch src/lambdas/transform/lambda_function.py
touch src/lambdas/transform/model_loader.py
touch src/lambdas/transform/sentiment_analyzer.py
touch src/lambdas/transform/Dockerfile  
touch src/lambdas/transform/requirements.txt
```

**Implementation**: 
- Load model from S3: `s3://absa-drift-models/mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/`
- Use your existing feature engineering from `data_utils.py`
- Return predictions in format expected by monitor lambda

#### Step 3: Implement Monitor Lambda
```bash
# Create files needed:
touch src/lambdas/monitor/lambda_function.py
touch src/lambdas/monitor/drift_detector.py
touch src/lambdas/monitor/Dockerfile
touch src/lambdas/monitor/requirements.txt
```

**Implementation**: Use Evidently to detect sentiment drift, trigger alerts if threshold exceeded

#### Step 4: Implement Alert Lambda  
```bash
# Create files needed:
touch src/lambdas/alert/lambda_function.py
touch src/lambdas/alert/notification_sender.py
touch src/lambdas/alert/Dockerfile
touch src/lambdas/alert/requirements.txt
```

**Implementation**: Send SNS notifications, trigger retraining workflows

### Phase 2: Infrastructure (Day 3)

#### Step 5: Create Terraform Modules
- Update S3 module to include MLflow model bucket access
- Configure IAM policies for Lambda to access S3 model bucket  
- Deploy ECR repositories for Lambda containers

#### Step 6: Build and Deploy Lambda Containers
```bash
# Build all containers
docker build -t absa-extract src/lambdas/extract/
docker build -t absa-transform src/lambdas/transform/  
docker build -t absa-monitor src/lambdas/monitor/
docker build -t absa-alert src/lambdas/alert/

# Push to ECR (after terraform creates repos)
```

### Phase 3: Orchestration (Day 4)

#### Step 7: Create Step Functions State Machine
- Implement the JSON definition from project_structure.txt
- Configure error handling and retries
- Test with sample data

#### Step 8: Setup EventBridge Scheduling
- Hourly trigger for Step Functions
- Configure environment variables for all Lambdas

### Phase 4: Testing & CI/CD (Day 4)

#### Step 9: Update SAM Template  
Remove LocalStack references, use real AWS credentials:
```yaml
Environment:
  Variables:
    MLFLOW_S3_ENDPOINT_URL: https://s3.amazonaws.com
    AWS_DEFAULT_REGION: us-east-1
    MODEL_S3_PATH: s3://absa-drift-models/mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/
```

## Key Environment Variables for Lambdas

### Transform Lambda (CRITICAL)
```bash
MODEL_S3_BUCKET=absa-drift-models
MODEL_S3_PATH=mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/
MLFLOW_TRACKING_URI=http://127.0.0.1:5001  # or your MLflow server
```

### All Lambdas
```bash
AWS_DEFAULT_REGION=us-east-1
ENVIRONMENT=dev
LOG_LEVEL=INFO
```

## Immediate Next Action

**START WITH**: Implement the Transform Lambda function since it's the core component that needs to load your trained model from S3. This is where your MLflow S3 integration will be tested.

The transform lambda should:
1. Download model artifacts from S3 on cold start
2. Load the model using `mlflow.pyfunc.load_model()`  
3. Use your existing `create_features()` function
4. Return predictions in the format expected by the monitoring lambda

Once transform lambda works, the rest of the pipeline becomes much simpler to implement.

## Testing Strategy

1. **Local Testing**: Use SAM CLI with real AWS credentials to test S3 model loading
2. **Integration Testing**: Test full pipeline with sample hourly data
3. **Deployment**: Deploy to dev environment and verify end-to-end flow

## Success Criteria

- [ ] Transform Lambda successfully loads model from S3
- [ ] Full Step Functions pipeline executes without errors  
- [ ] Drift detection triggers alerts when thresholds exceeded
- [ ] All infrastructure deployed via Terraform
- [ ] CI/CD pipeline deploys containers to ECR automatically

**Estimated Time**: 2-3 days of focused implementation work.