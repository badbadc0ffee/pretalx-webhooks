from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from pretalx.common.views.mixins import EventPermissionRequired

from .forms import ReleaseHookSettingsForm


class ReleaseHookSettingsView(EventPermissionRequired, FormView):
    permission_required = "event.update_event"
    template_name = "pretalx_release_hook/settings.html"
    form_class = ReleaseHookSettingsForm

    def dispatch(self, request, *args, **kwargs):
        if "pretalx_release_hook" not in request.event.plugin_list:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "event": self.request.event}

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header_formset"] = context["form"].header_formset
        return context

    def form_valid(self, form):
        with transaction.atomic():
            settings = form.save()
            form.header_formset.instance = settings
            form.header_formset.save()
        messages.success(self.request, _("Hook settings saved."))
        return super().form_valid(form)
