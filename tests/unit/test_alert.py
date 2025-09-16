import os
from src.lambdas.alert.lambda_function import lambda_handler

os.environ['ALERT_EMAIL_LIST'] = 'ja.harris@outlook.com'
os.environ['SENDER_EMAIL'] = 'ja.harr91@gmail.com'


def test_real_drift_alert():
    """Send actual email via AWS SES when drift detected - tests email structure too"""
    event = {
        "drift_detected": True,
        "alert_message": "🚨 Battery sentiment dropped 25% | Shipping improved 15%",
        "total_clusters": 5,
        "test": True
    }

    result = lambda_handler(event, None)

    assert result['status'] == 'alert_sent'
    assert result['drift_detected'] is True
    assert result['emails_sent'] == 1
    assert result['recipient'] == 'ja.harris@outlook.com'
    assert result['test'] is True
    assert 'timestamp' in result


def test_real_edge_cases():
    """Test edge cases with real AWS SES"""
    event = {}

    result = lambda_handler(event, None)

    assert result['status'] == 'no_alert_needed'
    assert result['drift_detected'] is False
    assert result['emails_sent'] == 0
    assert result['test'] is False


def test_no_drift():
    """No email sent when no drift detected"""
    event = {
        "drift_detected": False,
        "alert_message": "No drift detected",
        "total_clusters": 3,
        "test": True
    }

    result = lambda_handler(event, None)

    assert result['status'] == 'no_alert_needed'
    assert result['drift_detected'] is False
    assert result['emails_sent'] == 0


if __name__ == "__main__":
    print("Testing AWS SES alerts...")
    test_real_drift_alert()
    test_real_edge_cases()
    test_no_drift()
    print("✅ All tests passed - check ja.harris@outlook.com inbox!")