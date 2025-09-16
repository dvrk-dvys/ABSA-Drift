#!/usr/bin/env python3
"""
Test script to run monitor lambda locally
"""
import sys
import os
sys.path.append('/Users/jordanharris/Code/ABSA-Drift')

# Set environment variables for the lambda
os.environ['S3_DATA_BUCKET'] = 'absa-drift-data'
os.environ['S3_MODEL_BUCKET'] = 'absa-drift-models'

from src.lambdas.monitor.lambda_function import lambda_handler

if __name__ == "__main__":
    # Simulate a lambda event from transform output
    event = {
        "status": "success",
        "bucket": "absa-drift-data",
        "monitor_uri": "s3://absa-drift-data/monitoring/monitor_predictions.parquet",
        "new_predictions": 5,
        "prediction_summary": {
            "avg_sentiment": -0.237,
            "avg_engagement": 0.000045,
            "avg_implicitness": 0.298
        },
        "timestamp": "2025-08-05T00:15:00Z",
        "test": False
    }
    context = {}
    
    print("🚀 Testing Monitor Lambda Function locally...")
    try:
        result = lambda_handler(event, context)
        print("✅ Monitor Lambda succeeded!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Monitor Lambda failed: {e}")
        import traceback
        traceback.print_exc()