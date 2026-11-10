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
