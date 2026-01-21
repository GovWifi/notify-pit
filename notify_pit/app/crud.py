from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models, schemas


def get_notification(db: Session, notification_id: str):
    return db.query(models.Notification).filter(models.Notification.id == notification_id).first()

def create_notification(db: Session, notification: schemas.NotificationBase, type: str, phone_number: str = None, email_address: str = None):
    db_notification = models.Notification(
        type=type,
        template_id=str(notification.template_id),
        reference=notification.reference,
        phone_number=phone_number,
        email_address=email_address,
        personalisation=notification.personalisation,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_received_texts(db: Session):
    return db.query(models.Notification).filter(models.Notification.type == "sms").order_by(desc(models.Notification.created_at)).all()

# Testing helper for received texts
def create_received_text(db: Session, phone_number: str, content: str):
    db_notification = models.Notification(
        type="sms",
        phone_number=phone_number,
        content=content,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def get_templates(db: Session, type: str = None):
    query = db.query(models.Template)
    if type:
        query = query.filter(models.Template.type == type)
    return query.all()

def get_template(db: Session, template_id: str):
    return db.query(models.Template).filter(models.Template.id == template_id).first()

def create_template(db: Session, template: schemas.CreateTemplateRequest):
    db_template = models.Template(
        type=template.type,
        name=template.name,
        body=template.body,
        subject=template.subject,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        version=1
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def update_template(db: Session, template_id: str, template_update: schemas.CreateTemplateRequest):
    db_template = get_template(db, template_id)
    if not db_template:
        return None

    db_template.type = template_update.type
    db_template.name = template_update.name
    db_template.body = template_update.body
    db_template.subject = template_update.subject
    db_template.updated_at = datetime.now(timezone.utc)
    db_template.version += 1

    db.commit()
    db.refresh(db_template)
    return db_template

def delete_template(db: Session, template_id: str):
    db_template = get_template(db, template_id)
    if db_template:
        db.delete(db_template)
        db.commit()
        return True
    return False

def reset_db(db: Session):
    db.query(models.Notification).delete()
    db.query(models.Template).delete()
    db.commit()
