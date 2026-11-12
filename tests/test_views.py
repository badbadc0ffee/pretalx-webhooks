import html

import pytest
from django.http import Http404
from django.test import RequestFactory

from pretalx.event.models import Event

from pretalx_webhooks.models import WebhookHeader, WebhookSettings
from pretalx_webhooks.views import WebhookSettingsView

from .helpers import form_data, header_form_data, url, webhook_data, webhook_url

pytestmark = pytest.mark.django_db


def test_settings_view_rejects_inactive_plugin(event, orga_user):
    Event.objects.filter(pk=event.pk).update(plugins="")
    request = RequestFactory().get(url(event))
    request.event = Event.objects.get(pk=event.pk)
    request.user = orga_user
    with pytest.raises(Http404):
        WebhookSettingsView.as_view()(request, event=event.slug)


def test_settings_page_lists_webhooks(orga_client, event, hook):
    response = orga_client.get(url(event))
    content = response.content.decode()
    assert response.status_code == 200
    assert hook.url in content
    assert "A new schedule version was released." in content
    assert "pretalx.schedule.release" not in content
    assert webhook_url(event, hook) in content
    assert "settings.js" not in content


def test_add_webhook_creates_entry_and_redirects_to_details(orga_client, event):
    response = orga_client.post(url(event))
    webhook = WebhookSettings.objects.get(event=event)
    assert response.status_code == 302
    assert response.url == webhook_url(event, webhook)


def test_missing_webhook_returns_404(orga_client, event):
    missing_webhook = WebhookSettings(pk=123456, event=event)
    response = orga_client.get(webhook_url(event, missing_webhook))
    assert response.status_code == 404


def test_webhook_details_are_updated(orga_client, event, hook):
    settings_data = form_data(
        payload="\nreleased\n", action_type="pretalx.event.activate"
    )
    headers = [("Authorization", "Bearer secret"), ("X-Event", "democon")]
    response = orga_client.post(
        webhook_url(event, hook), webhook_data(*headers, **settings_data)
    )
    assert response.status_code == 302

    hook.refresh_from_db()
    assert hook.url == settings_data["url"]
    assert hook.method == settings_data["method"]
    assert hook.payload == settings_data["payload"]
    assert hook.action_type == settings_data["action_type"]
    assert list(hook.headers.order_by("pk").values_list("name", "value")) == headers


def test_webhook_details_survive_reload(orga_client, event, hook):
    settings_data = form_data(
        payload="\nreleased\n", action_type="pretalx.event.activate"
    )
    headers = [("Authorization", "Bearer secret"), ("X-Event", "democon")]
    response = orga_client.post(
        webhook_url(event, hook), webhook_data(*headers, **settings_data), follow=True
    )

    assert response.redirect_chain == [(webhook_url(event, hook), 302)]
    form = response.context["form"]
    assert all(form.initial[name] == value for name, value in settings_data.items())
    assert [
        (form.initial["name"], form.initial["value"])
        for form in response.context["header_formset"].initial_forms
    ] == headers
    assert b"Webhook settings saved." in response.content


def test_success_message_shows_rendered_payload(orga_client, event, hook):
    response = orga_client.post(
        webhook_url(event, hook),
        webhook_data(payload='{"event":"{event_slug}"}'),
        follow=True,
    )
    content = html.unescape(response.content.decode())
    assert "Webhook settings saved." in content
    assert 'Rendered payload: {"event":"test"}' in content


def test_unsupported_url_scheme_error_is_visible(orga_client, event, hook):
    response = orga_client.post(
        webhook_url(event, hook), webhook_data(url="ftp://example.org")
    )
    assert response.status_code == 200
    assert "Enter a valid URL." in response.content.decode()


def test_invalid_header_value_error_is_visible(orga_client, event, hook):
    response = orga_client.post(
        webhook_url(event, hook),
        webhook_data(("Authorization", "Bearer secret\r\nX-Injected: yes")),
    )
    assert response.status_code == 200
    assert "valid HTTP header value" in response.content.decode()
    assert not hook.headers.exists()


def test_unknown_payload_placeholder_error_is_visible(orga_client, event, hook):
    response = orga_client.post(
        webhook_url(event, hook), webhook_data(payload='{"event":"{unknown}"}')
    )
    assert response.status_code == 200
    assert "Unknown placeholder" in response.content.decode()


def test_header_can_be_deleted_without_javascript(orga_client, event, hook):
    header = WebhookHeader.objects.create(settings=hook, name="X-Old", value="yes")
    data = {
        **form_data(),
        **header_form_data(),
        "headers-TOTAL_FORMS": "2",
        "headers-INITIAL_FORMS": "1",
        "headers-0-id": str(header.pk),
        "headers-0-name": header.name,
        "headers-0-value": header.value,
        "headers-0-DELETE": "on",
        "headers-1-name": "",
        "headers-1-value": "",
    }
    response = orga_client.post(webhook_url(event, hook), data)
    assert response.status_code == 302
    assert not hook.headers.exists()


def test_webhook_can_be_deleted(orga_client, event, hook):
    response = orga_client.post(webhook_url(event, hook), {"delete": "1"})
    assert response.status_code == 302
    assert response.url == url(event)
    assert not event.webhooks.exists()
