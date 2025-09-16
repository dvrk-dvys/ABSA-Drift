from src.utils.alert_utils import send_drift_alert

def lambda_handler(event, context=None):
    """
    Simple alert system that sends email notifications when drift is detected.
    
    Expected event structure (output from monitor lambda):
    {
        "status": "success",
        "drift_detected": true/false,
        "alert_message": "string", 
        "total_clusters": int,
        "test": true/false
    }
    """
    drift_detected = event.get('drift_detected', False)
    alert_message = event.get('alert_message', 'No drift detected')
    total_clusters = event.get('total_clusters', 0)
    is_test = event.get('test', False)
    
    output = send_drift_alert(drift_detected, alert_message, total_clusters, is_test)
    
    print(output)
    return output