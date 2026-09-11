"""Authenticated encrypted bundle format for Layer 1."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import shutil
import struct
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC: Final = b"CMDP1ENC"
SCHEMA_VERSION: Final = 1
ALGORITHM: Final = "AES-256-GCM"
PAYLOAD_FORMAT: Final = "tar"
NONCE_BYTES: Final = 12
KEY_BYTES: Final = 32
TAG_BYTES: Final = 16
MAX_METADATA_BYTES: Final = 64 * 1024
_FIELDS: Final = frozenset({"schema_version", "algorithm", "source_model", "source_revision", "payload_format", "plaintext_sha256", "nonce_b64"})


class BundleError(ValueError):
    """Base class for safe-to-log bundle validation failures."""


class BundleFormatError(BundleError):
    """The input is not a supported CMDP1ENC bundle."""


class BundleAuthenticationError(BundleError):
    """The key, authenticated data, ciphertext or tag is invalid."""


class UnsafeArchiveError(BundleError):
    """The authenticated TAR cannot be safely extracted."""


@dataclass(frozen=True)
class DecryptedBundle:
    metadata: dict[str, object]
    tar_bytes: bytes


def canonical_metadata(metadata: dict[str, object]) -> bytes:
    """Return the sole permitted representation of metadata JSON."""
    return json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _require_key(key: bytes) -> None:
    if len(key) != KEY_BYTES:
        raise BundleFormatError("decryption key must contain exactly 32 bytes")


def _safe_name(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or "." in path.parts or ".." in path.parts:
        raise UnsafeArchiveError("archive contains an unsafe path")
    return path


def create_deterministic_tar(source_directory: Path) -> bytes:
    """Archive regular files below a directory with normalized TAR metadata."""
    source = source_directory.resolve()
    if not source.is_dir():
        raise BundleFormatError("bundle source must be an existing directory")
    files: list[Path] = []
    for path in source.rglob("*"):
        if path.is_symlink():
            raise BundleFormatError("bundle source may not contain symbolic links")
        if path.is_file():
            files.append(path)
        elif not path.is_dir():
            raise BundleFormatError("bundle source may contain only regular files")
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for path in sorted(files, key=lambda item: item.relative_to(source).as_posix()):
            name = path.relative_to(source).as_posix()
            _safe_name(name)
            data = path.read_bytes()
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), 0o644, 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    return output.getvalue()


def _make_metadata(tar_bytes: bytes, source_model: str, source_revision: str, nonce: bytes) -> dict[str, object]:
    if not source_model or not source_revision:
        raise BundleFormatError("source model and revision are required")
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM,
        "source_model": source_model,
        "source_revision": source_revision,
        "payload_format": PAYLOAD_FORMAT,
        "plaintext_sha256": hashlib.sha256(tar_bytes).hexdigest(),
        "nonce_b64": base64.b64encode(nonce).decode("ascii"),
    }


def create_bundle_from_tar(tar_bytes: bytes, key: bytes, *, source_model: str, source_revision: str, nonce: bytes | None = None) -> bytes:
    """Encrypt a TAR payload into a CMDP1ENC v1 bundle."""
    _require_key(key)
    nonce = os.urandom(NONCE_BYTES) if nonce is None else nonce
    if len(nonce) != NONCE_BYTES:
        raise BundleFormatError("AES-GCM nonce must contain exactly 12 bytes")
    metadata = canonical_metadata(_make_metadata(tar_bytes, source_model, source_revision, nonce))
    header = MAGIC + struct.pack(">I", len(metadata)) + metadata
    return header + AESGCM(key).encrypt(nonce, tar_bytes, header)


def create_bundle_from_directory(source_directory: Path, key: bytes, *, source_model: str, source_revision: str) -> bytes:
    """Create a deterministic TAR then encrypt it."""
    return create_bundle_from_tar(create_deterministic_tar(source_directory), key, source_model=source_model, source_revision=source_revision)


def _parse_metadata(raw: bytes) -> tuple[dict[str, object], bytes]:
    try:
        metadata = json.loads(raw.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BundleFormatError("bundle metadata is not valid JSON") from error
    if not isinstance(metadata, dict) or set(metadata) != _FIELDS or canonical_metadata(metadata) != raw:
        raise BundleFormatError("bundle metadata fields or representation are invalid")
    if metadata["schema_version"] != SCHEMA_VERSION or metadata["algorithm"] != ALGORITHM or metadata["payload_format"] != PAYLOAD_FORMAT:
        raise BundleFormatError("bundle metadata declares an unsupported format")
    if not isinstance(metadata["source_model"], str) or not metadata["source_model"] or not isinstance(metadata["source_revision"], str) or not metadata["source_revision"]:
        raise BundleFormatError("bundle metadata has an invalid model reference")
    digest = metadata["plaintext_sha256"]
    if not isinstance(digest, str) or len(digest) != 64:
        raise BundleFormatError("bundle metadata has an invalid plaintext hash")
    try:
        int(digest, 16)
        nonce = base64.b64decode(metadata["nonce_b64"], validate=True)
    except (TypeError, ValueError) as error:
        raise BundleFormatError("bundle metadata has an invalid nonce or hash") from error
    if len(nonce) != NONCE_BYTES:
        raise BundleFormatError("bundle metadata nonce has an invalid length")
    return metadata, nonce


def decrypt_bundle(bundle: bytes, key: bytes) -> DecryptedBundle:
    """Authenticate and decrypt a bundle without extracting its payload."""
    _require_key(key)
    if len(bundle) < len(MAGIC) + 4 + TAG_BYTES or bundle[: len(MAGIC)] != MAGIC:
        raise BundleFormatError("bundle magic is invalid")
    length = struct.unpack(">I", bundle[len(MAGIC) : len(MAGIC) + 4])[0]
    if not 0 < length <= MAX_METADATA_BYTES:
        raise BundleFormatError("bundle metadata length is invalid")
    start, end = len(MAGIC) + 4, len(MAGIC) + 4 + length
    if len(bundle) < end + TAG_BYTES:
        raise BundleFormatError("bundle is truncated")
    metadata, nonce = _parse_metadata(bundle[start:end])
    try:
        tar_bytes = AESGCM(key).decrypt(nonce, bundle[end:], bundle[:end])
    except InvalidTag as error:
        raise BundleAuthenticationError("bundle authentication failed") from error
    if hashlib.sha256(tar_bytes).hexdigest() != metadata["plaintext_sha256"]:
        raise BundleAuthenticationError("bundle plaintext hash does not match")
    return DecryptedBundle(metadata=metadata, tar_bytes=tar_bytes)


def _validated_members(tar_bytes: bytes) -> list[tarfile.TarInfo]:
    try:
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tar:
            members = tar.getmembers()
    except tarfile.TarError as error:
        raise UnsafeArchiveError("authenticated payload is not a valid TAR") from error
    names: set[str] = set()
    for member in members:
        _safe_name(member.name)
        if not member.isfile() or member.name in names:
            raise UnsafeArchiveError("archive contains an unsafe entry")
        names.add(member.name)
    return members


def extract_verified_tar(tar_bytes: bytes, destination: Path) -> None:
    """Validate all TAR entries then atomically materialize them at destination."""
    members = _validated_members(tar_bytes)
    destination = destination.resolve()
    if destination.exists():
        raise BundleFormatError("extraction destination already exists")
    if not destination.parent.is_dir():
        raise BundleFormatError("extraction destination parent does not exist")
    staging = Path(tempfile.mkdtemp(prefix=".bundle-", dir=destination.parent))
    try:
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tar:
            for member in members:
                source = tar.extractfile(member)
                if source is None:
                    raise UnsafeArchiveError("archive file entry cannot be read")
                output = staging.joinpath(*PurePosixPath(member.name).parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                with source, output.open("xb") as target:
                    shutil.copyfileobj(source, target)
                output.chmod(0o644)
        os.replace(staging, destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
