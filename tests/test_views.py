import pytest
from django.http import Http404
from django.test import RequestFactory

from pretalx.event.models import Event

from pretalx_release_hook.models import ReleaseHookSettings
from pretalx_release_hook.views import ReleaseHookSettingsView

from .helpers import form_data, url

pytestmark = pytest.mark.django_db


def test_settings_view_rejects_inactive_plugin(event, orga_user):
    Event.objects.filter(pk=event.pk).update(plugins="")
    request = RequestFactory().get(url(event))
    request.event = Event.objects.get(pk=event.pk)
    request.user = orga_user
    with pytest.raises(Http404):
        ReleaseHookSettingsView.as_view()(request, event=event.slug)


def test_settings_survive_reload(orga_client, event):
    data = form_data(payload="\nreleased\n")
    response = orga_client.post(url(event), data)
    assert response.status_code == 302
    response = orga_client.get(url(event))
    form = response.context["form"]
    assert all(form.initial[name] == value for name, value in data.items())
    assert b"Hook settings saved." in response.content


def test_unsupported_url_scheme_error_is_visible(orga_client, event):
    response = orga_client.post(url(event), form_data(url="ftp://example.org"))
    assert response.status_code == 200
    assert response.context["form"].errors
    assert "Enter a valid URL." in response.content.decode()
    assert not ReleaseHookSettings.objects.exists()
