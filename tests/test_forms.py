import pytest

from pretalx_webhooks.forms import WebhookSettingsForm

from .helpers import form_data

pytestmark = pytest.mark.django_db


def test_empty_url_is_saved(event, hook):
    form = WebhookSettingsForm(form_data(url=""), event=event)
    assert form.is_valid(), form.errors
    form.save()
    hook.refresh_from_db()
    assert hook.url == ""


def test_action_type_uses_activity_log_filter_choices(event):
    form = WebhookSettingsForm(event=event)
    field = form.fields["action_type"]
    assert not field.widget.allow_multiple_selected
    assert ("pretalx.schedule.release", "Released") in dict(field.choices)["Schedule"]
