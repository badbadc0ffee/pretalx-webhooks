from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from pretalx.common.views.mixins import EventPermissionRequired

from .forms import WebhookSettingsFormSet
from .payload import payload_has_placeholders, render_payload


class WebhookSettingsView(EventPermissionRequired, FormView):
    permission_required = "event.update_event"
    template_name = "pretalx_webhooks/settings.html"
    form_class = WebhookSettingsFormSet

    def dispatch(self, request, *args, **kwargs):
        if "pretalx_webhooks" not in request.event.plugin_list:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "instance": self.request.event,
            "prefix": "webhooks",
        }

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        with transaction.atomic():
            form.save()
        message = str(_("Webhook settings saved."))
        for webhook_form in form.forms:
            if not webhook_form.cleaned_data.get("DELETE"):
                payload = webhook_form.cleaned_data.get("payload", "")
                if webhook_form.cleaned_data.get(
                    "method"
                ) != "GET" and payload_has_placeholders(payload):
                    rendered_payload = render_payload(payload, self.request.event)
                    message += " " + str(_("Rendered payload: {payload}")).format(
                        payload=rendered_payload
                    )
        messages.success(self.request, message)
        return super().form_valid(form)
