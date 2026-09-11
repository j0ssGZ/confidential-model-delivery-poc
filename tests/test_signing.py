"""Signing, trust separation and exclusive key-generation regressions."""

from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from confidential_model_delivery_poc.signing import (
    SigningError, generate_signing_keys, load_private_key, load_public_key,
    main, sign_bundle, verify_bundle,
)


@pytest.fixture
def pair(tmp_path):
    private, public = tmp_path / "private.pem", tmp_path / "public.pem"
    generate_signing_keys(private, public)
    return private, public


def test_roundtrip_and_permissions(pair):
    private, public = pair
    signature = sign_bundle(b"exact bundle bytes", load_private_key(private))
    assert len(signature) == 64
    verify_bundle(b"exact bundle bytes", signature, load_public_key(public))
    assert private.stat().st_mode & 0o777 == 0o600
    assert public.read_bytes().startswith(b"-----BEGIN PUBLIC KEY-----")


@pytest.mark.parametrize("change", ["bundle", "signature", "key", "empty", "short", "long"])
def test_verification_rejects_changes(pair, tmp_path, change):
    private, public = pair
    bundle = b"bundle"
    signature = sign_bundle(bundle, load_private_key(private))
    if change == "bundle":
        bundle += b"!"
    elif change == "signature":
        signature = bytes([signature[0] ^ 1]) + signature[1:]
    elif change == "key":
        other = tmp_path / "other.pem"
        generate_signing_keys(tmp_path / "other-private.pem", other)
        public = other
    else:
        signature = {"empty": b"", "short": signature[:-1], "long": signature + b"!"}[change]
    with pytest.raises(SigningError):
        verify_bundle(bundle, signature, load_public_key(public))


@pytest.mark.parametrize("existing", ["private", "public"])
def test_existing_file_preserved_and_partial_pair_removed(tmp_path, existing):
    private, public = tmp_path / "private", tmp_path / "public"
    occupied = private if existing == "private" else public
    occupied.write_bytes(b"existing user data")
    with pytest.raises(SigningError):
        generate_signing_keys(private, public)
    assert occupied.read_bytes() == b"existing user data"
    assert not (public if existing == "private" else private).exists()


def test_same_path_and_symlink_rejected(tmp_path):
    path = tmp_path / "key"
    with pytest.raises(SigningError):
        generate_signing_keys(path, path)
    assert not path.exists()
    target = tmp_path / "target"
    target.write_bytes(b"preserve")
    path.symlink_to(target)
    with pytest.raises(SigningError):
        generate_signing_keys(path, tmp_path / "public")
    assert target.read_bytes() == b"preserve"
    assert path.is_symlink()


@pytest.mark.parametrize("kind", ["missing", "malformed", "wrong_algorithm", "encrypted"])
def test_invalid_private_keys_rejected(tmp_path, kind):
    path = tmp_path / "key"
    if kind == "malformed":
        path.write_bytes(b"sensitive-invalid-value")
    elif kind in ("wrong_algorithm", "encrypted"):
        key = ec.generate_private_key(ec.SECP256R1())
        encryption = serialization.BestAvailableEncryption(b"password") if kind == "encrypted" else serialization.NoEncryption()
        path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, encryption))
    with pytest.raises(SigningError, match="invalid or unreadable"):
        load_private_key(path)


@pytest.mark.parametrize("kind", ["missing", "malformed", "wrong_algorithm", "private"])
def test_invalid_public_keys_rejected(tmp_path, pair, kind):
    path = tmp_path / "bad-public"
    if kind == "malformed":
        path.write_bytes(b"invalid")
    elif kind == "private":
        path = pair[0]
    elif kind == "wrong_algorithm":
        path.write_bytes(ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    with pytest.raises(SigningError):
        load_public_key(path)


def test_cli_reports_only_safe_status(pair, tmp_path, capsys):
    assert main(["--private-key", str(tmp_path / "new-private"), "--public-key", str(tmp_path / "new-public")]) == 0
    assert capsys.readouterr().out == "signing_keys_created=true\n"
    with pytest.raises(SystemExit) as error:
        main(["--private-key", str(pair[0]), "--public-key", str(pair[1])])
    assert error.value.code == 2
    output = capsys.readouterr()
    assert not output.out
    assert "BEGIN PRIVATE KEY" not in output.err


def test_second_write_failure_removes_only_owned_private(tmp_path, monkeypatch):
    from confidential_model_delivery_poc import signing
    original = signing.os.open
    public = tmp_path / "public"
    def fail_public(path, flags, mode):
        if Path(path) == public:
            raise PermissionError("sensitive detail")
        return original(path, flags, mode)
    monkeypatch.setattr(signing.os, "open", fail_public)
    with pytest.raises(SigningError, match="keys not created"):
        generate_signing_keys(tmp_path / "private", public)
    assert not (tmp_path / "private").exists()
    assert not public.exists()
