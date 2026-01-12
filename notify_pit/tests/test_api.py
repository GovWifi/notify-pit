import jwt
import time
from app.auth import SECRET


def get_token(secret=SECRET, iat=None):
    """Helper to generate JWTs with configurable timing/secrets."""
    payload = {"iss": "test-service", "iat": iat or int(time.time())}
    return jwt.encode(payload, secret, algorithm="HS256")


def test_sms_endpoint_success(client):
    token = get_token()
    payload = {
        "phone_number": "07123456789",
        "template_id": "550e8400-e29b-41d4-a716-446655440000",
    }
    response = client.post(
        "/v2/notifications/sms",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


def test_letter_endpoint_success(client):
    token = get_token()
    payload = {
        "template_id": "550e8400-e29b-41d4-a716-446655440000",
        "personalisation": {"address_line_1": "123 Test St", "postcode": "SW1A 1AA"},
    }
    response = client.post(
        "/v2/notifications/letter",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


def test_token_expired(client):
    token = get_token(iat=int(time.time()) - 60)
    response = client.post(
        "/v2/notifications/sms", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Token expired"


def test_token_invalid_secret(client):
    token = get_token(secret="wrong-secret")
    response = client.post(
        "/v2/notifications/sms", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid token"


def test_pit_recovery_and_reset(client):
    client.get("/pit/notifications")
    client.delete("/pit/reset")
    res = client.get("/pit/notifications")
    assert res.json() == []


def test_received_text_flow(client):
    token = get_token()

    # 1. Inject a message via PIT endpoint
    inject_payload = {
        "user_number": "447700900000",
        "notify_number": "07537417417",
        "content": "GO",
    }
    client.post("/pit/received-text", json=inject_payload)

    # 2. Retrieve it via the standard Notify API
    response = client.get(
        "/v2/received-text-messages", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    messages = response.json()["received_text_messages"]
    assert len(messages) == 1
    assert messages[0]["content"] == "GO"
    assert messages[0]["user_number"] == "447700900000"


def test_received_text_unauthorized(client):
    # Ensure standard security is applied to the new Notify endpoint
    response = client.get("/v2/received-text-messages")
    assert response.status_code == 401
