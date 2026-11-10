import logging
from functools import partial
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.db import transaction
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_scopes import scopes_disabled

from pretalx.orga.signals import nav_event_settings
from pretalx.schedule.models import Schedule
from pretalx.schedule.signals import schedule_release

from .models import ReleaseHookSettings
from .payload import build_request

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
def send_release_hook(schedule_id):
    schedule = Schedule.objects.select_related("event").filter(pk=schedule_id).first()
    if not schedule:
        return
    event = schedule.event
    if "pretalx_release_hook" not in event.plugin_list:
        return
    config = ReleaseHookSettings.objects.filter(event=event).first()
    if not config or not config.url:
        return
    try:
        status = send_request(build_request(config.url, config.method, config.payload))
    except (ValidationError, TransportError):
        logger.warning("Release hook failed for schedule %s.", schedule_id)
        return
    if not 200 <= status < 300:
        logger.warning(
            "Release hook returned HTTP %s for schedule %s.", status, schedule_id
        )


@receiver(schedule_release, dispatch_uid="release_hook_schedule")
def release(sender, schedule, **kwargs):
    transaction.on_commit(partial(send_release_hook, schedule.pk), robust=True)


@receiver(nav_event_settings, dispatch_uid="release_hook_navigation")
def navigation(sender, request, **kwargs):
    if not request.user.has_perm("event.update_event", request.event):
        return []
    name = "plugins:pretalx_release_hook:settings"
    return [
        {
            "label": _("Release hook"),
            "url": reverse(name, kwargs={"event": request.event.slug}),
            "active": request.resolver_match.view_name == name,
        }
    ]
