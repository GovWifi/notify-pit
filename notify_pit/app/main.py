import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .auth import validate_notify_jwt
from .models import CreateTemplateRequest, EmailRequest, LetterRequest, SmsRequest
from .database import engine, Base, get_db
from .db_models import Notification, Template

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notify.pit")

# Setup Templates - pointing to the 'app/templates' directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount(
    "/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"
)
app.mount(
    "/assets", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"
)


def _render_notify_template(content: str, values: dict) -> str:
    """Simple replacement for ((placeholder)) style tags."""
    if not values:
        return content
    for key, val in values.items():
        # Notify uses double parentheses like ((name))
        placeholder = f"(({key}))"
        content = content.replace(placeholder, str(val))
    return content


@app.get("/", include_in_schema=False)
async def root(request: Request, db: Session = Depends(get_db)):
    # Fetch all data from DB for the dashboard
    notifications = db.query(Notification).all()
    templates_list = db.query(Template).all()

    # Convert ORM objects to dicts for JSON serialization in the frontend
    notifications_data = [
        {c.name: getattr(n, c.name) for c in n.__table__.columns} for n in notifications
    ]
    templates_data = [
        {c.name: getattr(t, c.name) for c in t.__table__.columns}
        for t in templates_list
    ]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "notifications": notifications,
            "templates": templates_list,
            # Pass the raw data as a JSON string for the frontend to use
            "notifications_json": json.dumps(notifications_data, default=str),
            "templates_json": json.dumps(templates_data, default=str),
        },
    )


@app.get("/healthcheck", include_in_schema=False)
async def healthcheck():
    return {"message": "Notify.pit is running"}


# --- NOTIFICATIONS ENDPOINTS ---


@app.post("/v2/notifications/sms", status_code=201)
async def send_sms(
    payload: SmsRequest,
    token: dict = Depends(validate_notify_jwt),
    db: Session = Depends(get_db),
):
    new_id = str(uuid.uuid4())
    db_item = Notification(
        id=new_id,
        type="sms",
        created_at=datetime.now(timezone.utc).isoformat(),
        reference=payload.reference,
        phone_number=payload.phone_number,
        template_id=str(payload.template_id),
        personalisation=payload.personalisation,
    )
    db.add(db_item)
    db.commit()
    return {"id": new_id, "reference": payload.reference}


@app.post("/v2/notifications/email", status_code=201)
async def send_email(
    payload: EmailRequest,
    token: dict = Depends(validate_notify_jwt),
    db: Session = Depends(get_db),
):
    new_id = str(uuid.uuid4())
    db_item = Notification(
        id=new_id,
        type="email",
        created_at=datetime.now(timezone.utc).isoformat(),
        reference=payload.reference,
        email_address=payload.email_address,
        template_id=str(payload.template_id),
        personalisation=payload.personalisation,
    )
    db.add(db_item)
    db.commit()
    return {"id": new_id, "reference": payload.reference}


@app.post("/v2/notifications/letter", status_code=201)
async def send_letter(
    payload: LetterRequest,
    token: dict = Depends(validate_notify_jwt),
    db: Session = Depends(get_db),
):
    new_id = str(uuid.uuid4())
    # Letter recipients are embedded in personalisation usually,
    # but we store the blob
    db_item = Notification(
        id=new_id,
        type="letter",
        created_at=datetime.now(timezone.utc).isoformat(),
        reference=payload.reference,
        template_id=str(payload.template_id),
        personalisation=payload.personalisation,
    )
    db.add(db_item)
    db.commit()
    return {"id": new_id, "reference": payload.reference}


@app.get("/v2/received-text-messages")
async def get_received_texts(
    token: dict = Depends(validate_notify_jwt), db: Session = Depends(get_db)
):
    """Notify API endpoint used by smoke tests to check replies."""
    sms_list = db.query(Notification).filter(Notification.type == "sms").all()

    results = []
    for sms in sms_list:
        content = "Mock Content"
        p = sms.personalisation or {}

        # If we had a specific 'content' field we could check it,
        # but currently logic relies on personalisation
        if "username" in p and "password" in p:
            content = f"Username:\n{p['username']}\nPassword:\n{p['password']}"
        elif not p:
            content = "Your GovWifi username and password has been removed"
        # Fallback for manual injection tests from original logic
        # In a real DB scenario, we might store 'content' on the model if needed specifically.
        # For now, we replicate logic based on personalisation existence.

        results.append(
            {
                "id": sms.id,
                "user_number": sms.phone_number,
                "notify_number": "407555000000",
                "service_id": "mock-service-id",
                "content": content,
                "created_at": sms.created_at,
            }
        )

    # For the specific test case `test_received_text_fallback_flow` where content was manually injected:
    # Since we can't easily "manually inject" into a DB object that lacks the column in a standard way
    # without altering the schema, we will stick to the standard behavior.
    # If explicit content support is required, we should add a `content` column to Notification.

    return {"received_text_messages": list(reversed(results))}


# --- TEMPLATE ENDPOINTS ---


@app.get("/v2/templates")
async def get_all_templates(
    type: Optional[str] = None,
    token: dict = Depends(validate_notify_jwt),
    db: Session = Depends(get_db),
):
    """List all templates, optionally filtered by type."""
    query = db.query(Template)
    if type:
        query = query.filter(Template.type == type)

    return {"templates": query.all()}


@app.get("/v2/template/{template_id}")
async def get_template_by_id(
    template_id: str,
    token: dict = Depends(validate_notify_jwt),
    db: Session = Depends(get_db),
):
    """Get a specific template."""
    t = db.query(Template).filter(Template.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@app.get("/v2/template/{template_id}/version/{version}")
async def get_template_version(
    template_id: str,
    version: int,
    token: dict = Depends(validate_notify_jwt),
    db: Session = Depends(get_db),
):
    # Mock behavior: just return current
    return await get_template_by_id(template_id, token, db)


@app.post("/v2/template/{template_id}/preview")
async def preview_template(
    template_id: str,
    request: Request,
    token: dict = Depends(validate_notify_jwt),
    db: Session = Depends(get_db),
):
    """Preview a template with personalisation."""
    t = db.query(Template).filter(Template.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        body = await request.json()
    except json.JSONDecodeError:
        body = {}

    personalisation = body.get("personalisation", {})

    rendered_body = _render_notify_template(t.body, personalisation)
    response = {
        "id": t.id,
        "type": t.type,
        "version": t.version,
        "body": rendered_body,
    }

    if t.type == "email" and t.subject:
        response["subject"] = _render_notify_template(t.subject, personalisation)

    return response


# --- PIT MANAGEMENT ENDPOINTS ---


@app.get("/pit/notifications")
async def get_pit_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).all()


@app.get("/pit/templates")
async def get_pit_templates(db: Session = Depends(get_db)):
    """Internal endpoint to list all templates without auth for the dashboard."""
    return db.query(Template).all()


@app.post("/pit/template", status_code=201)
async def create_pit_template(
    payload: CreateTemplateRequest, db: Session = Depends(get_db)
):
    """Internal endpoint to create a template for testing."""
    new_id = str(uuid.uuid4())
    db_item = Template(
        id=new_id,
        type=payload.type,
        name=payload.name,
        body=payload.body,
        subject=payload.subject,
        version=1,
        created_by="notify-pit@example.com",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.put("/pit/template/{template_id}")
async def update_pit_template(
    template_id: str, payload: CreateTemplateRequest, db: Session = Depends(get_db)
):
    """Internal endpoint to update a template."""
    t = db.query(Template).filter(Template.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")

    t.type = payload.type
    t.name = payload.name
    t.body = payload.body
    t.subject = payload.subject
    t.updated_at = datetime.now(timezone.utc).isoformat()
    t.version += 1

    db.commit()
    db.refresh(t)
    return t


@app.delete("/pit/template/{template_id}")
async def delete_pit_template(template_id: str, db: Session = Depends(get_db)):
    """Internal endpoint to delete a template."""
    t = db.query(Template).filter(Template.id == template_id).first()
    if t:
        db.delete(t)
        db.commit()
    return JSONResponse(content={"status": "deleted"}, status_code=200)


@app.delete("/pit/reset")
async def reset_pit(db: Session = Depends(get_db)):
    db.query(Notification).delete()
    db.query(Template).delete()
    db.commit()
    return {"status": "reset"}
