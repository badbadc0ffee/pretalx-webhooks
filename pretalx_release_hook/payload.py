import json

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _


def build_request(url, method, payload, custom_headers=()):
    URLValidator(schemes=["http", "https"])(url)
    if method not in {"GET", "POST", "PUT"}:
        raise ValidationError(_("Select GET, POST, or PUT."))
    body, headers = "", dict(custom_headers)
    if method != "GET" and payload:
        body = payload
        try:
            json.loads(payload)
        except (ValueError, RecursionError):
            content_type = "text/plain; charset=utf-8"
        else:
            content_type = "application/json"
        if not any(name.lower() == "content-type" for name in headers):
            headers["Content-Type"] = content_type
    return {"url": url, "method": method, "body": body, "headers": headers}
