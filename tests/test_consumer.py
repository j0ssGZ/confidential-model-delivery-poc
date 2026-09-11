"""Consumer tests without a real model or secret."""

from pathlib import Path

import pytest

from confidential_model_delivery_poc.bundle import BundleAuthenticationError, create_bundle_from_directory
from confidential_model_delivery_poc.consumer import consume_bundle
from confidential_model_delivery_poc.producer import MODEL_ID, MODEL_REVISION


def test_wrong_key_stops_before_recovered_directory_is_available(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "config.json").write_text("{}", encoding="utf-8")
    bundle = tmp_path / "bundle.enc"
    bundle.write_bytes(create_bundle_from_directory(source, b"a" * 32, source_model=MODEL_ID, source_revision=MODEL_REVISION))
    key = tmp_path / "key"
    key.write_bytes(b"b" * 32)
    work = tmp_path / "work"
    with pytest.raises(BundleAuthenticationError):
        consume_bundle(bundle, key, work)
    assert not (work / "recovered-model").exists()
