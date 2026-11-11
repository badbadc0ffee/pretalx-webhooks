from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from .models import ReleaseHookHeader, ReleaseHookSettings
from .payload import build_request, render_payload


class ReleaseHookHeaderForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Header"),
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Header")}),
        validators=[
            RegexValidator(
                regex=r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$",
                message=_("Enter a valid HTTP header name."),
            )
        ],
    )
    value = forms.CharField(
        label=_("Value"),
        required=False,
        strip=False,
        widget=forms.TextInput(attrs={"placeholder": _("Value")}),
        validators=[
            RegexValidator(
                regex=r"^[^\r\n]*$", message=_("Enter a valid HTTP header value.")
            )
        ],
    )

    class Meta:
        model = ReleaseHookHeader
        fields = ("name", "value")


ReleaseHookHeaderFormSet = inlineformset_factory(
    ReleaseHookSettings,
    ReleaseHookHeader,
    form=ReleaseHookHeaderForm,
    extra=1,
    can_delete=True,
)


class ReleaseHookSettingsForm(forms.ModelForm):
    def __init__(self, *args, event, **kwargs):
        instance = ReleaseHookSettings.objects.filter(
            event=event
        ).first() or ReleaseHookSettings(event=event)
        super().__init__(*args, instance=instance, **kwargs)
        self.fields["payload"].strip = False
        header_data = self.data if "headers-TOTAL_FORMS" in self.data else None
        self.header_formset = ReleaseHookHeaderFormSet(
            data=header_data, instance=self.instance, prefix="headers"
        )

    def is_valid(self):
        settings_valid = super().is_valid()
        headers_valid = (
            self.header_formset.is_valid() if self.header_formset.is_bound else True
        )
        return settings_valid and headers_valid

    def clean(self):
        data = super().clean()
        if not self.errors and data["url"]:
            try:
                payload = render_payload(data["payload"], self.instance.event)
                build_request(data["url"], data["method"], payload)
            except ValidationError as error:
                self.add_error(None, error)
        return data

    class Meta:
        model = ReleaseHookSettings
        fields = ("url", "method", "payload")
        help_texts = {
            "url": _("Use an HTTP or HTTPS URL. Leave empty to disable the hook."),
            "payload": _(
                "GET ignores the payload. POST and PUT send this text as the body. "
                "Event mail placeholders such as {event_slug} are supported."
            ),
        }
        widgets = {
            "url": forms.URLInput(attrs={"autocomplete": "off"}),
            "payload": forms.Textarea(attrs={"rows": 5}),
        }
