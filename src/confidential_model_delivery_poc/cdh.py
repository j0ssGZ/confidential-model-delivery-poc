"""Bounded key retrieval from the CoCo CDH endpoint in the Pod namespace."""

from __future__ import annotations

import http.client
import math
import re

from confidential_model_delivery_poc.bundle import BundleError


class KeyRetrievalError(BundleError):
    """A deliberately sanitized CDH failure."""


def retrieve_key(resource: str, timeout: float = 10.0) -> bytes:
    """Read exactly 32 bytes; never follow redirects, proxies or remote URLs."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", resource):
        raise KeyRetrievalError("invalid CDH resource identifier")
    if not math.isfinite(timeout) or timeout <= 0 or timeout > 60:
        raise KeyRetrievalError("CDH timeout must be greater than zero and at most 60 seconds")
    connection = http.client.HTTPConnection("127.0.0.1", 8006, timeout=timeout)
    try:
        connection.request("GET", "/cdh/resource/" + resource)
        response = connection.getresponse()
        if response.status != 200:
            raise KeyRetrievalError("CDH resource retrieval denied or unavailable")
        key = response.read(33)
        if len(key) != 32:
            raise KeyRetrievalError("CDH key must contain exactly 32 bytes")
        return key
    except KeyRetrievalError:
        raise
    except Exception:
        raise KeyRetrievalError("CDH resource retrieval failed") from None
    finally:
        connection.close()
