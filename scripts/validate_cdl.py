#!/usr/bin/env python3
"""
Validate CDL Notation in Mineral Database.

Runs comprehensive validation on all CDL strings in the mineral database and
outputs a detailed report with CDL alongside parsed linguistic descriptions
for manual review.

Validation checks:
1. Parse validation using cdl-parser
2. System/point group consistency between CDL and database fields
3. Point group validity for the given crystal system
4. Miller index notation (4-index for hex/trig, 3-index for others)
5. Modification syntax validation
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mineral_database.db import get_all_minerals, get_connection

# CDL parser imports
try:
    from cdl_parser import (
        CRYSTAL_SYSTEMS,
        MODIFICATION_TYPES,
        POINT_GROUPS,
        parse_cdl,
        validate_cdl,
    )
except ImportError:
    print("Error: cdl-parser is required. Install with: pip install -e ../cdl-parser")
    sys.exit(1)


@dataclass
class ParsedForm:
    """A parsed crystal form."""
    miller: str  # e.g., "{111}" or "{10-10}"
    miller_tuple: tuple  # e.g., (1, 1, 1) or (1, 0, -1, 0)
    scale: float
    name: str | None = None  # Named form if used


@dataclass
class ParsedCDL:
    """Fully parsed CDL description."""
    system: str
    point_group: str
    forms: list[ParsedForm]
    modifications: list[dict] = field(default_factory=list)
    twin: dict | None = None


@dataclass
class ValidationResult:
    """Validation result for a single mineral."""
    mineral_id: str
    name: str
    cdl: str
    db_system: str
    db_point_group: str
    parsed: ParsedCDL | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


def format_miller(miller) -> tuple[str, tuple]:
    """Format Miller index as string and tuple."""
    if miller.i is not None:
        # 4-index notation
        return f"{{{miller.h}{miller.k}{miller.i}{miller.l}}}", (miller.h, miller.k, miller.i, miller.l)
    else:
        # 3-index notation
        return f"{{{miller.h}{miller.k}{miller.l}}}", (miller.h, miller.k, miller.l)


def parse_and_validate(
    mineral_id: str,
    name: str,
    cdl: str,
    db_system: str,
    db_point_group: str,
) -> ValidationResult:
    """Parse and validate a single mineral's CDL notation.

    Returns a ValidationResult with parsed data and any issues found.
    """
    result = ValidationResult(
        mineral_id=mineral_id,
        name=name,
        cdl=cdl,
        db_system=db_system,
        db_point_group=db_point_group,
    )

    # Handle amorphous materials
    if db_system == 'amorphous' or 'amorphous' in cdl.lower():
        result.warnings.append("Amorphous material - standard CDL validation not applicable")
        return result

    # Check for unrecognized tokens after pipe (modifications/twins)
    # Parser may silently ignore invalid modifications
    if '|' in cdl:
        after_pipe = cdl.split('|', 1)[1].strip()
        # Check for anything that looks like a modification but isn't valid
        mod_pattern = re.findall(r'(\w+)\s*\(', after_pipe)
        for mod_name in mod_pattern:
            mod_lower = mod_name.lower()
            if mod_lower not in MODIFICATION_TYPES and mod_lower != 'twin':
                result.errors.append(f"Unrecognized modification '{mod_name}' (valid: {sorted(MODIFICATION_TYPES)})")

    # Phase 1: Parse validation
    valid, error = validate_cdl(cdl)
    if not valid:
        result.errors.append(f"Parse error: {error}")
        return result

    # Parse to get detailed structure
    try:
        desc = parse_cdl(cdl)
    except Exception as e:
        result.errors.append(f"Unexpected parse error: {e}")
        return result

    # Build parsed representation
    forms = []
    for form in desc.forms:
        miller_str, miller_tuple = format_miller(form.miller)
        forms.append(ParsedForm(
            miller=miller_str,
            miller_tuple=miller_tuple,
            scale=form.scale,
            name=form.name,
        ))

    modifications = []
    for mod in desc.modifications:
        modifications.append({
            'type': mod.type,
            'params': mod.params,
        })

    twin = None
    if desc.twin:
        twin = {
            'law': desc.twin.law,
            'axis': desc.twin.axis,
            'angle': desc.twin.angle,
            'type': desc.twin.twin_type,
            'count': desc.twin.count,
        }

    result.parsed = ParsedCDL(
        system=desc.system,
        point_group=desc.point_group,
        forms=forms,
        modifications=modifications,
        twin=twin,
    )

    # Phase 2: System consistency check
    if desc.system != db_system.lower():
        result.errors.append(
            f"System mismatch: CDL has '{desc.system}', database has '{db_system}'"
        )

    # Phase 3: Point group consistency check
    if desc.point_group != db_point_group:
        result.errors.append(
            f"Point group mismatch: CDL has '{desc.point_group}', database has '{db_point_group}'"
        )

    # Phase 4: Validate point group is valid for system
    if desc.system in POINT_GROUPS:
        valid_pgs = POINT_GROUPS[desc.system]
        if desc.point_group not in valid_pgs:
            result.errors.append(
                f"Point group '{desc.point_group}' is not valid for {desc.system} system "
                f"(valid: {sorted(valid_pgs)})"
            )

    # Phase 5: Miller index notation check
    uses_4_index = desc.system in ('hexagonal', 'trigonal')
    for form in desc.forms:
        miller = form.miller
        has_i_index = miller.i is not None

        if uses_4_index and not has_i_index:
            miller_str, _ = format_miller(miller)
            result.warnings.append(
                f"Form {miller_str} uses 3-index but {desc.system} typically uses 4-index {{hkil}}"
            )
        elif not uses_4_index and has_i_index:
            miller_str, _ = format_miller(miller)
            result.errors.append(
                f"Form {miller_str} uses 4-index but {desc.system} should use 3-index {{hkl}}"
            )

    return result


def run_validation(db_path: Path) -> list[ValidationResult]:
    """Run validation on all minerals in the database."""
    results = []

    with get_connection(db_path) as conn:
        minerals = get_all_minerals(conn)

        for mineral in minerals:
            result = parse_and_validate(
                mineral_id=mineral.id,
                name=mineral.name,
                cdl=mineral.cdl,
                db_system=mineral.system,
                db_point_group=mineral.point_group,
            )
            results.append(result)

    return results


def print_full_report(results: list[ValidationResult], show_valid: bool = True) -> None:
    """Print detailed report with CDL and parsed descriptions."""

    errors = [r for r in results if not r.is_valid]
    warnings = [r for r in results if r.is_valid and r.has_warnings]
    valid = [r for r in results if r.is_valid and not r.has_warnings]

    print("\n" + "=" * 80)
    print("CDL VALIDATION REPORT")
    print("=" * 80)
    print(f"\nTotal: {len(results)} minerals")
    print(f"  Valid: {len(valid)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Errors: {len(errors)}")

    if errors:
        print("\n" + "=" * 80)
        print("ERRORS")
        print("=" * 80)
        for r in errors:
            print_mineral_entry(r)

    if warnings:
        print("\n" + "=" * 80)
        print("WARNINGS")
        print("=" * 80)
        for r in warnings:
            print_mineral_entry(r)

    if show_valid and valid:
        print("\n" + "=" * 80)
        print("VALID ENTRIES")
        print("=" * 80)
        for r in valid:
            print_mineral_entry(r)


def print_mineral_entry(r: ValidationResult) -> None:
    """Print a single mineral entry with CDL and parsed description."""
    print(f"\n{'─' * 80}")
    print(f"ID: {r.mineral_id}")
    print(f"Name: {r.name}")
    print(f"CDL: {r.cdl}")
    print(f"DB System: {r.db_system} | DB Point Group: {r.db_point_group}")

    if r.parsed:
        print(f"\nParsed:")
        print(f"  System: {r.parsed.system}")
        print(f"  Point Group: {r.parsed.point_group}")
        print(f"  Forms:")
        for form in r.parsed.forms:
            name_part = f" ({form.name})" if form.name else ""
            print(f"    {form.miller}{name_part} @ {form.scale}")
        if r.parsed.modifications:
            print(f"  Modifications:")
            for mod in r.parsed.modifications:
                print(f"    {mod['type']}({mod['params']})")
        if r.parsed.twin:
            twin = r.parsed.twin
            if twin['law']:
                print(f"  Twin: {twin['law']} law")
            else:
                print(f"  Twin: axis={twin['axis']}, angle={twin['angle']}")

    if r.errors:
        print(f"\n  ERRORS:")
        for err in r.errors:
            print(f"    ❌ {err}")

    if r.warnings:
        print(f"\n  WARNINGS:")
        for warn in r.warnings:
            print(f"    ⚠️  {warn}")


def print_summary_table(results: list[ValidationResult]) -> None:
    """Print a compact summary table."""
    print("\n" + "=" * 120)
    print("SUMMARY TABLE")
    print("=" * 120)
    print(f"{'ID':<20} {'System':<12} {'PG':<8} {'Forms':<30} {'Status':<10}")
    print("-" * 120)

    for r in results:
        if r.parsed:
            forms_str = " + ".join(f"{f.miller}@{f.scale}" for f in r.parsed.forms)
            if len(forms_str) > 28:
                forms_str = forms_str[:25] + "..."
            system = r.parsed.system
            pg = r.parsed.point_group
        else:
            forms_str = "(parse failed)"
            system = r.db_system
            pg = r.db_point_group

        if r.errors:
            status = "❌ ERROR"
        elif r.warnings:
            status = "⚠️ WARN"
        else:
            status = "✅ OK"

        print(f"{r.mineral_id:<20} {system:<12} {pg:<8} {forms_str:<30} {status:<10}")


def export_json(results: list[ValidationResult], output_path: Path) -> None:
    """Export results as JSON for further analysis."""
    data = []
    for r in results:
        entry = {
            'id': r.mineral_id,
            'name': r.name,
            'cdl': r.cdl,
            'db_system': r.db_system,
            'db_point_group': r.db_point_group,
            'is_valid': r.is_valid,
            'errors': r.errors,
            'warnings': r.warnings,
        }
        if r.parsed:
            entry['parsed'] = {
                'system': r.parsed.system,
                'point_group': r.parsed.point_group,
                'forms': [
                    {
                        'miller': f.miller,
                        'miller_tuple': f.miller_tuple,
                        'scale': f.scale,
                        'name': f.name,
                    }
                    for f in r.parsed.forms
                ],
                'modifications': r.parsed.modifications,
                'twin': r.parsed.twin,
            }
        data.append(entry)

    output_path.write_text(json.dumps(data, indent=2))
    print(f"\nJSON exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate CDL notation in mineral database and output detailed report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Validate with full report
  %(prog)s --summary                # Show summary table only
  %(prog)s --errors-only            # Show only entries with errors
  %(prog)s --json report.json       # Export to JSON for analysis
        """
    )

    parser.add_argument(
        'database',
        type=Path,
        nargs='?',
        default=Path(__file__).parent.parent / 'src' / 'mineral_database' / 'data' / 'minerals.db',
        help='Path to mineral database (default: src/mineral_database/data/minerals.db)',
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary table instead of full report',
    )
    parser.add_argument(
        '--errors-only',
        action='store_true',
        help='Only show entries with errors',
    )
    parser.add_argument(
        '--warnings-only',
        action='store_true',
        help='Only show entries with warnings (excluding errors)',
    )
    parser.add_argument(
        '--json',
        type=Path,
        metavar='FILE',
        help='Export results to JSON file',
    )

    args = parser.parse_args()

    if not args.database.exists():
        print(f"Error: Database not found: {args.database}")
        sys.exit(1)

    print(f"Validating: {args.database}")

    results = run_validation(args.database)

    if args.json:
        export_json(results, args.json)

    if args.summary:
        print_summary_table(results)
    elif args.errors_only:
        errors = [r for r in results if not r.is_valid]
        if errors:
            print(f"\n{len(errors)} entries with errors:")
            for r in errors:
                print_mineral_entry(r)
        else:
            print("\n✅ No errors found!")
    elif args.warnings_only:
        warnings = [r for r in results if r.is_valid and r.has_warnings]
        if warnings:
            print(f"\n{len(warnings)} entries with warnings:")
            for r in warnings:
                print_mineral_entry(r)
        else:
            print("\n✅ No warnings found!")
    else:
        print_full_report(results, show_valid=True)

    # Exit with error code if there are errors
    errors = [r for r in results if not r.is_valid]
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
