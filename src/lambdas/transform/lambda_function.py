import os
from src.utils.transform_utils import transform_handler

MODEL_S3_URI = os.getenv(
    "MODEL_S3_URI",
    "models:/ABSA_Pipeline_v3/latest"
)

def lambda_handler(event, context):
    return transform_handler(event)