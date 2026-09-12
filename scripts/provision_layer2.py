"""Create Layer 2 public ConfigMap and AES Secret without printing their data."""

import argparse
import subprocess
from pathlib import Path

from confidential_model_delivery_poc.producer import read_key
from confidential_model_delivery_poc.signing import load_public_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context', required=True)
    parser.add_argument('--public-key', required=True, type=Path)
    parser.add_argument('--aes-key', required=True, type=Path)
    args = parser.parse_args()
    try:
        load_public_key(args.public_key)
        read_key(args.aes_key)
        base = ['kubectl', '--context', args.context, '-n', 'secure-ai-layer2']
        # Capture the Secret YAML in memory only; never print or persist it.
        for params in ([ 'configmap', 'model-signing-public-key', f'--from-file=public.pem={args.public_key}'],
                       [ 'secret', 'generic', 'model-decryption-key', f'--from-file=key={args.aes_key}']):
            data = subprocess.run(base + ['create', *params, '--dry-run=client', '-o', 'json'],
                                  capture_output=True, check=True).stdout
            subprocess.run(base + ['apply', '-f', '-'], input=data, capture_output=True, check=True)
    except Exception:
        parser.error('provisioning failed: check inputs, namespace, context and permissions')
    print('layer2_key_resources_applied=true')


if __name__ == '__main__':
    main()
