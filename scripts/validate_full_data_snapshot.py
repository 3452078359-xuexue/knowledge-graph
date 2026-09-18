#!/usr/bin/env python3
"""Validate full-data manifest integrity, GitHub file limits, and redaction."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/full-data-manifest.json"
GITHUB_HARD_LIMIT = 100 * 1024 * 1024

SENSITIVE_PATTERNS = {
    "local_absolute_path": re.compile(rb"/Users/[^/\s\"']+/"),
    "xiaohongshu_temporary_token": re.compile(rb"xsec_token=", re.IGNORECASE),
    "google_api_key": re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "assigned_secret": re.compile(
        rb"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|passwd|"
        rb"authorization|cookie|sessionid)\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=%-]{8,}"
    ),
}

TEXT_SUFFIXES = {
    ".csv",
    ".cypher",
    ".geojson",
    ".json",
    ".jsonl",
    ".md",
    ".ndjson",
    ".py",
    ".schema",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scan_sensitive(data: bytes, label: str, errors: list[str]) -> None:
    for name, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(data):
            errors.append(f"sensitive pattern {name}: {label}")


def scan_xlsx(path: Path, errors: list[str]) -> None:
    try:
        with zipfile.ZipFile(path) as workbook:
            for member in workbook.namelist():
                if member.endswith(".xml"):
                    scan_sensitive(
                        workbook.read(member),
                        f"{path.relative_to(ROOT)}::{member}",
                        errors,
                    )
    except zipfile.BadZipFile:
        errors.append(f"invalid XLSX archive: {path.relative_to(ROOT)}")


def main() -> int:
    if not MANIFEST.exists():
        print("FULL DATA SNAPSHOT VALIDATION FAILED\n- manifest missing")
        return 1

    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors: list[str] = []
    checked_files = 0
    checked_bytes = 0
    listed_paths: set[str] = set()

    for package in payload.get("packages", []):
        for item in package.get("files", []):
            relative = item["storedPath"]
            listed_paths.add(relative)
            path = ROOT / relative
            if not path.is_file():
                errors.append(f"missing stored file: {relative}")
                continue
            stored = path.read_bytes()
            checked_files += 1
            checked_bytes += len(stored)
            if len(stored) != item["storedBytes"]:
                errors.append(f"stored size mismatch: {relative}")
            if sha256(stored) != item["storedSha256"]:
                errors.append(f"stored checksum mismatch: {relative}")
            if len(stored) >= GITHUB_HARD_LIMIT:
                errors.append(f"GitHub 100 MiB limit reached: {relative}")

            source_suffix = Path(item["sourcePath"]).suffix.lower()
            sanitized = gzip.decompress(stored) if item["storage"] == "gzip" else stored
            if len(sanitized) != item["sanitizedBytes"]:
                errors.append(f"sanitized size mismatch: {relative}")
            if sha256(sanitized) != item["sanitizedSha256"]:
                errors.append(f"sanitized checksum mismatch: {relative}")
            if source_suffix in TEXT_SUFFIXES:
                scan_sensitive(sanitized, relative, errors)
            if source_suffix == ".xlsx":
                scan_xlsx(path, errors)

    for root in (ROOT / "data/guiyang/full_v11_2", ROOT / "data/thailand/full_20260913"):
        if not root.exists():
            errors.append(f"data root missing: {root.relative_to(ROOT)}")
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.relative_to(ROOT).as_posix() not in listed_paths:
                errors.append(f"unlisted file: {path.relative_to(ROOT)}")

    if errors:
        print("FULL DATA SNAPSHOT VALIDATION FAILED")
        for error in errors[:200]:
            print(f"- {error}")
        if len(errors) > 200:
            print(f"- ... {len(errors) - 200} additional errors")
        return 1

    print("FULL DATA SNAPSHOT VALIDATION PASSED")
    print(f"- files: {checked_files}")
    print(f"- stored bytes: {checked_bytes}")
    print("- files at or above 100 MiB: 0")
    print("- detected credentials or local absolute paths: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
