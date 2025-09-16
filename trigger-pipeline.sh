#!/bin/bash

# Trigger ABSA-Drift ML Pipeline manually
# Usage: ./trigger-pipeline.sh [environment]

ENVIRONMENT=${1:-stg}
STEP_FUNCTION_ARN="arn:aws:states:us-east-1:585315266445:stateMachine:absa-drift-pipeline-${ENVIRONMENT}"

echo "🚀 Triggering ABSA-Drift ML Pipeline for environment: ${ENVIRONMENT}"
echo "Step Function ARN: ${STEP_FUNCTION_ARN}"

# Generate unique execution name with timestamp
EXECUTION_NAME="manual-trigger-$(date +%Y%m%d-%H%M%S)"

# Start the execution
aws stepfunctions start-execution \
  --state-machine-arn "${STEP_FUNCTION_ARN}" \
  --name "${EXECUTION_NAME}" \
  --input '{"test": false}' \
  --region us-east-1

if [ $? -eq 0 ]; then
  echo "✅ Pipeline execution started successfully!"
  echo "Execution name: ${EXECUTION_NAME}"
  echo ""
  echo "Monitor execution status with:"
  echo "aws stepfunctions describe-execution --execution-arn \"${STEP_FUNCTION_ARN}:${EXECUTION_NAME}\" --region us-east-1"
else
  echo "❌ Failed to start pipeline execution"
  exit 1
fi