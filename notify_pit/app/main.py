import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .auth import validate_notify_jwt
from .models import CreateTemplateRequest, EmailRequest, LetterRequest, SmsRequest

app = FastAPI(title="Notify.pit")
notifications_db: list[dict[str, Any]] = []
templates_db: list[dict[str, Any]] = []

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
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "notifications": notifications_db,
            "templates": templates_db,
            # Pass the raw data as a JSON string for the frontend to use
            "notifications_json": json.dumps(notifications_db, default=str),
            "templates_json": json.dumps(templates_db, default=str),
        },
    )


@app.get("/healthcheck", include_in_schema=False)
async def healthcheck():
    return {"message": "Notify.pit is running"}


# --- NOTIFICATIONS ENDPOINTS ---


@app.post("/v2/notifications/sms", status_code=201)
async def send_sms(payload: SmsRequest, token: dict = Depends(validate_notify_jwt)):
    data = payload.model_dump()
    data.update(
        {
            "id": str(uuid.uuid4()),
            "type": "sms",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    notifications_db.append(data)
    return {"id": data["id"], "reference": data.get("reference")}


@app.post("/v2/notifications/email", status_code=201)
async def send_email(payload: EmailRequest, token: dict = Depends(validate_notify_jwt)):
    data = payload.model_dump()
    data.update(
        {
            "id": str(uuid.uuid4()),
            "type": "email",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    notifications_db.append(data)
    return {"id": data["id"], "reference": data.get("reference")}


@app.post("/v2/notifications/letter", status_code=201)
async def send_letter(
    payload: LetterRequest, token: dict = Depends(validate_notify_jwt)
):
    data = payload.model_dump()
    data.update(
        {
            "id": str(uuid.uuid4()),
            "type": "letter",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    notifications_db.append(data)
    return {"id": data["id"], "reference": data.get("reference")}


@app.get("/v2/received-text-messages")
async def get_received_texts(token: dict = Depends(validate_notify_jwt)):
    """Notify API endpoint used by smoke tests to check replies."""
    sms_list = [n for n in notifications_db if n.get("type") == "sms"]

    results = []
    for sms in sms_list:
        content = "Mock Content"
        p = sms.get("personalisation") or {}

        if "content" in sms:
            content = sms["content"]
        elif "username" in p and "password" in p:
            content = f"Username:\n{p['username']}\nPassword:\n{p['password']}"
        elif not p:
            content = "Your GovWifi username and password has been removed"

        results.append(
            {
                "id": sms["id"],
                "user_number": sms.get("phone_number"),
                "notify_number": "407555000000",
                "service_id": "mock-service-id",
                "content": content,
                "created_at": sms.get("created_at"),
            }
        )

    return {"received_text_messages": list(reversed(results))}


# --- TEMPLATE ENDPOINTS ---


@app.get("/v2/templates")
async def get_all_templates(
    type: Optional[str] = None, token: dict = Depends(validate_notify_jwt)
):
    """List all templates, optionally filtered by type."""
    if type:
        filtered = [t for t in templates_db if t["type"] == type]
        return {"templates": filtered}
    return {"templates": templates_db}


@app.get("/v2/template/{template_id}")
async def get_template_by_id(
    template_id: str, token: dict = Depends(validate_notify_jwt)
):
    """Get a specific template."""
    for t in templates_db:
        if t["id"] == template_id:
            return t
    raise HTTPException(status_code=404, detail="Template not found")


@app.get("/v2/template/{template_id}/version/{version}")
async def get_template_version(
    template_id: str, version: int, token: dict = Depends(validate_notify_jwt)
):
    """Get a specific version of a template (Mocked to return current)."""
    # In a full implementation, we would check the version.
    # For a mock, returning the current one is usually sufficient.
    return await get_template_by_id(template_id, token)


@app.post("/v2/template/{template_id}/preview")
async def preview_template(
    template_id: str,
    request: Request,
    token: dict = Depends(validate_notify_jwt),
):
    """Preview a template with personalisation."""
    template = await get_template_by_id(template_id, token)

    try:
        body = await request.json()
    except json.JSONDecodeError:
        body = {}

    personalisation = body.get("personalisation", {})

    rendered_body = _render_notify_template(template["body"], personalisation)
    response = {
        "id": template["id"],
        "type": template["type"],
        "version": template["version"],
        "body": rendered_body,
    }

    if template["type"] == "email" and template.get("subject"):
        response["subject"] = _render_notify_template(
            template["subject"], personalisation
        )

    return response


# --- PIT MANAGEMENT ENDPOINTS ---


@app.get("/pit/notifications")
async def get_pit_notifications():
    return notifications_db


@app.get("/pit/templates")
async def get_pit_templates():
    """Internal endpoint to list all templates without auth for the dashboard."""
    return templates_db


@app.post("/pit/template", status_code=201)
async def create_pit_template(payload: CreateTemplateRequest):
    """Internal endpoint to create a template for testing."""
    data = payload.model_dump()
    new_id = str(uuid.uuid4())
    template = {
        "id": new_id,
        "type": data["type"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "version": 1,
        "created_by": "notify-pit@example.com",
        "body": data["body"],
        "name": data["name"],
    }
    if data.get("subject"):
        template["subject"] = data["subject"]

    templates_db.append(template)
    return template


@app.put("/pit/template/{template_id}")
async def update_pit_template(template_id: str, payload: CreateTemplateRequest):
    """Internal endpoint to update a template."""
    for t in templates_db:
        if t["id"] == template_id:
            data = payload.model_dump()
            t.update(
                {
                    "type": data["type"],
                    "name": data["name"],
                    "body": data["body"],
                    "subject": data.get("subject"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "version": t["version"] + 1,
                }
            )
            return t
    raise HTTPException(status_code=404, detail="Template not found")


@app.delete("/pit/template/{template_id}")
async def delete_pit_template(template_id: str):
    """Internal endpoint to delete a template."""
    global templates_db
    templates_db = [t for t in templates_db if t["id"] != template_id]
    return JSONResponse(content={"status": "deleted"}, status_code=200)


@app.delete("/pit/reset")
async def reset_pit():
    notifications_db.clear()
    templates_db.clear()
    return {"status": "reset"}
