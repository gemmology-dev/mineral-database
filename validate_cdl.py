#!/usr/bin/env python3
"""Validate all CDL strings in the mineral database YAML source files."""

import json
import os
import sys

import cdl_parser
import crystal_geometry
import yaml
from cdl_parser.models import AmorphousDescription

SOURCE_DIRS = {
    "minerals": "data/source/minerals",
    "synthetics": "data/source/synthetics",
    "simulants": "data/source/simulants",
    "composites": "data/source/composites",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def collect_cdl_strings():
    """Walk all YAML source files and extract CDL strings."""
    entries = []
    for category, rel_dir in SOURCE_DIRS.items():
        dir_path = os.path.join(BASE_DIR, rel_dir)
        if not os.path.isdir(dir_path):
            print(f"WARNING: directory not found: {dir_path}", file=sys.stderr)
            continue
        for fname in sorted(os.listdir(dir_path)):
            if not fname.endswith(".yaml"):
                continue
            fpath = os.path.join(dir_path, fname)
            with open(fpath) as f:
                data = yaml.safe_load(f)
            if not data:
                continue

            mineral_name = data.get("name", fname)
            mineral_id = data.get("id", fname)

            # Top-level cdl field (if any)
            if data.get("cdl"):
                entries.append(
                    {
                        "mineral": mineral_name,
                        "mineral_id": mineral_id,
                        "file": fname,
                        "category": category,
                        "cdl": data["cdl"],
                        "source": "cdl",
                    }
                )

            # Expressions array
            for i, expr in enumerate(data.get("expressions", [])):
                cdl_str = expr.get("cdl", "")
                if not cdl_str or not cdl_str.strip():
                    entries.append(
                        {
                            "mineral": mineral_name,
                            "mineral_id": mineral_id,
                            "file": fname,
                            "category": category,
                            "cdl": "",
                            "source": f"expressions[{i}]",
                            "expr_name": expr.get("name", ""),
                            "empty": True,
                        }
                    )
                    continue
                entries.append(
                    {
                        "mineral": mineral_name,
                        "mineral_id": mineral_id,
                        "file": fname,
                        "category": category,
                        "cdl": cdl_str.strip(),
                        "source": f"expressions[{i}]",
                        "expr_name": expr.get("name", ""),
                    }
                )

    return entries


def validate_entry(entry):
    """Parse and attempt geometry generation for one CDL string."""
    result = {
        "mineral": entry["mineral"],
        "mineral_id": entry["mineral_id"],
        "file": entry["file"],
        "category": entry["category"],
        "cdl": entry["cdl"],
        "source": entry["source"],
    }
    if "expr_name" in entry:
        result["expr_name"] = entry["expr_name"]

    # Empty CDL strings
    if entry.get("empty"):
        result["warning"] = "Empty CDL string"
        return "warning", result

    cdl_str = entry["cdl"]

    # Step 1: Parse
    try:
        desc = cdl_parser.parse_cdl(cdl_str)
    except Exception as e:
        result["error"] = f"Parse error: {e}"
        return "invalid", result

    result["parsed"] = True

    # Step 2: Handle amorphous descriptions (no crystal geometry)
    if isinstance(desc, AmorphousDescription):
        result["type"] = "amorphous"
        result["subtype"] = desc.subtype
        result["shapes"] = desc.shapes
        return "valid", result

    # Step 3: Geometry for crystalline descriptions
    try:
        geom = crystal_geometry.cdl_to_geometry(desc)
        result["type"] = "crystalline"
        result["vertices"] = len(geom.vertices)
        result["faces"] = len(geom.faces)
    except Exception as e:
        result["warning"] = f"Geometry warning: {e}"
        return "warning", result

    return "valid", result


def main():
    entries = collect_cdl_strings()
    print(f"Collected {len(entries)} CDL entries from YAML files\n")

    valid = []
    invalid = []
    warnings = []

    amorphous_count = 0
    crystalline_count = 0
    aggregate_count = 0
    nested_count = 0

    for entry in entries:
        status, result = validate_entry(entry)
        if status == "valid":
            valid.append(result)
            icon = "OK"
            if result.get("type") == "amorphous":
                amorphous_count += 1
            else:
                crystalline_count += 1
            # Count v2 features
            cdl = entry["cdl"]
            if "~" in cdl:
                aggregate_count += 1
            if ">" in cdl and ">" != cdl[-1]:
                nested_count += 1
        elif status == "invalid":
            invalid.append(result)
            icon = "FAIL"
        else:
            warnings.append(result)
            icon = "WARN"

        cdl_display = result["cdl"][:60] if result["cdl"] else "(empty)"
        print(f"  [{icon:4s}] {result['mineral']:30s} {result['source']:18s} {cdl_display}")
        if status == "invalid":
            print(f"         ERROR: {result['error']}")
        elif status == "warning" and "warning" in result:
            print(f"         WARNING: {result['warning']}")

    # Summary
    total = len(valid) + len(invalid) + len(warnings)
    print(f"\n{'=' * 70}")
    print(
        f"SUMMARY: {total} total | {len(valid)} valid | {len(invalid)} invalid | {len(warnings)} warnings"
    )
    print(f"{'=' * 70}")
    print("\nBreakdown:")
    print(f"  Crystalline expressions:  {crystalline_count}")
    print(f"  Amorphous expressions:    {amorphous_count}")
    print(f"  Aggregate expressions:    {aggregate_count}")
    print(f"  Nested growth expressions:{nested_count}")
    print(
        f"  Parse success rate:       {len(valid)}/{total} ({100 * len(valid) / total:.1f}%)"
        if total
        else ""
    )

    report = {
        "summary": {
            "total": total,
            "valid": len(valid),
            "invalid": len(invalid),
            "warnings": len(warnings),
            "crystalline": crystalline_count,
            "amorphous": amorphous_count,
            "aggregates": aggregate_count,
            "nested_growth": nested_count,
        },
        "valid": valid,
        "invalid": invalid,
        "warnings": warnings,
    }

    report_path = os.path.join(BASE_DIR, "cdl-audit-report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
