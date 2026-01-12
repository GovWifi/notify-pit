import os

project_name = "notify_pit"
files = {
    "requirements.txt": "fastapi\nuvicorn\npyjwt\ncryptography\npytest\npytest-cov\nhttpx\npydantic\n",
    "Dockerfile": 'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY ./app /app/app\nCMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n',
    ".env.example": "NOTIFY_SECRET=3d844edf-8d35-48ac-975b-e847b4f122b0\nSERVICE_ID=26785a09-ab16-4eb0-8407-a37497a57506\n",
    "app/__init__.py": "",
    "app/auth.py": """import jwt
import time
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
# This matches the secret key format from the GOV.UK Notify spec
SECRET = "3d844edf-8d35-48ac-975b-e847b4f122b0"

def validate_notify_jwt(auth: HTTPAuthorizationCredentials = Security(security)):
    try:
        # Tokens must use HS256 and include 'iss' and 'iat'
        payload = jwt.decode(auth.credentials, SECRET, algorithms=["HS256"])
        # The token expires within 30 seconds of the current time
        if time.time() - payload['iat'] > 30:
            raise HTTPException(status_code=403, detail="Token expired")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
""",
    "app/models.py": """from pydantic import BaseModel, UUID4, EmailStr
from typing import Optional, Dict, Any

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
""",
    "app/main.py": """from fastapi import FastAPI, Depends
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
    return {"id": data['id'], "reference": data.get("reference")}

@app.post("/v2/notifications/email", status_code=201)
async def send_email(payload: EmailRequest, token: dict = Depends(validate_notify_jwt)):
    data = payload.model_dump()
    data.update({"id": str(uuid.uuid4()), "type": "email"})
    notifications_db.append(data)
    return {"id": data['id'], "reference": data.get("reference")}

@app.get("/pit/notifications")
async def get_pit_notifications():
    return notifications_db

@app.delete("/pit/reset")
async def reset_pit():
    notifications_db.clear()
    return {"status": "reset"}
""",
    "tests/__init__.py": "",
    "tests/conftest.py": """import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)
""",
    "tests/test_api.py": """import jwt
import time
from app.auth import SECRET

def test_sms_endpoint_authenticated(client):
    token = jwt.encode({"iss": "test-service", "iat": int(time.time())}, SECRET, algorithm="HS256")
    payload = {"phone_number": "07123456789", "template_id": "550e8400-e29b-41d4-a716-446655440000"}
    response = client.post("/v2/notifications/sms", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201

def test_sms_endpoint_unauthorized(client):
    response = client.post("/v2/notifications/sms", json={})
    assert response.status_code == 403
""",
}


def build():
    if not os.path.exists(project_name):
        os.makedirs(project_name)

    for path, content in files.items():
        full_path = os.path.join(project_name, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    print(f"Directory structure for '{project_name}' created successfully.")


if __name__ == "__main__":
    build()
