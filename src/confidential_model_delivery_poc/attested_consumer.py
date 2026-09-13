"""Verify Ed25519, retrieve AES through CoCo CDH, then authenticate and load."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
import tempfile

from confidential_model_delivery_poc.bundle import BundleError, BundleFormatError, decrypt_bundle, extract_verified_tar
from confidential_model_delivery_poc.cdh import KeyRetrievalError, retrieve_key
from confidential_model_delivery_poc.consumer import ARTIFACT_REPOSITORY, load_embedding
from confidential_model_delivery_poc.producer import MODEL_ID, MODEL_REVISION
from confidential_model_delivery_poc.signed_consumer import download_signed_bundle
from confidential_model_delivery_poc.signing import load_public_key, verify_bundle


def consume_attested_bundle(bundle_path: Path, signature_path: Path, public_key_path: Path,
                            key_provider: Callable[[], bytes], work_directory: Path,
                            report: Callable[[str], None] = lambda event: None) -> tuple[int, int]:
    """Keep one byte snapshot and never request a key before signature success."""
    bundle = bundle_path.read_bytes()
    verify_bundle(bundle, signature_path.read_bytes(), load_public_key(public_key_path))
    report("signature_verified")
    report("key_requested")
    key = key_provider()
    if not isinstance(key, bytes) or len(key) != 32:
        raise KeyRetrievalError("CDH key must contain exactly 32 bytes")
    report("key_retrieved")
    decrypted = decrypt_bundle(bundle, key)
    if (decrypted.metadata["source_model"], decrypted.metadata["source_revision"]) != (MODEL_ID, MODEL_REVISION):
        raise BundleFormatError("bundle model identity does not match the expected MiniLM revision")
    report("bundle_authenticated")
    work_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="attested-", dir=work_directory) as temporary:
        recovered = Path(temporary) / "recovered-model"
        extract_verified_tar(decrypted.tar_bytes, recovered)
        return load_embedding(recovered)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify signed MiniLM and retrieve its AES key through CoCo CDH")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--signature", type=Path)
    parser.add_argument("--public-key", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--repo-id", default=ARTIFACT_REPOSITORY)
    parser.add_argument("--revision")
    parser.add_argument("--key-resource", required=True)
    parser.add_argument("--cdh-timeout", type=float, default=10.0)
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
        shape = consume_attested_bundle(
            bundle, signature, args.public_key,
            lambda: retrieve_key(args.key_resource, args.cdh_timeout), args.work_dir,
            lambda event: print("stage=" + event, flush=True))
    except BundleError as error:
        parser.error(str(error))
    except Exception:
        parser.error("attested consumer failed: check inputs, CDH and download access")
    print(f"signature_verified=true key_retrieved=true model_loaded=true embedding_shape={shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
