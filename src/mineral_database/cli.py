"""
Mineral Database CLI.

Command-line interface for the mineral database.
"""

import argparse
import json
import sys

from . import __version__
from .queries import (
    count_presets,
    get_preset,
    list_preset_categories,
    list_presets,
    search_presets,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog='mineral-db',
        description='Mineral Database - Crystal Presets Query Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                  List all presets
  %(prog)s --list cubic            List cubic presets
  %(prog)s --info diamond          Show diamond preset info
  %(prog)s --search garnet         Search for garnet-related presets
  %(prog)s --json diamond          Output diamond preset as JSON
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    parser.add_argument(
        '--list', nargs='?', const='all', metavar='CATEGORY',
        help='List presets (optionally by crystal system or category)'
    )

    parser.add_argument(
        '--info', type=str, metavar='NAME',
        help='Show detailed info for a preset'
    )

    parser.add_argument(
        '--search', type=str, metavar='QUERY',
        help='Search presets by name/mineral/chemistry'
    )

    parser.add_argument(
        '--json', type=str, metavar='NAME',
        help='Output preset as JSON'
    )

    parser.add_argument(
        '--categories', action='store_true',
        help='List preset categories'
    )

    parser.add_argument(
        '--count', action='store_true',
        help='Show total number of presets'
    )

    parser.add_argument(
        '--props', type=str, metavar='GROUP',
        help='Property group for --info (basic, physical, optical, fga, etc.)'
    )

    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.count:
        print(f"Total presets: {count_presets()}")
        return 0

    if parsed_args.categories:
        print("Preset Categories:")
        for cat in list_preset_categories():
            presets = list_presets(cat)
            print(f"  {cat:15} ({len(presets)} presets)")
        return 0

    if parsed_args.list:
        if parsed_args.list == 'all':
            print(f"All Crystal Presets ({count_presets()} total):")
            for cat in list_preset_categories():
                presets = list_presets(cat)
                if presets:
                    print(f"\n  {cat.title()}:")
                    for name in presets:
                        preset = get_preset(name)
                        if preset:
                            print(f"    {name:25} - {preset['name']}")
        else:
            presets = list_presets(parsed_args.list)
            if presets:
                print(f"{parsed_args.list.title()} Presets:")
                for name in presets:
                    preset = get_preset(name)
                    if preset:
                        print(f"  {name:25} - {preset['name']}")
            else:
                print(f"No presets found for category: {parsed_args.list}")
        return 0

    if parsed_args.info:
        preset = get_preset(parsed_args.info)
        if preset:
            print(f"Preset: {parsed_args.info}")
            print(f"  Name:        {preset['name']}")
            print(f"  CDL:         {preset['cdl']}")
            print(f"  System:      {preset['system']}")
            print(f"  Point Group: {preset['point_group']}")
            print(f"  Chemistry:   {preset['chemistry']}")
            print(f"  Hardness:    {preset['hardness']}")
            print(f"  Description: {preset['description']}")
            if preset.get('localities'):
                print(f"  Localities:  {', '.join(preset['localities'])}")
            if preset.get('forms'):
                print(f"  Forms:       {', '.join(preset['forms'])}")
            if preset.get('sg'):
                print(f"  SG:          {preset['sg']}")
            if preset.get('ri'):
                print(f"  RI:          {preset['ri']}")
            if preset.get('twin_law'):
                print(f"  Twin Law:    {preset['twin_law']}")
        else:
            print(f"Preset not found: {parsed_args.info}")
            return 1
        return 0

    if parsed_args.search:
        matches = search_presets(parsed_args.search)
        if matches:
            print(f"Presets matching '{parsed_args.search}':")
            for name in matches:
                preset = get_preset(name)
                if preset:
                    print(f"  {name:25} - {preset['name']}")
        else:
            print(f"No presets found matching: {parsed_args.search}")
        return 0

    if parsed_args.json:
        preset = get_preset(parsed_args.json)
        if preset:
            print(json.dumps(preset, indent=2))
        else:
            print(f'{{"error": "Preset not found: {parsed_args.json}"}}')
            return 1
        return 0

    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
