import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("event", "0044_event_locales_json")]

    operations = [
        migrations.CreateModel(
            name="ReleaseHookSettings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("url", models.URLField()),
                (
                    "method",
                    models.CharField(
                        max_length=10,
                        choices=[("GET", "GET"), ("POST", "POST"), ("PUT", "PUT")],
                        default="POST",
                    ),
                ),
                ("payload", models.TextField(default="")),
                (
                    "event",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="event.event"
                    ),
                ),
            ],
        )
    ]
