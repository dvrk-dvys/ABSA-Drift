import pandas as pd
import numpy as np
import mlflow
from mlflow import pyfunc
import sys
sys.path.append('/Users/jordanharris/Code/ABSA-Drift/src')
from src.utils.data_utils import load_data_from_postgres, create_features, load_nlp_models

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)


def setup_mlflow():
    """Configure MLflow tracking to match training"""
    mlflow.set_tracking_uri("http://127.0.0.1:5001")
    mlflow.set_experiment("ABSA_Drift")

def load_model_from_mlflow(run_id):
    """Load model from MLflow using run ID"""
    model_uri = f"runs:/{run_id}/model"
    model = mlflow.pyfunc.load_model(model_uri)
    return model

def main():
    # Setup MLflow to match training configuration
    setup_mlflow()
    
    # Use the run ID from your output
    run_id = "0f8c8395930340aeb6100749dd255a9e"
    
    print("Loading model from MLflow...")
    model = load_model_from_mlflow(run_id)
    
    print("Getting sample data...")
    df = load_data_from_postgres(
        table_name='tiktok_comments_nlp',
        host='localhost',
        port=5432,
        database='absa_db',
        username='absa_user',
        password='absa_password'
    )
    # Take just first 5 rows for testing
    df = df.head(5)
    print(f"Loaded {len(df)} sample rows")
    print(df[['comment', 'polarity', 'implicitness']].head())
    
    print("\nLoading models and creating features...")
    tokenizer, embed_model = load_nlp_models('bert-base-uncased')
    features = create_features(df, embed_model, tokenizer)
    print(f"Created features with shape: {features.shape}")
    print(f"Feature columns: {list(features.columns)[:10]}...")  # Show first 10 columns
    
    print("\nRunning inference...")
    print(features.head())
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
    
    # Show prediction columns (should be sentiment_score, engagement_score, implicitness_degree)
    if predictions.shape[1] == 3:
        pred_df = pd.DataFrame(predictions, columns=['sentiment_score', 'engagement_score', 'implicitness_degree'])
        print(f"\nPrediction details:")
        print(pred_df)

if __name__ == "__main__":
    main()

    #Sentiment_score_map = {
    #    0: 1.0,  # positive → +1
    #    1: -1.0,  # negative → -1
    #    2: 0.0  # neutral  →  0
    #}