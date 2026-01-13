from fastapi import FastAPI, Depends
from .auth import validate_notify_jwt
from .models import SmsRequest, EmailRequest, LetterRequest
from datetime import datetime, timezone
import uuid

app = FastAPI(title="Notify.pit")
notifications_db = []


@app.get("/")
async def root():
    return {"message": "Notify.pit is running"}


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
    data.update({"id": str(uuid.uuid4()), "type": "email"})
    notifications_db.append(data)
    return {"id": data["id"], "reference": data.get("reference")}


@app.post("/v2/notifications/letter", status_code=201)
async def send_letter(
    payload: LetterRequest, token: dict = Depends(validate_notify_jwt)
):
    data = payload.model_dump()
    data.update({"id": str(uuid.uuid4()), "type": "letter"})
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

        # FIX: Check for explicit content FIRST to support manual injection
        if "content" in sms:
            content = sms["content"]
        # Branch 2: Signup logic (Username/Password)
        elif "username" in p and "password" in p:
            content = f"Username:\n{p['username']}\nPassword:\n{p['password']}"
        # Branch 3: Deletion logic (Empty personalisation)
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


@app.get("/pit/notifications")
async def get_pit_notifications():
    return notifications_db


@app.delete("/pit/reset")
async def reset_pit():
    notifications_db.clear()
    return {"status": "reset"}
