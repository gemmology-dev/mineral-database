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
    get_counterparts,
    get_family,
    get_preset,
    list_by_origin,
    list_preset_categories,
    list_presets,
    list_simulants,
    list_synthetics,
    search_presets,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="mineral-db",
        description="Mineral Database - Crystal Presets Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                  List all presets
  %(prog)s --list cubic            List cubic presets
  %(prog)s --info diamond          Show diamond preset info
  %(prog)s --search garnet         Search for garnet-related presets
  %(prog)s --json diamond          Output diamond preset as JSON
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    parser.add_argument(
        "--list",
        nargs="?",
        const="all",
        metavar="CATEGORY",
        help="List presets (optionally by crystal system or category)",
    )

    parser.add_argument("--info", type=str, metavar="NAME", help="Show detailed info for a preset")

    parser.add_argument(
        "--search", type=str, metavar="QUERY", help="Search presets by name/mineral/chemistry"
    )

    parser.add_argument("--json", type=str, metavar="NAME", help="Output preset as JSON")

    parser.add_argument("--categories", action="store_true", help="List preset categories")

    parser.add_argument("--count", action="store_true", help="Show total number of presets")

    parser.add_argument(
        "--props",
        type=str,
        metavar="GROUP",
        help="Property group for --info (basic, physical, optical, fga, synthetic, etc.)",
    )

    parser.add_argument(
        "--synthetics",
        nargs="?",
        const="all",
        metavar="METHOD",
        help="List synthetic materials (optionally filter by growth method: flux, cvd, hpht, etc.)",
    )

    parser.add_argument(
        "--simulants",
        nargs="?",
        const="all",
        metavar="TARGET",
        help="List simulant materials (optionally filter by target mineral, e.g., diamond)",
    )

    parser.add_argument(
        "--counterparts",
        type=str,
        metavar="NAME",
        help="List all synthetics and simulants for a natural mineral",
    )

    parser.add_argument(
        "--origin",
        type=str,
        metavar="TYPE",
        choices=["natural", "synthetic", "simulant", "composite"],
        help="Filter --list by origin type",
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

    if parsed_args.synthetics:
        method = None if parsed_args.synthetics == "all" else parsed_args.synthetics
        ids = list_synthetics(method)
        if ids:
            label = f"Synthetic Minerals ({parsed_args.synthetics})" if method else "All Synthetic Minerals"
            print(f"{label} ({len(ids)} total):")
            for fid in ids:
                family = get_family(fid)
                if family:
                    method_str = f" [{family.growth_method}]" if family.growth_method else ""
                    print(f"  {fid:40} - {family.name}{method_str}")
        else:
            print("No synthetic minerals found.")
        return 0

    if parsed_args.simulants:
        target = None if parsed_args.simulants == "all" else parsed_args.simulants
        ids = list_simulants(target)
        if ids:
            label = f"Simulants for {parsed_args.simulants}" if target else "All Simulants"
            print(f"{label} ({len(ids)} total):")
            for fid in ids:
                family = get_family(fid)
                if family:
                    counterpart = f" → {family.natural_counterpart_id}" if family.natural_counterpart_id else ""
                    print(f"  {fid:40} - {family.name}{counterpart}")
        else:
            print("No simulants found.")
        return 0

    if parsed_args.counterparts:
        result = get_counterparts(parsed_args.counterparts)
        print(f"Counterparts for '{parsed_args.counterparts}':")
        if result["synthetics"]:
            print("\n  Synthetics:")
            for fid in result["synthetics"]:
                family = get_family(fid)
                if family:
                    method_str = f" [{family.growth_method}]" if family.growth_method else ""
                    print(f"    {fid:38} - {family.name}{method_str}")
        else:
            print("\n  Synthetics: none")
        if result["simulants"]:
            print("\n  Simulants:")
            for fid in result["simulants"]:
                family = get_family(fid)
                if family:
                    print(f"    {fid:38} - {family.name}")
        else:
            print("\n  Simulants: none")
        return 0

    if parsed_args.list:
        if parsed_args.origin:
            # Filter by origin
            ids = list_by_origin(parsed_args.origin)
            if ids:
                print(f"{parsed_args.origin.title()} Minerals ({len(ids)} total):")
                for fid in ids:
                    family = get_family(fid)
                    if family:
                        print(f"  {fid:40} - {family.name}")
            else:
                print(f"No {parsed_args.origin} minerals found.")
        elif parsed_args.list == "all":
            print(f"All Crystal Presets ({count_presets()} total):")
            for cat in list_preset_categories():
                presets = list_presets(cat)
                if presets:
                    print(f"\n  {cat.title()}:")
                    for name in presets:
                        preset = get_preset(name)
                        if preset:
                            origin_tag = f" [{preset['origin']}]" if preset.get("origin", "natural") != "natural" else ""
                            print(f"    {name:25} - {preset['name']}{origin_tag}")
        else:
            presets = list_presets(parsed_args.list)
            if presets:
                print(f"{parsed_args.list.title()} Presets:")
                for name in presets:
                    preset = get_preset(name)
                    if preset:
                        origin_tag = f" [{preset['origin']}]" if preset.get("origin", "natural") != "natural" else ""
                        print(f"  {name:25} - {preset['name']}{origin_tag}")
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
            if preset.get("localities"):
                print(f"  Localities:  {', '.join(preset['localities'])}")
            if preset.get("forms"):
                print(f"  Forms:       {', '.join(preset['forms'])}")
            if preset.get("sg"):
                print(f"  SG:          {preset['sg']}")
            if preset.get("ri"):
                print(f"  RI:          {preset['ri']}")
            if preset.get("twin_law"):
                print(f"  Twin Law:    {preset['twin_law']}")
            # Synthetic/simulant fields
            origin = preset.get("origin", "natural")
            if origin != "natural":
                print(f"  Origin:      {origin}")
            if preset.get("growth_method"):
                print(f"  Growth:      {preset['growth_method']}")
            if preset.get("natural_counterpart_id"):
                print(f"  Counterpart: {preset['natural_counterpart_id']}")
            # Family-level fields (try loading family data)
            family = get_family(parsed_args.info)
            if family:
                if family.manufacturer:
                    print(f"  Manufacturer: {family.manufacturer}")
                if family.year_first_produced:
                    print(f"  Year First:  {family.year_first_produced}")
                if family.diagnostic_synthetic_features:
                    print(f"  Diagnostics: {family.diagnostic_synthetic_features.strip()}")
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


if __name__ == "__main__":
    sys.exit(main())
