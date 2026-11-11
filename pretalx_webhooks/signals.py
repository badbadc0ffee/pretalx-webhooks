import logging
from functools import partial
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_scopes import scopes_disabled

from pretalx.common.models.log import ActivityLog
from pretalx.orga.signals import nav_event_settings

from .payload import build_request, render_payload

logger = logging.getLogger(__name__)


class TransportError(Exception):
    pass


def send_request(request):
    url = urlsplit(request["url"])
    connection_type = HTTPSConnection if url.scheme == "https" else HTTPConnection
    connection = connection_type(url.hostname, url.port, timeout=10)
    target = urlunsplit(("", "", url.path or "/", url.query, ""))
    try:
        connection.request(
            request["method"],
            target,
            body=request["body"].encode("utf-8") or None,
            headers=request["headers"],
        )
        with connection.getresponse() as response:
            return response.status
    except (HTTPException, OSError):
        raise TransportError from None
    finally:
        connection.close()


@scopes_disabled()
def send_webhook(event):
    config = event.webhooksettings
    try:
        headers = config.headers.values_list("name", "value")
        payload = render_payload(config.payload, event)
        status = send_request(
            build_request(config.url, config.method, payload, headers)
        )
    except (ValidationError, TransportError):
        logger.warning("Webhook failed for event %s.", event.slug)
        return
    if not 200 <= status < 300:
        logger.warning("Webhook returned HTTP %s for event %s.", status, event.slug)


@receiver(post_save, sender=ActivityLog, dispatch_uid="webhook_activity_log_created")
def activity_log_created(sender, instance, created, **kwargs):
    if not created:
        return
    event = instance.event
    if not event:
        return
    event.refresh_from_db(fields=["plugins"])
    if "pretalx_webhooks" not in event.plugin_list:
        return
    config = getattr(event, "webhooksettings", None)
    if not config or config.action_type != instance.action_type or not config.url:
        return
    transaction.on_commit(partial(send_webhook, event), robust=True)


@receiver(nav_event_settings, dispatch_uid="webhook_navigation")
def navigation(sender, request, **kwargs):
    if not request.user.has_perm("event.update_event", request.event):
        return []
    name = "plugins:pretalx_webhooks:settings"
    return [
        {
            "label": _("Webhook"),
            "url": reverse(name, kwargs={"event": request.event.slug}),
            "active": request.resolver_match.view_name == name,
        }
    ]
