"""Keyed transport shell: key placement, plaintext ack, caps and error codes (no network)."""
from __future__ import annotations

import unittest
import urllib.error

from budongi.team_collection import contract as C
from budongi.team_collection.base import RequestSpec
from budongi.team_collection.credentials import KeyHandle
from budongi.team_collection.transport import build_url, fetch_page

CID = "12345678-1234-1234-1234-123456789abc"
KEY = "AbC123+xyz==key9876"


def spec(**overrides):
    fields = {"request_id": "r1", "lane": "B", "origin": "https://apis.data.go.kr",
              "url_template": "https://apis.data.go.kr/svc/list?serviceKey={KEY}&type=json",
              "credential_ref": "datagokr"}
    fields.update(overrides)
    return RequestSpec(**fields)


class FakeResponse:
    def __init__(self, payload=b"{}", status=200, content_type="application/json"):
        self.payload, self.status, self._offset = payload, status, 0
        self.headers = {"Content-Type": content_type}
        self.headers = type("H", (), {"get": lambda _self, name, default=None:
                                      content_type if name == "Content-Type" else default})()

    def read(self, n):
        chunk = self.payload[self._offset:self._offset + n]
        self._offset += n
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.urls = response or FakeResponse(), error, []

    def open(self, request, timeout=None):
        self.urls.append(request.full_url)
        if self.error:
            raise self.error
        return self.response


def http_error(code):
    return urllib.error.HTTPError("url", code, "msg", None, None)


class BuildUrlTests(unittest.TestCase):
    def test_key_is_encoded_into_template_and_params_follow(self):
        handle = KeyHandle("datagokr", KEY, CID)
        url = build_url(spec(params=(("pageNo", "1"),)), handle)
        self.assertIn("serviceKey=AbC123%2Bxyz%3D%3Dkey9876", url)
        self.assertIn("&pageNo=1", url)
        self.assertNotIn(KEY, url)  # only the encoded form is on the wire

    def test_specs_that_could_journal_a_key_are_refused(self):
        handle = KeyHandle("datagokr", KEY, CID)
        for bad, code in [
                (spec(credential_ref=None), "keyless_spec_in_keyed_lane"),
                (spec(url_template="https://apis.data.go.kr/svc/list"), "keyed_template_missing_key"),
                (spec(url_template="https://evil.example/x?serviceKey={KEY}"), "origin_mismatch"),
                (spec(params=(("serviceKey", "x"),)), "auth_param_outside_template"),
                (spec(headers=(("Token", "x"),)), "auth_param_outside_template")]:
            with self.assertRaisesRegex(C.ContractError, code):
                build_url(bad, handle)


class FetchPageTests(unittest.TestCase):
    def setUp(self):
        self.handle = KeyHandle("seoul_open_data", KEY, CID)
        self.seoul = spec(origin="http://openapi.seoul.go.kr:8088",
                          url_template="http://openapi.seoul.go.kr:8088/{KEY}/json/svc/1/1000/",
                          credential_ref="seoul_open_data")

    def test_http_needs_ack_and_result_carries_payload(self):
        opener = FakeOpener(FakeResponse(b'{"ok": 1}'))
        with self.assertRaisesRegex(C.ContractError, "http_key_not_acknowledged"):
            fetch_page(self.seoul, self.handle, opener=opener)
        result = fetch_page(self.seoul, self.handle, opener=opener, allow_http=True,
                            clock=lambda: "2026-10-30T01:00:00Z")
        self.assertEqual(result, {"payload": b'{"ok": 1}', "http_status": 200,
                                  "content_type": "application/json",
                                  "retrieved_at_utc": "2026-10-30T01:00:00Z"})
        self.assertIn("/AbC123%2Bxyz%3D%3Dkey9876/json/", opener.urls[-1])

    def test_error_codes_hide_transport_detail(self):
        for error, code in [(http_error(401), "authentication_error"),
                            (http_error(429), "transient_http_error"),
                            (http_error(500), "transient_http_error"),
                            (http_error(404), "http_error"),
                            (urllib.error.URLError("boom"), "transient_transport_error")]:
            with self.assertRaisesRegex(C.ContractError, code):
                fetch_page(spec(), self.handle, opener=FakeOpener(error=error))

    def test_size_cap_and_reflected_key_refuse_the_payload(self):
        with self.assertRaisesRegex(C.ContractError, "response_too_large"):
            fetch_page(spec(), self.handle, opener=FakeOpener(FakeResponse(b"x" * 64)), max_bytes=63)
        reflected = FakeOpener(FakeResponse(b"error key=" + KEY.encode("ascii")))
        with self.assertRaisesRegex(C.ContractError, "key_reflected_in_response"):
            fetch_page(spec(), self.handle, opener=reflected)


if __name__ == "__main__":
    unittest.main()
