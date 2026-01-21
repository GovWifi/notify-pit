import uuid

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    template_id = Column(
        String, nullable=True
    )  # Optional, strictly speaking, but usually present
    reference = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email_address = Column(String, nullable=True)
    personalisation = Column(JSON, nullable=True)
    status = Column(String, default="created")
    # For received texts
    content = Column(String, nullable=True)
    service_id = Column(String, nullable=True)
    notify_number = Column(String, nullable=True)
    user_number = Column(String, nullable=True)


class Template(Base):
    __tablename__ = "templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String, nullable=False)
    body = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    version = Column(Integer, default=1)
    created_by = Column(String, default="notify-pit@example.com")
