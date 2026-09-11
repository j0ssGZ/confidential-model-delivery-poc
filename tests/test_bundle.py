"""Security-relevant tests for the Layer 1 bundle format."""

from __future__ import annotations

import io
import json
import struct
import tarfile
from pathlib import Path

import pytest

from confidential_model_delivery_poc.bundle import (
    MAGIC, BundleAuthenticationError, BundleFormatError, UnsafeArchiveError,
    TAG_BYTES, canonical_metadata, create_bundle_from_directory, create_bundle_from_tar,
    create_deterministic_tar, decrypt_bundle, extract_verified_tar,
)

KEY = b"k" * 32
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def _bundle(tmp_path: Path) -> bytes:
    source = tmp_path / "source"
    source.mkdir()
    (source / "config.json").write_text('{"hidden_size":384}', encoding="utf-8")
    child = source / "tokenizer"
    child.mkdir()
    (child / "vocab.txt").write_text("hello\nworld\n", encoding="utf-8")
    assert create_deterministic_tar(source) == create_deterministic_tar(source)
    return create_bundle_from_directory(source, KEY, source_model=MODEL, source_revision=REVISION)


def test_round_trip_extracts_only_after_authentication(tmp_path: Path) -> None:
    decrypted = decrypt_bundle(_bundle(tmp_path), KEY)
    destination = tmp_path / "recovered"
    extract_verified_tar(decrypted.tar_bytes, destination)
    assert decrypted.metadata["source_model"] == MODEL
    assert (destination / "tokenizer" / "vocab.txt").read_text(encoding="utf-8") == "hello\nworld\n"


def test_wrong_key_and_ciphertext_tampering_are_rejected(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    with pytest.raises(BundleAuthenticationError):
        decrypt_bundle(bundle, b"x" * 32)
    tampered = bytearray(bundle)
    tampered[-TAG_BYTES - 1] ^= 1
    with pytest.raises(BundleAuthenticationError):
        decrypt_bundle(bytes(tampered), KEY)

    tampered_tag = bytearray(bundle)
    tampered_tag[-1] ^= 1
    with pytest.raises(BundleAuthenticationError):
        decrypt_bundle(bytes(tampered_tag), KEY)


@pytest.mark.parametrize("offset", [0, len(MAGIC) + 3])
def test_header_tampering_is_rejected(tmp_path: Path, offset: int) -> None:
    tampered = bytearray(_bundle(tmp_path))
    tampered[offset] ^= 1
    with pytest.raises(BundleFormatError):
        decrypt_bundle(bytes(tampered), KEY)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_model", "sentence-transformers/other-MiniLM"),
        ("source_revision", "0000a243fdf4706b3f48f1d95db1a4f5529b4d41"),
        ("plaintext_sha256", "0" * 64),
        ("nonce_b64", "AAAAAAAAAAAAAAAA"),
    ],
)
def test_authenticated_metadata_tampering_is_rejected(
    tmp_path: Path, field: str, value: str
) -> None:
    bundle = _bundle(tmp_path)
    length = struct.unpack(">I", bundle[len(MAGIC) : len(MAGIC) + 4])[0]
    start, end = len(MAGIC) + 4, len(MAGIC) + 4 + length
    metadata = json.loads(bundle[start:end])
    metadata[field] = value
    changed = canonical_metadata(metadata)
    tampered = MAGIC + struct.pack(">I", len(changed)) + changed + bundle[end:]
    with pytest.raises(BundleAuthenticationError):
        decrypt_bundle(tampered, KEY)


def test_unsafe_tar_is_rejected_before_writing(tmp_path: Path) -> None:
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as tar:
        info = tarfile.TarInfo("../escape.txt")
        info.size = 4
        tar.addfile(info, io.BytesIO(b"nope"))
    decrypted = decrypt_bundle(create_bundle_from_tar(archive.getvalue(), KEY, source_model=MODEL, source_revision=REVISION), KEY)
    destination = tmp_path / "recovered"
    with pytest.raises(UnsafeArchiveError):
        extract_verified_tar(decrypted.tar_bytes, destination)
    assert not destination.exists()
