import os
import pandas as pd
import numpy as np
import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# S3 configuration - use terraform staging bucket with fresh monitoring data
S3_BUCKET = os.getenv('S3_BUCKET', 'absa-drift-data-stg')
S3_KEY = os.getenv('S3_KEY', 'monitoring/monitor_predictions.parquet')

# Use same database connection as training pipeline
POSTGRES_HOST = 'localhost'
POSTGRES_DB = 'absa_db'
POSTGRES_USER = 'absa_user'
POSTGRES_PASSWORD = 'absa_password'
POSTGRES_PORT = 5432
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
MONITORING_TABLE = f'absa_monitoring_data_{ENVIRONMENT}'

def get_db_connection():
    """Create database connection using same credentials as training pipeline"""
    connection_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    return create_engine(connection_string)

def init_monitoring_table():
    """Initialize monitoring table with same schema as training data"""
    logger.info("Initializing monitoring table...")
    engine = get_db_connection()
    
    # Create table similar to tiktok_comments_nlp but for monitoring data
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {MONITORING_TABLE} (
        id SERIAL PRIMARY KEY,
        comment_id BIGINT,
        comment_text TEXT,
        aspectterm VARCHAR(255),
        comment_time TIMESTAMP WITH TIME ZONE,
        polarity INTEGER,
        implicitness BOOLEAN,
        sentiment_score FLOAT,
        engagement_score FLOAT,
        implicitness_degree FLOAT,
        cluster_id VARCHAR(50),
        "Digg Count" INTEGER,
        "Reply Count" INTEGER,
        loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(comment_id, aspectterm)
    );
    
    CREATE INDEX IF NOT EXISTS idx_monitoring_comment_time ON {MONITORING_TABLE}(comment_time);
    CREATE INDEX IF NOT EXISTS idx_monitoring_aspectterm ON {MONITORING_TABLE}(aspectterm);
    CREATE INDEX IF NOT EXISTS idx_monitoring_polarity ON {MONITORING_TABLE}(polarity);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    logger.info(f"Monitoring table {MONITORING_TABLE} initialized successfully")

def load_data_from_s3():
    """Load data from S3 parquet file"""
    logger.info(f"Loading data from S3: s3://{S3_BUCKET}/{S3_KEY}")
    
    s3_client = boto3.client('s3')
    local_file = '/tmp/monitoring_data.parquet'
    
    s3_client.download_file(S3_BUCKET, S3_KEY, local_file)
    df = pd.read_parquet(local_file)
    
    logger.info(f"Loaded {len(df)} records from S3")
    return df

def normalize_columns(df):
    """Normalize column names like the adhoc script"""
    df.columns = (
        df.columns
          .str.lower()
          .str.replace(r'[ \-]+', '_', regex=True)
    )
    return df

def detect_array_columns(df):
    """Detect and handle array-type columns"""
    array_cols = []
    for col in df.columns:
        if df[col].dtype == 'object':
            non_null = df[col].dropna()
            sample_values = non_null.head(min(len(non_null), 5))
            if len(sample_values) > 0 and all(isinstance(v, (list, tuple, np.ndarray)) for v in sample_values):
                array_cols.append(col)
    
    # Convert numpy arrays to lists
    for col in array_cols:
        df[col] = df[col].apply(lambda arr: None
                                if arr is None else
                                arr.tolist() if isinstance(arr, np.ndarray) else
                                list(arr) if isinstance(arr, (list, tuple)) else
                                arr)
    return df, array_cols

def process_and_store_data(df):
    """Process data and store in PostgreSQL using same approach as training pipeline"""
    logger.info(f"Processing {len(df)} records...")
    

    df = normalize_columns(df)
    logger.info(f"Normalized columns: {df.columns.tolist()}")
    
    # Handle array columns
    df, array_cols = detect_array_columns(df)
    if array_cols:
        logger.info(f"Detected array columns: {array_cols}")
    
    # Store in database
    engine = get_db_connection()
    dtype_map = {col: JSONB() for col in array_cols}
    
    df.to_sql(
        MONITORING_TABLE,
        engine,
        if_exists='replace',
        index=False,
        chunksize=10_000,
        dtype=dtype_map
    )
    
    logger.info(f"Stored {len(df)} records in {MONITORING_TABLE} table")
    if array_cols:
        logger.info(f"JSONB array columns: {array_cols}")

def load_monitoring_data():
    """Simple one-time data loading function for Grafana"""
    logger.info("Loading ABSA monitoring data from S3...")
    
    try:
        init_monitoring_table()
        
        df = load_data_from_s3()
        process_and_store_data(df)
        
        logger.info("Data loading completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in data loading: {e}")
        return False

def main():
    """Main entry point - simple one-time load"""
    success = load_monitoring_data()
    if success:
        logger.info("✅ Monitoring data loaded successfully")
    else:
        logger.error("❌ Failed to load monitoring data")
        exit(1)

if __name__ == "__main__":
    main()