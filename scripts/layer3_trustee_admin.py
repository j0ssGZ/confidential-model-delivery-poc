"""Scoped lab provisioning via the official pinned kbs-client; never print secrets.

Run on the trusted Ubuntu operator host. --check-audience only reads policies.
--key-file provisions an existing AES; it never generates or overwrites a key.
"""

import argparse
import base64
import http.client
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from cryptography.hazmat.primitives.serialization import load_pem_private_key


def b64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", required=True, type=Path)
    parser.add_argument("--check-audience", action="store_true")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    secret = json.loads(subprocess.check_output([
        "kubectl", "-n", "coco-trustee", "get", "secret",
        "trustee-bootstrap-user-keys", "-o", "json"]))["data"]
    token = base64.b64decode(secret["KBS_ADMIN_TOKEN"]).strip()
    with tempfile.TemporaryDirectory(prefix="cmdp-trustee-admin-") as directory:
        root = Path(directory)
        token_file = root / "token"
        token_file.write_bytes(token)
        with (root / "forward.log").open("w+") as log:
            forward = subprocess.Popen(["kubectl", "-n", "coco-trustee", "port-forward",
                                        "svc/trustee-kbs", "18083:8080"], stdout=log, stderr=log)
            try:
                for attempt in range(50):
                    if forward.poll() is not None:
                        raise RuntimeError("port-forward failed")
                    if "Forwarding from 127.0.0.1:18083" in (root / "forward.log").read_text():
                        break
                    time.sleep(0.1)
                else:
                    raise RuntimeError("port-forward readiness timeout")
                if args.check_audience:
                    header, payload, _ = token.split(b".")
                    claims = json.loads(base64.urlsafe_b64decode(payload + b"=" * (-len(payload) % 4)))
                    if claims["aud"] != ["KBS"]:
                        raise RuntimeError("unexpected audience in bootstrap token")
                    claims["aud"] = ["cmdp-wrong-audience"]
                    signed = header + b"." + b64url(json.dumps(claims).encode())
                    private = load_pem_private_key(base64.b64decode(secret["KBS_ADMIN_PRIVATE_KEY"]), None)
                    wrong_token = signed + b"." + b64url(private.sign(signed))
                    for label, candidate, expected in [("valid", token, 200), ("wrong", wrong_token, 401)]:
                        connection = http.client.HTTPConnection("127.0.0.1", 18083, timeout=10)
                        try:
                            connection.request("GET", "/kbs/v0/resource-policy",
                                               headers={"Authorization": "Bearer " + candidate.decode()})
                            status = connection.getresponse().status
                            if status != expected:
                                raise RuntimeError("unexpected admin authorization result")
                            print(f"admin_audience_{label}_http={status}")
                        finally:
                            connection.close()
                def provision(path, file):
                    subprocess.run([str(args.client), "--url", "http://127.0.0.1:18083",
                        "config", "--admin-token-file", str(token_file), "set-resource",
                        "--path", path, "--resource-file", str(file)], check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("resource_provisioned=" + path)
                if args.fixture:
                    fixture = root / "fixture"
                    fixture.write_bytes(b"\x00" * 32)
                    provision("default/test/wrong-aes", fixture)
                if args.key_file:
                    key = args.key_file.read_bytes()
                    if len(key) != 32 or key == b"\x00" * 32:
                        raise RuntimeError("invalid existing AES or fixture collision")
                    provision("default/key/minilm-l6-v2", args.key_file)
            finally:
                forward.terminate()
                forward.wait(timeout=10)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Trustee administration failed; inspect authorized configuration without dumping secrets") from None
