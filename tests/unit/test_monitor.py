import os
import json
import pytest
import pandas as pd
import numpy as np
import boto3
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.lambdas.monitor.lambda_function import lambda_handler
from src.utils.monitor_utils import detect_drift, cluster_aspect_terms_simple

env_bucket = os.environ.get('TEST_S3_BUCKET', 'absa-drift-data')


@pytest.fixture
def sample_predictions_data():
    """Create sample predictions data for testing"""
    np.random.seed(42)
    
    aspect_terms = [
        'authentic', 'genuine', 'real', 'trustworthy',  # Similar cluster
        'quality', 'durability', 'craftsmanship',       # Similar cluster  
        'price', 'cost', 'value', 'affordable'          # Similar cluster
    ]
    
    data = []
    for term in aspect_terms:
        for _ in range(20):  # 20 samples per term
            data.append({
                'aspectterm': term,
                'comment': f'Sample comment about {term}',
                'sentiment_score': np.random.normal(0.5, 0.2),
                'engagement_score': np.random.normal(0.7, 0.15),
                'implicitness_degree': np.random.normal(0.3, 0.1)
            })
    
    return pd.DataFrame(data)


@pytest.fixture
def drift_predictions_data():
    """Create predictions data with intentional drift"""
    np.random.seed(123)
    
    aspect_terms = ['authentic', 'genuine', 'quality', 'price']
    
    reference_data = []
    for term in aspect_terms:
        for _ in range(15):
            reference_data.append({
                'aspectterm': term,
                'comment': f'Reference comment about {term}',
                'sentiment_score': np.random.normal(0.5, 0.1),
                'engagement_score': np.random.normal(0.7, 0.1),
                'implicitness_degree': np.random.normal(0.3, 0.1)
            })
    
    current_data = []
    for term in aspect_terms:
        sentiment_mean = 0.8 if term in ['authentic', 'genuine'] else 0.5  # Drift!
        for _ in range(15):
            current_data.append({
                'aspectterm': term,
                'comment': f'Current comment about {term}',
                'sentiment_score': np.random.normal(sentiment_mean, 0.1),
                'engagement_score': np.random.normal(0.7, 0.1),
                'implicitness_degree': np.random.normal(0.3, 0.1)
            })
    
    return pd.DataFrame(reference_data), pd.DataFrame(current_data)


def test_cluster_aspect_terms_simple():
    """Test simple clustering functionality"""
    aspect_terms = ['authentic', 'genuine', 'real', 'quality', 'price', 'cost']
    
    clusters = cluster_aspect_terms_simple(aspect_terms, min_cluster_size=2)
    
    assert isinstance(clusters, dict)
    assert len(clusters) > 0
    
    all_clustered_terms = [term for cluster_terms in clusters.values() for term in cluster_terms]
    assert set(all_clustered_terms) == set(aspect_terms)


def test_detect_drift_no_drift(sample_predictions_data):
    """Test drift detection when no drift exists"""
    mid_point = len(sample_predictions_data) // 2
    reference_data = sample_predictions_data.iloc[:mid_point].copy()
    current_data = sample_predictions_data.iloc[mid_point:].copy()
    
    drift_results = detect_drift(current_data, reference_data, threshold=0.3)
    
    assert drift_results['overall_drift_detected'] is False
    assert 'cluster_results' in drift_results
    assert drift_results['total_clusters'] > 0


def test_detect_drift_with_drift(drift_predictions_data):
    """Test drift detection when drift exists"""
    reference_data, current_data = drift_predictions_data
    
    drift_results = detect_drift(current_data, reference_data, threshold=0.2)
    
    assert drift_results['overall_drift_detected'] is True
    assert 'cluster_results' in drift_results
    assert drift_results['total_clusters'] > 0
    
    drifted_clusters = [
        cluster_name for cluster_name, cluster_data in drift_results['cluster_results'].items()
        if cluster_data['cluster_drift_detected']
    ]
    assert len(drifted_clusters) > 0


@pytest.fixture(scope='module')
def s3_client():
    return boto3.client('s3')


def test_monitor_lambda_with_existing_predictions_on_s3(s3_client):
    """
    Test monitor lambda handler using existing test predictions data from transform lambda.
    This uses real aspect terms from the processed dataset, not synthetic ones.
    """
    monitor_key = "monitoring/test_monitor_predictions.parquet"
    
    head = s3_client.head_object(Bucket=env_bucket, Key=monitor_key)
    assert head['ContentLength'] > 0
    print(f"Found existing test data: {head['ContentLength']} bytes")
    
    event = {
        'bucket': env_bucket,
        'drift_threshold': 0.3,
        'min_cluster_size': 1,
        'test': True
    }
    
    result = lambda_handler(event, context=None, monitor_key=monitor_key)
    
    assert result['status'] == 'success'
    assert 'drift_detected' in result
    assert 'alert_message' in result
    assert 'cluster_results' in result
    assert 'timestamp' in result
    assert 'data_saved_to' in result
    assert 'total_clusters' in result
    
    print(f"Monitor results: drift_detected={result['drift_detected']}, clusters={result['total_clusters']}")
    
    cluster_data_key = result['data_saved_to']
    head = s3_client.head_object(Bucket=env_bucket, Key=cluster_data_key)
    assert head['ContentLength'] > 0
    
    df_with_clusters = pd.read_parquet(f"s3://{env_bucket}/{cluster_data_key}")
    assert isinstance(df_with_clusters, pd.DataFrame)
    assert 'cluster_id' in df_with_clusters.columns
    assert 'aspectterm' in df_with_clusters.columns
    assert 'sentiment_score' in df_with_clusters.columns
    assert 'engagement_score' in df_with_clusters.columns
    assert 'implicitness_degree' in df_with_clusters.columns
    
    print(f"Enhanced data shape: {df_with_clusters.shape}")
    print(f"Unique aspect terms: {df_with_clusters['aspectterm'].nunique()}")
    print(f"Unique clusters: {df_with_clusters['cluster_id'].nunique()}")
    
    cluster_ids = df_with_clusters['cluster_id'].unique()
    assert len(cluster_ids) > 0
    
    sample_clusters = df_with_clusters[['aspectterm', 'cluster_id']].drop_duplicates().head(10)
    print("Sample cluster assignments:")
    for _, row in sample_clusters.iterrows():
        print(f"  {row['aspectterm']} -> {row['cluster_id']}")
    
    assert result['total_clusters'] > 0
    cluster_results = result['cluster_results']
    
    for cluster_name, cluster_data in cluster_results.items():
        assert 'aspect_terms' in cluster_data
        assert 'metrics' in cluster_data
        assert 'current_sample_size' in cluster_data
        assert 'reference_sample_size' in cluster_data
        assert 'cluster_drift_detected' in cluster_data
        
        if cluster_data['metrics']:
            for metric in ['sentiment_score', 'engagement_score', 'implicitness_degree']:
                assert metric in cluster_data['metrics']
                metric_data = cluster_data['metrics'][metric]
                assert 'current_mean' in metric_data
                assert 'reference_mean' in metric_data
                assert 'drift_magnitude' in metric_data
                assert 'drift_detected' in metric_data