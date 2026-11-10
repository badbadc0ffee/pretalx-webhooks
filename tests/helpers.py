from django.urls import reverse


def form_data(**kwargs):
    return {
        "url": "https://example.org/hook",
        "method": "POST",
        "payload": '{"action":"released"}',
        **kwargs,
    }


def url(event):
    return reverse(
        "plugins:pretalx_release_hook:settings", kwargs={"event": event.slug}
    )
