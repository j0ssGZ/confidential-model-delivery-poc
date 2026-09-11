"""Consume an authenticated encrypted MiniLM bundle without model fallback."""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer

from confidential_model_delivery_poc.bundle import decrypt_bundle, extract_verified_tar
from confidential_model_delivery_poc.producer import BUNDLE_NAME, read_key

ARTIFACT_REPOSITORY = "j0ssGZ/confidential-model-delivery-artifacts"


def download_bundle(repo_id: str, revision: str, destination: Path) -> Path:
    """Download one bundle at an immutable Hub revision into a work directory."""
    destination.mkdir(parents=True, exist_ok=True)
    return Path(hf_hub_download(repo_id, BUNDLE_NAME, revision=revision, local_dir=destination))


def load_embedding(model_directory: Path) -> tuple[int, int]:
    """Load only local recovered files and validate one fixed embedding."""
    with tempfile.TemporaryDirectory(prefix="cmdp-consumer-cache-") as cache:
        old = os.environ.get("HF_HUB_OFFLINE")
        os.environ["HF_HUB_OFFLINE"] = "1"
        try:
            model = SentenceTransformer(str(model_directory), cache_folder=cache, local_files_only=True, trust_remote_code=False)
            embedding = model.encode(["confidential model delivery verification"])
        finally:
            if old is None:
                os.environ.pop("HF_HUB_OFFLINE", None)
            else:
                os.environ["HF_HUB_OFFLINE"] = old
    shape = tuple(embedding.shape)
    if shape != (1, 384) or not np.isfinite(embedding).all():
        raise ValueError("recovered model did not produce a finite (1, 384) embedding")
    return shape


def consume_bundle(bundle_path: Path, key_file: Path, work_directory: Path) -> tuple[int, int]:
    """Authenticate, extract and load a local bundle, cleaning plaintext on exit."""
    work_directory.mkdir(parents=True, exist_ok=True)
    recovered = work_directory / "recovered-model"
    try:
        decrypted = decrypt_bundle(bundle_path.read_bytes(), read_key(key_file))
        extract_verified_tar(decrypted.tar_bytes, recovered)
        return load_embedding(recovered)
    finally:
        shutil.rmtree(recovered, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load a verified encrypted MiniLM bundle")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--repo-id", default=ARTIFACT_REPOSITORY)
    parser.add_argument("--revision")
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    bundle = args.bundle
    if bundle is None:
        if not args.revision:
            parser.error("--revision is required when downloading from Hugging Face")
        bundle = download_bundle(args.repo_id, args.revision, args.work_dir / "download")
    try:
        shape = consume_bundle(bundle, args.key_file, args.work_dir)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"model_loaded=true embedding_shape={shape}")
    return 0
