#!/usr/bin/env python3
"""
Test script to run extract lambda locally
"""
import sys
import os
sys.path.append('/Users/jordanharris/Code/ABSA-Drift')

# Set environment variables for the lambda
os.environ['S3_DATA_BUCKET'] = 'absa-drift-data'
os.environ['S3_MODEL_BUCKET'] = 'absa-drift-models'

from src.lambdas.extract.lambda_function import lambda_handler

if __name__ == "__main__":
    # Simulate a lambda event
    event = {}
    context = {}
    
    print("🚀 Testing Extract Lambda Function locally...")
    try:
        result = lambda_handler(event, context)
        print("✅ Extract Lambda succeeded!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Extract Lambda failed: {e}")
        import traceback
        traceback.print_exc()