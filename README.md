# Notify.pit

![Notify.pit's project icon which is a dog with a letter in its mouth](./docs/notify-pit-project-icon.png "Notify.pit")

A drop-in mock service for the **GOV.UK Notify API**. This service is
designed for local integration testing and end-to-end verification,
allowing teams to test notification logic without contacting real
government services.

<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/GovWifi/notify-pit/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-100%25-brightgreen.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/__init__.py">__init__.py</a></td><td>0</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/auth.py">auth.py</a></td><td>15</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/main.py">main.py</a></td><td>62</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><a href="https://github.com/GovWifi/notify-pit/blob/main/models.py">models.py</a></td><td>14</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><b>TOTAL</b></td><td><b>91</b></td><td><b>0</b></td><td><b>100%</b></td><td>&nbsp;</td></tr></tbody></table></details>
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
