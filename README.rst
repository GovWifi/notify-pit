==========
Notify.pit
==========

.. image:: https://assets.publishing.service.gov.uk/media/65d342e5e1bdec7737322247/s300_Untitled__1_.png
   :alt: GOV.UK Notify
   :align: center

.. contents:: Table of Contents
   :depth: 2
   :local:

A drop-in mock service for the **GOV.UK Notify API**. This service is designed for local integration testing and end-to-end verification, allowing teams to test notification logic without contacting real government services.

Features
--------

* **API Parity**: Mocked implementations for SMS, Email, and Letter endpoints based on the official spec.
* **JWT Security**: Strictly validates JWT tokens using the 30-second expiry window and ``iss`` and ``iat`` claims.
* **Recovery APIs**: Custom ``/pit`` endpoints to retrieve or reset received data for test assertions.
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

To start the service on your local machine:

.. code-block:: bash

   docker run -p 8000:8000 notify-pit

The service will be available at ``http://localhost:8000``. You can view the interactive documentation at ``http://localhost:8000/docs``.

Testing and Coverage
--------------------

To run the test suite and verify code coverage, mount the local ``tests`` directory into the container to ensure the latest tests are run without a full rebuild:

.. code-block:: bash

   docker run -v $(pwd)/tests:/app/tests notify-pit pytest --cov=app tests/

PIT (Point-In-Time) Endpoints
-----------------------------

These extra endpoints are provided for testing and recovery purposes:

* **Get Received Data**: ``GET /pit/notifications``
* **Clear Store**: ``DELETE /pit/reset``