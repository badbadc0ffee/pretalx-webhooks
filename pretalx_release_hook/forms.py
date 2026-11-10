from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import ReleaseHookSettings
from .payload import build_request


class ReleaseHookSettingsForm(forms.ModelForm):
    def __init__(self, *args, event, **kwargs):
        instance = ReleaseHookSettings.objects.filter(
            event=event
        ).first() or ReleaseHookSettings(event=event)
        super().__init__(*args, instance=instance, **kwargs)
        self.fields["payload"].strip = False

    def clean(self):
        data = super().clean()
        if not self.errors and data["url"]:
            try:
                build_request(data["url"], data["method"], data["payload"])
            except ValidationError as error:
                self.add_error(None, error)
        return data

    class Meta:
        model = ReleaseHookSettings
        fields = ("url", "method", "payload")
        help_texts = {
            "url": _("Use an HTTP or HTTPS URL. Leave empty to disable the hook."),
            "payload": _(
                "GET ignores the payload. POST and PUT send this text as the body."
            ),
        }
        widgets = {
            "url": forms.URLInput(attrs={"autocomplete": "off"}),
            "payload": forms.Textarea(attrs={"rows": 5}),
        }
