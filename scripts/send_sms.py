# Sending an SMS notification using the Notifications API Client. This works
# against both Notify.pit and the real GOV.UK Notify service.
#
# python -m venv venv
# source venv/bin/activate
# python -m pip install notifications-python-client
# python send_sms.py
#
import os
from notifications_python_client.notifications import NotificationsAPIClient

# "https://api.notifications.service.gov.uk"
base_url = os.getenv("NOTIFICATIONS_BASE_URL", "http://localhost:8000")
api_key = os.getenv(
    "NOTIFICATIONS_API_KEY",
    "mytestkey-00000000-0000-0000-0000-000000000000-3d844edf-8d35-48ac-975b-e847b4f122b0",
)
notifications_client = NotificationsAPIClient(api_key=api_key, base_url=base_url)

response = notifications_client.send_sms_notification(
    phone_number="+447700900123",
    template_id="f33517ff-2a88-4f6e-b855-c550268ce08a",
)


print(
    f"""

Response:
{response}

      """
)
