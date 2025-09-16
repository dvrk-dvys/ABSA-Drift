import json
import os
import boto3
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
from src.utils.monitor_utils import detect_drift, get_drift_alert_message, load_monitoring_data_window

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# PostgreSQL configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'absa_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'absa_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'absa_password')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))

def get_db_connection():
    """Create database connection"""
    connection_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    return create_engine(connection_string)

def get_environment_suffix():
    environment = os.getenv('ENVIRONMENT', 'dev')

    if environment == 'monitor':
        function_name = os.getenv('AWS_LAMBDA_FUNCTION_NAME', '')
        if 'stg' in function_name:
            return 'stg'
        elif 'prod' in function_name:
            return 'prod'
        else:
            return 'dev'
    return environment

def init_monitoring_table(environment_suffix):
    """Initialize monitoring table with environment-specific name"""
    table_name = f'absa_monitoring_data_{environment_suffix}'
    print(f"Initializing monitoring table: {table_name}")
    
    engine = get_db_connection()
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
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
        drift_analysis_timestamp TIMESTAMP WITH TIME ZONE,
        drift_threshold_used FLOAT,
        overall_drift_detected BOOLEAN,
        loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(comment_id, aspectterm)
    );
    
    CREATE INDEX IF NOT EXISTS idx_{environment_suffix}_comment_time ON {table_name}(comment_time);
    CREATE INDEX IF NOT EXISTS idx_{environment_suffix}_aspectterm ON {table_name}(aspectterm);
    CREATE INDEX IF NOT EXISTS idx_{environment_suffix}_polarity ON {table_name}(polarity);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print(f"Monitoring table {table_name} initialized successfully")
    return table_name

def normalize_columns(df):
    """Normalize column names"""
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
    

    for col in array_cols:
        df[col] = df[col].apply(lambda arr: None
                                if arr is None else
                                arr.tolist() if isinstance(arr, np.ndarray) else
                                list(arr) if isinstance(arr, (list, tuple)) else
                                arr)
    return df, array_cols

def load_to_postgresql(df, environment_suffix):
    """Load data to PostgreSQL with environment-specific table"""
    try:

        table_name = init_monitoring_table(environment_suffix)
        

        df = normalize_columns(df)
        print(f"Normalized columns: {df.columns.tolist()}")
        

        df, array_cols = detect_array_columns(df)
        if array_cols:
            print(f"Detected array columns: {array_cols}")
        

        engine = get_db_connection()
        dtype_map = {col: JSONB() for col in array_cols}
        
        df.to_sql(
            table_name,
            engine,
            if_exists='append',
            index=False,
            chunksize=1000,
            dtype=dtype_map
        )
        
        print(f"Successfully loaded {len(df)} records to {table_name}")
        return True
        
    except Exception as e:
        print(f"Error loading to PostgreSQL: {e}")
        return False

def lambda_handler(event, context=None, monitor_key="monitoring/monitor_predictions.parquet"):
    bucket = event['bucket']
    drift_threshold = event.get('drift_threshold', 0.2)  
    min_cluster_size = event.get('min_cluster_size', 1)
    days_back = event.get('days_back', 7)
    is_test = event.get('test', False)
    

    prefix = "test_" if is_test else ""
    monitor_key_final = f"monitoring/{prefix}monitor_predictions.parquet" if is_test else monitor_key
    

    current_data, reference_data = load_monitoring_data_window(
        bucket=bucket,
        key=monitor_key_final,
        days_back=days_back
    )
    

    drift_results = detect_drift(
        current_data=current_data,
        reference_data=reference_data,
        threshold=drift_threshold,
        min_cluster_size=min_cluster_size
    )
    

    alert_message = get_drift_alert_message(drift_results)
    

    current_with_clusters = drift_results['current_data_with_clusters']
    

    analysis_timestamp = datetime.now().isoformat() + 'Z'
    current_with_clusters['drift_analysis_timestamp'] = analysis_timestamp
    current_with_clusters['drift_threshold_used'] = drift_threshold
    current_with_clusters['overall_drift_detected'] = drift_results['overall_drift_detected']
    

    current_key = f"monitoring/{prefix}drift_monitoring_history.parquet"
    

    monitor_uri = f"s3://{bucket}/{current_key}"
    try:
        existing_df = pd.read_parquet(monitor_uri)
        combined_df = pd.concat([existing_df, current_with_clusters], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['comment_id', 'aspectterm'], keep='last')
    except:
        combined_df = current_with_clusters
    
    combined_df.to_parquet(monitor_uri, index=False)
    print(combined_df.head())
    

    environment_suffix = get_environment_suffix()
    postgres_success = load_to_postgresql(combined_df, environment_suffix)
    
    output = {
        "status": "success",
        "drift_detected": drift_results['overall_drift_detected'],
        "alert_message": alert_message,
        "timestamp": drift_results['timestamp'],
        "total_clusters": drift_results['total_clusters'],
        "threshold_used": drift_results['threshold_used'],
        "cluster_results": drift_results['cluster_results'],
        "data_saved_to": current_key,
        "postgres_loaded": postgres_success,
        "postgres_table": f"absa_monitoring_data_{environment_suffix}",
        "test": is_test
    }
    
    print(output)
    return output