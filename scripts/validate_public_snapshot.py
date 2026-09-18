#!/usr/bin/env python3
"""Validate the public-safe knowledge graph snapshot with the standard library."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_GITHUB_FILE_BYTES = 100 * 1024 * 1024

EXPECTED_CSV_ROWS = {
    "data/guiyang/spatial/guiyang-city.csv": 1,
    "data/guiyang/spatial/guiyang-admin-areas.csv": 157,
    "data/guiyang/spatial/guiyang-admin-registry-review.csv": 157,
    "data/guiyang/spatial/guiyang-h3-cells-r7-r8.csv": 13_011,
    "data/thailand/administrative/泰国_ADM0_国家表.csv": 1,
    "data/thailand/administrative/泰国_ADM1_府级表.csv": 77,
    "data/thailand/administrative/泰国_ADM2_县区表.csv": 928,
    "data/thailand/administrative/泰国_ADM3_乡分区表.csv": 7_436,
}

EXPECTED_GEOJSON_FEATURES = {
    "data/thailand/administrative/泰国_ADM0_国家边界.geojson": 1,
    "data/thailand/administrative/泰国_ADM1_府级边界.geojson": 77,
    "data/thailand/administrative/泰国_ADM2_县区边界.geojson": 928,
    "data/thailand/administrative/泰国_ADM3_乡分区边界.geojson": 7_436,
}

TEXT_SUFFIXES = {
    ".csv",
    ".cypher",
    ".geojson",
    ".json",
    ".md",
    ".schema",
    ".txt",
    ".yaml",
    ".yml",
}

SENSITIVE_PATTERNS = {
    "local_absolute_path": re.compile(r"/Users/[^/\s]+/"),
    "xiaohongshu_temporary_token": re.compile(r"xsec_token=", re.IGNORECASE),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "assigned_secret": re.compile(
        r"(?i)(?:api[_-]?key|secret|password|passwd|access[_-]?token)"
        r"\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"
    ),
}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def validate_json(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # noqa: BLE001 - aggregate all validation errors
            fail(f"invalid JSON: {path.relative_to(ROOT)}: {exc}", errors)


def validate_csv_counts(errors: list[str]) -> None:
    for relative, expected in EXPECTED_CSV_ROWS.items():
        path = ROOT / relative
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = sum(1 for _ in csv.reader(handle)) - 1
        if rows != expected:
            fail(f"CSV row count mismatch: {relative}: {rows} != {expected}", errors)


def validate_all_csv(errors: list[str]) -> tuple[int, int]:
    csv.field_size_limit(sys.maxsize)
    file_count = 0
    data_rows = 0
    for path in sorted(ROOT.rglob("*.csv")):
        if ".git" in path.parts:
            continue
        file_count += 1
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                first_row = next(reader)
                width = len(first_row)
                if path.parent.name == "csv_export" and width == 0:
                    fail(f"exported CSV has zero columns: {path.relative_to(ROOT)}", errors)
                    continue
                if any(cell != "" for cell in first_row):
                    data_rows += 1
                for row_number, row in enumerate(reader, start=2):
                    if any(cell != "" for cell in row):
                        data_rows += 1
                    if path.parent.name == "csv_export" and len(row) != width:
                        fail(
                            f"exported CSV width mismatch at row {row_number}: "
                            f"{path.relative_to(ROOT)}: {len(row)} != {width}",
                            errors,
                        )
                        break
        except (UnicodeDecodeError, csv.Error, StopIteration) as exc:
            fail(f"invalid CSV: {path.relative_to(ROOT)}: {exc}", errors)
    return file_count, data_rows


def validate_geojson_counts(errors: list[str]) -> None:
    for relative, expected in EXPECTED_GEOJSON_FEATURES.items():
        path = ROOT / relative
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if payload.get("type") != "FeatureCollection":
            fail(f"not a FeatureCollection: {relative}", errors)
            continue
        actual = len(payload.get("features", []))
        if actual != expected:
            fail(f"GeoJSON feature count mismatch: {relative}: {actual} != {expected}", errors)


def validate_public_safety(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        size = path.stat().st_size
        if size >= MAX_GITHUB_FILE_BYTES:
            fail(f"file reaches GitHub 100MB limit: {path.relative_to(ROOT)}", errors)
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                fail(f"sensitive pattern {label}: {path.relative_to(ROOT)}", errors)


def main() -> int:
    errors: list[str] = []
    validate_json(errors)
    validate_csv_counts(errors)
    csv_files, csv_rows = validate_all_csv(errors)
    validate_geojson_counts(errors)
    validate_public_safety(errors)

    if errors:
        print("PUBLIC SNAPSHOT VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PUBLIC SNAPSHOT VALIDATION PASSED")
    print(f"- JSON files: {sum(1 for _ in ROOT.rglob('*.json'))}")
    print(f"- Parsed CSV files: {csv_files}")
    print(f"- Parsed CSV data rows: {csv_rows}")
    print(f"- Checked fixed CSV contracts: {len(EXPECTED_CSV_ROWS)}")
    print(f"- Checked GeoJSON contracts: {len(EXPECTED_GEOJSON_FEATURES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
