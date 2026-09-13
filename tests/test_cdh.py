"""CDH transport boundaries; no real secrets or external endpoints."""

import pytest

from confidential_model_delivery_poc import cdh


def connection(monkeypatch, payload=b"k" * 32, status=200, failure=None):
    events = []

    class Connection:
        def __init__(self, host, port, timeout):
            events.append((host, port, timeout))

        def request(self, method, path):
            events.append((method, path))
            if failure:
                raise failure

        def getresponse(self):
            return self

        def read(self, limit):
            events.append(("read", limit))
            return payload[:limit]

        def close(self):
            events.append("closed")

    Connection.status = status
    monkeypatch.setattr(cdh.http.client, "HTTPConnection", Connection)
    return events


def test_local_endpoint_bounded_read_and_no_proxy(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://do-not-use.invalid:1234")
    events = connection(monkeypatch)
    assert cdh.retrieve_key("default/key/minilm-l6-v2") == b"k" * 32
    assert events == [("127.0.0.1", 8006, 10.0),
                      ("GET", "/cdh/resource/default/key/minilm-l6-v2"), ("read", 33), "closed"]


@pytest.mark.parametrize("length", [0, 1, 21, 31, 33, 10000])
def test_rejects_wrong_lengths(monkeypatch, length):
    events = connection(monkeypatch, b"x" * length)
    with pytest.raises(cdh.KeyRetrievalError, match="exactly 32"):
        cdh.retrieve_key("default/test/resource")
    assert events[-1] == "closed"


@pytest.mark.parametrize("status", [301, 302, 307, 401, 403, 404, 500])
def test_http_failure_never_reads_body_or_follows_redirect(monkeypatch, status):
    events = connection(monkeypatch, status=status)
    with pytest.raises(cdh.KeyRetrievalError, match="denied or unavailable"):
        cdh.retrieve_key("default/test/resource")
    assert ("read", 33) not in events
    assert events[-1] == "closed"


@pytest.mark.parametrize("resource", ["", "../key/a", "a/b/..", "a/b/c?x=y", "a/b/c%2F", "http://remote/a", "a/b/c/d"])
def test_invalid_identifier_makes_no_connection(monkeypatch, resource):
    events = connection(monkeypatch)
    with pytest.raises(cdh.KeyRetrievalError):
        cdh.retrieve_key(resource)
    assert events == []


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), 61])
def test_invalid_timeout_makes_no_connection(monkeypatch, timeout):
    events = connection(monkeypatch)
    with pytest.raises(cdh.KeyRetrievalError):
        cdh.retrieve_key("a/b/c", timeout)
    assert events == []


def test_transport_error_sanitized(monkeypatch):
    events = connection(monkeypatch, failure=TimeoutError("secret-body-value"))
    with pytest.raises(cdh.KeyRetrievalError, match="retrieval failed") as error:
        cdh.retrieve_key("a/b/c")
    assert "secret-body-value" not in str(error.value)
    assert events[-1] == "closed"
