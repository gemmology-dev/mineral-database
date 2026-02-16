#!/usr/bin/env python3
"""
Generate 3D models for all minerals and expressions in the database.

This script generates SVG, STL, and glTF models for each mineral/expression using
the CDL parser, crystal geometry engine, and crystal renderer.
"""

import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mineral_database.db import (
    get_all_expressions,
    get_all_minerals,
    get_connection,
    get_expression_by_id,
    get_mineral_by_id,
    update_expression_models,
    update_mineral_models,
)


def generate_models_for_cdl(
    item_id: str, cdl: str, system: str = "cubic", verbose: bool = False
) -> tuple[str | None, bytes | None, str | None]:
    """Generate SVG, STL, and glTF models from a CDL expression.

    Args:
        item_id: Item ID (for error messages and glTF naming)
        cdl: CDL notation string
        system: Crystal system (for color selection)
        verbose: Print progress

    Returns:
        Tuple of (svg_string, stl_bytes, gltf_json_string)
    """
    try:
        from cdl_parser import parse_cdl
        from crystal_geometry import cdl_to_geometry
        from crystal_renderer.formats import geometry_to_gltf, geometry_to_stl
    except ImportError as e:
        print(f"Error: Required packages not installed: {e}")
        print("Install with: pip install cdl-parser crystal-geometry crystal-renderer")
        return None, None, None

    if verbose:
        print(f"  Parsing CDL: {cdl}")

    # Parse CDL and generate geometry
    try:
        description = parse_cdl(cdl)
        geometry = cdl_to_geometry(description)
    except Exception as e:
        print(f"  Error parsing CDL for {item_id}: {e}")
        return None, None, None

    # Generate SVG to string buffer
    svg_string = None
    try:
        svg_buffer = io.BytesIO()
        # Import matplotlib with Agg backend
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        from crystal_renderer.data import HABIT_COLOURS
        from crystal_renderer.projection import (
            calculate_axis_origin,
            calculate_vertex_visibility,
            calculate_view_bounds,
        )
        from crystal_renderer.rendering import draw_crystallographic_axes
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        # Create figure
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection="3d")
        ax.set_proj_type("ortho")
        elev, azim = 30, -45
        ax.view_init(elev=elev, azim=azim)

        # Get colors based on crystal system
        default_colours = HABIT_COLOURS.get(description.system, HABIT_COLOURS["cubic"])

        # Draw faces
        face_vertices = [[geometry.vertices[i] for i in face] for face in geometry.faces]
        poly = Poly3DCollection(
            face_vertices,
            alpha=0.7,
            facecolor=default_colours["face"],
            edgecolor=default_colours["edge"],
            linewidth=1.5,
        )
        ax.add_collection3d(poly)

        # Add vertices with depth-based visibility
        front_mask = calculate_vertex_visibility(geometry.vertices, geometry.faces, elev, azim)

        if np.any(front_mask):
            ax.scatter3D(
                geometry.vertices[front_mask, 0],
                geometry.vertices[front_mask, 1],
                geometry.vertices[front_mask, 2],
                color=default_colours["edge"],
                s=30,
                alpha=0.9,
                zorder=10,
            )

        back_mask = ~front_mask
        if np.any(back_mask):
            ax.scatter3D(
                geometry.vertices[back_mask, 0],
                geometry.vertices[back_mask, 1],
                geometry.vertices[back_mask, 2],
                color=default_colours["edge"],
                s=30,
                alpha=0.3,
                zorder=5,
            )

        # Draw axes
        axis_origin, axis_length = calculate_axis_origin(geometry.vertices, elev, azim)
        draw_crystallographic_axes(ax, axis_origin, axis_length)

        # Calculate view bounds including axes
        center, half_extent = calculate_view_bounds(geometry.vertices, axis_origin, axis_length)

        # Set axis limits
        ax.set_xlim([center[0] - half_extent, center[0] + half_extent])
        ax.set_ylim([center[1] - half_extent, center[1] + half_extent])
        ax.set_zlim([center[2] - half_extent, center[2] + half_extent])

        # Clean up axes
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_zlabel("")
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_zticklabels([])

        # Save to buffer
        plt.tight_layout()
        plt.savefig(svg_buffer, format="svg", dpi=100, bbox_inches="tight")
        plt.close(fig)

        svg_string = svg_buffer.getvalue().decode("utf-8")
        if verbose:
            print(f"  SVG: {len(svg_string)} bytes")
    except Exception as e:
        print(f"  Error generating SVG for {item_id}: {e}")

    # Generate STL
    stl_bytes = None
    try:
        stl_bytes = geometry_to_stl(geometry.vertices, geometry.faces, binary=True)
        if verbose:
            print(f"  STL: {len(stl_bytes)} bytes")
    except Exception as e:
        print(f"  Error generating STL for {item_id}: {e}")

    # Generate glTF
    gltf_string = None
    try:
        gltf_dict = geometry_to_gltf(geometry.vertices, geometry.faces, name=item_id)
        gltf_string = json.dumps(gltf_dict)
        if verbose:
            print(f"  glTF: {len(gltf_string)} bytes")
    except Exception as e:
        print(f"  Error generating glTF for {item_id}: {e}")

    return svg_string, stl_bytes, gltf_string


# Legacy function for backwards compatibility
def generate_models_for_mineral(
    mineral_id: str, cdl: str, verbose: bool = False
) -> tuple[str | None, bytes | None, str | None]:
    """Generate SVG, STL, and glTF models for a mineral.

    Args:
        mineral_id: Mineral preset ID
        cdl: CDL notation string
        verbose: Print progress

    Returns:
        Tuple of (svg_string, stl_bytes, gltf_json_string)
    """
    return generate_models_for_cdl(mineral_id, cdl, verbose=verbose)


def generate_all_expression_models(
    db_path: Path,
    output_dir: Path | None = None,
    verbose: bool = False,
) -> tuple[int, int]:
    """Generate models for all expressions in the database.

    Args:
        db_path: Path to the database file
        output_dir: Optional directory to output static SVG files
        verbose: Print progress

    Returns:
        Tuple of (success_count, failure_count)
    """
    success = 0
    failure = 0
    family_fallbacks: dict[str, str] = {}  # family_id -> primary expression SVG

    with get_connection(db_path) as conn:
        expressions = get_all_expressions(conn)
        total = len(expressions)

        print(f"Generating models for {total} expressions...")

        for i, expr in enumerate(expressions, 1):
            print(f"[{i}/{total}] {expr.id}: {expr.name} (family: {expr.family_id})")

            svg, stl, gltf = generate_models_for_cdl(expr.id, expr.cdl, verbose=verbose)

            if svg or stl or gltf:
                timestamp = datetime.now(timezone.utc).isoformat()
                update_expression_models(
                    conn,
                    expr.id,
                    svg=svg,
                    stl=stl,
                    gltf=gltf,
                    generated_at=timestamp,
                )

                # Optionally write static SVG file
                if output_dir and svg:
                    svg_path = output_dir / f"{expr.id}.svg"
                    svg_path.write_text(svg)
                    if verbose:
                        print(f"  Wrote {svg_path}")

                    # Track primary expressions for family fallback files
                    if expr.is_primary and expr.id != expr.family_id:
                        family_fallbacks[expr.family_id] = svg

                success += 1
            else:
                failure += 1

        conn.commit()

    # Write family fallback SVG files (copy primary expression SVG to family ID)
    if output_dir and family_fallbacks:
        print(f"\nCreating {len(family_fallbacks)} family fallback SVG files...")
        for family_id, svg_content in family_fallbacks.items():
            family_svg_path = output_dir / f"{family_id}.svg"
            family_svg_path.write_text(svg_content)
            if verbose:
                print(f"  Wrote {family_svg_path} (fallback)")

    return success, failure


def generate_all_models(db_path: Path, verbose: bool = False) -> tuple[int, int]:
    """Generate models for all minerals in the database (legacy table).

    Args:
        db_path: Path to the database file
        verbose: Print progress

    Returns:
        Tuple of (success_count, failure_count)
    """
    success = 0
    failure = 0

    with get_connection(db_path) as conn:
        minerals = get_all_minerals(conn)
        total = len(minerals)

        print(f"Generating models for {total} minerals...")

        for i, mineral in enumerate(minerals, 1):
            print(f"[{i}/{total}] {mineral.id}: {mineral.name}")

            svg, stl, gltf = generate_models_for_mineral(mineral.id, mineral.cdl, verbose=verbose)

            if svg or stl or gltf:
                timestamp = datetime.now(timezone.utc).isoformat()
                update_mineral_models(
                    conn,
                    mineral.id,
                    svg=svg,
                    stl=stl,
                    gltf=gltf,
                    generated_at=timestamp,
                )
                success += 1
            else:
                failure += 1

        conn.commit()

    return success, failure


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D models for minerals/expressions in the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate models for all expressions (recommended)
  %(prog)s data/minerals.db --expressions

  # Generate models for all expressions and output static SVGs
  %(prog)s data/minerals.db --expressions --output-dir /path/to/crystals/

  # Generate models for a specific expression
  %(prog)s data/minerals.db --expression fluorite-octahedron

  # Legacy: Generate models for all minerals (old table)
  %(prog)s data/minerals.db --minerals

  # Legacy: Generate model for a specific mineral
  %(prog)s data/minerals.db --mineral diamond
        """,
    )

    parser.add_argument("database", type=Path, help="Path to minerals.db file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--expressions",
        action="store_true",
        help="Generate models for all expressions (new family/expression tables)",
    )
    mode_group.add_argument(
        "--minerals",
        action="store_true",
        help="Generate models for all minerals (legacy table)",
    )
    mode_group.add_argument(
        "--expression",
        type=str,
        metavar="ID",
        help="Generate model for a specific expression",
    )
    mode_group.add_argument(
        "-m",
        "--mineral",
        type=str,
        metavar="ID",
        help="Generate model for a specific mineral (legacy)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for static SVG files (expressions mode only)",
    )

    args = parser.parse_args()

    if not args.database.exists():
        print(f"Error: Database not found: {args.database}")
        sys.exit(1)

    # Default to expressions mode if nothing specified
    if not any([args.expressions, args.minerals, args.expression, args.mineral]):
        args.expressions = True

    if args.expression:
        # Generate model for a single expression
        with get_connection(args.database) as conn:
            expression = get_expression_by_id(conn, args.expression)
            if not expression:
                print(f"Error: Expression not found: {args.expression}")
                sys.exit(1)

            print(f"Generating models for {expression.id}: {expression.name}")
            svg, stl, gltf = generate_models_for_cdl(expression.id, expression.cdl, verbose=True)

            if svg or stl or gltf:
                timestamp = datetime.now(timezone.utc).isoformat()
                update_expression_models(
                    conn,
                    expression.id,
                    svg=svg,
                    stl=stl,
                    gltf=gltf,
                    generated_at=timestamp,
                )
                conn.commit()

                # Optionally write static SVG
                if args.output_dir and svg:
                    args.output_dir.mkdir(parents=True, exist_ok=True)
                    svg_path = args.output_dir / f"{expression.id}.svg"
                    svg_path.write_text(svg)
                    print(f"Wrote {svg_path}")

                print(f"Successfully generated models for {expression.id}")
            else:
                print(f"Failed to generate any models for {expression.id}")
                sys.exit(1)

    elif args.mineral:
        # Generate model for a single mineral (legacy)
        with get_connection(args.database) as conn:
            mineral = get_mineral_by_id(conn, args.mineral)
            if not mineral:
                print(f"Error: Mineral not found: {args.mineral}")
                sys.exit(1)

            print(f"Generating models for {mineral.id}: {mineral.name}")
            svg, stl, gltf = generate_models_for_mineral(mineral.id, mineral.cdl, verbose=True)

            if svg or stl or gltf:
                timestamp = datetime.now(timezone.utc).isoformat()
                update_mineral_models(
                    conn,
                    mineral.id,
                    svg=svg,
                    stl=stl,
                    gltf=gltf,
                    generated_at=timestamp,
                )
                conn.commit()
                print(f"Successfully generated models for {mineral.id}")
            else:
                print(f"Failed to generate any models for {mineral.id}")
                sys.exit(1)

    elif args.expressions:
        # Generate models for all expressions
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Static SVGs will be written to: {args.output_dir}")

        success, failure = generate_all_expression_models(
            args.database,
            output_dir=args.output_dir,
            verbose=args.verbose,
        )
        print(f"\nGeneration complete: {success} success, {failure} failures")

        if failure > 0:
            sys.exit(1)

    else:
        # Generate models for all minerals (legacy)
        success, failure = generate_all_models(args.database, verbose=args.verbose)
        print(f"\nGeneration complete: {success} success, {failure} failures")

        if failure > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
