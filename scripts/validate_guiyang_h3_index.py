#!/usr/bin/env python3
"""Validate the finalized Guiyang R9/R7 and R8/R7 H3 index contracts."""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import h3


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/guiyang/full_v11_2"
CATALOG = PACKAGE / "数据目录.json"
REPORT = ROOT / "data/guiyang/H3_INDEX_VALIDATION.json"


def load_json(path: Path) -> object:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    compressed = Path(str(path) + ".gz")
    if compressed.exists():
        with gzip.open(compressed, "rt", encoding="utf-8-sig") as handle:
            return json.load(handle)
    raise FileNotFoundError(path)


def add_error(errors: list[dict[str, str]], entity_type: str, record_id: object, message: str) -> None:
    if len(errors) < 500:
        errors.append(
            {"entityType": entity_type, "id": str(record_id or ""), "message": message}
        )


def main() -> int:
    catalog = load_json(CATALOG)
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    stats: Counter[str] = Counter()
    by_entity: dict[str, Counter[str]] = defaultdict(Counter)
    coordinate_systems: Counter[str] = Counter()

    for dataset in catalog["datasets"]:
        entity_type = dataset["entityType"]
        payload = load_json(PACKAGE / dataset["file"])
        records = payload.get("records", [])
        if payload.get("entityType") != entity_type:
            add_error(errors, entity_type, "", "entityType differs from catalog")
        if len(records) != dataset["recordCount"] or len(records) != payload.get("recordCount"):
            warnings.append(
                {
                    "entityType": entity_type,
                    "message": (
                        f"catalog={dataset['recordCount']}, payload={payload.get('recordCount')}, "
                        f"actual={len(records)}; H3 validation uses actual canonical records"
                    ),
                }
            )

        for record in records:
            record_id = record.get("id")
            by_entity[entity_type]["records"] += 1

            if entity_type == "GeoCell":
                cell = str(record_id or "")
                resolution = record.get("h3Resolution")
                if not h3.is_valid_cell(cell):
                    add_error(errors, entity_type, record_id, "invalid GeoCell id")
                    continue
                if h3.get_resolution(cell) != resolution:
                    add_error(errors, entity_type, record_id, "GeoCell resolution mismatch")
                by_entity[entity_type][f"r{resolution}"] += 1
                stats["geocells_validated"] += 1
                continue

            if entity_type == "PlaceAlias":
                for field, resolution in (("targetCell", 8), ("targetCellR9", 9)):
                    cell = record.get(field)
                    if not cell:
                        continue
                    if not h3.is_valid_cell(cell) or h3.get_resolution(cell) != resolution:
                        add_error(errors, entity_type, record_id, f"invalid {field}")
                    else:
                        stats[f"place_alias_{field}_validated"] += 1
                continue

            precision = record.get("geoPrecision")
            latitude = record.get("latitude")
            longitude = record.get("longitude")
            fine = record.get("h3Index")
            coarse = record.get("h3IndexCoarse")
            coordinate_system = record.get("coordinateSystem")
            if coordinate_system:
                coordinate_systems[str(coordinate_system)] += 1

            if precision == "exact":
                if latitude is None or longitude is None:
                    add_error(errors, entity_type, record_id, "exact point lacks coordinates")
                    continue
                if not fine or not coarse:
                    add_error(errors, entity_type, record_id, "exact point lacks R9/R7 pair")
                    continue
                expected_fine = h3.latlng_to_cell(float(latitude), float(longitude), 9)
                expected_coarse = h3.latlng_to_cell(float(latitude), float(longitude), 7)
                if fine != expected_fine:
                    add_error(errors, entity_type, record_id, "R9 differs from coordinate recomputation")
                if coarse != expected_coarse:
                    add_error(errors, entity_type, record_id, "R7 differs from coordinate recomputation")
                stats["exact_points_validated"] += 1
                by_entity[entity_type]["exact"] += 1
            elif precision in {"approx", "none"}:
                if fine or coarse:
                    add_error(errors, entity_type, record_id, f"{precision} point contains H3 index")
                by_entity[entity_type][precision] += 1

    report = {
        "validatedAt": datetime.now(timezone.utc).isoformat(),
        "h3Library": "h3-py",
        "h3Version": h3.__version__,
        "coordinateContract": {
            "projectCoordinateSystem": "GCJ02",
            "fineResolution": 9,
            "coarseResolution": 7,
            "frameworkResolutions": [8, 7],
            "warning": (
                "These H3 IDs are derived from the project's GCJ02 runtime coordinates. "
                "They must not be mixed with H3 IDs derived from WGS84 coordinates."
            ),
        },
        "statistics": dict(sorted(stats.items())),
        "coordinateSystems": dict(sorted(coordinate_systems.items())),
        "byEntity": {name: dict(sorted(values.items())) for name, values in sorted(by_entity.items())},
        "errorCount": len(errors),
        "errors": errors,
        "warningCount": len(warnings),
        "warnings": warnings,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        print(f"GUIYANG H3 VALIDATION FAILED: {len(errors)} errors")
        for error in errors[:30]:
            print(f"- {error['entityType']} {error['id']}: {error['message']}")
        return 1

    print("GUIYANG H3 VALIDATION PASSED")
    print(f"- h3-py: {h3.__version__}")
    print(f"- exact R9/R7 points: {stats['exact_points_validated']}")
    print(f"- framework cells: {stats['geocells_validated']}")
    print(f"- PlaceAlias R8 anchors: {stats['place_alias_targetCell_validated']}")
    print(f"- PlaceAlias R9 anchors: {stats['place_alias_targetCellR9_validated']}")
    print(f"- catalog count warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
