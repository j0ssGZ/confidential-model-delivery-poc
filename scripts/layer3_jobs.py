"""Render a separate Kata Job with public inputs only; never apply it implicitly."""

import argparse
import ipaddress
import json
from pathlib import Path
import re

CASES = ("synthetic", "positive", "tampered-signature", "denied", "wrong-aes")
RUNNER = '''
import os
from pathlib import Path
from confidential_model_delivery_poc.attested_consumer import main
from confidential_model_delivery_poc.cdh import retrieve_key
from confidential_model_delivery_poc.signed_consumer import download_signed_bundle
case = os.environ['CHECK_CASE']
if case == 'synthetic':
    assert retrieve_key('default/test/wrong-aes') == bytes(32)
    print('cdh_python_synthetic_ok=true', flush=True)
    raise SystemExit(0)
resource = {'denied': 'default/test/denied', 'wrong-aes': 'default/test/wrong-aes'}.get(case, 'default/key/minilm-l6-v2')
args = ['--public-key', '/etc/model-signing/public.pem', '--work-dir', '/work/check',
        '--key-resource', resource, '--cdh-timeout', '30']
if case == 'tampered-signature':
    bundle, signature = download_signed_bundle(os.environ['BUNDLE_REPOSITORY'], os.environ['BUNDLE_REVISION'], Path('/work/download'))
    data = bytearray(signature.read_bytes())
    data[-1] ^= 1
    altered = Path('/work/altered.sig')
    altered.write_bytes(data)
    args += ['--bundle', str(bundle), '--signature', str(altered)]
else:
    args += ['--repo-id', os.environ['BUNDLE_REPOSITORY'], '--revision', os.environ['BUNDLE_REVISION']]
raise SystemExit(main(args))
'''


def render(case: str, image: str, kbs_ip: str) -> dict:
    if case not in CASES:
        raise ValueError("unsupported case")
    if not re.fullmatch(r"[a-z0-9./_-]+@sha256:[a-f0-9]{64}", image):
        raise ValueError("image must use an explicit repository and SHA-256 digest")
    address = ipaddress.IPv4Address(kbs_ip)
    if not address.is_private or address.is_loopback or address.is_unspecified:
        raise ValueError("KBS must be an internal IPv4 ClusterIP")
    job = json.loads((Path(__file__).resolve().parents[1] / "k8s/layer3/consumer-job.json").read_text())
    job["metadata"]["generateName"] = f"attested-{case}-"
    template = job["spec"]["template"]
    template["metadata"]["labels"]["case"] = case
    template["metadata"]["annotations"] = {
        "io.containerd.cri.runtime-handler": "kata-qemu-coco-dev",
        "io.katacontainers.config.runtime.create_container_timeout": "300",
        "io.katacontainers.config.hypervisor.kernel_params": f"agent.aa_kbc_params=cc_kbc::http://{address}:8080",
    }
    container = template["spec"]["containers"][0]
    container["image"] = image
    container["command"] = ["python", "-c", RUNNER]
    container["env"] = [{"name": "CHECK_CASE", "value": case}]
    return job


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--kbs-ip", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(render(args.case, args.image, args.kbs_ip)))
    except ValueError as error:
        parser.error(str(error))
