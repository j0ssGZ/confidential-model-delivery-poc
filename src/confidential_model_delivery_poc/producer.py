"""Build a Layer 1 encrypted model bundle from the pinned MiniLM revision."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer

from confidential_model_delivery_poc.bundle import (
    BundleError, BundleFormatError,
    create_bundle_from_directory,
)

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
BUNDLE_NAME = "minilm-l6-v2.bundle.enc"
_IGNORE_PATTERNS = [
    ".gitattributes",
    "*.bin",
    "*.h5",
    "*.onnx",
    "*.msgpack",
    "*.ot",
    "openvino/*",
]


def read_key(key_file: Path) -> bytes:
    """Read exactly one raw 32-byte key without interpreting it as text."""
    try:
        key = key_file.read_bytes()
    except OSError as error:
        raise BundleFormatError("unable to read producer key file") from error
    if len(key) != 32:
        raise BundleFormatError("producer key file must contain exactly 32 bytes")
    return key


def download_model(destination: Path) -> Path:
    """Download only the PyTorch/safetensors files needed by the pinned model."""
    destination.mkdir(parents=True, exist_ok=True)
    downloaded = snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=destination,
        ignore_patterns=_IGNORE_PATTERNS,
    )
    return Path(downloaded)


def verify_local_model(model_directory: Path) -> None:
    """Load MiniLM solely from disk before encrypting it.

    ``local_files_only`` and a fresh cache ensure this check does not silently
    complete missing files from the Hub. The producer does not log model data.
    """
    if not model_directory.is_dir():
        raise BundleFormatError("downloaded model directory does not exist")
    with tempfile.TemporaryDirectory(prefix="cmdp-producer-cache-") as cache:
        SentenceTransformer(
            str(model_directory),
            cache_folder=cache,
            local_files_only=True,
            trust_remote_code=False,
        )


def produce(model_directory: Path, key_file: Path, output_file: Path) -> Path:
    """Verify, encrypt and atomically write the public bundle artifact."""
    verify_local_model(model_directory)
    bundle = create_bundle_from_directory(
        model_directory,
        read_key(key_file),
        source_model=MODEL_ID,
        source_revision=MODEL_REVISION,
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="producer-", dir=output_file.parent) as directory:
        temporary = Path(directory) / "bundle.tmp"
        temporary.write_bytes(bundle)
        temporary.replace(output_file)
    return output_file


def main(argv: list[str] | None = None) -> int:
    """Run the producer with local model/key paths supplied by the operator."""
    parser = argparse.ArgumentParser(description="Create the encrypted MiniLM bundle")
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--download-model", action="store_true")
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts") / BUNDLE_NAME)
    args = parser.parse_args(argv)
    try:
        if args.download_model:
            download_model(args.model_dir)
        result = produce(args.model_dir, args.key_file, args.output)
    except BundleError as error:
        parser.error(str(error))
    except Exception:
        parser.error("producer failed: check local inputs, model files and download access")
    print(f"bundle_created={result}")
    return 0
