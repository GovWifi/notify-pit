from sqlalchemy import JSON, Column, Integer, String, Text

from .database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, index=True)
    created_at = Column(String)
    reference = Column(String, nullable=True)
    template_id = Column(String, nullable=True)

    # Specific fields flattened or stored loosely
    phone_number = Column(String, nullable=True)
    email_address = Column(String, nullable=True)

    # Store personalisation as a JSON blob
    personalisation = Column(JSON, nullable=True)


class Template(Base):
    __tablename__ = "templates"

    id = Column(String, primary_key=True, index=True)
    type = Column(String)
    name = Column(String)
    body = Column(Text)
    subject = Column(String, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(String)
    updated_at = Column(String)
    created_by = Column(String)
