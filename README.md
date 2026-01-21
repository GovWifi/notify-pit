# Notify.pit

<table>
  <tr>
    <td width="33%" valign="middle">
      <img src="./docs/notify-pit-project-icon.png" alt="Notify.pit Logo">
    </td>
    <td width="66%" valign="middle">
      <img src="./docs/ 2026-01-14-dashboard-screenshot.png" alt="Notify.pit Dashboard Screenshot">
    </td>
  </tr>
</table>

A drop-in mock service for the **GOV.UK Notify API**. This service is
designed for local integration testing and end-to-end verification,
allowing teams to test notification logic without contacting real
government services.

<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/GovWifi/notify-pit/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-94%25-brightgreen.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/__init__.py">__init__.py</a></td><td>0</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/auth.py">auth.py</a></td><td>15</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/crud.py">crud.py</a></td><td>57</td><td>2</td><td>96%</td><td><a href="https://github.com/GovWifi/notify-pit/blob/main/crud.py#L10">10</a>, <a href="https://github.com/GovWifi/notify-pit/blob/main/crud.py#L114">114</a></td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/database.py">database.py</a></td><td>12</td><td>4</td><td>66%</td><td><a href="https://github.com/GovWifi/notify-pit/blob/main/database.py#L18-L20">18&ndash;20</a>, <a href="https://github.com/GovWifi/notify-pit/blob/main/database.py#L22">22</a></td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/main.py">main.py</a></td><td>123</td><td>8</td><td>93%</td><td><a href="https://github.com/GovWifi/notify-pit/blob/main/main.py#L23">23</a>, <a href="https://github.com/GovWifi/notify-pit/blob/main/main.py#L25-L28">25&ndash;28</a>, <a href="https://github.com/GovWifi/notify-pit/blob/main/main.py#L33">33</a>, <a href="https://github.com/GovWifi/notify-pit/blob/main/main.py#L232">232</a>, <a href="https://github.com/GovWifi/notify-pit/blob/main/main.py#L268">268</a></td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/models.py">models.py</a></td><td>32</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/schemas.py">schemas.py</a></td><td>17</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><b>TOTAL</b></td><td><b>256</b></td><td><b>14</b></td><td><b>94%</b></td><td>&nbsp;</td></tr></tbody></table></details>
<!-- Pytest Coverage Comment:End -->

## Features

- **Web Dashboard**: A real-time visual dashboard at the root URL (`/`) to view sent notifications, styled with the GOV.UK Design System.
- **API Parity**: Mocked implementations for SMS, Email, Letter, and Received Text endpoints based on the official spec.
- **Loopback Logic**: Automatically generates "received" text messages based on sent SMS content (e.g. sending a signup SMS generates a reply with credentials).
- **JWT Security**: Strictly validates JWT tokens using the 30-second expiry window and `iss` and `iat` claims.
- **Recovery APIs**: Custom `/pit` endpoints to retrieve, inject, or reset received data for test assertions.

## Prerequisites

- Docker installed and running.
- (Optional) `make` tool (standard on Linux/Mac, available on
    Windows).

## Installation

**Clone the repository**:

``` bash
git clone https://github.com/yourusername/notify_pit.git
cd notify_pit
```

**Build the Docker image**:

You can use the provided Makefile to handle the build process:

``` bash
make build
```

Alternatively, using Docker directly:

``` bash
docker build -t notify-pit .
```

## Running the Service

To start the service on your local machine (port 8000) with
hot-reloading enabled:

``` bash
make run
```

The service will be available at <http://localhost:8000>.

- Dashboard: Visit <http://localhost:8000/> to view sent messages.
- API Docs: Visit <http://localhost:8000/docs> for interactive API documentation.

## Configuration

By default, the service uses a hardcoded secret key for validation. If
your client uses a specific API key, you must configure the service to
match that key\'s secret.

To do this, set the `NOTIFY_SECRET` environment variable. This should be
the **last 36 characters** of your API key (the secret key UUID).

``` bash
# Example for API Key: key_name-iss_uuid-574329d4-b6dd-4982-9204-c33fc3c45dbb
docker run --rm -p 8000:8000 -e NOTIFY_SECRET=574329d4-b6dd-4982-9204-c33fc3c45dbb notify-pit
```

## Testing and Coverage

We use pytest and pytest-cov to ensure the service behaves as expected. The Makefile maps your local directories into the container, so you can run tests against your latest code changes without rebuilding the image.

To run the full test suite and check coverage:

``` bash
make test
```

### Special Helper Endpoints

These extra endpoints are provided for testing and recovery purposes:

- **Web Dashboard**: `GET /` (Visual interface for sent notifications)
- **Healthcheck**: `GET /healthcheck` (Simple JSON status response)
- **Get Sent Notifications**: `GET /pit/notifications` (JSON list of all messages)
- **Get Received Texts**: `GET /v2/received-text-messages` (Implements loopback logic for smoke tests)
- **Clear Store**: `DELETE /pit/reset` (Wipes all sent and received data)
