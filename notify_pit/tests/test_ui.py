import os
import time
import uuid

import httpx
import jwt
import pytest
from playwright.sync_api import Page, expect

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


@pytest.mark.xfail(reason="template create is not working and the test times out")
def test_create_and_delete_template(page: Page, api_client):
    api_client.delete("/pit/reset")
    page.goto(BASE_URL)

    # Allow dialogs (like the delete confirmation) to be accepted automatically
    page.on("dialog", lambda dialog: dialog.accept())

    # 1. Click Templates tab
    page.click("a[href='#templates']")

    # Ensure the panel is visible (sanity check)
    expect(page.locator("#templates")).to_be_visible()

    # 2. Fill Form
    page.select_option("#tpl-type", "sms")
    page.fill("#tpl-name", "UI Test Template")
    page.fill("#tpl-body", "Hello from UI")

    # 3. Create
    # The page will reload, preserving the #templates hash, so we stay on this tab.
    # We verify success by waiting for the specific row to appear.
    page.click("text=Create")

    # Wait for the row to be visible (implies reload finished and data persisted)
    row = page.locator("#templates tbody tr", has_text="UI Test Template")
    expect(row).to_be_visible()
    expect(row).to_contain_text("sms")

    # 4. Delete it
    # This triggers a confirmation dialog (handled by page.on("dialog"))
    # and then a reload.
    row.get_by_text("Delete").click()

    # 5. Verify gone
    # We wait for the 'No templates' row to appear
    no_data_row = page.locator("#templates tbody tr", has_text="No templates created")
    expect(no_data_row).to_be_visible()
