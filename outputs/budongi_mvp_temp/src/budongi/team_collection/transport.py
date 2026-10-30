"""Keyed HTTP transport for lanes B/C/D: the only module that puts a key on the wire.

The resolved URL exists only inside fetch_page; journals and errors carry the
{KEY} template or a stable code. HTTP (plaintext) origins need the registry's
http_key_exposure_ack, which the caller passes as allow_http.
"""
from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

from . import contract as C
from ._reuse import secret_reflected, utc_z
from .base import RequestSpec
from .credentials import KeyHandle

ContractError = C.ContractError
CHUNK = 256 * 1024
AUTH_PARAM_NAMES = frozenset({"servicekey", "key", "apikey", "api_key", "auth", "token"})


def check_spec(spec: RequestSpec) -> None:
    """Reject a spec whose journalled parts could ever carry a key."""
    if spec.credential_ref is None:
        raise ContractError("keyless_spec_in_keyed_lane")
    if spec.url_template.count("{KEY}") != 1:
        raise ContractError("keyed_template_missing_key")
    if not spec.url_template.startswith(spec.origin.rstrip("/") + "/"):
        raise ContractError("origin_mismatch")
    for name, _ in (*spec.params, *spec.form, *spec.headers):
        if name.casefold() in AUTH_PARAM_NAMES:
            raise ContractError("auth_param_outside_template")


def build_url(spec: RequestSpec, handle: KeyHandle) -> str:
    """Resolve {KEY} (URL-encoded) and append non-auth params. Never journal the result."""
    check_spec(spec)
    url = spec.url_template.replace("{KEY}", urllib.parse.quote(handle.reveal(), safe=""))
    if spec.params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(list(spec.params))
    return url


def fetch_page(spec: RequestSpec, handle: KeyHandle, *, opener, allow_http: bool = False,
               clock=utc_z, timeout: float = 60, max_bytes: int = C.MAX_RESPONSE_BYTES) -> dict:
    """One keyed call -> {payload, http_status, content_type, retrieved_at_utc}.

    Raises ContractError codes only: authentication_error (never retried upstream),
    transient_http_error, http_error, transient_transport_error, response_too_large,
    key_reflected_in_response, http_key_not_acknowledged.
    """
    url = build_url(spec, handle)
    if urllib.parse.urlsplit(url).scheme != "https" and not allow_http:
        raise ContractError("http_key_not_acknowledged")
    data = urllib.parse.urlencode(list(spec.form)).encode("ascii") if spec.method == "POST" else None
    headers = {"User-Agent": C.USER_AGENT, **dict(spec.headers)}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=data, headers=headers, method=spec.method)
    retrieved_at = clock()
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        code = exc.code
        exc.close()
        if code in {401, 403}:
            raise ContractError("authentication_error") from None
        raise ContractError("transient_http_error" if code == 429 or code >= 500
                            else "http_error") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ContractError("transient_transport_error") from None  # no URL, no exception text
    with response:
        chunks, size = [], 0
        for chunk in iter(lambda: response.read(CHUNK), b""):
            size += len(chunk)
            if size > max_bytes:
                raise ContractError("response_too_large")
            chunks.append(chunk)
        payload = b"".join(chunks)
        status = response.status
        content_type = response.headers.get("Content-Type")
    if secret_reflected(payload, handle.reveal()):
        raise ContractError("key_reflected_in_response")  # payload is dropped, never persisted
    return {"payload": payload, "http_status": status, "content_type": content_type,
            "retrieved_at_utc": retrieved_at}
