from django.apps import AppConfig
from django.utils.translation import gettext_lazy

from . import __version__


class PluginApp(AppConfig):
    name = "pretalx_webhooks"
    verbose_name = "pretalx Webhooks"

    class PretalxPluginMeta:
        name = "pretalx Webhooks"
        author = "Florian Mösch"
        description = gettext_lazy("Call a webhook for selected event activity.")
        visible = True
        version = __version__
        category = "FEATURE"
        settings_links = [
            (gettext_lazy("Settings"), "plugins:pretalx_webhooks:settings", {})
        ]

    def ready(self):
        from . import signals  # noqa: PLC0415, F401
