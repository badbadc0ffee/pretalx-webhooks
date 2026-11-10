from django.apps import AppConfig
from django.utils.translation import gettext_lazy

from . import __version__


class PluginApp(AppConfig):
    name = "pretalx_release_hook"
    verbose_name = "pretalx Release Hook"

    class PretalxPluginMeta:
        name = gettext_lazy("pretalx Release Hook")
        author = "Florian Mösch"
        description = gettext_lazy(
            "Call a webhook when a schedule version is released."
        )
        visible = True
        version = __version__
        category = "FEATURE"
        settings_links = [
            (gettext_lazy("Settings"), "plugins:pretalx_release_hook:settings", {})
        ]

    def ready(self):
        from . import signals  # noqa: PLC0415, F401
