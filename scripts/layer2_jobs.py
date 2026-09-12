"""Render an isolated signed Job; no cluster writes or secrets in output."""

import argparse
import json
import re
from pathlib import Path

RUNNER = '''
import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from confidential_model_delivery_poc.signed_consumer import download_signed_bundle, main
case = os.environ['CHECK_CASE']
if os.environ['INPUT_MODE'] == 'fixture':
    bundle = Path('/fixtures/minilm-l6-v2.bundle.enc')
    signature = Path(str(bundle) + '.sig')
else:
    bundle, signature = download_signed_bundle(os.environ['BUNDLE_REPOSITORY'], os.environ['BUNDLE_REVISION'], Path('/work/download'))
public = Path('/etc/model-signing/public.pem')
aes = Path('/var/run/secrets/model-delivery/key')
if case in ('tampered-bundle', 'tampered-signature'):
    source = bundle if case == 'tampered-bundle' else signature
    data = bytearray(source.read_bytes())
    data[-1] ^= 1
    target = Path('/work/altered')
    target.write_bytes(data)
    if case == 'tampered-bundle': bundle = target
    else: signature = target
elif case == 'wrong-public':
    public = Path('/work/wrong-public.pem')
    public.write_bytes(Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
elif case == 'wrong-aes':
    aes = Path('/work/wrong-aes')
    aes.write_bytes(os.urandom(32))
raise SystemExit(main(['--bundle', str(bundle), '--signature', str(signature), '--public-key', str(public), '--key-file', str(aes), '--work-dir', '/work/check']))
'''


def render(case: str, revision: str | None, fixture_path: str | None, repository: str) -> dict:
    if bool(revision) == bool(fixture_path):
        raise ValueError("choose exactly one revision or fixture path")
    if revision and not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        raise ValueError("revision must be a full Git commit")
    if fixture_path and (not Path(fixture_path).is_absolute() or fixture_path == "/"):
        raise ValueError("fixture path must be an explicit non-root absolute node directory")
    job = json.loads((Path(__file__).resolve().parents[1] / 'k8s/layer2/job.json').read_text())
    mode = 'fixture' if fixture_path else 'hub'
    job['metadata']['name'] = f'signed-{mode}-{case}'
    pod = job['spec']['template']['spec']
    container = pod['containers'][0]
    container['command'] = ['python', '-c', RUNNER]
    container['env'] = [{'name': name, 'value': value} for name, value in {
        'CHECK_CASE': case, 'INPUT_MODE': mode, 'BUNDLE_REPOSITORY': repository,
        'BUNDLE_REVISION': revision or ''}.items()]
    if fixture_path:
        pod['volumes'].append({'name': 'fixtures', 'hostPath': {'path': fixture_path, 'type': 'Directory'}})
        container['volumeMounts'].append({'name': 'fixtures', 'mountPath': '/fixtures', 'readOnly': True})
    return job


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['positive', 'tampered-bundle', 'tampered-signature', 'wrong-public', 'wrong-aes'], required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--revision')
    source.add_argument('--fixture-path')
    parser.add_argument('--repo-id', default='j0ssGZ/confidential-model-delivery-artifacts')
    args = parser.parse_args()
    try:
        print(json.dumps(render(args.case, args.revision, args.fixture_path, args.repo_id)))
    except ValueError as error:
        parser.error(str(error))
