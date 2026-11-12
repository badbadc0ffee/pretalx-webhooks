from django.urls import path

from .views import WebhookSettingsView, WebhookView

urlpatterns = [
    path(
        "orga/event/<slug:event>/settings/p/pretalx_webhooks/",
        WebhookSettingsView.as_view(),
        name="settings",
    ),
    path(
        "orga/event/<slug:event>/settings/p/pretalx_webhooks/<int:pk>/",
        WebhookView.as_view(),
        name="webhook",
    ),
]
