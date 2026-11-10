import json

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _


def build_request(url, method, payload):
    URLValidator(schemes=["http", "https"])(url)
    if method not in {"GET", "POST", "PUT"}:
        raise ValidationError(_("Select GET, POST, or PUT."))
    body, headers = "", {}
    if method != "GET" and payload:
        body = payload
        try:
            json.loads(payload)
        except (ValueError, RecursionError):
            headers = {"Content-Type": "text/plain; charset=utf-8"}
        else:
            headers = {"Content-Type": "application/json"}
    return {"url": url, "method": method, "body": body, "headers": headers}
