"""Ed25519 signatures over exact bundle bytes; no model or network access."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from confidential_model_delivery_poc.bundle import BundleError

SIGNATURE_BYTES = 64


class SigningError(BundleError):
    """A safe-to-log signing input or verification failure."""


def load_private_key(path: Path) -> Ed25519PrivateKey:
    """Load an unencrypted Ed25519 PKCS8 PEM without exposing input errors."""
    try:
        data = path.read_bytes()
        if not data.startswith(b"-----BEGIN PRIVATE KEY-----"):
            raise ValueError
        key = serialization.load_pem_private_key(data, password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError
        return key
    except (OSError, ValueError, TypeError, UnsupportedAlgorithm) as error:
        raise SigningError("invalid or unreadable Ed25519 private PEM key") from error


def load_public_key(path: Path) -> Ed25519PublicKey:
    """Load the operator-provisioned Ed25519 public PEM."""
    try:
        key = serialization.load_pem_public_key(path.read_bytes())
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError
        return key
    except (OSError, ValueError, TypeError, UnsupportedAlgorithm) as error:
        raise SigningError("invalid or unreadable Ed25519 public PEM key") from error


def sign_bundle(bundle: bytes, private_key: Ed25519PrivateKey) -> bytes:
    """Sign all supplied bytes; caller is responsible for trusted provenance."""
    return private_key.sign(bundle)


def verify_bundle(bundle: bytes, signature: bytes, public_key: Ed25519PublicKey) -> None:
    """Reject invalid signatures before a caller may use bundle plaintext."""
    if len(signature) != SIGNATURE_BYTES:
        raise SigningError("bundle signature must contain exactly 64 bytes")
    try:
        public_key.verify(signature, bundle)
    except InvalidSignature as error:
        raise SigningError("bundle signature verification failed") from error


def generate_signing_keys(private_path: Path, public_path: Path) -> None:
    """Exclusively create a PEM pair; remove only owned files on failure.

    The two-file operation is not crash-atomic. A process interruption can leave
    an incomplete pair; callers must inspect it, never overwrite it on retry.
    """
    if private_path.resolve() == public_path.resolve():
        raise SigningError("private and public key paths must differ")
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.PEM,
                                           serialization.PublicFormat.SubjectPublicKeyInfo)
    created: list[Path] = []
    try:
        for path, data in ((private_path, private), (public_path, public)):
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            with os.fdopen(descriptor, "wb") as target:
                target.write(data)
    except OSError as error:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise SigningError("keys not created: check permissions and choose NEW paths") from error


def main(argv: list[str] | None = None) -> int:
    """Generate a signing pair without printing any key material."""
    parser = argparse.ArgumentParser(description="Create a NEW Ed25519 PEM signing pair")
    parser.add_argument("--private-key", required=True, type=Path)
    parser.add_argument("--public-key", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        generate_signing_keys(args.private_key, args.public_key)
    except SigningError as error:
        parser.error(str(error))
    except Exception:
        parser.error("signing key generation failed")
    print("signing_keys_created=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
