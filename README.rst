pretalx-webhooks
================

``pretalx-webhooks`` sends HTTP requests for selected pretalx activity log
entries. Each event can use multiple webhooks.

Installation
------------

Install the plugin in the same Python environment as pretalx::

    python -m pip install pretalx-webhooks
    python -m pretalx migrate

Restart pretalx. In the organiser area, open **Settings → Plugins** and enable
the plugin for the event.

Configuration
-------------

Open **Settings → Webhook** in the event settings. The page lists all webhooks
for the event.

Select **Add webhook** to create a webhook. Then configure these fields:

* **Action**: The activity log entry that sends the webhook.
* **URL**: An HTTP or HTTPS target. An empty URL disables the webhook.
* **Method**: ``GET``, ``POST``, or ``PUT``.
* **Payload**: The request body for ``POST`` and ``PUT``.
* **HTTP Header**: Optional request header names and values.

Select a webhook in the list to edit or delete it.

Payload
-------

``GET`` does not send a request body. ``POST`` and ``PUT`` send the payload as
UTF-8 text. A valid JSON payload uses ``application/json``. Other payloads use
``text/plain`` unless a custom ``Content-Type`` header is present.

The payload supports pretalx event mail placeholders. For example::

    {"event": "{event_slug}"}

JSON object braces do not need escaping. The configuration page shows an error
for an unknown placeholder.

pretalx writes failed requests and non-success HTTP responses to its log.

Development
-----------

Install `uv`_ and `just`_. Then run the checks::

    just fmt-check
    just test

Use ``just install-pretalx-local /path/to/pretalx`` to test with a local pretalx
checkout.

License
-------

Copyright 2026 Florian Mösch

Released under the terms of the Apache License 2.0

.. _just: https://just.systems/
.. _uv: https://docs.astral.sh/uv/
