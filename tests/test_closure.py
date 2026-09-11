"""Regression tests for the documentation review's concrete failure modes."""

import importlib.util
import io
import json
import socket
import tarfile
from pathlib import Path

import numpy as np
import pytest

from confidential_model_delivery_poc import bundle, consumer, producer


def fixture_bundle(tmp_path, model=producer.MODEL_ID):
    source = tmp_path / "source"
    source.mkdir()
    (source / "config.json").write_text("{}")
    encrypted = tmp_path / "bundle.enc"
    encrypted.write_bytes(bundle.create_bundle_from_directory(
        source, b"a" * 32, source_model=model, source_revision=producer.MODEL_REVISION))
    key = tmp_path / "key"
    key.write_bytes(b"a" * 32)
    return encrypted, key


@pytest.mark.parametrize("fail", [False, True])
def test_consumer_preserves_preexisting_data_and_cleans_own_temp(tmp_path, monkeypatch, fail):
    encrypted, key = fixture_bundle(tmp_path)
    work = tmp_path / "work"
    old = work / "recovered-model"
    old.mkdir(parents=True)
    sentinel = old / "keep.txt"
    sentinel.write_text("operator data")

    def load(path):
        assert path != old
        assert (path / "config.json").exists()
        if fail:
            raise RuntimeError("load failure")
        return (1, 384)

    monkeypatch.setattr(consumer, "load_embedding", load)
    if fail:
        with pytest.raises(RuntimeError):
            consumer.consume_bundle(encrypted, key, work)
    else:
        assert consumer.consume_bundle(encrypted, key, work) == (1, 384)
    assert sentinel.read_text() == "operator data"
    assert list(work.iterdir()) == [old]


def test_authenticated_wrong_identity_stops_before_extraction(tmp_path, monkeypatch):
    encrypted, key = fixture_bundle(tmp_path, model="another/model")
    calls = []
    monkeypatch.setattr(consumer, "extract_verified_tar", lambda *args: calls.append(args))
    with pytest.raises(bundle.BundleFormatError, match="identity"):
        consumer.consume_bundle(encrypted, key, tmp_path / "work")
    assert calls == []
    assert list((tmp_path / "work").iterdir()) == []


@pytest.mark.parametrize("revision", ["main", "latest", "1234", "z" * 40])
def test_mutable_revision_rejected_before_network(tmp_path, monkeypatch, revision):
    calls = []
    monkeypatch.setattr(consumer, "hf_hub_download", lambda *a, **kw: calls.append(kw))
    with pytest.raises(bundle.BundleFormatError, match="Git commit"):
        consumer.download_bundle("repo", revision, tmp_path / "download")
    assert calls == []


def test_download_failure_does_not_print_sensitive_exception(tmp_path, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("hf_fake_sensitive_token https://user:password@example.test")
    monkeypatch.setattr(consumer, "hf_hub_download", fail)
    with pytest.raises(SystemExit) as exit:
        consumer.main(["--revision", "a" * 40, "--key-file", "unused", "--work-dir", str(tmp_path)])
    assert exit.value.code == 2
    output = capsys.readouterr().err
    assert "consumer failed" in output
    assert "sensitive_token" not in output and "password" not in output


def test_incomplete_existing_model_does_not_connect(tmp_path, monkeypatch):
    model = tmp_path / "incomplete"
    model.mkdir()
    (model / "config.json").write_text(json.dumps({"model_type": "bert", "hidden_size": 384,
        "num_hidden_layers": 1, "num_attention_heads": 12, "intermediate_size": 512}))
    attempts = []
    def connect(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("network forbidden during model load")
    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket, "create_connection", connect)
    monkeypatch.setattr(socket, "getaddrinfo", connect)
    with pytest.raises((OSError, ValueError)):
        consumer.load_embedding(model)
    assert attempts == []


@pytest.mark.parametrize("array", [np.zeros((1, 12)), np.full((1, 384), np.nan), np.full((1, 384), np.inf)])
def test_embedding_shape_and_finiteness(tmp_path, monkeypatch, array):
    caches = []
    class Model:
        def __init__(self, directory, **kwargs):
            assert kwargs["local_files_only"] is True
            assert kwargs["trust_remote_code"] is False
            cache = Path(kwargs["cache_folder"])
            assert list(cache.iterdir()) == []
            caches.append(cache)
        def encode(self, text):
            return array
    monkeypatch.setattr(consumer, "SentenceTransformer", Model)
    with pytest.raises(ValueError, match="finite"):
        consumer.load_embedding(tmp_path)
    assert all(not p.exists() for p in caches)


@pytest.mark.parametrize("names", [["a", "a/b"], ["a/../b"], ["a//b"], ["./a"], ["/a"], ["a", "a"]])
def test_ambiguous_and_conflicting_tar_paths_rejected(tmp_path, names):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as tar:
        for name in names:
            info = tarfile.TarInfo(name)
            info.size = 1
            tar.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(bundle.UnsafeArchiveError):
        bundle.extract_verified_tar(output.getvalue(), tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("raw", [b"not JSON", b"[]", b"{}"])
def test_malformed_metadata_rejected(raw):
    with pytest.raises(bundle.BundleFormatError):
        bundle._parse_metadata(raw)


def test_invalid_tar_rejected_before_destination(tmp_path):
    with pytest.raises(bundle.UnsafeArchiveError):
        bundle.extract_verified_tar(b"not a tar", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_local_cache_does_not_change_tar(tmp_path):
    (tmp_path / "config.json").write_text("{}")
    before = bundle.create_deterministic_tar(tmp_path)
    cache = tmp_path / ".cache"
    cache.mkdir()
    (cache / "download-metadata").write_text("timestamp dependent")
    assert bundle.create_deterministic_tar(tmp_path) == before


def test_generate_key_is_exclusive_and_private(tmp_path):
    spec = importlib.util.spec_from_file_location("generate_key", Path(__file__).parents[1] / "scripts/generate_key.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "key"
    module.generate_key(path)
    first = path.read_bytes()
    assert len(first) == 32
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        module.generate_key(path)
    assert path.read_bytes() == first
