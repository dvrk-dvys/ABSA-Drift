import os
import pickle
from datetime import datetime

import pandas as pd
import base64
import json

import boto3
import mlflow.pyfunc
from src.utils.data_utils import load_nlp_models, create_features

MODEL_S3_URI = os.getenv(
    "MODEL_S3_URI",
    "s3://absa-drift-models/mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/"
)

def download_model_mlflow(model_uri):
    model = mlflow.pyfunc.load_model(model_uri)
    return model

def download_model_from_s3(bucket_name, s3_key):
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
    model = pickle.loads(response["Body"].read())
    print(f"✅ Loaded model from S3: {type(model)}")
    return model


def load_extracted_data(bucket, key, nlp_model='bert-base-uncased'):
    tokenizer, embed_model = load_nlp_models(nlp_model)

    s3_uri = f"s3://{bucket}/{key}"
    original_df = pd.read_parquet(s3_uri)

    original_df = original_df.head(5)
    print(f"Loaded {len(original_df)} sample rows")
    print(original_df[['comment', 'polarity', 'implicitness']].head())
    features_df = create_features(df=original_df, embed_model=embed_model, tokenizer=tokenizer)
    print(f"Created features with shape: {features_df.shape}")
    print(f"Feature columns: {list(features_df.columns)[:10]}...")
    return original_df, features_df


def predict(model, features):
    print("\nRunning inference...")

    predictions = model.predict(features)
    pred_df = pd.DataFrame(predictions,
                           columns=['sentiment_score', 'engagement_score', 'implicitness_degree']
                           )

    # enforce range
    pred_df['sentiment_score'] = pred_df['sentiment_score'].clip(-1.0, 1.0)
    pred_df['engagement_score'] = pred_df['engagement_score'].clip(lower=0.0)
    pred_df['implicitness_degree'] = pred_df['implicitness_degree'].clip(0.0, 1.0)

    print(f"Predictions shape: {predictions.shape}")
    print(f"Predictions:\n{predictions}")

    return pred_df


def lambda_handler(event, monitor_key="monitoring/monitor_predictions.parquet"):
    bucket = event['bucket']
    key = event['key']

    model = download_model_mlflow(MODEL_S3_URI)
    orig_df, feat_df = load_extracted_data(bucket, key)
    pred_df = predict(model, feat_df)

    monitor_df = pd.concat([
        orig_df[['comment', 'aspectterm', 'comment_id', 'polarity', 'implicitness']],
        pred_df
    ], axis=1)


    monitor_uri = f"s3://{bucket}/{monitor_key}"

    # Append to existing or create new
    try:
        existing_df = pd.read_parquet(monitor_uri)
        combined_df = pd.concat([existing_df, monitor_df], ignore_index=True)
    except:
        combined_df = monitor_df

    combined_df.to_parquet(monitor_uri, index=False)

    return {
        "status": "success",
        "bucket": bucket,
        "monitor_uri": monitor_uri,
        "new_predictions": len(pred_df),
        "prediction_summary": {
            "avg_sentiment": float(pred_df['sentiment_score'].mean()),
            "avg_engagement": float(pred_df['engagement_score'].mean()),
            "avg_implicitness": float(pred_df['implicitness_degree'].mean())
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


if __name__ == '__main__':

    MODEL_S3_URI = os.getenv(
        "MODEL_S3_URI",
        "s3://absa-drift-models/mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/"
    )

    bucket_name = 'absa-drift-data'
    DATA_S3_KEY = 'prep_transform/extracted_ae17638f-8665-40eb-84ee-ff9d6bedef66.parquet'
    #{'status': 'success', 'bucket': 'absa-drift-data', 'key': 'prep_transform/extracted_ae17638f-8665-40eb-84ee-ff9d6bedef66.parquet', 'records_processed': 228, 'uploaded_at': '2025-07-30T14:17:03Z'}

    model = download_model_mlflow(MODEL_S3_URI)
    f_df = load_extracted_data(bucket_name, DATA_S3_KEY)
    p_df = predict(model, f_df)


