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

base_url = "http://localhost:8000"
# base_url = "https://api.notifications.service.gov.uk"
api_key = "mytestkey-00000000-0000-0000-0000-000000000000-574329d4-b6dd-4982-9204-c33fc3c45dbb"

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
