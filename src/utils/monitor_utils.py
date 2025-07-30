import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


def detect_drift(
    current_data: pd.DataFrame,
    reference_data: pd.DataFrame,
    threshold: float = 0.2
) -> Dict:
    """
    Simple drift detector for ABSA sentiment, engagement, and implicitness scores.
    
    Args:
        current_data: Recent predictions DataFrame
        reference_data: Baseline/reference predictions DataFrame  
        threshold: Drift threshold for alerting (default 0.2)
        
    Returns:
        Dict with drift metrics and alert status
    """
    metrics = ['sentiment_score', 'engagement_score', 'implicitness_degree']
    drift_results = {}
    
    for metric in metrics:
        current_mean = current_data[metric].mean()
        reference_mean = reference_data[metric].mean()
        
        # Calculate relative drift
        drift_magnitude = abs(current_mean - reference_mean) / (abs(reference_mean) + 1e-8)
        
        drift_results[metric] = {
            'current_mean': float(current_mean),
            'reference_mean': float(reference_mean),
            'drift_magnitude': float(drift_magnitude),
            'drift_detected': drift_magnitude > threshold
        }
    
    # Overall alert status
    any_drift = any(result['drift_detected'] for result in drift_results.values())
    
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'overall_drift_detected': any_drift,
        'metrics': drift_results,
        'threshold_used': threshold,
        'current_sample_size': len(current_data),
        'reference_sample_size': len(reference_data)
    }


def get_drift_alert_message(drift_results: Dict) -> str:
    """Generate alert message for marketing/brand teams"""
    if not drift_results['overall_drift_detected']:
        return "No significant drift detected in aspect sentiment metrics."
    
    alerts = []
    for metric, results in drift_results['metrics'].items():
        if results['drift_detected']:
            direction = "increased" if results['current_mean'] > results['reference_mean'] else "decreased"
            alerts.append(f"{metric.replace('_', ' ').title()} has {direction} by {results['drift_magnitude']:.2%}")
    
    return f"🚨 DRIFT ALERT: {', '.join(alerts)}"


def load_monitoring_data_window(
    bucket: str,
    key: str = "monitoring/monitor_predictions.parquet",
    days_back: int = 7
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load recent vs reference data windows for drift detection.
    
    Returns:
        Tuple of (recent_data, reference_data)
    """
    s3_uri = f"s3://{bucket}/{key}"
    df = pd.read_parquet(s3_uri)
    
    # For now, use simple split since we don't have timestamps in the data yet
    # In production, you'd filter by actual timestamps
    split_point = len(df) // 2
    reference_data = df.iloc[:split_point]
    current_data = df.iloc[split_point:]
    
    return current_data, reference_data