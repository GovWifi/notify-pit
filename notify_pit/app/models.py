from typing import Any, Dict, Optional

from pydantic import UUID4, BaseModel


class NotificationBase(BaseModel):
    template_id: UUID4
    personalisation: Optional[Dict[str, Any]] = None
    reference: Optional[str] = None


class SmsRequest(NotificationBase):
    phone_number: str


class EmailRequest(NotificationBase):
    email_address: str


class LetterRequest(NotificationBase):
    personalisation: Dict[str, Any]
