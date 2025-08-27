import os
from src.utils.transform_utils import lambda_handler

MODEL_S3_URI = os.getenv(
    "MODEL_S3_URI",
    "s3://absa-drift-models/mlflow/1/models/m-315e95fac3ac42ac9e8577e8d445d190/artifacts/"
)

def lambda_handler(event, context):
    return lambda_handler(event)