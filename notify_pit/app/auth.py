import jwt
import time
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

SECRET = os.environ.get("NOTIFY_SECRET", "3d844edf-8d35-48ac-975b-e847b4f122b0")


def validate_notify_jwt(auth: HTTPAuthorizationCredentials = Security(security)):
    try:
        # Tokens must use HS256 and include 'iss' and 'iat'
        payload = jwt.decode(auth.credentials, SECRET, algorithms=["HS256"])
        # The token expires within 30 seconds of the current time
        if time.time() - payload["iat"] > 30:
            raise HTTPException(status_code=403, detail="Token expired")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
