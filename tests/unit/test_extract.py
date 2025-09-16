import os
import time
import json
import boto3
import pandas as pd
import pytest
from pathlib import Path


from src.lambdas.extract.lambda_function import lambda_handler

# Configuration via environment or defaults
env_bucket = os.environ.get('TEST_S3_BUCKET', 'absa-drift-data')
env_function = os.environ.get('EXTRACT_FUNCTION_NAME', 'lambda-extract')

@pytest.fixture(scope='module')
def s3_client():
    return boto3.client('s3')

@pytest.fixture(scope='module')
def lambda_client():
    return boto3.client('lambda')


@pytest.fixture(scope='function')
def upload_test_data(s3_client):
    bucket = 'absa-drift-data'
    prefix = 'hourly_tiktok_comments_nlp/'

    test_keys = [
        f"{prefix}test_data_1.parquet",
        f"{prefix}test_data_2.parquet"
    ]

    local_files = [
        '../../data/raw/absa_debug_train_dataframe_with_replies.parquet',
        '../../data/raw/absa_debug_train_dataframe.parquet/part-00005-aabf7d53-3cc0-453c-83e9-e73d9d7bab7c-c000.snappy.parquet'
    ]

    for local_file in local_files:
        print(f"File exists: {Path(local_file).exists()} - {local_file}")

    #for key in test_keys:
    #    try:
    #        s3_client.delete_object(Bucket=bucket, Key=key)
    #    except:
    #        pass

    for local_file, s3_key in zip(local_files, test_keys):
        if Path(local_file).exists():
            with open(local_file, 'rb') as f:
                s3_client.upload_fileobj(f, bucket, s3_key)

    yield test_keys



def test_extract_local_writes_parquet(s3_client, upload_test_data):
    """
    Call the extract lambda handler locally and verify a parquet file is written to S3.
    """
    result = lambda_handler({}, None)
    assert result['status'] == 'success'
    key = result['key']
    assert key.startswith('prep_transform/extracted_')
    time.sleep(2)
    head = s3_client.head_object(Bucket=env_bucket, Key=key)
    assert head['ContentLength'] > 0, "Parquet file should have non-zero size"

    obj = s3_client.get_object(Bucket=env_bucket, Key=key)
    df = pd.read_parquet(f"s3://{env_bucket}/{key}")
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == result['records_processed']
