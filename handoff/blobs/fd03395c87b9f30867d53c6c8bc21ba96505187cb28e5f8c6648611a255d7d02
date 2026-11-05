"""Current operator decision; no credentials, environment override, or ledger writes."""
from .contracts import HarnessError

# Legacy behavior is exercised only by offline fixtures patching this constant.
GMS_DEFERRED = True


def deferred(provider):
    return provider == "gms" and GMS_DEFERRED


def require_available(provider):
    if deferred(provider):
        raise HarnessError("DEFERRED_GMS")
