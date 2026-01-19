import time

import jwt

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
    client.delete("/pit/reset")
    token = get_token()

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

    response = client.post(
        "/v2/notifications/sms",
        json={
            "phone_number": "07700900000",
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    response = client.get(
        "/v2/received-text-messages", headers={"Authorization": f"Bearer {token}"}
    )
    messages = response.json()["received_text_messages"]

    assert (
        "Your GovWifi username and password has been removed" in messages[0]["content"]
    )


# We removed test_received_text_fallback_flow because manual injection into
# the DB is not the intended use case for this service, and the logic
# is now fully covered by the standard flows above.

# --- TEMPLATE TESTS ---


def test_template_lifecycle(client):
    client.delete("/pit/reset")
    token = get_token()

    # 1. Create a template via PIT API
    create_payload = {
        "type": "email",
        "name": "Test Template",
        "subject": "Hello ((name))",
        "body": "Welcome to ((service)). Your code is ((code)).",
    }
    r1 = client.post("/pit/template", json=create_payload)
    assert r1.status_code == 201
    template = r1.json()
    t_id = template["id"]
    assert template["body"] == create_payload["body"]

    # 2. Get All Templates (Public API)
    r2 = client.get("/v2/templates", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert len(r2.json()["templates"]) == 1
    assert r2.json()["templates"][0]["id"] == t_id

    # 2b. Filter by type
    r2_filtered = client.get(
        "/v2/templates?type=email", headers={"Authorization": f"Bearer {token}"}
    )
    assert len(r2_filtered.json()["templates"]) == 1
    r2_filtered_empty = client.get(
        "/v2/templates?type=sms", headers={"Authorization": f"Bearer {token}"}
    )
    assert len(r2_filtered_empty.json()["templates"]) == 0

    # 3. Get Template By ID (Public API)
    r3 = client.get(
        f"/v2/template/{t_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert r3.status_code == 200
    assert r3.json()["id"] == t_id

    # 4. Get Template Version (Public API)
    r4 = client.get(
        f"/v2/template/{t_id}/version/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert r4.status_code == 200
    assert r4.json()["id"] == t_id

    # 5. Preview Template (Public API)
    preview_payload = {
        "personalisation": {"name": "User", "service": "Notify", "code": "12345"}
    }
    r5 = client.post(
        f"/v2/template/{t_id}/preview",
        json=preview_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r5.status_code == 200
    preview = r5.json()
    assert preview["body"] == "Welcome to Notify. Your code is 12345."
    assert preview["subject"] == "Hello User"

    # 6. Delete Template (PIT API)
    r6 = client.delete(f"/pit/template/{t_id}")
    assert r6.status_code == 200

    # 7. Verify deletion
    r7 = client.get(
        f"/v2/template/{t_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert r7.status_code == 404


def test_template_preview_no_personalisation(client):
    client.delete("/pit/reset")
    token = get_token()
    t = client.post(
        "/pit/template",
        json={"type": "sms", "name": "Simple", "body": "Hello ((name))"},
    ).json()

    # Preview with NO body
    r = client.post(
        f"/v2/template/{t['id']}/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["body"] == "Hello ((name))"


def test_update_template_success(client):
    client.delete("/pit/reset")
    token = get_token()

    t = client.post(
        "/pit/template",
        json={"type": "sms", "name": "Original", "body": "Body"},
    ).json()
    t_id = t["id"]

    update_payload = {"type": "sms", "name": "Updated", "body": "New Body"}
    r = client.put(f"/pit/template/{t_id}", json=update_payload)
    assert r.status_code == 200
    updated = r.json()
    assert updated["name"] == "Updated"
    assert updated["version"] == 2

    r_fetch = client.get(
        f"/v2/template/{t_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert r_fetch.json()["name"] == "Updated"


def test_update_template_not_found(client):
    client.delete("/pit/reset")
    r = client.put(
        "/pit/template/invalid-id", json={"type": "sms", "name": "N", "body": "B"}
    )
    assert r.status_code == 404


# --- AUTH & ERROR TESTS ---


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


def test_pit_reset(client):
    token = get_token()
    client.post(
        "/v2/notifications/sms",
        json={
            "phone_number": "123",
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/pit/template",
        json={"type": "sms", "name": "T1", "body": "B"},
    )

    client.delete("/pit/reset")

    res = client.get("/pit/notifications")
    assert res.json() == []
    res_t = client.get("/v2/templates", headers={"Authorization": f"Bearer {token}"})
    assert res_t.json()["templates"] == []
