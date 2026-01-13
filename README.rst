==========
Notify.pit
==========

.. image:: https://assets.publishing.service.gov.uk/media/65d342e5e1bdec7737322247/s300_Untitled__1_.png
   :alt: GOV.UK Notify
   :align: center

A drop-in mock service for the **GOV.UK Notify API**. This service is designed for local integration testing and end-to-end verification, allowing teams to test notification logic without contacting real government services.

Features
--------

* **API Parity**: Mocked implementations for SMS, Email, Letter, and Received Text endpoints based on the official spec.
* **JWT Security**: Strictly validates JWT tokens using the 30-second expiry window and ``iss`` and ``iat`` claims.
* **Recovery APIs**: Custom ``/pit`` endpoints to retrieve, inject, or reset received data for test assertions.
* **High Reliability**: Maintained with a 93% test coverage threshold.

Prerequisites
-------------

* Docker installed and running.
* (Optional) Python 3.12+ for local development.

Installation & Build
--------------------

1. **Clone the repository**:

   .. code-block:: bash

      git clone https://github.com/yourusername/notify_pit.git
      cd notify_pit

2. **Build the Docker image**:

   .. code-block:: bash

      docker build -t notify-pit .

Running the Service
-------------------

To start the service on your local machine using the default configuration:

.. code-block:: bash

   docker run --rm -p 8000:8000 notify-pit

The service will be available at ``http://localhost:8000``.
You can view the interactive documentation at ``http://localhost:8000/docs``.

Configuration
-------------

By default, the service uses a hardcoded secret key for validation. If your client uses a specific API key, you must configure the service to match that key's secret.

To do this, set the ``NOTIFY_SECRET`` environment variable to the **last 36 characters** of your API key (the secret key UUID).

.. code-block:: bash

   # Example for API Key: key_name-iss_uuid-574329d4-b6dd-4982-9204-c33fc3c45dbb
   docker run --rm -p 8000:8000 -e NOTIFY_SECRET=574329d4-b6dd-4982-9204-c33fc3c45dbb notify-pit

Testing and Coverage
--------------------

To run the test suite and verify code coverage, mount the local ``tests`` directory into the container to ensure the latest tests are run without a full rebuild:

.. code-block:: bash

   docker run --rm -v $(pwd)/tests:/app/tests notify-pit pytest --cov=app tests/

Special Helper Endpoints
------------------------

These extra endpoints are provided for testing and recovery purposes:

* **Get Sent Notifications**: ``GET /pit/notifications``
* **Inject Received Text**: ``POST /pit/received-text`` (Simulates a user sending a text *to* Notify)
* **Clear Store**: ``DELETE /pit/reset`` (Wipes all sent and received data)
