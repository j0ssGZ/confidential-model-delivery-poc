"""Read-only verification of an existing Layer 3 Job; save public evidence."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import time


def kubectl(*args):
    return subprocess.check_output(["kubectl", *args], text=True)


def verify(job, case, directory, timeout=1200):
    if not re.fullmatch(r"attested-[a-z0-9-]+", job):
        raise ValueError("expected an attested Job name")
    target = directory / job
    target.mkdir(parents=True, exist_ok=False)
    deadline = time.monotonic() + timeout
    while True:
        pods = json.loads(kubectl("-n", "secure-ai-layer3", "get", "pods", "-l", "job-name=" + job, "-o", "json"))["items"]
        if len(pods) == 1 and pods[0]["status"].get("phase") in ("Succeeded", "Failed"):
            break
        if time.monotonic() >= deadline:
            raise TimeoutError("Job did not terminate; inspect events without deleting evidence")
        time.sleep(5)
    pod = pods[0]
    name = pod["metadata"]["name"]
    logs = kubectl("-n", "secure-ai-layer3", "logs", name, "--timestamps")
    kbs = kubectl("-n", "coco-trustee", "logs", "deployment/trustee-kbs", "--since-time=" + pod["metadata"]["creationTimestamp"])
    ip = pod["status"].get("podIP", "")
    # Keep only public HTTP access lines, not general Trustee output or tokens.
    requests = [line for line in kbs.splitlines() if ip and ip in line and 'GET /kbs/v0/resource/' in line]
    statuses = pod["status"].get("containerStatuses", [])
    code = statuses[0]["state"]["terminated"]["exitCode"] if statuses else None
    spec = pod["spec"]
    assert not spec["automountServiceAccountToken"]
    assert spec["runtimeClassName"] == "kata-qemu-coco-dev"
    assert all("secret" not in volume and "projected" not in volume and "hostPath" not in volume for volume in spec.get("volumes", []))
    assert spec["containers"][0]["securityContext"]["readOnlyRootFilesystem"]
    assert "@sha256:" in spec["containers"][0]["image"]
    stages = re.findall(r"stage=([a-z_]+)", logs)
    expected = {
        "synthetic": (0, [], "cdh_python_synthetic_ok=true", "200"),
        "positive": (0, ["signature_verified", "key_requested", "key_retrieved", "bundle_authenticated"], "model_loaded=true embedding_shape=(1, 384)", "200"),
        "tampered-signature": (2, [], "bundle signature verification failed", None),
        "denied": (2, ["signature_verified", "key_requested"], "CDH resource retrieval denied or unavailable", "401"),
        "wrong-aes": (2, ["signature_verified", "key_requested", "key_retrieved"], "bundle authentication failed", "200"),
    }[case]
    http_ok = not requests if expected[3] is None else any(re.search(r'HTTP/1\.1" ' + expected[3] + r'\b', line) for line in requests)
    result = {"job": job, "pod": name, "case": case, "pod_ip": ip,
              "created": pod["metadata"]["creationTimestamp"], "exit_code": code,
              "stages": stages, "runtime": spec["runtimeClassName"],
              "image": spec["containers"][0]["image"],
              "image_id": statuses[0].get("imageID") if statuses else None,
              "aes_secret_mounted": False, "kbs_resource_requests": len(requests),
              "passed": bool(ip) and code == expected[0] and stages == expected[1] and expected[2] in logs and http_ok}
    (target / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    (target / "consumer.log").write_text(logs)
    (target / "kbs-access.log").write_text("\n".join(requests) + "\n")
    (target / "pod.json").write_text(json.dumps(pod, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    if not result["passed"]:
        raise RuntimeError("unexpected evidence; inspect saved logs, never count this as a passing negative")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True)
    parser.add_argument("--case", choices=["synthetic", "positive", "tampered-signature", "denied", "wrong-aes"], required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    verify(args.job, args.case, args.evidence_dir)
