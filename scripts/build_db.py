#!/usr/bin/env python3
"""
Build Mineral Database.

Converts YAML source files to SQLite database, or imports from
the legacy crystal_presets.py dictionary format.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mineral_database.db import get_connection, init_database, insert_mineral, insert_category
from mineral_database.models import Mineral


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
        for preset_id, preset_data in presets_dict.items():
            mineral = Mineral.from_dict(preset_id, preset_data)
            insert_mineral(conn, mineral)
            count += 1

        for category_name, preset_ids in categories_dict.items():
            insert_category(conn, category_name, preset_ids)

        conn.commit()

    return count


def import_from_yaml(yaml_dir: Path, db_path: Path) -> int:
    """Import presets from YAML files.

    Args:
        yaml_dir: Directory containing YAML files
        db_path: Path to output database

    Returns:
        Number of presets imported
    """
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is required for YAML import. Install with: pip install pyyaml")
        sys.exit(1)

    init_database(db_path)

    count = 0
    with get_connection(db_path) as conn:
        for yaml_file in yaml_dir.glob('*.yaml'):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            preset_id = yaml_file.stem
            mineral = Mineral.from_dict(preset_id, data)
            insert_mineral(conn, mineral)
            count += 1

        conn.commit()

    return count


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
            del data['id']

            yaml_file = yaml_dir / f"{mineral.id}.yaml"
            with open(yaml_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description='Build mineral database from source files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --from-yaml data/source/minerals -o data/minerals.db
  %(prog)s --from-legacy crystal_presets.py -o data/minerals.db
  %(prog)s --export-yaml data/minerals.db -o data/source/minerals
        """
    )

    parser.add_argument('--from-yaml', type=Path, metavar='DIR',
                        help='Import from YAML directory')
    parser.add_argument('--from-legacy', type=Path, metavar='FILE',
                        help='Import from legacy crystal_presets.py')
    parser.add_argument('--export-yaml', type=Path, metavar='DB',
                        help='Export database to YAML files')
    parser.add_argument('-o', '--output', type=Path, required=True,
                        help='Output file/directory')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    if args.from_yaml:
        if not args.from_yaml.is_dir():
            print(f"Error: {args.from_yaml} is not a directory")
            sys.exit(1)
        count = import_from_yaml(args.from_yaml, args.output)
        print(f"Imported {count} presets from YAML to {args.output}")

    elif args.from_legacy:
        if not args.from_legacy.exists():
            print(f"Error: {args.from_legacy} does not exist")
            sys.exit(1)

        # Import the legacy module
        import importlib.util
        spec = importlib.util.spec_from_file_location("crystal_presets", args.from_legacy)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        presets = getattr(module, 'CRYSTAL_PRESETS', {})
        categories = getattr(module, 'PRESET_CATEGORIES', {})

        count = import_from_python_dict(presets, categories, args.output)
        print(f"Imported {count} presets from legacy module to {args.output}")

    elif args.export_yaml:
        if not args.export_yaml.exists():
            print(f"Error: {args.export_yaml} does not exist")
            sys.exit(1)
        count = export_to_yaml(args.export_yaml, args.output)
        print(f"Exported {count} presets to YAML in {args.output}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
