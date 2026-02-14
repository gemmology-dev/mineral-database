#!/usr/bin/env python3
"""
Build Mineral Database.

Converts YAML source files to SQLite database, or imports from
the legacy crystal_presets.py dictionary format.

Supports both:
- Legacy flat YAML format (single mineral per file with `cdl` field)
- New family+expression format (family properties with `expressions` array)
"""

import argparse
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mineral_database.db import (
    get_connection,
    init_database,
    init_reference_tables,
    insert_category,
    insert_expression,
    insert_family,
    insert_mineral,
)
from mineral_database.models import Mineral, MineralExpression, MineralFamily


def import_from_python_dict(presets_dict: dict, categories_dict: dict, db_path: Path) -> int:
    """Import presets from Python dictionary format.

    Args:
        presets_dict: Dictionary of preset_id -> preset_data
        categories_dict: Dictionary of category_name -> list of preset_ids
        db_path: Path to output database

    Returns:
        Number of presets imported
    """
    init_database(db_path)

    count = 0
    with get_connection(db_path) as conn:
        # Populate reference tables (shape factors, thresholds)
        init_reference_tables(conn)

        for preset_id, preset_data in presets_dict.items():
            mineral = Mineral.from_dict(preset_id, preset_data)
            insert_mineral(conn, mineral)
            count += 1

        for category_name, preset_ids in categories_dict.items():
            insert_category(conn, category_name, preset_ids)

        conn.commit()

    return count


def _is_family_format(data: dict[str, Any]) -> bool:
    """Check if YAML data is in the new family+expression format."""
    return "expressions" in data and isinstance(data["expressions"], list)


def _import_family_yaml(
    family_id: str,
    data: dict[str, Any],
    conn,
    verbose: bool = False,
) -> tuple[int, int]:
    """Import a family+expression YAML file.

    Args:
        family_id: Family identifier (YAML filename stem)
        data: Parsed YAML data
        conn: Database connection
        verbose: Print progress

    Returns:
        Tuple of (family_count, expression_count)
    """
    # Create MineralFamily
    family = MineralFamily.from_dict(family_id, data)
    insert_family(conn, family)

    if verbose:
        print(f"  Family: {family.name} ({family_id})")

    # Create MineralExpressions
    expression_count = 0
    for i, expr_data in enumerate(data.get("expressions", [])):
        slug = expr_data.get("slug", "default")
        expression_id = f"{family_id}-{slug}" if slug != "default" else family_id

        expression = MineralExpression.from_dict(
            family_id=family_id,
            expression_data=expr_data,
            expression_id=expression_id,
        )
        # Set sort order if not specified
        if expression.sort_order == 0 and not expr_data.get("is_primary"):
            expression.sort_order = i

        insert_expression(conn, expression)
        expression_count += 1

        if verbose:
            primary_mark = " (primary)" if expression.is_primary else ""
            print(f"    Expression: {expression.name}{primary_mark}")

    # Also insert into legacy minerals table for backwards compatibility
    for expr_data in data.get("expressions", []):
        slug = expr_data.get("slug", "default")
        expression_id = f"{family_id}-{slug}" if slug != "default" else family_id

        # Build a flat mineral dict combining family + expression data
        mineral_data = {
            "name": (
                f"{family.name} ({expr_data.get('name', slug.title())})"
                if slug != "default"
                else family.name
            ),
            "cdl": expr_data["cdl"],
            "system": family.crystal_system,
            "point_group": expr_data.get("point_group") or family.point_group,
            "chemistry": family.chemistry,
            "hardness": family.hardness_min,  # Use min for backwards compat
            "description": expr_data.get("form_description") or family.description,
            "localities": family.localities,
            "forms": expr_data.get("forms") or family.forms,
            "sg": family.sg_min,
            "ri": family.ri_min,
            "birefringence": family.birefringence,
            "optical_character": family.optical_character,
            "dispersion": family.dispersion,
            "lustre": family.lustre,
            "cleavage": family.cleavage,
            "fracture": family.fracture,
            "pleochroism": family.pleochroism,
            "pleochroism_strength": family.pleochroism_strength,
            "pleochroism_color1": family.pleochroism_color1,
            "pleochroism_color2": family.pleochroism_color2,
            "pleochroism_color3": family.pleochroism_color3,
            "pleochroism_notes": family.pleochroism_notes,
            "colors": family.colors,
            "treatments": family.treatments,
            "inclusions": family.inclusions,
            "twin_law": family.twin_law,
            "phenomenon": family.phenomenon,
            "note": expr_data.get("note") or family.notes,
            "ri_min": family.ri_min,
            "ri_max": family.ri_max,
            "sg_min": family.sg_min,
            "sg_max": family.sg_max,
            "heat_treatment_temp_min": family.heat_treatment_temp_min,
            "heat_treatment_temp_max": family.heat_treatment_temp_max,
            "origin": family.origin,
            "growth_method": family.growth_method,
            "natural_counterpart_id": family.natural_counterpart_id,
        }

        mineral = Mineral.from_dict(expression_id, mineral_data)
        insert_mineral(conn, mineral)

    return 1, expression_count


def _import_legacy_yaml(
    mineral_id: str,
    data: dict[str, Any],
    conn,
    verbose: bool = False,
) -> int:
    """Import a legacy flat YAML file.

    Args:
        mineral_id: Mineral identifier (YAML filename stem)
        data: Parsed YAML data
        conn: Database connection
        verbose: Print progress

    Returns:
        Number of minerals imported (always 1)
    """
    mineral = Mineral.from_dict(mineral_id, data)
    insert_mineral(conn, mineral)

    if verbose:
        print(f"  Mineral: {mineral.name} ({mineral_id})")

    return 1


def import_from_yaml(
    yaml_dir: Path,
    db_path: Path,
    verbose: bool = False,
) -> tuple[int, int, int]:
    """Import presets from YAML files.

    Supports both legacy flat format and new family+expression format.
    Scans the given directory and also checks for synthetics/, simulants/,
    and composites/ subdirectories.

    Args:
        yaml_dir: Directory containing YAML files (e.g., data/source/minerals/)
        db_path: Path to output database
        verbose: Print progress

    Returns:
        Tuple of (family_count, expression_count, legacy_mineral_count)
    """
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is required for YAML import. Install with: pip install pyyaml")
        sys.exit(1)

    init_database(db_path)

    family_count = 0
    expression_count = 0
    legacy_count = 0

    # Collect all directories to scan: the main dir + sibling directories
    # for synthetics, simulants, composites
    scan_dirs: list[tuple[Path, str]] = [(yaml_dir, "minerals")]
    parent = yaml_dir.parent
    for subdir_name in ("synthetics", "simulants", "composites"):
        subdir = parent / subdir_name
        if subdir.is_dir():
            scan_dirs.append((subdir, subdir_name))

    with get_connection(db_path) as conn:
        # Populate reference tables (shape factors, thresholds)
        init_reference_tables(conn)

        for scan_dir, category_label in scan_dirs:
            yaml_files = sorted(scan_dir.glob("*.yaml"))
            if yaml_files and verbose:
                print(f"\n--- {category_label} ({len(yaml_files)} files) ---")

            for yaml_file in yaml_files:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                if data is None:
                    continue

                file_id = yaml_file.stem

                if _is_family_format(data):
                    fc, ec = _import_family_yaml(file_id, data, conn, verbose)
                    family_count += fc
                    expression_count += ec
                else:
                    legacy_count += _import_legacy_yaml(file_id, data, conn, verbose)

        conn.commit()

    return family_count, expression_count, legacy_count


def export_to_yaml(db_path: Path, yaml_dir: Path) -> int:
    """Export database to YAML files.

    Args:
        db_path: Path to database
        yaml_dir: Output directory for YAML files

    Returns:
        Number of files exported
    """
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is required for YAML export. Install with: pip install pyyaml")
        sys.exit(1)

    yaml_dir.mkdir(parents=True, exist_ok=True)

    from mineral_database.db import get_all_minerals

    count = 0
    with get_connection(db_path) as conn:
        minerals = get_all_minerals(conn)
        for mineral in minerals:
            data = mineral.to_dict()
            # Remove id from data (it's in the filename)
            del data["id"]

            yaml_file = yaml_dir / f"{mineral.id}.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Build mineral database from source files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --from-yaml data/source/minerals -o data/minerals.db
  %(prog)s --from-legacy crystal_presets.py -o data/minerals.db
  %(prog)s --export-yaml data/minerals.db -o data/source/minerals
        """,
    )

    parser.add_argument(
        "--from-yaml",
        type=Path,
        metavar="DIR",
        help="Import from YAML directory (also scans sibling synthetics/, simulants/, composites/)",
    )
    parser.add_argument(
        "--from-legacy", type=Path, metavar="FILE", help="Import from legacy crystal_presets.py"
    )
    parser.add_argument(
        "--export-yaml", type=Path, metavar="DB", help="Export database to YAML files"
    )
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output file/directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--with-models", action="store_true", help="Generate SVG/STL/glTF models for each mineral"
    )

    args = parser.parse_args()

    db_created = False

    if args.from_yaml:
        if not args.from_yaml.is_dir():
            print(f"Error: {args.from_yaml} is not a directory")
            sys.exit(1)

        family_count, expr_count, legacy_count = import_from_yaml(
            args.from_yaml, args.output, args.verbose
        )

        if family_count > 0:
            print(f"Imported {family_count} families with {expr_count} expressions")
        if legacy_count > 0:
            print(f"Imported {legacy_count} legacy minerals")
        print(f"Database written to: {args.output}")
        db_created = True

    elif args.from_legacy:
        if not args.from_legacy.exists():
            print(f"Error: {args.from_legacy} does not exist")
            sys.exit(1)

        # Import the legacy module
        import importlib.util

        spec = importlib.util.spec_from_file_location("crystal_presets", args.from_legacy)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        presets = getattr(module, "CRYSTAL_PRESETS", {})
        categories = getattr(module, "PRESET_CATEGORIES", {})

        count = import_from_python_dict(presets, categories, args.output)
        print(f"Imported {count} presets from legacy module to {args.output}")
        db_created = True

    elif args.export_yaml:
        if not args.export_yaml.exists():
            print(f"Error: {args.export_yaml} does not exist")
            sys.exit(1)
        count = export_to_yaml(args.export_yaml, args.output)
        print(f"Exported {count} presets to YAML in {args.output}")

    else:
        parser.print_help()
        sys.exit(1)

    # Generate models if requested
    if args.with_models and db_created:
        print("\nGenerating 3D models...")
        try:
            from generate_models import generate_all_models

            success, failure = generate_all_models(args.output, verbose=args.verbose)
            print(f"Model generation complete: {success} success, {failure} failures")
        except ImportError as e:
            print(f"Warning: Could not generate models. Missing dependencies: {e}")
            print("Install with: pip install cdl-parser crystal-geometry crystal-renderer")


if __name__ == "__main__":
    main()
