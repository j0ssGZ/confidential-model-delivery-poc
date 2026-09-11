"""Mandatory Ed25519 verification before the Layer 1 decryption pipeline."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from huggingface_hub import hf_hub_download

from confidential_model_delivery_poc.bundle import BundleError, BundleFormatError
from confidential_model_delivery_poc.consumer import ARTIFACT_REPOSITORY, consume_bundle_bytes
from confidential_model_delivery_poc.producer import BUNDLE_NAME
from confidential_model_delivery_poc.signing import load_public_key, verify_bundle

SIGNATURE_NAME = BUNDLE_NAME + ".sig"


def download_signed_bundle(repo_id: str, revision: str, destination: Path) -> tuple[Path, Path]:
    """Fetch bundle and detached signature from the same full Hub commit."""
    if not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        raise BundleFormatError("bundle revision must be a full 40-character Git commit")
    destination.mkdir(parents=True, exist_ok=True)
    return tuple(Path(hf_hub_download(repo_id, name, revision=revision, local_dir=destination))
                 for name in (BUNDLE_NAME, SIGNATURE_NAME))


def consume_signed_bundle(bundle_path: Path, signature_path: Path, public_key_path: Path,
                          key_file: Path, work_directory: Path) -> tuple[int, int]:
    """Keep one byte snapshot from verification through authenticated decryption."""
    bundle = bundle_path.read_bytes()
    verify_bundle(bundle, signature_path.read_bytes(), load_public_key(public_key_path))
    return consume_bundle_bytes(bundle, key_file, work_directory)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Require a trusted Ed25519 signature before decrypting MiniLM")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--signature", type=Path)
    parser.add_argument("--public-key", required=True, type=Path)
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--repo-id", default=ARTIFACT_REPOSITORY)
    parser.add_argument("--revision")
    args = parser.parse_args(argv)
    if (args.bundle is None) != (args.signature is None):
        parser.error("--bundle and --signature must be provided together")
    if args.bundle is not None and args.revision is not None:
        parser.error("local files and --revision are mutually exclusive")
    if args.bundle is None and not args.revision:
        parser.error("--revision is required for signed downloads")
    try:
        bundle, signature = (args.bundle, args.signature) if args.bundle is not None else download_signed_bundle(
            args.repo_id, args.revision, args.work_dir / "download")
        shape = consume_signed_bundle(bundle, signature, args.public_key, args.key_file, args.work_dir)
    except BundleError as error:
        parser.error(str(error))
    except Exception:
        parser.error("signed consumer failed: check inputs and download access")
    print(f"signature_verified=true model_loaded=true embedding_shape={shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
