from http.client import HTTPException
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pretalx.event.models import Event

from pretalx_release_hook import signals
from pretalx_release_hook.signals import navigation

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_data():
    return {
        "url": "https://example.org/hook",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": '{"version":"1.0"}',
    }


def test_https_request_sends_body_and_headers(request_data):
    with patch.object(signals, "HTTPSConnection") as factory:
        connection = factory.return_value
        response = connection.getresponse.return_value.__enter__.return_value
        response.status = 204
        assert signals.send_request(request_data) == 204
    factory.assert_called_once_with("example.org", None, timeout=10)
    assert connection.request.call_args.args == ("POST", "/hook")
    options = connection.request.call_args.kwargs
    assert options["body"] == request_data["body"].encode("utf-8")
    assert options["headers"] == request_data["headers"]
    connection.close.assert_called_once()


def test_transport_error_hides_exception_message(request_data):
    with patch.object(signals, "HTTPSConnection") as factory:
        connection = factory.return_value
        connection.request.side_effect = HTTPException("secret")
        with pytest.raises(signals.TransportError) as result:
            signals.send_request(request_data)
    assert "secret" not in str(result.value)
    connection.close.assert_called_once()


def test_missing_schedule_is_skipped():
    with patch.object(signals, "send_request") as send:
        signals.send_release_hook(999)
    send.assert_not_called()


def test_inactive_plugin_is_skipped(schedule, hook):
    Event.objects.filter(pk=schedule.event_id).update(plugins="")
    with patch.object(signals, "send_request") as send:
        signals.send_release_hook(schedule.pk)
    send.assert_not_called()


def test_hook_is_skipped_without_settings(schedule):
    with patch.object(signals, "send_request") as send:
        signals.send_release_hook(schedule.pk)
    send.assert_not_called()


def test_unsupported_url_scheme_logs_hook_failure(schedule, hook, caplog):
    hook.url = "ftp://example.org"
    hook.save()
    with patch.object(signals, "send_request") as send:
        signals.send_release_hook(schedule.pk)
    send.assert_not_called()
    assert "Release hook failed" in caplog.text


def test_http_failure_is_logged(schedule, hook, caplog):
    with patch.object(signals, "send_request", return_value=500) as send:
        signals.send_release_hook(schedule.pk)
    send.assert_called_once()
    assert "HTTP 500" in caplog.text


def test_release_hook_renders_mail_placeholders(schedule, hook):
    hook.payload = '{"event":"{event_slug}"}'
    hook.save()
    with patch.object(signals, "send_request", return_value=204) as send:
        signals.send_release_hook(schedule.pk)
    request = send.call_args.args[0]
    assert request["body"] == '{"event":"test"}'
    assert request["headers"]["Content-Type"] == "application/json"


def test_release_sends_hook_once_after_commit(
    schedule, hook, django_capture_on_commit_callbacks
):
    with (
        patch.object(signals, "send_request", return_value=204) as send,
        django_capture_on_commit_callbacks(execute=True),
    ):
        signals.release(sender=schedule.event, schedule=schedule)
        send.assert_not_called()
    send.assert_called_once()


def test_navigation_requires_permission(event):
    request = SimpleNamespace(event=event, user=MagicMock())
    request.user.has_perm.return_value = False
    assert navigation(event, request) == []
