"""Create a new operator key without overwriting any existing file."""

import argparse
import os
import secrets
from pathlib import Path


def generate_key(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as target:
        target.write(secrets.token_bytes(32))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        generate_key(args.path)
    except OSError:
        parser.error("key not created: check permissions and choose a NEW path")
    print("key_created=true")
