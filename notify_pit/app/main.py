from fastapi import FastAPI, Depends
from .auth import validate_notify_jwt
from .models import SmsRequest, EmailRequest, LetterRequest
import uuid

app = FastAPI(title="Notify.pit")
notifications_db = []


@app.post("/v2/notifications/sms", status_code=201)
async def send_sms(payload: SmsRequest, token: dict = Depends(validate_notify_jwt)):
    data = payload.model_dump()
    data.update({"id": str(uuid.uuid4()), "type": "sms"})
    notifications_db.append(data)
    return {"id": data["id"], "reference": data.get("reference")}


@app.post("/v2/notifications/email", status_code=201)
async def send_email(payload: EmailRequest, token: dict = Depends(validate_notify_jwt)):
    data = payload.model_dump()
    data.update({"id": str(uuid.uuid4()), "type": "email"})
    notifications_db.append(data)
    return {"id": data["id"], "reference": data.get("reference")}


# FIX: Added missing letter endpoint
@app.post("/v2/notifications/letter", status_code=201)
async def send_letter(
    payload: LetterRequest, token: dict = Depends(validate_notify_jwt)
):
    data = payload.model_dump()
    data.update({"id": str(uuid.uuid4()), "type": "letter"})
    notifications_db.append(data)
    return {"id": data["id"], "reference": data.get("reference")}


@app.get("/pit/notifications")
async def get_pit_notifications():
    return notifications_db


@app.delete("/pit/reset")
async def reset_pit():
    notifications_db.clear()
    return {"status": "reset"}
