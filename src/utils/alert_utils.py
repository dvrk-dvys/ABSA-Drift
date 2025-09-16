import os
import boto3
from datetime import datetime


def send_drift_alert(drift_detected, alert_message, total_clusters, is_test=False):
    """
    Send email alert when drift is detected.
    
    Args:
        drift_detected: Boolean indicating if drift was detected
        alert_message: String message describing the drift
        total_clusters: Number of clusters analyzed
        is_test: Boolean indicating if this is a test run
        
    Returns:
        Dict with alert results
    """
    email_list = os.getenv('ALERT_EMAIL_LIST', 'ja.harr91@gmail.com').split(',')
    sender_email = os.getenv('SENDER_EMAIL', 'ja.harr91@gmail.com')
    
    print(f"Drift detected: {drift_detected}")
    print(f"Alert message: {alert_message}")
    print(f"Total clusters: {total_clusters}")
    print(f"Test mode: {is_test}")
    
    if drift_detected:
        ses_client = boto3.client('ses')
        
        subject = f"🚨 ABSA Drift Alert - {total_clusters} Clusters Affected"
        body = f"""
                ABSA Drift Detection Alert
                
                {alert_message}
                
                Total Clusters Analyzed: {total_clusters}
                Timestamp: {datetime.utcnow().isoformat()}Z
                Test Mode: {'Yes' if is_test else 'No'}
                
                Please review the drift analysis and take appropriate action.
                """
        
        recipient = email_list[0].strip()
        
        print(f"Sending alert email to: {recipient}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        
        ses_client.send_email(
            Source=sender_email,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        
        return {
            "status": "alert_sent",
            "drift_detected": drift_detected,
            "alert_message": alert_message,
            "emails_sent": 1,
            "recipient": recipient,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test": is_test
        }
    else:
        print("No alert needed - no drift detected")
        return {
            "status": "no_alert_needed", 
            "drift_detected": drift_detected,
            "alert_message": alert_message,
            "emails_sent": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test": is_test
        }


if __name__ == '__main__':
    print("=== ABSA Alert Utils Test ===")
    
    print("\n--- Test 1: No Drift ---")
    result1 = send_drift_alert(
        drift_detected=False,
        alert_message="No significant drift detected in aspect sentiment metrics.",
        total_clusters=3,
        is_test=True
    )
    print(f"Result: {result1}")
    
    print("\n--- Test 2: Drift Detected ---")
    result2 = send_drift_alert(
        drift_detected=True,
        alert_message="🚨 DRIFT ALERT: Cluster 'authentic_genuine': Sentiment Score increased by 45.23%",
        total_clusters=5,
        is_test=True
    )
    print(f"Result: {result2}")
    
    print("\n=== Alert Utils Test Complete ===")