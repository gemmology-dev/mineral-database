#!/usr/bin/env python3
"""
Migrate flat mineral YAMLs to family+expression structure.

This script:
1. Identifies minerals with multiple crystal forms (e.g., fluorite-*)
2. Groups them into families with shared gemmological properties
3. Creates new consolidated YAML files with expressions array
4. Archives old flat YAML files

Usage:
    python scripts/migrate_to_families.py [--dry-run] [--verbose]
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


# Family group definitions
# Maps family_id -> list of (yaml_stem, expression_slug, expression_name, is_primary)
FAMILY_GROUPS: dict[str, list[tuple[str, str, str, bool]]] = {
    "fluorite": [
        ("fluorite", "cube", "Cube", True),
        ("fluorite-octahedron", "octahedron", "Octahedron", False),
        ("fluorite-cuboctahedron", "cuboctahedron", "Cuboctahedron", False),
        ("fluorite-twin", "twin", "Penetration Twin", False),
        ("fluorite-interpenetrating", "interpenetrating", "Interpenetrating Twin", False),
    ],
    "quartz": [
        ("quartz", "prism", "Prismatic", True),
        ("quartz-short", "short", "Short Prism", False),
        ("quartz-scepter", "scepter", "Scepter", False),
        ("quartz-faden", "faden", "Faden", False),
        ("quartz-japan-twin", "japan-twin", "Japan Law Twin", False),
        ("quartz-dauphine-twin", "dauphine-twin", "Dauphine Twin", False),
        ("quartz-brazil-twin", "brazil-twin", "Brazil Law Twin", False),
    ],
    "pyrite": [
        ("pyrite", "cube", "Cube", True),
        ("pyrite-pyritohedron", "pyritohedron", "Pyritohedron", False),
        ("pyrite-iron-cross", "iron-cross", "Iron Cross Twin", False),
    ],
    "garnet": [
        ("garnet", "combination", "Combination", True),
        ("garnet-dodecahedron", "dodecahedron", "Rhombic Dodecahedron", False),
        ("garnet-trapezohedron", "trapezohedron", "Trapezohedron", False),
    ],
    "diamond": [
        ("diamond", "octahedron", "Octahedron", True),
        ("diamond-cube", "cube", "Cube", False),
        ("diamond-macle", "macle", "Macle Twin", False),
    ],
    "beryl": [
        ("beryl", "prism", "Hexagonal Prism", True),
        ("beryl-tabular", "tabular", "Tabular", False),
    ],
    "calcite": [
        ("calcite-scalenohedron", "scalenohedron", "Scalenohedron", True),
        ("calcite-rhomb", "rhomb", "Rhombohedron", False),
        ("calcite-nailhead", "nailhead", "Nailhead", False),
    ],
    "corundum": [
        ("corundum", "bipyramid", "Hexagonal Bipyramid", True),
        ("corundum-barrel", "barrel", "Barrel", False),
    ],
    "gypsum": [
        ("gypsum", "tabular", "Tabular", True),
        ("gypsum-swallowtail", "swallowtail", "Swallowtail Twin", False),
    ],
    "spinel": [
        ("spinel", "octahedron", "Octahedron", True),
        ("spinel-macle", "macle", "Macle Twin", False),
    ],
    "staurolite": [
        ("staurolite-cross-90", "cross-90", "90 Degree Cross", True),
        ("staurolite-cross-60", "cross-60", "60 Degree Cross", False),
    ],
    "topaz": [
        ("topaz", "prism", "Prismatic", True),
        ("topaz-tabular", "tabular", "Tabular", False),
    ],
    "tourmaline": [
        ("tourmaline", "prism", "Prismatic", True),
        ("tourmaline-watermelon", "watermelon", "Watermelon", False),
    ],
    "chrysoberyl": [
        ("chrysoberyl", "tabular", "Tabular Twin", True),
        ("chrysoberyl-trilling", "trilling", "Trilling", False),
    ],
    "orthoclase": [
        ("orthoclase", "prismatic", "Prismatic", True),
        ("orthoclase-carlsbad", "carlsbad", "Carlsbad Twin", False),
    ],
}

# Properties that should be shared (extracted from base)
SHARED_PROPERTIES = [
    "name",
    "system",
    "point_group",
    "chemistry",
    "hardness",
    "sg",
    "ri",
    "birefringence",
    "optical_character",
    "dispersion",
    "lustre",
    "cleavage",
    "fracture",
    "pleochroism",
    "pleochroism_strength",
    "pleochroism_color1",
    "pleochroism_color2",
    "pleochroism_color3",
    "pleochroism_notes",
    "colors",
    "treatments",
    "inclusions",
    "localities",
    "fluorescence",
    "twin_law",
    "phenomenon",
]

# Properties specific to each expression
EXPRESSION_PROPERTIES = [
    "cdl",
    "description",
    "forms",
    "note",
]


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    """Save data to a YAML file with nice formatting."""
    with open(path, "w") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=100,
        )


def extract_base_name(full_name: str) -> str:
    """Extract base mineral name from full name with form suffix.

    Examples:
        'Fluorite (Octahedron)' -> 'Fluorite'
        'Quartz (Japan Twin)' -> 'Quartz'
        'Diamond' -> 'Diamond'
    """
    if " (" in full_name:
        return full_name.split(" (")[0]
    return full_name


def migrate_family(
    family_id: str,
    members: list[tuple[str, str, str, bool]],
    source_dir: Path,
    output_dir: Path,
    archive_dir: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Migrate a family from flat files to consolidated structure.

    Args:
        family_id: Family identifier (e.g., 'fluorite')
        members: List of (yaml_stem, slug, name, is_primary) tuples
        source_dir: Directory containing source YAML files
        output_dir: Directory for output YAML files
        archive_dir: Directory to move old files
        dry_run: If True, don't write files
        verbose: If True, print detailed output

    Returns:
        True if migration succeeded, False otherwise
    """
    if verbose:
        print(f"\nProcessing family: {family_id}")

    # Load all member files
    member_data: dict[str, dict[str, Any]] = {}
    for yaml_stem, slug, name, is_primary in members:
        yaml_path = source_dir / f"{yaml_stem}.yaml"
        if not yaml_path.exists():
            print(f"  Warning: {yaml_path} not found, skipping")
            continue
        member_data[yaml_stem] = load_yaml(yaml_path)
        if verbose:
            print(f"  Loaded: {yaml_stem}.yaml")

    if not member_data:
        print(f"  Error: No member files found for {family_id}")
        return False

    # Find the primary member to extract base properties
    primary_stem = next(
        (stem for stem, slug, name, is_primary in members if is_primary),
        list(member_data.keys())[0],
    )
    primary_data = member_data.get(primary_stem, list(member_data.values())[0])

    # Build family data from primary member
    family_data: dict[str, Any] = {
        "id": family_id,
        "name": extract_base_name(primary_data.get("name", family_id.title())),
        "crystal_system": primary_data.get("system", "cubic"),
    }

    # Copy shared properties from primary
    for prop in SHARED_PROPERTIES:
        if prop in primary_data and prop not in ["name", "system"]:
            family_data[prop] = primary_data[prop]

    # Build expressions array
    expressions: list[dict[str, Any]] = []
    for yaml_stem, slug, expr_name, is_primary in members:
        if yaml_stem not in member_data:
            continue

        data = member_data[yaml_stem]
        expr: dict[str, Any] = {
            "slug": slug,
            "name": expr_name,
            "cdl": data["cdl"],
        }

        if is_primary:
            expr["is_primary"] = True

        # Add expression-specific properties
        if "description" in data:
            expr["form_description"] = data["description"]
        if "forms" in data:
            expr["forms"] = data["forms"]
        if "note" in data and data["note"] != family_data.get("note"):
            expr["note"] = data["note"]

        # Check for point group override
        if data.get("point_group") != primary_data.get("point_group"):
            expr["point_group"] = data.get("point_group")

        expressions.append(expr)

    family_data["expressions"] = expressions

    if verbose:
        print(f"  Created family with {len(expressions)} expressions")

    # Write consolidated YAML
    if not dry_run:
        output_path = output_dir / f"{family_id}.yaml"
        save_yaml(output_path, family_data)
        if verbose:
            print(f"  Wrote: {output_path}")

        # Archive old files (except the base file which we replace)
        archive_dir.mkdir(parents=True, exist_ok=True)
        for yaml_stem, _, _, _ in members:
            if yaml_stem == family_id:
                continue  # Don't archive the base file
            old_path = source_dir / f"{yaml_stem}.yaml"
            if old_path.exists():
                archive_path = archive_dir / f"{yaml_stem}.yaml"
                shutil.move(str(old_path), str(archive_path))
                if verbose:
                    print(f"  Archived: {yaml_stem}.yaml")

    return True


def migrate_single_mineral(
    yaml_stem: str,
    source_dir: Path,
    output_dir: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Convert a single mineral to family+expression format.

    Args:
        yaml_stem: YAML file stem (e.g., 'ruby')
        source_dir: Directory containing source YAML files
        output_dir: Directory for output YAML files
        dry_run: If True, don't write files
        verbose: If True, print detailed output

    Returns:
        True if migration succeeded, False otherwise
    """
    yaml_path = source_dir / f"{yaml_stem}.yaml"
    if not yaml_path.exists():
        return False

    data = load_yaml(yaml_path)

    # Build family data
    family_data: dict[str, Any] = {
        "id": yaml_stem,
        "name": data.get("name", yaml_stem.replace("-", " ").title()),
        "crystal_system": data.get("system", "cubic"),
    }

    # Copy shared properties
    for prop in SHARED_PROPERTIES:
        if prop in data and prop not in ["name", "system"]:
            family_data[prop] = data[prop]

    # Single expression
    expr: dict[str, Any] = {
        "slug": "default",
        "name": family_data["name"],
        "cdl": data["cdl"],
        "is_primary": True,
    }

    if "description" in data:
        expr["form_description"] = data["description"]
    if "forms" in data:
        expr["forms"] = data["forms"]
    if "note" in data:
        expr["note"] = data["note"]

    family_data["expressions"] = [expr]

    if not dry_run:
        output_path = output_dir / f"{yaml_stem}.yaml"
        save_yaml(output_path, family_data)
        if verbose:
            print(f"  Converted: {yaml_stem}.yaml")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate flat mineral YAMLs to family+expression structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed progress",
    )
    parser.add_argument(
        "--families-only",
        action="store_true",
        help="Only migrate multi-form families, skip single minerals",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "source" / "minerals",
        help="Source directory containing YAML files",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "archive",
        help="Directory to archive old variant files",
    )

    args = parser.parse_args()

    source_dir = args.source_dir
    archive_dir = args.archive_dir

    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        sys.exit(1)

    if args.dry_run:
        print("DRY RUN - no files will be modified\n")

    # Track which files are part of families
    family_members: set[str] = set()
    for family_id, members in FAMILY_GROUPS.items():
        for yaml_stem, _, _, _ in members:
            family_members.add(yaml_stem)

    # Migrate multi-form families
    print("Migrating multi-form families...")
    family_success = 0
    family_fail = 0

    for family_id, members in FAMILY_GROUPS.items():
        if migrate_family(
            family_id=family_id,
            members=members,
            source_dir=source_dir,
            output_dir=source_dir,  # Output to same dir, archive variants
            archive_dir=archive_dir,
            dry_run=args.dry_run,
            verbose=args.verbose,
        ):
            family_success += 1
        else:
            family_fail += 1

    print(f"\nFamilies: {family_success} migrated, {family_fail} failed")

    if args.families_only:
        return

    # Migrate single minerals (those not part of a family group)
    print("\nConverting single minerals to family format...")
    single_success = 0
    single_skip = 0

    for yaml_file in sorted(source_dir.glob("*.yaml")):
        stem = yaml_file.stem
        if stem in family_members:
            continue  # Already handled as part of a family

        # Check if already migrated (has expressions array)
        data = load_yaml(yaml_file)
        if "expressions" in data:
            if args.verbose:
                print(f"  Skipping (already migrated): {stem}.yaml")
            single_skip += 1
            continue

        if migrate_single_mineral(
            yaml_stem=stem,
            source_dir=source_dir,
            output_dir=source_dir,
            dry_run=args.dry_run,
            verbose=args.verbose,
        ):
            single_success += 1

    print(f"Singles: {single_success} converted, {single_skip} already migrated")

    print("\nMigration complete!")
    if not args.dry_run:
        print(f"Archived variant files are in: {archive_dir}")


if __name__ == "__main__":
    main()
