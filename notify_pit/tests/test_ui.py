import pytest
from playwright.sync_api import Page, expect
import uuid
import os
import httpx
import jwt
import time

# Get the URL from environment (Docker) or default to localhost (Local)
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
# Default secret matches app/auth.py
SECRET = os.getenv("NOTIFY_SECRET", "3d844edf-8d35-48ac-975b-e847b4f122b0")


def create_token():
    """Generates a valid Notify JWT token."""
    payload = {"iss": "test-service", "iat": int(time.time())}
    return jwt.encode(payload, SECRET, algorithm="HS256")


@pytest.fixture(scope="function")
def api_client():
    """Returns a client for making HTTP requests to the running app."""
    return httpx.Client(base_url=BASE_URL)


@pytest.fixture(scope="function")
def seed_data(api_client):
    """
    Injects known data into the RUNNING app via HTTP requests.
    Requires Auth Headers.
    """
    # 1. Clear existing data (Does not require auth in our implementation)
    api_client.delete("/pit/reset")

    # 2. Generate Auth Header
    token = create_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Add an SMS
    r1 = api_client.post(
        "/v2/notifications/sms",
        json={"phone_number": "07700900001", "template_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert r1.status_code == 201, f"Seed SMS failed: {r1.text}"

    # 4. Add an Email
    r2 = api_client.post(
        "/v2/notifications/email",
        json={"email_address": "test@example.com", "template_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert r2.status_code == 201, f"Seed Email failed: {r2.text}"

    # 5. Add a Letter
    r3 = api_client.post(
        "/v2/notifications/letter",
        json={
            "template_id": str(uuid.uuid4()),
            "personalisation": {
                "address_line_1": "10 Downing St",
                "postcode": "SW1A 2AA",
            },
        },
        headers=headers,
    )
    assert r3.status_code == 201, f"Seed Letter failed: {r3.text}"


def test_dashboard_loads(page: Page, seed_data):
    page.goto(BASE_URL)
    expect(page).to_have_title("Notify.pit Dashboard")
    expect(page.locator("#total-count")).to_have_text("3")


def test_filter_by_type(page: Page, seed_data):
    page.goto(BASE_URL)
    page.select_option("#filter-type", "email")

    rows = page.locator("#notifications-table tbody tr:visible")
    expect(rows).to_have_count(1)
    expect(rows.first).to_contain_text("email")
    expect(page.locator("#total-count")).to_have_text("1")


def test_sort_columns(page: Page, seed_data):
    page.goto(BASE_URL)
    # Sort by Type -> Ascending (Email, Letter, SMS)
    # Note: Sorting relies on the exact text in the cell.
    # 'email', 'letter', 'sms' tags should sort alphabetically.
    page.click("button:has-text('Type')")

    rows = page.locator("#notifications-table tbody tr")

    # Check first row is email
    expect(rows.nth(0)).to_contain_text("email")
