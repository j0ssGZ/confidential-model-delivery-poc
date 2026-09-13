"""Scan every regular file in every docker-save layer without printing secrets."""

import argparse
import base64
import json
from pathlib import Path
import re
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--known-secret", action="append", type=Path, default=[])
    args = parser.parse_args()
    needles = []
    for path in args.known_secret:
        value = path.read_bytes()
        needles.extend((value, base64.b64encode(value), value.hex().encode()))
    findings = []
    markers = []
    files = 0
    with tarfile.open(args.archive) as archive:
        manifest = json.load(archive.extractfile("manifest.json"))
        for layer_path in dict.fromkeys(layer for image in manifest for layer in image["Layers"]):
            with tarfile.open(fileobj=archive.extractfile(layer_path), mode="r|*") as layer:
                for member in layer:
                    if not member.isfile():
                        continue
                    files += 1
                    data = layer.extractfile(member).read()
                    if any(secret in data for secret in needles):
                        findings.append(member.name)
                    if re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|hf_[A-Za-z0-9]{30,}|gh[pousr]_[A-Za-z0-9]{30,}", data):
                        markers.append(member.name)
                    if re.search(r"^(?:app/)?(?:secrets|models|artifacts)/|(?:^|/)\.cache/|\.(safetensors|enc)$", member.name.removeprefix("./")):
                        findings.append(member.name)
    print(f"image_layer_files={files} known_secret_or_artifact_findings={len(findings)} marker_files={len(markers)}")
    for name in sorted(set(findings)):
        print("finding_path=" + name)
    for name in sorted(set(markers)):
        print("review_marker_path=" + name)
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
