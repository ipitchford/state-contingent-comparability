#!/usr/bin/env python3
"""Verify every distributed file, excluding the manifest and Git metadata."""
from pathlib import Path, PurePosixPath
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = ROOT / "SHA256SUMS.txt"
    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        relative = PurePosixPath(name)
        if (len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)
                or relative.is_absolute() or ".." in relative.parts
                or name in expected or name != relative.as_posix()
                or name == manifest.name):
            raise ValueError("Invalid or duplicate manifest entry: " + name)
        expected[name] = digest
    actual = set()
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] == ".git":
            continue
        if path.is_symlink():
            raise ValueError("Unexpected symbolic link: " + str(path))
        if path.is_file() and path != manifest:
            actual.add(relative.as_posix())
    if actual != set(expected):
        raise ValueError("File-set mismatch: " + repr(sorted(actual ^ set(expected))))
    for name, digest in expected.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("SHA-256 mismatch: " + name)
    print(json.dumps({"status": "passed", "files": len(expected),
                      "scope": "All distributed bytes except SHA256SUMS.txt; repository .git metadata is outside the distribution; no authenticity claim"}))


if __name__ == "__main__":
    main()
