"""
ABSA Drift Training Script - Core Features Only

This script trains a multi-output XGBoost regressor for three core targets:
- Sentiment Score (-1 to +1 continuous)  
- Engagement Score (log-transformed)
- Implicitness Score (0-1 continuous)

The model uses only core linguistic and context features without any aspect-specific data
for maximum simplicity and interpretability.
"""

import pandas as pd
import numpy as np
import argparse
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor
import mlflow
from mlflow.models.signature import infer_signature


import sys
sys.path.append('/Users/jordanharris/Code/ABSA-Drift/src')
from src.utils.data_utils import load_data_from_postgres, create_targets, create_features


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)


def setup_mlflow():
    """Configure MLflow tracking"""
    mlflow.set_tracking_uri("http://127.0.0.1:5001")
    mlflow.set_experiment("ABSA_Drift")


def print_data_info(df, targets, features):
    """Print dataset information"""
    print(f"Loaded data from database: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst 3 rows:")
    print(df.head(3))
    
    print(f"\nCreated targets: {targets.shape}")
    print("Targets columns:", list(targets.columns))
    print("First 3 target rows:")
    print(targets.head(3))
    
    print(f"\nCreated features: {features.shape}")
    print("Features columns:", list(features.columns))
    print("First 3 feature rows (non-embedding columns):")
    non_emb_cols = [col for col in features.columns if not col.startswith('emb_')]
    print(features[non_emb_cols].head(3))


def train_model(X_train, y_train, X_test, y_test):
    """Train and evaluate the multi-output XGBoost model with core features only"""
    with mlflow.start_run(run_name="ABSA_XGBReg_CoreFeatures_v3"):
        mlflow.set_tag("model_type", 'XGBReg_MultiOut_CoreFeatures')
        mlflow.set_tag("status", "production_v3")
        mlflow.set_tag("feature_type", "core_linguistic_only")


        model = MultiOutputRegressor(estimator=XGBRegressor(
            random_state=42,
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1
        ))


        print("Training model...")
        model.fit(X_train, y_train)
        model_pred = model.predict(X_test)
        print(f"Predictions shape: {model_pred.shape}")


        mse_sent = mean_squared_error(y_test['sentiment_score'], model_pred[:, 0])
        mse_eng = mean_squared_error(y_test['engagement_score'], model_pred[:, 1])
        mse_imp = mean_squared_error(y_test['implicitness_degree'], model_pred[:, 2])
        overall_mse = np.mean([mse_sent, mse_eng, mse_imp])


        r2_sent = r2_score(y_test['sentiment_score'], model_pred[:, 0])
        r2_eng = r2_score(y_test['engagement_score'], model_pred[:, 1])
        r2_imp = r2_score(y_test['implicitness_degree'], model_pred[:, 2])


        mlflow.log_metric("sentiment_mse", mse_sent)
        mlflow.log_metric("engagement_mse", mse_eng)
        mlflow.log_metric("implicitness_mse", mse_imp)
        mlflow.log_metric("overall_mse", overall_mse)
        mlflow.log_metric("sentiment_r2", r2_sent)
        mlflow.log_metric("engagement_r2", r2_eng)
        mlflow.log_metric("implicitness_r2", r2_imp)


        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 6)
        mlflow.log_param("learning_rate", 0.1)
        mlflow.log_param("feature_count", X_train.shape[1])


        signature = infer_signature(X_train, y_train)
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            signature=signature,
            registered_model_name="ABSA_Pipeline_v3"
        )
    print("Done. Metrics:")
    print(f"  MSE - Sentiment: {mse_sent:.4f}, Engagement: {mse_eng:.4f}, Implicitness: {mse_imp:.4f}")
    print(f"  R2  - Sentiment: {r2_sent:.4f}, Engagement: {r2_eng:.4f}, Implicitness: {r2_imp:.4f}")
    return model

if __name__ == '__main__':
    setup_mlflow()


    parser = argparse.ArgumentParser(
        description="Load ABSA-Drift data from Postgres and split for training"
    )
    parser.add_argument('--table_name', default='tiktok_comments_nlp',
                        help="Postgres table to read")
    parser.add_argument('--host',       default='localhost')
    parser.add_argument('--port',       default=5432, type=int)
    parser.add_argument('--database',   default='absa_db')
    parser.add_argument('--username',   default='absa_user')
    parser.add_argument('--password',   default='absa_password')
    parser.add_argument('--test-size',  type=float, default=0.2,
                        help="Fraction for test split")
    parser.add_argument('--random-state', type=int, default=42)
    args = parser.parse_args()


    df = load_data_from_postgres(
        table_name=args.table_name,
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=args.password
    )


    targets = create_targets(df)
    features = create_features(df)
    

    print_data_info(df, targets, features)


    X_train, X_test, y_train, y_test = train_test_split(
        features, targets,
        test_size=args.test_size,
        random_state=args.random_state
    )


    model = train_model(X_train, y_train, X_test, y_test)


    local_model_dir = "/Users/jordanharris/Code/ABSA-Drift/models/artifacts"
    os.makedirs(local_model_dir, exist_ok=True)

    model_path = os.path.join(local_model_dir, "absa_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved locally to: {model_path}")