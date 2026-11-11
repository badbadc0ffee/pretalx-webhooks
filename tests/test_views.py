import html

import pytest
from django.http import Http404
from django.test import RequestFactory

from pretalx.event.models import Event

from pretalx_webhooks.models import WebhookSettings
from pretalx_webhooks.views import WebhookSettingsView

from .helpers import form_data, header_form_data, url

pytestmark = pytest.mark.django_db


def test_settings_view_rejects_inactive_plugin(event, orga_user):
    Event.objects.filter(pk=event.pk).update(plugins="")
    request = RequestFactory().get(url(event))
    request.event = Event.objects.get(pk=event.pk)
    request.user = orga_user
    with pytest.raises(Http404):
        WebhookSettingsView.as_view()(request, event=event.slug)


def test_settings_model_is_updated(orga_client, event):
    settings_data = form_data(
        payload="\nreleased\n", action_type="pretalx.event.activate"
    )
    headers = [("Authorization", "Bearer secret"), ("X-Event", "democon")]
    data = {**settings_data, **header_form_data(*headers)}
    response = orga_client.post(url(event), data)
    assert response.status_code == 302

    settings = WebhookSettings.objects.get(event=event)
    assert settings.url == settings_data["url"]
    assert settings.method == settings_data["method"]
    assert settings.payload == settings_data["payload"]
    assert settings.action_type == settings_data["action_type"]
    assert list(settings.headers.order_by("pk").values_list("name", "value")) == headers


def test_settings_survive_reload(orga_client, event):
    settings_data = form_data(
        payload="\nreleased\n", action_type="pretalx.event.activate"
    )
    headers = [("Authorization", "Bearer secret"), ("X-Event", "democon")]
    data = {**settings_data, **header_form_data(*headers)}
    response = orga_client.post(url(event), data, follow=True)

    assert response.redirect_chain == [(url(event), 302)]
    form = response.context["form"]
    assert all(form.initial[name] == value for name, value in settings_data.items())
    header_formset = response.context["header_formset"]
    assert [
        (form.initial["name"], form.initial["value"])
        for form in header_formset.initial_forms
    ] == headers
    assert b"Webhook settings saved." in response.content


def test_success_message_shows_rendered_payload(orga_client, event):
    response = orga_client.post(
        url(event), form_data(payload='{"event":"{event_slug}"}'), follow=True
    )
    assert response.status_code == 200
    content = html.unescape(response.content.decode())
    assert "Webhook settings saved." in content
    assert 'Rendered payload: {"event":"test"}' in content


def test_unsupported_url_scheme_error_is_visible(orga_client, event):
    response = orga_client.post(url(event), form_data(url="ftp://example.org"))
    assert response.status_code == 200
    assert response.context["form"].errors
    assert "Enter a valid URL." in response.content.decode()
    assert not WebhookSettings.objects.exists()


def test_invalid_header_value_error_is_visible(orga_client, event):
    data = {
        **form_data(),
        **header_form_data(("Authorization", "Bearer secret\r\nX-Injected: yes")),
    }
    response = orga_client.post(url(event), data)
    assert response.status_code == 200
    assert "valid HTTP header value" in response.content.decode()
    assert not WebhookSettings.objects.exists()


def test_unknown_payload_placeholder_error_is_visible(orga_client, event):
    response = orga_client.post(url(event), form_data(payload='{"event":"{unknown}"}'))
    assert response.status_code == 200
    assert "Unknown placeholder" in response.content.decode()
    assert not WebhookSettings.objects.exists()
