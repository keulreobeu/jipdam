"""Facade over proven primitives from budongi.collection and jipdam_harness.

Pure outsourced units never import this module; they receive callables. Shells do.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
from datetime import datetime, timezone

from budongi.collection import (CollectionError, _NoRedirect, _secret_reflected, digest_file,
                                read_json, safe_file, write_json)
from jipdam_harness.contracts import safe as screen_outbound
from jipdam_harness.isolation import process_alive

from .contract import ContractError

__all__ = ["CollectionError", "ContractError", "digest_file", "read_json", "safe_file", "write_json",
           "secret_reflected", "screen_outbound", "process_alive", "utc_z", "no_proxy_opener",
           "file_opener"]


def utc_z(moment: datetime | None = None) -> str:
    """UTC ISO-8601 with a Z suffix, as team_collection_v1 requires for every *_utc field."""
    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        raise ContractError("naive_datetime")
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def secret_reflected(payload: bytes, key: str) -> bool:
    return _secret_reflected(payload, key)


def no_proxy_opener() -> urllib.request.OpenerDirector:
    """Keyed calls: ignore environment proxies (HTTP URLs carry keys) and refuse redirects."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())


class _AllowlistRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts: frozenset):
        super().__init__()
        self._hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        if target.scheme != "https" or (target.hostname or "").casefold() not in self._hosts:
            raise ContractError("redirect_not_allowed")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def file_opener(allowed_hosts) -> urllib.request.OpenerDirector:
    """Keyless downloads: no proxies; redirects only to allowlisted HTTPS hosts."""
    hosts = frozenset(h.casefold() for h in allowed_hosts)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _AllowlistRedirect(hosts),
                                       urllib.request.HTTPCookieProcessor())
