import os
import boto3
import pandas as pd
import pytest
from pathlib import Path

from src.utils.transform_utils import lambda_handler

env_bucket = os.environ.get('TEST_S3_BUCKET', 'absa-drift-data')
model_s3_uri = os.getenv(
    "MODEL_S3_URI",
    "s3://absa-drift-models/mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/"
)

@pytest.fixture(scope='module')
def s3_client():
    return boto3.client('s3')

@pytest.fixture(scope='function')
def upload_test_extracted_data(s3_client):
    """Upload test extracted data that mimics extract lambda output"""
    bucket = 'absa-drift-data'
    prefix = 'prep_transform/'
    
    test_key = f"{prefix}test_extracted_data.parquet"

    monitor_key = "monitoring/test_monitor_predictions.parquet"
    try:
        s3_client.delete_object(Bucket=bucket, Key=monitor_key)
    except:
        pass

    local_file = '../../data/raw/absa_debug_train_dataframe_with_replies.parquet'
    
    print(f"File exists: {Path(local_file).exists()} - {local_file}")
    
    # Upload fresh test extracted data
    if Path(local_file).exists():
        with open(local_file, 'rb') as f:
            s3_client.upload_fileobj(f, bucket, test_key)
    
    yield test_key

def test_transform_creates_predictions_on_s3(s3_client, upload_test_extracted_data):
    """
    Test transform lambda handler with mock extract output and verify predictions written to S3.
    """
    mock_event = {
        'bucket': env_bucket,
        'key': upload_test_extracted_data
    }

    monitor_key = "monitoring/test_monitor_predictions.parquet"
    result = lambda_handler(mock_event, monitor_key=monitor_key)
    
    assert result['status'] == 'success'
    assert result['bucket'] == env_bucket
    assert result['monitor_uri'] == f"s3://{env_bucket}/{monitor_key}"
    assert result['new_predictions'] > 0
    
    # Verify predictions were written to S3
    test_monitor_key = "monitoring/test_monitor_predictions.parquet"
    head = s3_client.head_object(Bucket=env_bucket, Key=test_monitor_key)
    assert head['ContentLength'] > 0
    
    # Verify predictions data structure
    df = pd.read_parquet(f"s3://{env_bucket}/{test_monitor_key}")
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] >= result['new_predictions']
    assert 'aspectterm' in df.columns
    assert 'comment' in df.columns
    assert 'sentiment_score' in df.columns
    assert 'engagement_score' in df.columns
    assert 'implicitness_degree' in df.columns
    
    # Verify prediction ranges
    assert df['sentiment_score'].min() >= -1.0
    assert df['sentiment_score'].max() <= 1.0
    assert df['engagement_score'].min() >= 0.0
    assert df['implicitness_degree'].min() >= 0.0
    assert df['implicitness_degree'].max() <= 1.0