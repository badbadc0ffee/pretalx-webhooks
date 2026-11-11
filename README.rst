pretalx-release-hook
====================

Call one HTTP or HTTPS URL when a new schedule version is released.

Install in the pretalx environment::

    pip install /path/to/pretalx-release-hook
    python -m pretalx migrate

Restart pretalx. Enable the plugin for the event. Open **Settings → Release hook**.
Set the URL, GET/POST/PUT, payload, and optional HTTP header name/value pairs.
Leave the URL empty to disable the hook.

GET ignores the payload. POST and PUT send the payload as
UTF-8 text. JSON bodies use application/json. Other bodies use text/plain.
Event mail placeholders can be used in the payload, for example
``{"event":"{event_slug}"}``. JSON object braces do not need to be escaped.
Failed requests are logged.

Run tests::

    pip install -e ".[dev]"
    pytest
