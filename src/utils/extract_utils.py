import json
import os
import boto3
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

_s3 = boto3.client('s3')


def get_recent_files(bucket: str, prefix: str, minutes: int = 60) -> list:
    """
    Return list of keys under `prefix` in `bucket` modified within the last `minutes`.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    resp = _s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    contents = resp.get('Contents', [])
    if not contents:
        return None
    recent = []
    for obj in resp.get('Contents', []):
        if obj['Key'].endswith('.parquet'):
            lm = obj['LastModified'].replace(tzinfo=None)
            if lm > cutoff:
                recent.append(obj['Key'])
    return recent

def extract_from_s3(bucket, key, prev_df=None):
    s3_path = f"s3://{bucket}/{key}"
    df = pd.read_parquet(s3_path)
    if prev_df:
        prev_df.append(df)
        return prev_df
    return df



if __name__ == '__main__':
    bucket = 'absa-drift-data'
    prefix = 'hourly_tiktok_comments_nlp/'
    minutes = 60

    recent_uploads = get_recent_files(bucket, prefix, minutes)
    print(recent_uploads)
    if len(recent_uploads) > 1:
        final_df = extract_from_s3(bucket, recent_uploads[0])

    else:
        dfs = [pd.DataFrame()]
        for f_key in recent_uploads:
            dfs = extract_from_s3(bucket, f_key, dfs)
        final_df = pd.concat(dfs, ignore_index=True)


    print(final_df.shape)
    print(final_df.columns)
    print(final_df.head())
