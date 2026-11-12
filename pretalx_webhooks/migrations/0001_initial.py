import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("event", "0044_event_locales_json")]

    operations = [
        migrations.CreateModel(
            name="WebhookSettings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                (
                    "action_type",
                    models.CharField(
                        default="pretalx.schedule.release", max_length=200
                    ),
                ),
                ("url", models.URLField()),
                ("method", models.CharField(default="POST", max_length=10)),
                ("payload", models.TextField(default="")),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="webhooks",
                        to="event.event",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WebhookHeader",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("value", models.TextField()),
                (
                    "settings",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="headers",
                        to="pretalx_webhooks.webhooksettings",
                    ),
                ),
            ],
        ),
    ]
