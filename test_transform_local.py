#!/usr/bin/env python3
"""
Test script to run transform lambda locally
"""
import sys
import os
sys.path.append('/Users/jordanharris/Code/ABSA-Drift')

# Set environment variables for the lambda
os.environ['S3_DATA_BUCKET'] = 'absa-drift-data'
os.environ['S3_MODEL_BUCKET'] = 'absa-drift-models'

from src.lambdas.transform.lambda_function import lambda_handler

if __name__ == "__main__":
    # Simulate a lambda event with the data we uploaded
    event = {
        "bucket": "absa-drift-data",
        "key": "hourly_tiktok_comments_nlp/test_data_1.parquet",
        "records_processed": 228
    }
    context = {}
    
    print("🚀 Testing Transform Lambda Function locally...")
    try:
        result = lambda_handler(event, context)
        print("✅ Transform Lambda succeeded!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Transform Lambda failed: {e}")
        import traceback
        traceback.print_exc()