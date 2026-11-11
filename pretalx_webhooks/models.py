from django.db import models
from django.utils.translation import gettext_lazy as _


class WebhookSettings(models.Model):
    event = models.OneToOneField("event.Event", on_delete=models.CASCADE)
    url = models.URLField(blank=True, verbose_name="URL")
    method = models.CharField(
        max_length=10, default="POST", choices=[(v, v) for v in ("GET", "POST", "PUT")]
    )
    payload = models.TextField(blank=True, default="", verbose_name=_("Payload"))


class WebhookHeader(models.Model):
    settings = models.ForeignKey(
        WebhookSettings, on_delete=models.CASCADE, related_name="headers"
    )
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    value = models.TextField(blank=True, verbose_name=_("Value"))
