import importlib.util
import json
from pathlib import Path

import pytest

MODULE = importlib.util.spec_from_file_location("layer3_jobs", Path(__file__).resolve().parents[1] / "scripts/layer3_jobs.py")
jobs = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(jobs)
IMAGE = "docker.io/example/consumer@sha256:" + "a" * 64


@pytest.mark.parametrize("case", jobs.CASES)
def test_jobs_keep_attested_boundary(case):
    job = jobs.render(case, IMAGE, "10.100.4.169")
    pod = job["spec"]["template"]["spec"]
    assert pod["runtimeClassName"] == "kata-qemu-coco-dev"
    assert pod["automountServiceAccountToken"] is False
    assert pod["securityContext"]["runAsNonRoot"] is True
    assert set(volume["name"] for volume in pod["volumes"]) == {"work", "signing-public"}
    assert '"secret"' not in json.dumps(job).lower()
    assert '"hostPath"' not in json.dumps(job)
    assert "--key-file" not in json.dumps(job)
    container = pod["containers"][0]
    assert container["image"] == IMAGE
    assert container["securityContext"] == {"allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True, "capabilities": {"drop": ["ALL"]}}
    assert "cc_kbc::http://10.100.4.169:8080" in str(job)
    compile(jobs.RUNNER, "runner", "exec")


@pytest.mark.parametrize("image", ["consumer:latest", "consumer:v1", "consumer@sha256:abc", "a b@sha256:" + "a" * 64])
def test_requires_digest(image):
    with pytest.raises(ValueError):
        jobs.render("positive", image, "10.100.4.169")


@pytest.mark.parametrize("ip", ["127.0.0.1", "0.0.0.0", "8.8.8.8", "::1", "10.0.0.1; echo hi"])
def test_kbs_ip_is_public_configuration_not_shell(ip):
    with pytest.raises(ValueError):
        jobs.render("positive", IMAGE, ip)


def test_unsupported_case_rejected():
    with pytest.raises(ValueError):
        jobs.render("unexpected", IMAGE, "10.100.4.169")
