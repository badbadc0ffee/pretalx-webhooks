import json
import re

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _

from pretalx.common.text.formatting import MODE_PLAIN, format_map
from pretalx.mail.domain.context import get_mail_context

PLACEHOLDER_RE = re.compile(r"(?<!{){([A-Za-z_][A-Za-z0-9_]*)}(?!})")


def payload_has_placeholders(payload):
    return bool(PLACEHOLDER_RE.search(payload))


def render_payload(payload, event):
    context = get_mail_context(event=event)
    placeholders = set(PLACEHOLDER_RE.findall(payload))
    if unknown := placeholders - context.keys():
        rendered = ", ".join("{" + name + "}" for name in sorted(unknown))
        raise ValidationError(str(_("Unknown placeholder!")) + " " + rendered)
    return PLACEHOLDER_RE.sub(
        lambda match: format_map(match.group(0), context, mode=MODE_PLAIN), payload
    )


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
