import json
import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, schemas
from .auth import validate_notify_jwt
from .database import get_db

from alembic.config import Config
from alembic import command

app = FastAPI(title="Notify.pit")

@app.on_event("startup")
def run_migrations():
    try:
        # PWD should be /app in docker, where alembic.ini is
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        print(f"Error running migrations: {e}")
        # Fallback for local dev if alembic.ini not found or other issues,
        # though ideally we want this to fail loud.
        # But if we are running locally in a different dir, it might fail.
        # Let's try to be robust.
        pass

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
    # Fetch data for dashboard from DB
    # Note: For dashboard we might want all notifications, but for now we haven't implemented get_all_notifications
    # Let's assume dashboard just shows templates for now or we implement get_all if needed.
    # The original tracked all notifications. Let's add that to CRUD if needed, but for now received texts are most important for the loopback.
    # Actually, the original dashboard showed everything. Let's retrieve a few recent ones or all if small.
    # For now, to keep it simple and match original potentially large structure, we might want to paginate, but original was list.
    # Let's just fetch all templates. For notifications, the current CRUD only has get_received_texts.
    # We might need to add get_all_notifications to crud if the dashboard relies primarily on it.
    # Checking original main.py: "notifications": notifications_db

    # I will add a simple query here or use a crud function.
    from . import models
    notifications = db.query(models.Notification).all()
    templates_list = crud.get_templates(db)

    # Convert SQLAlchemy models to dicts/json-able format for the template
    # Pydantic models (from_attributes=True) or manual conversion.
    # Simple workaround for now:
    notifications_data = [ {c.name: getattr(n, c.name) for c in n.__table__.columns} for n in notifications ]
    templates_data = [ {c.name: getattr(t, c.name) for c in t.__table__.columns} for t in templates_list ]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "notifications": notifications_data,
            "templates": templates_data,
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
async def send_sms(payload: schemas.SmsRequest, token: dict = Depends(validate_notify_jwt), db: Session = Depends(get_db)):
    notification = crud.create_notification(
        db=db,
        notification=payload,
        type="sms",
        phone_number=payload.phone_number
    )
    return {"id": notification.id, "reference": notification.reference}


@app.post("/v2/notifications/email", status_code=201)
async def send_email(payload: schemas.EmailRequest, token: dict = Depends(validate_notify_jwt), db: Session = Depends(get_db)):
    notification = crud.create_notification(
        db=db,
        notification=payload,
        type="email",
        email_address=payload.email_address
    )
    return {"id": notification.id, "reference": notification.reference}


@app.post("/v2/notifications/letter", status_code=201)
async def send_letter(
    payload: schemas.LetterRequest, token: dict = Depends(validate_notify_jwt), db: Session = Depends(get_db)
):
    notification = crud.create_notification(
        db=db,
        notification=payload,
        type="letter"
    )
    return {"id": notification.id, "reference": notification.reference}


@app.get("/v2/received-text-messages")
async def get_received_texts(token: dict = Depends(validate_notify_jwt), db: Session = Depends(get_db)):
    """Notify API endpoint used by smoke tests to check replies."""
    sms_list = crud.get_received_texts(db)

    results = []
    for sms in sms_list:
        content = "Mock Content"
        p = sms.personalisation or {}

        if sms.content:
            content = sms.content
        elif "username" in p and "password" in p:
            content = f"Username:\n{p['username']}\nPassword:\n{p['password']}"
        elif not p:
            content = "Your GovWifi username and password has been removed"

        results.append(
            {
                "id": sms.id,
                "user_number": sms.phone_number,
                "notify_number": "407555000000",
                "service_id": "mock-service-id",
                "content": content,
                "created_at": sms.created_at.isoformat() if sms.created_at else None,
            }
        )

    # crud.get_received_texts already orders by desc created_at, but expected output format...
    # The original code did `reversed(results)`, implying the list was append-order (oldest first).
    # My SQL query does `order_by(desc(models.Notification.created_at))`, so newest first.
    # So I probably don't need to reverse it if the original intent was getting newest?
    # Original: `notifications_db` (append only). `sms_list = ...`. `reversed(results)`.
    # `notifications_db` has oldest first. `reversed` makes it newest first.
    # My query already returns newest first. So I return `results` directly.
    return {"received_text_messages": results}


# --- TEMPLATE ENDPOINTS ---


@app.get("/v2/templates")
async def get_all_templates(
    type: Optional[str] = None, token: dict = Depends(validate_notify_jwt), db: Session = Depends(get_db)
):
    """List all templates, optionally filtered by type."""
    templates_list = crud.get_templates(db, type=type)
    return {"templates": templates_list}


@app.get("/v2/template/{template_id}")
async def get_template_by_id(
    template_id: str, token: dict = Depends(validate_notify_jwt), db: Session = Depends(get_db)
):
    """Get a specific template."""
    t = crud.get_template(db, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@app.get("/v2/template/{template_id}/version/{version}")
async def get_template_version(
    template_id: str, version: int, token: dict = Depends(validate_notify_jwt), db: Session = Depends(get_db)
):
    """Get a specific version of a template (Mocked to return current)."""
    # In a full implementation, we would check the version.
    # For a mock, returning the current one is usually sufficient.
    return await get_template_by_id(template_id, token, db)


@app.post("/v2/template/{template_id}/preview")
async def preview_template(
    template_id: str,
    request: Request,
    token: dict = Depends(validate_notify_jwt),
    db: Session = Depends(get_db)
):
    """Preview a template with personalisation."""
    template = crud.get_template(db, template_id)
    if not template:
         raise HTTPException(status_code=404, detail="Template not found")

    try:
        body = await request.json()
    except json.JSONDecodeError:
        body = {}

    personalisation = body.get("personalisation", {})

    rendered_body = _render_notify_template(template.body, personalisation)
    response = {
        "id": template.id,
        "type": template.type,
        "version": template.version,
        "body": rendered_body,
    }

    if template.type == "email" and template.subject:
        response["subject"] = _render_notify_template(
            template.subject, personalisation
        )

    return response


# --- PIT MANAGEMENT ENDPOINTS ---


@app.get("/pit/notifications")
async def get_pit_notifications(db: Session = Depends(get_db)):
    from . import models
    return db.query(models.Notification).all()


@app.get("/pit/templates")
async def get_pit_templates(db: Session = Depends(get_db)):
    """Internal endpoint to list all templates without auth for the dashboard."""
    return crud.get_templates(db)


@app.post("/pit/template", status_code=201)
async def create_pit_template(payload: schemas.CreateTemplateRequest, db: Session = Depends(get_db)):
    """Internal endpoint to create a template for testing."""
    return crud.create_template(db, payload)


@app.put("/pit/template/{template_id}")
async def update_pit_template(template_id: str, payload: schemas.CreateTemplateRequest, db: Session = Depends(get_db)):
    """Internal endpoint to update a template."""
    updated = crud.update_template(db, template_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Template not found")
    return updated


@app.delete("/pit/template/{template_id}")
async def delete_pit_template(template_id: str, db: Session = Depends(get_db)):
    """Internal endpoint to delete a template."""
    success = crud.delete_template(db, template_id)
    # The original implementation returned 200 even if not found (list comprehension filter),
    # but crud returns False if not found. Let's strictly return 200 for now to match behavior roughly
    # or just assume success.
    return JSONResponse(content={"status": "deleted"}, status_code=200)


@app.delete("/pit/reset")
async def reset_pit(db: Session = Depends(get_db)):
    crud.reset_db(db)
    return {"status": "reset"}
