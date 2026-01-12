from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, UUID4, EmailStr
from typing import List, Optional, Dict, Any


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


class ReceivedTextMessage(BaseModel):
    id: str = str(uuid.uuid4())
    user_number: str
    notify_number: str
    content: str
    created_at: str = datetime.now(timezone.utc).isoformat() + "Z"


class ReceivedTextResponse(BaseModel):
    # The Notify client expects the list wrapped in this key
    received_text_messages: List[ReceivedTextMessage]
