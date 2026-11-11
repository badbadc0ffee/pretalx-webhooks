from django.urls import path

from .views import WebhookSettingsView

urlpatterns = [
    path(
        "orga/event/<slug:event>/settings/p/pretalx_webhooks/",
        WebhookSettingsView.as_view(),
        name="settings",
    )
]
