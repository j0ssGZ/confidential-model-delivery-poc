"""Instrument real signing/GCM and assert the exact Layer 3 boundaries."""

from pathlib import Path

import pytest

from confidential_model_delivery_poc import attested_consumer as attested
from confidential_model_delivery_poc import producer
from confidential_model_delivery_poc.bundle import BundleAuthenticationError, create_bundle_from_directory
from confidential_model_delivery_poc.cdh import KeyRetrievalError
from confidential_model_delivery_poc.signing import generate_signing_keys, load_private_key, sign_bundle


@pytest.fixture
def inputs(tmp_path):
    model = tmp_path / "source"
    model.mkdir()
    (model / "config.json").write_text("{}")
    private, public = tmp_path / "private", tmp_path / "public"
    generate_signing_keys(private, public)
    bundle = tmp_path / "bundle"
    bundle.write_bytes(create_bundle_from_directory(model, b"k" * 32,
        source_model=producer.MODEL_ID, source_revision=producer.MODEL_REVISION))
    signature = tmp_path / "signature"
    signature.write_bytes(sign_bundle(bundle.read_bytes(), load_private_key(private)))
    return bundle, signature, public


def forbidden(*args):
    pytest.fail("a forbidden later stage ran")


def test_success_exact_order_snapshot_and_cleanup(inputs, tmp_path, monkeypatch):
    events = []
    bundle, signature, public = inputs
    def key():
        events.append("provider")
        bundle.write_bytes(b"changed after verification")
        return b"k" * 32
    def load(path):
        events.append("load")
        assert (path / "config.json").read_text() == "{}"
        return (1, 384)
    monkeypatch.setattr(attested, "load_embedding", load)
    work = tmp_path / "work"
    work.mkdir()
    (work / "preserve").write_text("old")
    assert attested.consume_attested_bundle(*inputs, key, work, events.append) == (1, 384)
    assert events == ["signature_verified", "key_requested", "provider", "key_retrieved", "bundle_authenticated", "load"]
    assert list(work.iterdir()) == [work / "preserve"]


@pytest.mark.parametrize("fault", ["bundle", "signature", "public"])
def test_signature_failure_never_calls_provider_or_decrypt(inputs, tmp_path, monkeypatch, fault):
    bundle, signature, public = inputs
    if fault == "public":
        generate_signing_keys(tmp_path / "other-private", tmp_path / "other-public")
        public = tmp_path / "other-public"
    else:
        target = bundle if fault == "bundle" else signature
        target.write_bytes(target.read_bytes() + b"x")
    monkeypatch.setattr(attested, "decrypt_bundle", forbidden)
    with pytest.raises(ValueError):
        attested.consume_attested_bundle(bundle, signature, public, forbidden, tmp_path / "work")


def test_denied_resource_never_decrypts(inputs, tmp_path, monkeypatch):
    def denied():
        raise KeyRetrievalError("denied")
    monkeypatch.setattr(attested, "decrypt_bundle", forbidden)
    with pytest.raises(KeyRetrievalError):
        attested.consume_attested_bundle(*inputs, denied, tmp_path / "work")
    assert not (tmp_path / "work").exists()


@pytest.mark.parametrize("key", [b"x" * 31, b"x" * 33, "k" * 32, None])
def test_invalid_key_never_decrypts(inputs, tmp_path, monkeypatch, key):
    monkeypatch.setattr(attested, "decrypt_bundle", forbidden)
    with pytest.raises(KeyRetrievalError):
        attested.consume_attested_bundle(*inputs, lambda: key, tmp_path / "work")


def test_wrong_aes_fails_before_extraction(inputs, tmp_path, monkeypatch):
    events = []
    monkeypatch.setattr(attested, "extract_verified_tar", forbidden)
    monkeypatch.setattr(attested, "load_embedding", forbidden)
    with pytest.raises(BundleAuthenticationError):
        attested.consume_attested_bundle(*inputs, lambda: b"w" * 32, tmp_path / "work", events.append)
    assert events == ["signature_verified", "key_requested", "key_retrieved"]


def test_load_failure_cleans_only_own_plaintext(inputs, tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    (work / "old").write_text("preserve")
    def fail(path):
        raise RuntimeError("load failed")
    monkeypatch.setattr(attested, "load_embedding", fail)
    with pytest.raises(RuntimeError):
        attested.consume_attested_bundle(*inputs, lambda: b"k" * 32, work)
    assert list(work.iterdir()) == [work / "old"]


def test_cli_sanitizes_unexpected_errors(inputs, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(attested, "retrieve_key", lambda *a: (_ for _ in ()).throw(RuntimeError("private-value")))
    bundle, signature, public = inputs
    with pytest.raises(SystemExit) as error:
        attested.main(["--bundle", str(bundle), "--signature", str(signature),
                      "--public-key", str(public), "--work-dir", str(tmp_path / "work"),
                      "--key-resource", "a/b/c"])
    assert error.value.code == 2
    assert "private-value" not in capsys.readouterr().err
