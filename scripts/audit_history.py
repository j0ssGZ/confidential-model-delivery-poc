"""Scoped Git-history scan: known local key bytes and common credential patterns.

Reports object IDs only, never matched values. This is not a proof that all
possible secrets are absent. Fixture-like matches require manual assessment.
"""

import argparse
import base64
import re
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", type=Path, action="append", default=[])
    args = parser.parse_args()
    needles = []
    for path in args.key_file:
        value = path.read_bytes()
        if len(value) != 32:
            parser.error("known key must have exactly 32 bytes")
        needles.extend([value, base64.b64encode(value), value.hex().encode()])
    pattern = re.compile(rb"(?:hf_[A-Za-z0-9]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
    objects = {line.split(b" ", 1)[0] for line in git("rev-list", "--objects", "--all").splitlines()}
    blobs = 0
    findings = []
    for oid in sorted(objects):
        if git("cat-file", "-t", oid.decode()).strip() != b"blob":
            continue
        blobs += 1
        data = git("cat-file", "blob", oid.decode())
        if pattern.search(data) or any(needle in data for needle in needles):
            findings.append(oid.decode())
    print(f"history_blobs_scanned={blobs} known_keys={len(args.key_file)} findings={len(findings)}")
    for oid in findings:
        print(f"review_blob={oid}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
