import pytest
from django.core.exceptions import ValidationError

from pretalx_release_hook.payload import build_request


def test_unsupported_method_is_rejected():
    with pytest.raises(ValidationError):
        build_request("https://example.org/hook", "DELETE", "")


def test_get_ignores_payload():
    url = "http://localhost/hook?existing=value"
    assert build_request(url, "GET", "text") == {
        "url": url,
        "method": "GET",
        "body": "",
        "headers": {},
    }


def test_custom_headers_are_added_to_request():
    assert build_request(
        "https://example.org/hook",
        "POST",
        '{"action":"released"}',
        [("Authorization", "Bearer secret"), ("X-Event", "democon")],
    )["headers"] == {
        "Authorization": "Bearer secret",
        "Content-Type": "application/json",
        "X-Event": "democon",
    }


def test_custom_content_type_overrides_inferred_content_type():
    request = build_request(
        "https://example.org/hook",
        "POST",
        '{"action":"released"}',
        [("Content-Type", "application/cloudevents+json")],
    )
    assert request["headers"] == {"Content-Type": "application/cloudevents+json"}
