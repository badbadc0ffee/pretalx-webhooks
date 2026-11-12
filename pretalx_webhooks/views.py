from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView

from pretalx.common.views.mixins import EventPermissionRequired

from .forms import WebhookHeaderFormSet, WebhookSettingsForm
from .models import WebhookSettings
from .payload import payload_has_placeholders, render_payload


class WebhookPluginMixin(EventPermissionRequired):
    permission_required = "event.update_event"

    def dispatch(self, request, *args, **kwargs):
        if "pretalx_webhooks" not in request.event.plugin_list:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class WebhookSettingsView(WebhookPluginMixin, TemplateView):
    template_name = "pretalx_webhooks/settings.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "webhooks": self.request.event.webhooks.order_by("pk"),
        }

    def post(self, request, *args, **kwargs):
        webhook = WebhookSettings.objects.create(event=request.event)
        return redirect(
            "plugins:pretalx_webhooks:webhook", event=request.event.slug, pk=webhook.pk
        )


class WebhookView(WebhookPluginMixin, FormView):
    template_name = "pretalx_webhooks/webhook.html"
    form_class = WebhookSettingsForm

    def dispatch(self, request, *args, **kwargs):
        self.webhook = request.event.webhooks.filter(pk=kwargs["pk"]).first()
        if not self.webhook:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "instance": self.webhook}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "header_formset" not in context:
            context["header_formset"] = WebhookHeaderFormSet(
                instance=self.webhook, prefix="headers"
            )
        return context

    def get_success_url(self):
        return reverse(
            "plugins:pretalx_webhooks:webhook",
            kwargs={"event": self.request.event.slug, "pk": self.webhook.pk},
        )

    def post(self, request, *args, **kwargs):
        if "delete" in request.POST:
            self.webhook.delete()
            messages.success(request, str(_("Webhook deleted.")))
            return redirect(
                "plugins:pretalx_webhooks:settings", event=request.event.slug
            )
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        header_formset = WebhookHeaderFormSet(
            self.request.POST, instance=self.webhook, prefix="headers"
        )
        if not header_formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, header_formset=header_formset)
            )

        with transaction.atomic():
            form.save()
            header_formset.save()

        message = str(_("Webhook settings saved."))
        payload = form.cleaned_data.get("payload", "")
        if form.cleaned_data.get("method") != "GET" and payload_has_placeholders(
            payload
        ):
            message += " " + str(_("Rendered payload: {payload}")).format(
                payload=render_payload(payload, self.request.event)
            )
        messages.success(self.request, message)
        return super().form_valid(form)

    def form_invalid(self, form):
        header_formset = WebhookHeaderFormSet(
            self.request.POST, instance=self.webhook, prefix="headers"
        )
        header_formset.is_valid()
        return self.render_to_response(
            self.get_context_data(form=form, header_formset=header_formset)
        )
