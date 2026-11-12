from django.urls import reverse


def form_data(**kwargs):
    return {
        "action_type": "pretalx.schedule.release",
        "url": "https://example.org/hook",
        "method": "POST",
        "payload": '{"action":"released"}',
        **kwargs,
    }


def header_form_data(*headers, prefix="headers"):
    data = {f"{prefix}-TOTAL_FORMS": str(len(headers)), f"{prefix}-INITIAL_FORMS": "0"}
    for index, (name, value) in enumerate(headers):
        data[f"{prefix}-{index}-name"] = name
        data[f"{prefix}-{index}-value"] = value
    return data


def url(event):
    return reverse("plugins:pretalx_webhooks:settings", kwargs={"event": event.slug})


def webhook_url(event, webhook):
    return reverse(
        "plugins:pretalx_webhooks:webhook",
        kwargs={"event": event.slug, "pk": webhook.pk},
    )


def webhook_data(*headers, **kwargs):
    return {**form_data(**kwargs), **header_form_data(*headers)}
