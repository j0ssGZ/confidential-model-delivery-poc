"""Run with sudo on the lab node; preserve original config and tune guest pull."""

import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    path = Path("/var/lib/kubelet/config.yaml")
    text = path.read_text()
    if re.search(r"^runtimeRequestTimeout: 10m0s$", text, re.M):
        print("kubelet_runtime_timeout_already_configured=true")
        return
    if len(re.findall(r"^runtimeRequestTimeout: 0s$", text, re.M)) != 1:
        raise RuntimeError("unexpected kubelet config; inspect before changing")
    backup = Path(tempfile.mkdtemp(prefix="cmdp-kubelet-backup-", dir="/var/lib/kubelet"))
    target = backup / "config.yaml"
    target.write_text(text)
    target.chmod(0o600)
    metadata = path.stat()
    fd, replacement = tempfile.mkstemp(prefix="cmdp-config-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(re.sub(r"^runtimeRequestTimeout: 0s$", "runtimeRequestTimeout: 10m0s", text, flags=re.M))
        os.chmod(replacement, metadata.st_mode & 0o777)
        os.chown(replacement, metadata.st_uid, metadata.st_gid)
        os.replace(replacement, path)
        subprocess.run(["systemctl", "restart", "kubelet"], check=True)
        subprocess.run(["systemctl", "is-active", "kubelet"], check=True)
    finally:
        Path(replacement).unlink(missing_ok=True)
    print("kubelet_runtime_timeout=10m backup=" + str(target))


if __name__ == "__main__":
    main()
