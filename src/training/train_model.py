import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sklearn
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import train_test_split

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor

import mlflow
from mlflow import pyfunc
from sklearn.pipeline import make_pipeline
from mlflow.models.signature import infer_signature

from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm




#mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_tracking_uri("http://127.0.0.1:5001")

mlflow.set_experiment("ABSA_Drift")

df = pd.read_parquet('/Users/jordanharris/Code/ABSA-Drift/data/raw/absa_debug_train_dataframe.parquet')


def create_advanced_targets(df):
    targets = pd.DataFrame()

    targets['sentiment_score'] = df['polarity'].map({0: 1.0, 1: -1.0, 2: 0.0})
    targets['engagement_score'] = np.log(df['digg_count'] + 1)

    # Predict how "strongly implicit" the sentiment is
    # For implicit comments: how subtle/sophisticated is the implicitness?
    targets['implicitness_strength'] = np.where(
        df['implicitness'] == True,
        df['contextual_surprisal'] / df['contextual_surprisal'].max(),  # 0-1 scale
        0.0  # Explicit comments get 0
    )

    return targets


def create_implicitness_degree_target(df):
    """
    Create continuous implicitness score (0-1) using multiple signals
    """
    implicitness_degree = pd.Series(index=df.index, dtype=float)

    for idx, row in df.iterrows():
        if row['implicitness'] == False:
            # Explicit comments get low scores
            implicitness_degree[idx] = 0.1 + (row['contextual_surprisal'] * 0.1)  # 0.0-0.2 range
        else:
            # Implicit comments: calculate degree based on sophistication
            base_score = 0.5  # Start at moderate implicitness

            # Linguistic sophistication factors
            entropy_factor = min(row['shannon_entropy'] / 5.0, 0.2)  # Up to +0.2
            surprisal_factor = min(row['contextual_surprisal'], 0.2)  # Up to +0.2

            # Reasoning sophistication !!!no!!!
            #reasoning_length = len(row['reasoning']) if pd.notna(row['reasoning']) else 0
            #reasoning_factor = min(reasoning_length / 1000, 0.1)  # Up to +0.1

            # Calculate final score
            implicitness_degree[idx] = min(base_score + entropy_factor + surprisal_factor + reasoning_factor, 1.0)

    return implicitness_degree


def create_aspect_features(df):
    aspect_features = pd.DataFrame()

    # === ASPECT MASK FEATURES (instead of one-hot) ===
    if 'aspect_mask' in df.columns:
        # Parse aspect masks from JSONB
        for idx, mask in enumerate(df['aspect_mask']):
            if mask is not None:
                try:
                    mask_array = mask if isinstance(mask, list) else json.loads(mask)

                    # Create features from aspect mask
                    aspect_features.loc[idx, 'aspect_token_count'] = sum(mask_array)
                    aspect_features.loc[idx, 'aspect_positions'] = len(
                        [i for i, val in enumerate(mask_array) if val == 1])
                    aspect_features.loc[idx, 'aspect_early_position'] = mask_array.index(1) if 1 in mask_array else -1
                    aspect_features.loc[idx, 'aspect_span_length'] = (
                        max([i for i, val in enumerate(mask_array) if val == 1]) -
                        min([i for i, val in enumerate(mask_array) if val == 1]) + 1
                        if 1 in mask_array else 0
                    )

                except:
                    # Handle parsing errors
                    aspect_features.loc[idx, 'aspect_token_count'] = 0
                    aspect_features.loc[idx, 'aspect_positions'] = 0
                    aspect_features.loc[idx, 'aspect_early_position'] = -1
                    aspect_features.loc[idx, 'aspect_span_length'] = 0
            else:
                aspect_features.loc[idx, 'aspect_token_count'] = 0
                aspect_features.loc[idx, 'aspect_positions'] = 0
                aspect_features.loc[idx, 'aspect_early_position'] = -1
                aspect_features.loc[idx, 'aspect_span_length'] = 0

    # === ASPECT TERM CATEGORICAL (as backup) ===
    # Keep this as additional feature, not replacement
    aspect_dummies = pd.get_dummies(df['aspectterm'], prefix='aspect')

    return pd.concat([aspect_features, aspect_dummies], axis=1)



X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2)


multi_reg = MultiOutputRegressor(
  estimator = XGBRegressor()
)

multi_reg.fit(X_train, y_train)
multi_reg_pred = multi_reg.predict(X_test)
print(multi_reg_pred.shape)  # (n_samples, 3) - matches y_train columns

# predictions[:, 0] = sentiment predictions
# predictions[:, 1] = engagement predictions
# predictions[:, 2] = implicitness predictions

pd.DataFrame(multi_reg_pred, columns=['Y1', 'Y2', 'Y3'])





'''
For Gradient Boosting:

Flatten your tokenized features into numerical vectors
Use your rich NLP features (entropy, surprisal) as main features
Add tokenized features as supplementary
'''



reasoning_quality = (
    df['has_evidence'] * 0.3 +           # From your reasoning analysis
    df['reasoning_complexity'] * 0.2 +   # Token count / avg token count
    (1 - df['has_uncertainty']) * 0.2 +  # Confidence indicators
    df['mutual_information_score'] * 0.3 # Coherent word relationships
)

# Feature engineering
df['is_reply'] = df['reply_to_which_comment'].notna()
df['engagement_quality'] = np.where(
    df['is_reply'],
    df['digg_count'] * 2.0,  # Replies get bonus for deeper engagement
    df['digg_count']         # Original comments use raw engagement
)

# Separate models or weighted targets
df['reply_depth_engagement'] = df['digg_count'] / (df['reply_depth'] + 1)

from transformers import TFRobertaModel, AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained(bert_model_path)

targets = [
    'sentiment_score',
    'engagement_score',
    'implicitness_score'
]
'''
Three Core Targets:

Sentiment Score (-1 to +1 continuous)
Engagement Score (log-transformed)
Implicitness Score (0-1 continuous) ← Your new addition
'''






#-----------------

#model_classes = [RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor, LinearSVR]
#model_names = ["RandomForest", "GradientBoosting", "ExtraTrees", "LinearSVR"]

#model_classes = [GradientBoostingRegressor]
#model_names = ["GradientBoosting"]

#for model_class, model_name in zip(model_classes, model_names):

#    with mlflow.start_run(run_name=f"FINAL_{model_name.lower()}"):
#        mlflow.set_tag("model_type", model_name)
#        mlflow.set_tag("status", "final_pipeline")

#        mlflow.log_param("train-data-path", "./data/green_tripdata_2021-01.csv")
#        mlflow.log_param("valid-data-path", "./data/green_tripdata_2021-02.csv")

#        mlmodel = model_class()
#        pipeline = make_pipeline(dv, mlmodel)
#        pipeline.fit(train_dicts, y_train)

#        y_pred = pipeline.predict(val_dicts)

#        mse = mean_squared_error(y_val, y_pred)
#        rmse = np.sqrt(mse)
#        mae = mean_absolute_error(y_val, y_pred)
#        r2 = r2_score(y_val, y_pred)

#        print(f"{model_name} - MSE: {mse:.3f}, RMSE: {rmse:.3f}, MAE: {mae:.3f}, R²: {r2:.3f}")

#        mlflow.log_metric("mse", mse)
#        mlflow.log_metric("rmse", rmse)
#        mlflow.log_metric("mae", mae)
#        mlflow.log_metric("R²", r2)

#        signature = infer_signature(train_dicts[:100], y_train[:100])

#        mlflow.sklearn.log_model(
#            sk_model=pipeline,
#            name=f"{model_name}_pipeline_model",
#            signature=signature,
#            registered_model_name=f"{model_name}_pipeline"
#        )

#https://towardsdatascience.com/gradient-boosting-regressor-explained-a-visual-guide-with-code-examples-c098d1ae425c/



