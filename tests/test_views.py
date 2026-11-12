import html

import pytest
from django.http import Http404
from django.test import RequestFactory

from pretalx.event.models import Event

from pretalx_webhooks.models import WebhookSettings
from pretalx_webhooks.views import WebhookSettingsView

from .helpers import form_data, url, webhook_formset_data

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
    data = webhook_formset_data({**settings_data, "headers": headers})
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
    data = webhook_formset_data({**settings_data, "headers": headers})
    response = orga_client.post(url(event), data, follow=True)

    assert response.redirect_chain == [(url(event), 302)]
    formset = response.context["form"]
    form = formset.forms[0]
    assert all(form.initial[name] == value for name, value in settings_data.items())
    header_formset = form.header_formset
    assert [
        (form.initial["name"], form.initial["value"])
        for form in header_formset.initial_forms
    ] == headers
    assert b"Webhook settings saved." in response.content


def test_success_message_shows_rendered_payload(orga_client, event):
    response = orga_client.post(
        url(event),
        webhook_formset_data(form_data(payload='{"event":"{event_slug}"}')),
        follow=True,
    )
    assert response.status_code == 200
    content = html.unescape(response.content.decode())
    assert "Webhook settings saved." in content
    assert 'Rendered payload: {"event":"test"}' in content


def test_unsupported_url_scheme_error_is_visible(orga_client, event):
    response = orga_client.post(
        url(event), webhook_formset_data(form_data(url="ftp://example.org"))
    )
    assert response.status_code == 200
    assert response.context["form"].errors
    assert "Enter a valid URL." in response.content.decode()
    assert not WebhookSettings.objects.exists()


def test_invalid_header_value_error_is_visible(orga_client, event):
    data = webhook_formset_data(
        {
            **form_data(),
            "headers": (("Authorization", "Bearer secret\r\nX-Injected: yes"),),
        }
    )
    response = orga_client.post(url(event), data)
    assert response.status_code == 200
    assert "valid HTTP header value" in response.content.decode()
    assert not WebhookSettings.objects.exists()


def test_unknown_payload_placeholder_error_is_visible(orga_client, event):
    response = orga_client.post(
        url(event), webhook_formset_data(form_data(payload='{"event":"{unknown}"}'))
    )
    assert response.status_code == 200
    assert "Unknown placeholder" in response.content.decode()
    assert not WebhookSettings.objects.exists()


def test_multiple_webhooks_are_saved_with_separate_headers(orga_client, event):
    response = orga_client.post(
        url(event),
        webhook_formset_data(
            {**form_data(), "headers": (("X-Hook", "first"),)},
            {
                **form_data(
                    action_type="pretalx.event.activate",
                    url="https://example.org/activated",
                ),
                "headers": (("X-Hook", "second"),),
            },
        ),
    )
    assert response.status_code == 302
    webhooks = list(event.webhooks.order_by("pk"))
    assert len(webhooks) == 2
    assert list(webhooks[0].headers.values_list("name", "value")) == [
        ("X-Hook", "first")
    ]
    assert list(webhooks[1].headers.values_list("name", "value")) == [
        ("X-Hook", "second")
    ]


def test_settings_dialog_has_an_additional_empty_webhook_form(orga_client, event, hook):
    response = orga_client.get(url(event))
    formset = response.context["form"]
    assert len(formset.initial_forms) == 1
    assert len(formset.extra_forms) == 1


def test_existing_webhook_is_updated(orga_client, event, hook):
    response = orga_client.post(
        url(event),
        webhook_formset_data(form_data(id=hook.pk, url="https://example.org/updated")),
    )
    assert response.status_code == 302
    hook.refresh_from_db()
    assert hook.url == "https://example.org/updated"
    assert event.webhooks.count() == 1


def test_existing_webhook_can_be_deleted(orga_client, event, hook):
    response = orga_client.post(
        url(event), webhook_formset_data(form_data(id=hook.pk, DELETE="on"))
    )
    assert response.status_code == 302
    assert not event.webhooks.exists()


def test_second_webhook_can_be_deleted(orga_client, event, hook):
    second_hook = WebhookSettings.objects.create(
        event=event,
        action_type="pretalx.event.activate",
        url="https://example.org/activated",
    )
    response = orga_client.post(
        url(event),
        webhook_formset_data(
            form_data(id=hook.pk), form_data(id=second_hook.pk, DELETE="on")
        ),
    )
    assert response.status_code == 302
    assert list(event.webhooks.all()) == [hook]


def test_empty_additional_form_does_not_create_webhook(orga_client, event):
    data = webhook_formset_data(form_data(url="", payload=""))
    response = orga_client.post(url(event), data)
    assert response.status_code == 302
    assert not event.webhooks.exists()


def test_webhook_delete_buttons_do_not_use_nested_formset_javascript(
    orga_client, event, hook
):
    WebhookSettings.objects.create(
        event=event,
        action_type="pretalx.event.activate",
        url="https://example.org/activated",
    )
    response = orga_client.get(url(event))
    content = response.content.decode()
    assert content.count("data-webhook-delete-button") == 2
    assert 'data-formset-prefix="webhooks"' not in content
