from django.urls import path

from .views import ReleaseHookSettingsView

urlpatterns = [
    path(
        "orga/event/<slug:event>/settings/p/pretalx_release_hook/",
        ReleaseHookSettingsView.as_view(),
        name="settings",
    )
]
