from django.urls import reverse


def form_data(**kwargs):
    return {
        "url": "https://example.org/hook",
        "method": "POST",
        "payload": '{"action":"released"}',
        **kwargs,
    }


def header_form_data(*headers):
    data = {"headers-TOTAL_FORMS": str(len(headers)), "headers-INITIAL_FORMS": "0"}
    for index, (name, value) in enumerate(headers):
        data[f"headers-{index}-name"] = name
        data[f"headers-{index}-value"] = value
    return data


def url(event):
    return reverse(
        "plugins:pretalx_release_hook:settings", kwargs={"event": event.slug}
    )
