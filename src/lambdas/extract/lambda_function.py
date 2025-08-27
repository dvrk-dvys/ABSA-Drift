import uuid
from datetime import datetime
import pandas as pd
from src.utils.extract_utils import get_recent_files, extract_from_s3

bucket = 'absa-drift-data'
prefix = 'hourly_tiktok_comments_nlp/'
minutes = 60

#https://us-east-1.console.aws.amazon.com/s3/buckets/absa-drift-data?region=us-east-1&bucketType=general&tab=objects

def lambda_handler(event, context):
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

    intermediate_key = f"prep_transform/extracted_{uuid.uuid4()}.parquet"
    s3_uri = f"s3://{bucket}/{intermediate_key}"
    final_df.to_parquet(s3_uri, index=False)

    upload_time = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    output = {
        "status": "success",
        "bucket": bucket,
        "key": intermediate_key,
        "records_processed": final_df.shape[0],
        "uploaded_at": upload_time
    }

    print(output)
    return output










