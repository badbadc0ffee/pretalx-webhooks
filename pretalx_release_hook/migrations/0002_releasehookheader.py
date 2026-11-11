import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("pretalx_release_hook", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ReleaseHookHeader",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="Name")),
                ("value", models.TextField(blank=True, verbose_name="Value")),
                (
                    "settings",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="headers",
                        to="pretalx_release_hook.releasehooksettings",
                    ),
                ),
            ],
        )
    ]
