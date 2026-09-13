"""Patch the fixed Trustee chart's missing admin audience, preserving KBS data.

Run only on the trusted lab operator host with its kubeconfig, before AES
provisioning. Backups are private and remain on that host; never commit them.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def kubectl(*args, **kwargs):
    return subprocess.run(["kubectl", "-n", "coco-trustee", *args],
                          check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-parent", required=True, type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    config = json.loads(kubectl("get", "cm", "trustee-kbs-config", "-o", "json",
                                capture_output=True).stdout)
    original = config["data"]["kbs-config.toml"]
    expected = '{ issuer = "TrusteeInHelm", public_key_uri = '
    if 'audience = "KBS"' in original:
        print("admin_audience_already_configured=true")
        return
    if original.count(expected) != 1:
        parser.error("unexpected KBS config; stop and inspect the pinned chart")
    args.backup_parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix="kbs-audience-", dir=args.backup_parent))
    (backup / "config.json").write_text(json.dumps(config))
    for component in ("kbs", "as", "rvps"):
        result = kubectl("logs", "deployment/trustee-" + component,
                         "--all-containers=true", capture_output=True)
        (backup / (component + ".log")).write_bytes(result.stdout)
    with (backup / "repository.tar").open("wb") as archive:
        kubectl("exec", "deployment/trustee-kbs", "-c", "kbs", "--", "tar",
                "-C", "/opt/confidential-containers/kbs/repository", "-cf", "-", ".",
                stdout=archive)
    patched = original.replace(expected, '{ issuer = "TrusteeInHelm", audience = "KBS", public_key_uri = ')
    kubectl("patch", "cm", "trustee-kbs-config", "--type=merge", "-p",
            json.dumps({"data": {"kbs-config.toml": patched}}), stdout=subprocess.DEVNULL)
    kubectl("rollout", "restart", "deployment/trustee-kbs")
    kubectl("rollout", "status", "deployment/trustee-kbs", "--timeout=180s")
    with (backup / "repository.tar").open("rb") as archive:
        kubectl("exec", "-i", "deployment/trustee-kbs", "-c", "kbs", "--", "tar",
                "-C", "/opt/confidential-containers/kbs/repository", "-xf", "-", stdin=archive)
    print("admin_audience_configured=true backup=" + str(backup))


if __name__ == "__main__":
    main()
