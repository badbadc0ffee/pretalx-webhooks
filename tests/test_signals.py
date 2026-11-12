from http.client import HTTPException
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.contenttypes.models import ContentType

from pretalx.common.models.log import ActivityLog
from pretalx.event.models import Event
from pretalx.schedule.domain.release import freeze_schedule

from pretalx_webhooks import signals
from pretalx_webhooks.models import WebhookSettings
from pretalx_webhooks.signals import navigation

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


def test_inactive_plugin_is_skipped(schedule, hook, django_capture_on_commit_callbacks):
    Event.objects.filter(pk=schedule.event_id).update(plugins="")
    with (
        patch.object(signals, "send_request") as send,
        django_capture_on_commit_callbacks(execute=True) as callbacks,
    ):
        schedule.log_action("pretalx.schedule.release")
    assert callbacks == []
    send.assert_not_called()


def test_hook_is_skipped_without_settings(schedule, django_capture_on_commit_callbacks):
    with (
        patch.object(signals, "send_request") as send,
        django_capture_on_commit_callbacks(execute=True) as callbacks,
    ):
        schedule.log_action("pretalx.schedule.release")
    assert callbacks == []
    send.assert_not_called()


def test_unsupported_url_scheme_logs_hook_failure(event, hook, caplog):
    hook.url = "ftp://example.org"
    hook.save()
    with patch.object(signals, "send_request") as send:
        signals.send_webhook(event, hook)
    send.assert_not_called()
    assert "Webhook failed" in caplog.text


def test_http_failure_is_logged(event, hook, caplog):
    with patch.object(signals, "send_request", return_value=500) as send:
        signals.send_webhook(event, hook)
    send.assert_called_once()
    assert "HTTP 500" in caplog.text


def test_webhook_renders_mail_placeholders(event, hook):
    hook.payload = '{"event":"{event_slug}"}'
    hook.save()
    with patch.object(signals, "send_request", return_value=204) as send:
        signals.send_webhook(event, hook)
    request = send.call_args.args[0]
    assert request["body"] == '{"event":"test"}'
    assert request["headers"]["Content-Type"] == "application/json"


def test_schedule_release_activity_log_sends_hook_after_commit(
    schedule, hook, django_capture_on_commit_callbacks
):
    with (
        patch.object(signals, "send_request", return_value=204) as send,
        django_capture_on_commit_callbacks(execute=True),
    ):
        schedule.log_action("pretalx.schedule.release")
        send.assert_not_called()
    send.assert_called_once()


def test_other_activity_log_action_does_not_send_hook(
    schedule, hook, django_capture_on_commit_callbacks
):
    with (
        patch.object(signals, "send_request") as send,
        django_capture_on_commit_callbacks(execute=True) as callbacks,
    ):
        schedule.log_action("pretalx.schedule.update")
    assert callbacks == []
    send.assert_not_called()


def test_selected_action_type_sends_hook(
    schedule, hook, django_capture_on_commit_callbacks
):
    hook.action_type = "pretalx.event.activate"
    hook.save()
    with (
        patch.object(signals, "send_request", return_value=204) as send,
        django_capture_on_commit_callbacks(execute=True),
    ):
        schedule.log_action("pretalx.event.activate")
    send.assert_called_once()


def test_event_can_have_multiple_webhooks(event, hook):
    second_hook = WebhookSettings.objects.create(
        event=event,
        action_type="pretalx.event.activate",
        url="https://example.org/activated",
    )
    assert list(event.webhooks.order_by("pk")) == [hook, second_hook]


def test_all_matching_webhooks_are_sent_after_commit(
    schedule, hook, django_capture_on_commit_callbacks
):
    WebhookSettings.objects.create(
        event=schedule.event,
        action_type="pretalx.schedule.release",
        url="https://example.org/second",
    )
    with (
        patch.object(signals, "send_request", return_value=204) as send,
        django_capture_on_commit_callbacks(execute=True) as callbacks,
    ):
        schedule.log_action("pretalx.schedule.release")
    assert len(callbacks) == 2
    assert {call.args[0]["url"] for call in send.call_args_list} == {
        hook.url,
        "https://example.org/second",
    }


def test_only_webhooks_matching_the_action_type_are_sent(
    schedule, hook, django_capture_on_commit_callbacks
):
    WebhookSettings.objects.create(
        event=schedule.event,
        action_type="pretalx.event.activate",
        url="https://example.org/activated",
    )
    with (
        patch.object(signals, "send_request", return_value=204) as send,
        django_capture_on_commit_callbacks(execute=True) as callbacks,
    ):
        schedule.log_action("pretalx.event.activate")
    assert len(callbacks) == 1
    assert send.call_args.args[0]["url"] == "https://example.org/activated"


def test_updated_activity_log_does_not_send_hook(
    schedule, hook, django_capture_on_commit_callbacks
):
    activity_log = schedule.log_action("pretalx.schedule.release")
    with (
        patch.object(signals, "send_request") as send,
        django_capture_on_commit_callbacks(execute=True),
    ):
        activity_log.data = {"updated": True}
        activity_log.save(update_fields=["data"])
    send.assert_not_called()


def test_activity_log_without_event_does_not_send_hook(
    schedule, hook, django_capture_on_commit_callbacks
):
    with (
        patch.object(signals, "send_request") as send,
        django_capture_on_commit_callbacks(execute=True) as callbacks,
    ):
        ActivityLog.objects.create(
            content_type=ContentType.objects.get_for_model(schedule),
            object_id=schedule.pk,
            action_type="pretalx.schedule.release",
        )
    assert callbacks == []
    send.assert_not_called()


def test_real_schedule_release_sends_hook_after_commit(
    event, hook, django_capture_on_commit_callbacks
):
    with (
        patch.object(signals, "send_request", return_value=204) as send,
        django_capture_on_commit_callbacks(execute=True),
    ):
        freeze_schedule(event.wip_schedule, "1.0", notify_speakers=False)
        send.assert_not_called()
    send.assert_called_once()


def test_navigation_requires_permission(event):
    request = SimpleNamespace(event=event, user=MagicMock())
    request.user.has_perm.return_value = False
    assert navigation(event, request) == []
