import jwt
import time
import pytest
from app.auth import SECRET


def get_token(secret=SECRET, iat=None):
    """Helper to generate JWTs with configurable timing/secrets."""
    payload = {"iss": "test-service", "iat": iat or int(time.time())}
    return jwt.encode(payload, secret, algorithm="HS256")


def test_dashboard_at_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.content.decode().find("Notify.pit Dashboard") != -1


def test_root_endpoint(client):
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"message": "Notify.pit is running"}


# --- STANDARD NOTIFICATION TESTS ---


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
    assert "id" in response.json()


def test_email_endpoint_success(client):
    token = get_token()
    payload = {
        "email_address": "test@example.com",
        "template_id": "550e8400-e29b-41d4-a716-446655440000",
    }
    response = client.post(
        "/v2/notifications/email",
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


# --- RECEIVED TEXT (LOOPBACK) TESTS ---


def test_received_text_signup_flow(client):
    """Test Branch 1: Personalisation with username/password becomes the message content."""
    client.delete("/pit/reset")  # Ensure clean state
    token = get_token()

    # 1. Send SMS with credentials AND VALID UUID
    response = client.post(
        "/v2/notifications/sms",
        json={
            "phone_number": "07700900000",
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
            "personalisation": {"username": "user1", "password": "password1"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # 2. Check Loopback
    response = client.get(
        "/v2/received-text-messages", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    messages = response.json()["received_text_messages"]

    assert messages[0]["content"] == "Username:\nuser1\nPassword:\npassword1"
    assert messages[0]["user_number"] == "07700900000"


def test_received_text_deletion_flow(client):
    """Test Branch 2: Empty personalisation becomes 'removed' message."""
    client.delete("/pit/reset")
    token = get_token()

    # 1. Send SMS with NO personalisation AND VALID UUID
    response = client.post(
        "/v2/notifications/sms",
        json={
            "phone_number": "07700900000",
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # 2. Check Loopback
    response = client.get(
        "/v2/received-text-messages", headers={"Authorization": f"Bearer {token}"}
    )
    messages = response.json()["received_text_messages"]

    assert (
        "Your GovWifi username and password has been removed" in messages[0]["content"]
    )


def test_received_text_fallback_flow(client):
    """Test Branch 3: Manually injected content hits the fallback."""
    client.delete("/pit/reset")
    # Manually inject to force coverage of the explicit content path
    from app.main import notifications_db

    notifications_db.append(
        {
            "id": "manual-id",
            "type": "sms",
            "phone_number": "07700900000",
            "content": "Direct Content",
            "created_at": "2023-01-01T00:00:00",
        }
    )

    token = get_token()
    response = client.get(
        "/v2/received-text-messages", headers={"Authorization": f"Bearer {token}"}
    )

    msgs = [
        m for m in response.json()["received_text_messages"] if m["id"] == "manual-id"
    ]
    assert msgs[0]["content"] == "Direct Content"


# --- AUTH & ERROR TESTS ---


def test_token_expired(client):
    # Token issued 60 seconds ago (limit is 30)
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


def test_pit_reset(client):
    # Create data then clear it
    token = get_token()
    client.post(
        "/v2/notifications/sms",
        json={
            "phone_number": "123",
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    client.delete("/pit/reset")

    res = client.get("/pit/notifications")
    assert res.json() == []
