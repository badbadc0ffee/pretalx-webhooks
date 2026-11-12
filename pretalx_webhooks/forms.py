from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils.translation import gettext_lazy as _

from pretalx.common.log import ACTION_TYPE_GROUPS

from .models import WebhookHeader, WebhookSettings
from .payload import build_request, render_payload

ACTION_TYPE_CHOICES = tuple(ACTION_TYPE_GROUPS.items())


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


class BaseWebhookSettingsFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.header_formset = WebhookHeaderFormSet(
            data=self.data if self.is_bound else None,
            instance=form.instance,
            prefix=f"{form.prefix}-headers",
        )

    def is_valid(self):
        settings_valid = super().is_valid()
        headers_valid = True
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            headers_valid = form.header_formset.is_valid() and headers_valid
        return settings_valid and headers_valid

    def save(self):
        instances = super().save()
        for form in self.forms:
            if form.instance.pk and not self._should_delete_form(form):
                form.header_formset.instance = form.instance
                form.header_formset.save()
        return instances


WebhookSettingsFormSet = inlineformset_factory(
    parent_model=WebhookSettings._meta.get_field("event").related_model,
    model=WebhookSettings,
    form=WebhookSettingsForm,
    formset=BaseWebhookSettingsFormSet,
    extra=1,
    can_delete=True,
)
