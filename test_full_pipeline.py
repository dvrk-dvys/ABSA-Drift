#!/usr/bin/env python3
"""
End-to-end test of the complete ABSA-Drift pipeline
"""
import sys
import os
import uuid
from datetime import datetime
sys.path.append('/Users/jordanharris/Code/ABSA-Drift')

# Set environment variables for the lambdas
os.environ['S3_DATA_BUCKET'] = 'absa-drift-data'
os.environ['S3_MODEL_BUCKET'] = 'absa-drift-models'

from src.lambdas.extract.lambda_function import lambda_handler as extract_handler
from src.lambdas.transform.lambda_function import lambda_handler as transform_handler
from src.lambdas.monitor.lambda_function import lambda_handler as monitor_handler
from src.lambdas.alert.lambda_function import lambda_handler as alert_handler

def test_full_pipeline():
    """Test the complete pipeline with the full dataset"""
    print("🚀 Starting Full ABSA-Drift Pipeline Test")
    print("=" * 60)
    
    # Step 1: Upload full dataset to simulate extraction
    import boto3
    import pandas as pd
    
    s3_client = boto3.client('s3')
    bucket = 'absa-drift-data'
    
    # Read and upload full dataset
    full_df = pd.read_parquet('/Users/jordanharris/Code/ABSA-Drift/data/raw/absa_debug_train_dataframe_with_replies.parquet')
    print(f"📊 Full dataset: {full_df.shape[0]} records, {full_df.shape[1]} columns")
    
    # Create a fresh extracted file for testing
    extract_key = f"prep_transform/pipeline_test_{uuid.uuid4()}.parquet"
    extract_uri = f"s3://{bucket}/{extract_key}"
    full_df.to_parquet(extract_uri, index=False)
    print(f"📤 Uploaded full dataset to: {extract_uri}")
    
    # Step 2: Transform - Run ML predictions
    print("\n🔄 Step 2: Transform (ML Predictions)")
    transform_event = {
        'bucket': bucket,
        'key': extract_key,
        'records_processed': full_df.shape[0]
    }
    
    transform_result = transform_handler(transform_event, {})
    print(f"✅ Transform completed: {transform_result['new_predictions']} predictions")
    print(f"   📈 Avg sentiment: {transform_result['prediction_summary']['avg_sentiment']:.3f}")
    print(f"   📊 Avg engagement: {transform_result['prediction_summary']['avg_engagement']:.6f}")
    print(f"   🎯 Avg implicitness: {transform_result['prediction_summary']['avg_implicitness']:.3f}")
    
    # Step 3: Monitor - Drift Detection
    print("\n🔍 Step 3: Monitor (Drift Detection)")
    monitor_result = monitor_handler(transform_result, {})
    print(f"✅ Monitor completed: Drift detected = {monitor_result['drift_detected']}")
    print(f"   🎯 Clusters analyzed: {monitor_result['total_clusters']}")
    print(f"   📊 Threshold used: {monitor_result['threshold_used']}")
    
    # Step 4: Alert - Notification (if drift detected)
    print("\n🚨 Step 4: Alert")
    if monitor_result['drift_detected']:
        alert_result = alert_handler(monitor_result, {})
        print(f"✅ Alert sent: {alert_result['alert_message']}")
    else:
        print("ℹ️  No drift detected - no alert needed")
        alert_result = {"status": "no_alert_needed", "message": "No significant drift detected"}
    
    # Step 5: Verify data flow
    print("\n📋 Step 5: Data Verification")
    
    # Check monitoring data in S3
    monitor_uri = transform_result['monitor_uri']
    monitor_df = pd.read_parquet(monitor_uri)
    print(f"✅ Monitoring data: {monitor_df.shape[0]} records saved to S3")
    
    # Check drift history
    drift_df = pd.read_parquet(f"s3://{bucket}/monitoring/drift_monitoring_history.parquet")
    print(f"✅ Drift history: {drift_df.shape[0]} records in drift monitoring")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 PIPELINE TEST COMPLETE!")
    print("=" * 60)
    print(f"📊 Total records processed: {full_df.shape[0]}")
    print(f"🔄 Predictions generated: {transform_result['new_predictions']}")
    print(f"🔍 Drift detected: {monitor_result['drift_detected']}")
    print(f"📈 Monitoring data points: {monitor_df.shape[0]}")
    print(f"📋 Drift history entries: {drift_df.shape[0]}")
    
    # Data quality checks
    print("\n📋 Data Quality Checks:")
    print(f"✅ Sentiment scores in range [-1,1]: {monitor_df['sentiment_score'].between(-1, 1).all()}")
    print(f"✅ Engagement scores >= 0: {(monitor_df['engagement_score'] >= 0).all()}")
    print(f"✅ Implicitness in range [0,1]: {monitor_df['implicitness_degree'].between(0, 1).all()}")
    print(f"✅ All aspects have terms: {monitor_df['aspectterm'].notna().all()}")
    
    return {
        'pipeline_status': 'success',
        'records_processed': full_df.shape[0],
        'predictions_generated': transform_result['new_predictions'],
        'drift_detected': monitor_result['drift_detected'],
        'monitoring_records': monitor_df.shape[0],
        'drift_history_records': drift_df.shape[0]
    }

if __name__ == "__main__":
    try:
        result = test_full_pipeline()
        print(f"\n🏆 Pipeline test result: {result}")
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()