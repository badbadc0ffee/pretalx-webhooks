import pytest

from pretalx_release_hook.forms import ReleaseHookSettingsForm

from .helpers import form_data

pytestmark = pytest.mark.django_db


def test_empty_url_is_saved(event, hook):
    form = ReleaseHookSettingsForm(form_data(url=""), event=event)
    assert form.is_valid(), form.errors
    form.save()
    hook.refresh_from_db()
    assert hook.url == ""
