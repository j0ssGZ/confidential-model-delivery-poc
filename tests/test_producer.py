"""Producer checks that do not download a model or create a real key."""

from pathlib import Path

import pytest

from confidential_model_delivery_poc.bundle import BundleFormatError
from confidential_model_delivery_poc.producer import read_key, verify_local_model


def test_read_key_requires_exactly_32_raw_bytes(tmp_path: Path) -> None:
    key_file = tmp_path / "model-key.bin"
    key_file.write_bytes(b"k" * 32)
    assert read_key(key_file) == b"k" * 32

    key_file.write_bytes(b"short")
    with pytest.raises(BundleFormatError, match="exactly 32"):
        read_key(key_file)


def test_missing_model_directory_fails_without_remote_fallback(tmp_path: Path) -> None:
    with pytest.raises(BundleFormatError, match="does not exist"):
        verify_local_model(tmp_path / "missing")
