"""Verify signed pipeline ordering, byte identity and Layer 1 compatibility."""

from pathlib import Path

import pytest

from confidential_model_delivery_poc import consumer, producer, signed_consumer as signed
from confidential_model_delivery_poc.bundle import BundleAuthenticationError, BundleFormatError, create_bundle_from_directory
from confidential_model_delivery_poc.signing import generate_signing_keys, load_private_key, load_public_key, sign_bundle, verify_bundle


@pytest.fixture
def inputs(tmp_path):
    source = tmp_path / "model"
    source.mkdir()
    (source / "config.json").write_text("{}")
    key = tmp_path / "aes"
    key.write_bytes(b"k" * 32)
    private, public = tmp_path / "private", tmp_path / "public"
    generate_signing_keys(private, public)
    bundle = tmp_path / producer.BUNDLE_NAME
    bundle.write_bytes(create_bundle_from_directory(source, key.read_bytes(), source_model=producer.MODEL_ID, source_revision=producer.MODEL_REVISION))
    signature = Path(str(bundle) + ".sig")
    signature.write_bytes(sign_bundle(bundle.read_bytes(), load_private_key(private)))
    return source, key, private, public, bundle, signature


def test_positive_and_cleanup(inputs, tmp_path, monkeypatch):
    source, key, private, public, bundle, signature = inputs
    def load(path):
        assert (path / "config.json").read_text() == "{}"
        return (1, 384)
    monkeypatch.setattr(consumer, "load_embedding", load)
    work = tmp_path / "work"
    assert signed.consume_signed_bundle(bundle, signature, public, key, work) == (1, 384)
    assert not list(work.iterdir())


@pytest.mark.parametrize("fault", ["bundle", "signature", "missing_signature", "public"])
def test_signature_failures_never_decrypt(inputs, tmp_path, monkeypatch, fault):
    _, key, private, public, bundle, signature = inputs
    if fault == "bundle":
        bundle.write_bytes(bundle.read_bytes() + b"!")
    elif fault == "signature":
        signature.write_bytes(b"x" * 64)
    elif fault == "missing_signature":
        signature.unlink()
    else:
        public = tmp_path / "wrong-public"
        generate_signing_keys(tmp_path / "wrong-private", public)
    def forbidden(*args):
        pytest.fail("decryption/extraction/load must not run")
    for name in ("decrypt_bundle", "extract_verified_tar", "load_embedding"):
        monkeypatch.setattr(consumer, name, forbidden)
    with pytest.raises((ValueError, OSError)):
        signed.consume_signed_bundle(bundle, signature, public, key, tmp_path / "work")
    assert not (tmp_path / "work").exists()


def test_verified_bytes_survive_file_replacement(inputs, tmp_path, monkeypatch):
    _, key, _, public, bundle, signature = inputs
    original = bundle.read_bytes()
    verify = signed.verify_bundle
    def verify_then_replace(data, sig, pub):
        verify(data, sig, pub)
        bundle.write_bytes(b"replaced after verification")
    monkeypatch.setattr(signed, "verify_bundle", verify_then_replace)
    def consume(data, *args):
        assert data == original
        return (1, 384)
    monkeypatch.setattr(signed, "consume_bundle_bytes", consume)
    assert signed.consume_signed_bundle(bundle, signature, public, key, tmp_path / "work") == (1, 384)


def test_valid_signature_wrong_aes_fails_after_verification(inputs, tmp_path, monkeypatch):
    _, key, _, public, bundle, signature = inputs
    key.write_bytes(b"w" * 32)
    events = []
    verify = signed.verify_bundle
    decrypt = consumer.decrypt_bundle
    def checked_verify(*args):
        verify(*args)
        events.append("verified")
    def checked_decrypt(*args):
        events.append("decrypt")
        return decrypt(*args)
    monkeypatch.setattr(signed, "verify_bundle", checked_verify)
    monkeypatch.setattr(consumer, "decrypt_bundle", checked_decrypt)
    with pytest.raises(BundleAuthenticationError):
        signed.consume_signed_bundle(bundle, signature, public, key, tmp_path / "work")
    assert events == ["verified", "decrypt"]


def test_download_same_revision(inputs, tmp_path, monkeypatch):
    calls = []
    def download(repo, name, **kwargs):
        calls.append((repo, name, kwargs["revision"]))
        return str(tmp_path / name)
    monkeypatch.setattr(signed, "hf_hub_download", download)
    signed.download_signed_bundle("repo", "a" * 40, tmp_path)
    assert calls == [("repo", producer.BUNDLE_NAME, "a" * 40), ("repo", signed.SIGNATURE_NAME, "a" * 40)]
    with pytest.raises(BundleFormatError):
        signed.download_signed_bundle("repo", "main", tmp_path)
    assert len(calls) == 2


@pytest.mark.parametrize("extra", [[], ["--bundle", "x"], ["--signature", "y"], ["--bundle", "x", "--signature", "y", "--revision", "a" * 40]])
def test_cli_rejects_incomplete_or_ambiguous_inputs(extra, monkeypatch):
    monkeypatch.setattr(signed, "download_signed_bundle", lambda *a: pytest.fail("no download"))
    with pytest.raises(SystemExit) as error:
        signed.main(["--public-key", "p", "--key-file", "k", "--work-dir", "w", *extra])
    assert error.value.code == 2


def test_download_error_sanitized(monkeypatch, capsys):
    def fail(*args):
        raise RuntimeError("sensitive-token-value")
    monkeypatch.setattr(signed, "download_signed_bundle", fail)
    with pytest.raises(SystemExit):
        signed.main(["--public-key", "p", "--key-file", "k", "--work-dir", "w", "--revision", "a" * 40])
    assert "sensitive-token-value" not in capsys.readouterr().err


def test_producer_signs_output(inputs, tmp_path, monkeypatch):
    source, key, private, public, _, _ = inputs
    monkeypatch.setattr(producer, "verify_local_model", lambda path: None)
    output = tmp_path / "new.enc"
    producer.produce(source, key, output, private)
    verify_bundle(output.read_bytes(), Path(str(output) + ".sig").read_bytes(), load_public_key(public))


@pytest.mark.parametrize("occupied", ["bundle", "signature"])
def test_producer_preserves_existing_outputs(inputs, tmp_path, monkeypatch, occupied):
    source, key, private, _, _, _ = inputs
    monkeypatch.setattr(producer, "verify_local_model", lambda path: None)
    output = tmp_path / "new.enc"
    sig = Path(str(output) + ".sig")
    existing = output if occupied == "bundle" else sig
    existing.write_bytes(b"preserve")
    with pytest.raises(BundleFormatError):
        producer.produce(source, key, output, private)
    assert existing.read_bytes() == b"preserve"
    assert not (sig if occupied == "bundle" else output).exists()


def test_signing_failure_publishes_nothing(inputs, tmp_path, monkeypatch):
    source, key, private, _, _, _ = inputs
    monkeypatch.setattr(producer, "verify_local_model", lambda path: None)
    def fail(*args):
        raise RuntimeError("signer failed")
    monkeypatch.setattr(producer, "sign_bundle", fail)
    output = tmp_path / "new.enc"
    with pytest.raises(RuntimeError):
        producer.produce(source, key, output, private)
    assert not output.exists()
    assert not Path(str(output) + ".sig").exists()
