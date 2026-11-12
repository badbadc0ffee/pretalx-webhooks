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


def webhook_formset_data(*webhooks):
    initial_forms = sum(bool(webhook.get("id")) for webhook in webhooks)
    data = {
        "webhooks-TOTAL_FORMS": str(len(webhooks)),
        "webhooks-INITIAL_FORMS": str(initial_forms),
    }
    for index, webhook in enumerate(webhooks):
        webhook_values = webhook.copy()
        headers = webhook_values.pop("headers", ())
        values = form_data(**webhook_values)
        for name, value in values.items():
            data[f"webhooks-{index}-{name}"] = value
        data.update(header_form_data(*headers, prefix=f"webhooks-{index}-headers"))
    return data


def url(event):
    return reverse("plugins:pretalx_webhooks:settings", kwargs={"event": event.slug})
