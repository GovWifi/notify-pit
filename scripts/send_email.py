# Sending an email notification using the Notifications API Client. This works
# against both Notify.pit and the real GOV.UK Notify service.
#
# python -m venv venv
# source venv/bin/activate
# python -m pip install notifications-python-client
# python send_sms.py
#
import os
from notifications_python_client.notifications import NotificationsAPIClient


base_url = os.getenv("NOTIFICATIONS_BASE_URL", "http://localhost:8000")
api_key = os.getenv(
    "NOTIFICATIONS_API_KEY",
    "mytestkey-00000000-0000-0000-0000-000000000000-3d844edf-8d35-48ac-975b-e847b4f122b0",
)
notifications_client = NotificationsAPIClient(api_key=api_key, base_url=base_url)

magic_link_email_template_id = "006e8a3d-2cc3-4c97-b36d-d554f00a34fd"

response = notifications_client.send_email_notification(
    email_address="oisin.mulvihill@digital.cabinet-office.gov.uk",
    template_id=magic_link_email_template_id,
    personalisation={
        "name": "Amala",
        "magic_authorisation_link": "https://www.google.com",
    },
)


print(
    f"""

Response:
{response}

      """
)
