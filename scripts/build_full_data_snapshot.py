#!/usr/bin/env python3
"""Build a sanitized, GitHub-compatible full data snapshot.

The source packages stay untouched. Text files are copied after credential and
local-path redaction. Files above the configured threshold are stored as
deterministic gzip streams so no ordinary Git object reaches GitHub's 100 MiB
hard limit. Duplicate archives, caches, backups, lock files, debug inspections,
and failure screenshots are intentionally excluded and recorded in a manifest.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


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
    ".sha256",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}

EXCLUDED_COMPONENTS = {
    ".git",
    "__pycache__",
    "失败截图",
    "分业务ZIP",
}

EXCLUDED_NAMES = {
    ".DS_Store",
    ".collector.lock",
}

EXCLUDED_SUFFIXES = {
    ".lock",
    ".log",
    ".pyc",
    ".sqlite",
    ".sqlite3",
    ".tmp",
    ".zip",
}

LOCAL_PATH_RE = re.compile(rb"/Users/[^/\s\"']+/")
URL_SECRET_RE = re.compile(
    rb"(?i)(xsec_token|access_token|api_key|apikey|key)="
    rb"[A-Za-z0-9._~+/=%-]{12,}"
)
ASSIGNED_SECRET_RE = re.compile(
    rb"(?i)(\"?(?:api[_-]?key|access[_-]?token|client[_-]?secret|"
    rb"password|passwd|authorization|cookie|sessionid)\"?\s*[:=]\s*)"
    rb"(\"[^\"]*\"|'[^']*'|[A-Za-z0-9._~+/=%-]{8,})"
)
GOOGLE_KEY_RE = re.compile(rb"AIza[0-9A-Za-z_-]{30,}")
AWS_KEY_RE = re.compile(rb"AKIA[0-9A-Z]{16}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guiyang-source", type=Path, required=True)
    parser.add_argument("--thailand-source", type=Path, required=True)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--max-regular-file-mib",
        type=int,
        default=45,
        help="Files at or above this size are stored as .gz (default: 45 MiB).",
    )
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exclusion_reason(relative: Path) -> str | None:
    if any(part in EXCLUDED_COMPONENTS for part in relative.parts):
        return "non_canonical_directory"
    if any(part.startswith("_backup_") for part in relative.parts):
        return "duplicate_backup"
    if relative.name in EXCLUDED_NAMES or relative.name.startswith("._"):
        return "operating_system_or_lock_file"
    if relative.name.endswith(".inspect.ndjson"):
        return "debug_inspection_artifact"
    if "过期需重导" in relative.name:
        return "obsolete_export"
    if relative.suffix.lower() in EXCLUDED_SUFFIXES:
        return "cache_database_or_duplicate_archive"
    return None


def redact_text(data: bytes) -> tuple[bytes, Counter[str]]:
    counts: Counter[str] = Counter()

    data, count = LOCAL_PATH_RE.subn(b"[LOCAL_HOME]/", data)
    counts["local_absolute_path"] += count

    def redact_url(match: re.Match[bytes]) -> bytes:
        key = match.group(1).lower()
        counts[f"url_parameter_{key.decode('ascii', errors='replace')}"] += 1
        return key + b"_redacted=1"

    data = URL_SECRET_RE.sub(redact_url, data)

    def redact_assignment(match: re.Match[bytes]) -> bytes:
        counts["assigned_secret"] += 1
        return match.group(1) + b'"[REDACTED]"'

    data = ASSIGNED_SECRET_RE.sub(redact_assignment, data)
    data, count = GOOGLE_KEY_RE.subn(b"[REDACTED_GOOGLE_KEY]", data)
    counts["google_api_key"] += count
    data, count = AWS_KEY_RE.subn(b"[REDACTED_AWS_KEY]", data)
    counts["aws_access_key"] += count
    return data, counts


def apply_known_repairs(label: str, relative: Path, data: bytes) -> tuple[bytes, list[str]]:
    """Repair confirmed package-index defects without touching source packages."""
    repairs: list[str] = []
    if label == "guiyang_v11_2_full" and relative.as_posix() == "数据目录.json":
        old = "02_Data数据/02_贵阳市景区数据/贵阳市子景点数据.json".encode("utf-8")
        new = "02_Data数据/02_贵阳市景区数据/贵阳市景点数据.json".encode("utf-8")
        if old in data:
            data = data.replace(old, new)
            repairs.append("Area 数据目录路径由不存在的“子景点数据”修正为正式“景点数据”文件")
    return data, repairs


def xlsx_contains_sensitive_text(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as workbook:
            for name in workbook.namelist():
                if not name.endswith(".xml"):
                    continue
                data = workbook.read(name)
                if (
                    LOCAL_PATH_RE.search(data)
                    or URL_SECRET_RE.search(data)
                    or ASSIGNED_SECRET_RE.search(data)
                    or GOOGLE_KEY_RE.search(data)
                    or AWS_KEY_RE.search(data)
                ):
                    return True
    except zipfile.BadZipFile:
        return True
    return False


def deterministic_gzip(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            zipped.write(data)


def prepare_destination(path: Path, repo_root: Path, replace: bool) -> None:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve()
    if resolved_root not in resolved_path.parents:
        raise ValueError(f"destination escapes repository: {path}")
    if path.exists():
        if not replace:
            raise FileExistsError(f"destination exists; use --replace: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True)


def copy_package(
    *,
    label: str,
    source: Path,
    destination: Path,
    repo_root: Path,
    max_regular_bytes: int,
    replace: bool,
) -> dict[str, object]:
    if not source.is_dir():
        raise FileNotFoundError(source)
    prepare_destination(destination, repo_root, replace)

    files: list[dict[str, object]] = []
    exclusions: list[dict[str, str]] = []
    redactions: dict[str, dict[str, int]] = {}
    repairs: dict[str, list[str]] = {}
    totals = Counter()

    for source_path in sorted(source.rglob("*")):
        if not source_path.is_file():
            continue
        relative = source_path.relative_to(source)
        reason = exclusion_reason(relative)
        if reason:
            exclusions.append({"path": relative.as_posix(), "reason": reason})
            totals["excluded_files"] += 1
            totals["excluded_bytes"] += source_path.stat().st_size
            continue
        if source_path.suffix.lower() == ".xlsx" and xlsx_contains_sensitive_text(source_path):
            exclusions.append(
                {"path": relative.as_posix(), "reason": "spreadsheet_contains_sensitive_text"}
            )
            totals["excluded_files"] += 1
            totals["excluded_bytes"] += source_path.stat().st_size
            continue

        source_bytes = source_path.read_bytes()
        output_bytes = source_bytes
        file_redactions: Counter[str] = Counter()
        if source_path.suffix.lower() in TEXT_SUFFIXES:
            output_bytes, file_redactions = redact_text(source_bytes)
        if file_redactions:
            redactions[relative.as_posix()] = dict(sorted(file_redactions.items()))
        output_bytes, file_repairs = apply_known_repairs(label, relative, output_bytes)
        if file_repairs:
            repairs[relative.as_posix()] = file_repairs

        stored_relative = relative
        storage = "regular"
        if len(output_bytes) >= max_regular_bytes:
            stored_relative = Path(relative.as_posix() + ".gz")
            storage = "gzip"

        destination_path = destination / stored_relative
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if storage == "gzip":
            deterministic_gzip(destination_path, output_bytes)
        else:
            destination_path.write_bytes(output_bytes)

        stored_bytes = destination_path.read_bytes()
        files.append(
            {
                "sourcePath": relative.as_posix(),
                "storedPath": destination_path.relative_to(repo_root).as_posix(),
                "storage": storage,
                "sourceBytes": len(source_bytes),
                "sanitizedBytes": len(output_bytes),
                "storedBytes": len(stored_bytes),
                "sanitizedSha256": sha256_bytes(output_bytes),
                "storedSha256": sha256_bytes(stored_bytes),
            }
        )
        totals["included_files"] += 1
        totals["source_bytes"] += len(source_bytes)
        totals["sanitized_bytes"] += len(output_bytes)
        totals["stored_bytes"] += len(stored_bytes)
        totals[f"storage_{storage}"] += 1

    return {
        "label": label,
        "sourcePackage": source.name,
        "destination": destination.relative_to(repo_root).as_posix(),
        "totals": dict(sorted(totals.items())),
        "files": files,
        "redactions": redactions,
        "repairs": repairs,
        "exclusions": exclusions,
    }


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    max_regular_bytes = args.max_regular_file_mib * 1024 * 1024
    packages = [
        copy_package(
            label="guiyang_v11_2_full",
            source=args.guiyang_source.resolve(),
            destination=repo_root / "data/guiyang/full_v11_2",
            repo_root=repo_root,
            max_regular_bytes=max_regular_bytes,
            replace=args.replace,
        ),
        copy_package(
            label="thailand_20260913_full",
            source=args.thailand_source.resolve(),
            destination=repo_root / "data/thailand/full_20260913",
            repo_root=repo_root,
            max_regular_bytes=max_regular_bytes,
            replace=args.replace,
        ),
    ]

    manifest = {
        "snapshotVersion": "full-data-v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "regularFileLimitMiB": args.max_regular_file_mib,
        "privacyBoundary": (
            "Sanitized private-repository snapshot; credentials, local paths, caches, "
            "duplicate archives, obsolete backups, debug inspections, and failure "
            "screenshots are excluded."
        ),
        "packages": packages,
    }
    manifest_path = repo_root / "data/full-data-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("FULL DATA SNAPSHOT BUILT")
    for package in packages:
        totals = package["totals"]
        print(
            f"- {package['label']}: {totals['included_files']} files, "
            f"{totals['stored_bytes']} stored bytes, "
            f"{totals.get('excluded_files', 0)} exclusions"
        )
    print(f"- manifest: {manifest_path.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
