from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from pretalx.common.log import ACTION_TYPE_GROUPS, LOG_ALIASES, LOG_NAMES

from .models import WebhookHeader, WebhookSettings
from .payload import build_request, render_payload

LEGACY_ACTION_TYPES = {*LOG_ALIASES, "pretalx.submission.deleted"}
ACTION_TYPE_CHOICES = tuple(
    (
        group,
        tuple(
            (action_type, LOG_NAMES.get(action_type, label))
            for action_type, label in actions
            if action_type not in LEGACY_ACTION_TYPES
        ),
    )
    for group, actions in ACTION_TYPE_GROUPS.items()
)


class WebhookHeaderForm(forms.ModelForm):
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
        model = WebhookHeader
        fields = ("name", "value")


WebhookHeaderFormSet = inlineformset_factory(
    WebhookSettings, WebhookHeader, form=WebhookHeaderForm, extra=1, can_delete=True
)


class WebhookSettingsForm(forms.ModelForm):
    action_type = forms.ChoiceField(
        choices=ACTION_TYPE_CHOICES,
        initial="pretalx.schedule.release",
        label=_("Action"),
        widget=forms.Select(),
    )

    def __init__(self, *args, event=None, **kwargs):
        if event and "instance" not in kwargs:
            kwargs["instance"] = WebhookSettings.objects.filter(
                event=event
            ).first() or WebhookSettings(event=event)
        super().__init__(*args, **kwargs)
        self.fields["payload"].strip = False

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
        model = WebhookSettings
        fields = ("action_type", "url", "method", "payload")
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
