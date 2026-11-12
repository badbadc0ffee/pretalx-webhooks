pretalx-webhooks
================

Call configurable HTTP or HTTPS webhooks for selected pretalx event activity.

Install in the pretalx environment::

    pip install /path/to/pretalx-webhooks
    python -m pretalx migrate

Restart pretalx. Enable the plugin for the event. Open **Settings → Webhook**.
For every webhook, select an action and set the URL, GET/POST/PUT, payload,
and optional HTTP header name/value pairs. The additional empty form creates a
new webhook when saved. Leave a URL empty to disable that webhook.

GET ignores the payload. POST and PUT send the payload as
UTF-8 text. JSON bodies use application/json. Other bodies use text/plain.
Event mail placeholders can be used in the payload, for example
``{"event":"{event_slug}"}``. JSON object braces do not need to be escaped.
Failed requests are logged.

Run tests::

    pip install -e ".[dev]"
    pytest
