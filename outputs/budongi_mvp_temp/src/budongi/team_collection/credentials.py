"""Vault-backed key handles for keyed lanes (CRED-001). Keys never leave the collector process."""
from __future__ import annotations

import hashlib
import re
import urllib.parse
from contextlib import contextmanager

from .contract import ContractError

CREDENTIAL_ID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


class KeyHandle:
    """Holds one API key; repr and str never show it."""

    __slots__ = ("_value", "service", "key_ref")

    def __init__(self, service: str, value: str, credential_id: str):
        self._value = value
        self.service = service
        self.key_ref = hashlib.sha256(credential_id.encode("ascii")).hexdigest()

    def reveal(self) -> str:
        if not self._value:
            raise ContractError("credential_cleared")
        return self._value

    def clear(self) -> None:
        self._value = ""

    def __repr__(self) -> str:
        return f"KeyHandle(service={self.service!r}, key_ref={self.key_ref[:8]})"

    __str__ = __repr__


def resolve(credential_ids: dict, *, vault=None, expected_providers: dict | None = None) -> dict:
    """service -> opaque credential ID  =>  service -> KeyHandle (fails closed)."""
    expected_providers = expected_providers or {}
    handles = {}
    for service, credential_id in credential_ids.items():
        if not CREDENTIAL_ID_RE.fullmatch(credential_id or ""):
            raise ContractError("invalid_opaque_credential_id")
        if vault is None:
            from budongi.credential_vault import CredentialVault  # cryptography loads only when a key is needed
            vault = CredentialVault()
        try:
            secret = vault.get_secret(credential_id, expected_provider_id=expected_providers.get(service))
        except Exception:  # vault/keystore errors are reported as one safe code
            raise ContractError("credential_unavailable") from None
        value = urllib.parse.unquote(secret.strip()).strip()
        if not value or any(ch.isspace() for ch in value):
            raise ContractError("credential_contains_internal_whitespace")
        handles[service] = KeyHandle(service, value, credential_id)
    return handles


@contextmanager
def opened(credential_ids: dict, **kwargs):
    handles = resolve(credential_ids, **kwargs)
    try:
        yield handles
    finally:
        for handle in handles.values():
            handle.clear()
