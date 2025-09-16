import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict


def cosine_similarity(text1: str, text2: str) -> float:
    """Simple text similarity using word overlap for lambda-friendly clustering."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def cluster_aspect_terms_simple(aspect_terms: List[str], similarity_threshold: float = 0.3, min_cluster_size: int = 1) -> Dict[int, List[str]]:
    """Simple clustering for aspect terms using text similarity (lambda-friendly)."""
    if len(aspect_terms) < min_cluster_size:
        return {0: aspect_terms}
    
    clusters = []
    
    for term in aspect_terms:
        assigned = False
        for cluster in clusters:
            if any(cosine_similarity(term, existing_term) > similarity_threshold for existing_term in cluster):
                cluster.append(term)
                assigned = True
                break
        
        if not assigned:
            clusters.append([term])
    
    large_clusters = [c for c in clusters if len(c) >= min_cluster_size]
    small_terms = [term for c in clusters if len(c) < min_cluster_size for term in c]
    
    if small_terms:
        large_clusters.append(small_terms)
    
    return {i: cluster for i, cluster in enumerate(large_clusters)}


def add_cluster_ids(df: pd.DataFrame, aspect_clusters: Dict[int, List[str]]) -> pd.DataFrame:
    """Add cluster_id column to DataFrame based on aspect term clustering."""
    df = df.copy()
    
    term_to_cluster = {}
    for cluster_id, terms in aspect_clusters.items():
        readable_cluster_id = "_".join(sorted(terms)[:3])  # Use first 3 terms to avoid overly long IDs
        for term in terms:
            term_to_cluster[term] = readable_cluster_id
    
    df['cluster_id'] = df['aspectterm'].map(term_to_cluster)
    return df


def detect_drift(
    current_data: pd.DataFrame,
    reference_data: pd.DataFrame,
    threshold: float = 0.2,
    min_cluster_size: int = 1
) -> Dict:
    """
    Aspect-aware drift detector that monitors drift per semantic aspect term cluster.
    
    Args:
        current_data: Recent predictions DataFrame with 'aspectterm' column
        reference_data: Baseline/reference predictions DataFrame
        threshold: Drift threshold for alerting (default 0.2)
        min_cluster_size: Minimum cluster size for significance
        
    Returns:
        Dict with drift metrics per aspect cluster and overall status
    """
    metrics = ['sentiment_score', 'engagement_score', 'implicitness_degree']
    
    all_terms = list(set(current_data['aspectterm'].tolist() + reference_data['aspectterm'].tolist()))
    
    aspect_clusters = cluster_aspect_terms_simple(all_terms, min_cluster_size=min_cluster_size)
    
    cluster_drift_results = {}
    
    for cluster_id, terms in aspect_clusters.items():
        current_cluster = current_data[current_data['aspectterm'].isin(terms)]
        reference_cluster = reference_data[reference_data['aspectterm'].isin(terms)]
        
        if len(current_cluster) == 0 or len(reference_cluster) == 0:
            cluster_name = "_".join(sorted(terms)[:3])
            cluster_drift_results[cluster_name] = {
                'aspect_terms': terms,
                'metrics': {},
                'current_sample_size': len(current_cluster),
                'reference_sample_size': len(reference_cluster),
                'cluster_drift_detected': False,
                'warning': 'Insufficient data for drift analysis'
            }
            continue
        
        cluster_metrics = {}
        for metric in metrics:
            current_mean = current_cluster[metric].mean()
            reference_mean = reference_cluster[metric].mean()
            
            drift_magnitude = abs(current_mean - reference_mean) / (abs(reference_mean) + 1e-8)
            
            cluster_metrics[metric] = {
                'current_mean': float(current_mean),
                'reference_mean': float(reference_mean),
                'drift_magnitude': float(drift_magnitude),
                'drift_detected': drift_magnitude > threshold
            }
        
        cluster_name = "_".join(sorted(terms)[:3])
        
        cluster_drift_results[cluster_name] = {
            'aspect_terms': terms,
            'metrics': cluster_metrics,
            'current_sample_size': len(current_cluster),
            'reference_sample_size': len(reference_cluster),
            'cluster_drift_detected': any(m['drift_detected'] for m in cluster_metrics.values())
        }
    
    overall_drift = any(cluster['cluster_drift_detected'] for cluster in cluster_drift_results.values())
    
    current_with_clusters = add_cluster_ids(current_data, aspect_clusters)
    reference_with_clusters = add_cluster_ids(reference_data, aspect_clusters)
    
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'overall_drift_detected': overall_drift,
        'cluster_results': cluster_drift_results,
        'threshold_used': threshold,
        'total_clusters': len(cluster_drift_results),
        'current_sample_size': len(current_data),
        'reference_sample_size': len(reference_data),
        'current_data_with_clusters': current_with_clusters,
        'reference_data_with_clusters': reference_with_clusters
    }


def get_drift_alert_message(drift_results: Dict) -> str:
    """Generate alert message for marketing/brand teams with cluster-specific information"""
    if not drift_results['overall_drift_detected']:
        return "No significant drift detected in aspect sentiment metrics."
    
    alerts = []
    for cluster_name, cluster_results in drift_results['cluster_results'].items():
        if cluster_results['cluster_drift_detected']:
            cluster_alerts = []
            for metric, results in cluster_results['metrics'].items():
                if results['drift_detected']:
                    direction = "increased" if results['current_mean'] > results['reference_mean'] else "decreased"
                    cluster_alerts.append(f"{metric.replace('_', ' ').title()} {direction} by {results['drift_magnitude']:.2%}")
            
            if cluster_alerts:
                alerts.append(f"Cluster '{cluster_name}': {', '.join(cluster_alerts)}")
    
    return f"🚨 DRIFT ALERT: {' | '.join(alerts)}"


def load_monitoring_data_window(
    bucket: str,
    key: str = "monitoring/monitor_predictions.parquet",
    days_back: int = 7
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load recent vs reference data windows for drift detection using timestamps.
    
    Args:
        bucket: S3 bucket name
        key: S3 key for monitoring data
        days_back: Number of days to look back for current window
        
    Returns:
        Tuple of (current_data, reference_data)
    """
    s3_uri = f"s3://{bucket}/{key}"
    df = pd.read_parquet(s3_uri)
    
    if 'comment_time' in df.columns:
        df['comment_time'] = pd.to_datetime(df['comment_time'])
        
        df = df.sort_values('comment_time')
        
        max_time = df['comment_time'].max()
        current_window_start = max_time - pd.Timedelta(days=days_back)
        reference_window_end = current_window_start
        reference_window_start = reference_window_end - pd.Timedelta(days=days_back)
        
        current_data = df[df['comment_time'] >= current_window_start].copy()
        reference_data = df[
            (df['comment_time'] >= reference_window_start) & 
            (df['comment_time'] < reference_window_end)
        ].copy()
        
        print(f"Time-based windowing:")
        print(f"  Reference period: {reference_window_start} to {reference_window_end}")
        print(f"  Current period: {current_window_start} to {max_time}")
        print(f"  Reference data: {len(reference_data)} rows")
        print(f"  Current data: {len(current_data)} rows")
        
        if len(current_data) < 10 or len(reference_data) < 10:
            print("Warning: Time windows too small, falling back to split method")
            split_point = len(df) // 2
            reference_data = df.iloc[:split_point].copy()
            current_data = df.iloc[split_point:].copy()
    else:
        print("Warning: No 'comment_time' column found, using simple split method")
        split_point = len(df) // 2
        reference_data = df.iloc[:split_point].copy()
        current_data = df.iloc[split_point:].copy()
    
    return current_data, reference_data


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    bucket = 'absa-drift-data'
    predictions_key = 'monitoring/test_monitor_predictions.parquet'
    
    print("Loading monitoring data...")
    current_data, reference_data = load_monitoring_data_window(bucket, predictions_key)
    
    print(f"Current data shape: {current_data.shape}")
    print(f"Reference data shape: {reference_data.shape}")
    print(f"Current data columns: {current_data.columns.tolist()}")
    print("\nCurrent data sample:")
    print(current_data.head())
    
    print("\nUnique aspect terms:")
    all_terms = list(set(current_data['aspectterm'].tolist() + reference_data['aspectterm'].tolist()))
    print(all_terms)
    
    print("\nClustering aspect terms...")
    clusters = cluster_aspect_terms_simple(all_terms, min_cluster_size=1)
    print(f"Created {len(clusters)} clusters:")
    for cluster_id, terms in clusters.items():
        print(f"  Cluster {cluster_id}: {terms}")
    
    print("\nDetecting drift...")
    drift_results = detect_drift(current_data, reference_data, threshold=0.2, min_cluster_size=1)
    
    print(f"Overall drift detected: {drift_results['overall_drift_detected']}")
    print(f"Total clusters: {drift_results['total_clusters']}")
    
    print("\nCluster drift results:")
    for cluster_name, cluster_data in drift_results['cluster_results'].items():
        print(f"\n{cluster_name}:")
        print(f"  Aspect terms: {cluster_data['aspect_terms']}")
        print(f"  Drift detected: {cluster_data['cluster_drift_detected']}")
        print(f"  Sample sizes: current={cluster_data['current_sample_size']}, reference={cluster_data['reference_sample_size']}")
        
        for metric, metric_data in cluster_data['metrics'].items():
            if metric_data['drift_detected']:
                print(f"  {metric}: {metric_data['current_mean']:.3f} -> {metric_data['reference_mean']:.3f} (drift: {metric_data['drift_magnitude']:.3f})")
    
    print("\nData with clusters sample:")
    current_with_clusters = drift_results['current_data_with_clusters']
    print(current_with_clusters[['aspectterm', 'cluster_id', 'sentiment_score']].head(10))