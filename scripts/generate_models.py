#!/usr/bin/env python3
"""
Generate 3D models for all minerals in the database.

This script generates SVG, STL, and glTF models for each mineral using
the CDL parser, crystal geometry engine, and crystal renderer.
"""

import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from mineral_database.db import (
    get_all_minerals,
    get_connection,
    update_mineral_models,
)


def generate_models_for_mineral(
    mineral_id: str,
    cdl: str,
    verbose: bool = False
) -> tuple[str | None, bytes | None, str | None]:
    """Generate SVG, STL, and glTF models for a mineral.

    Args:
        mineral_id: Mineral preset ID
        cdl: CDL notation string
        verbose: Print progress

    Returns:
        Tuple of (svg_string, stl_bytes, gltf_json_string)
    """
    try:
        from cdl_parser import parse_cdl
        from crystal_geometry import cdl_to_geometry
        from crystal_renderer import generate_cdl_svg
        from crystal_renderer.formats import geometry_to_stl, geometry_to_gltf
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
        print(f"  Error parsing CDL for {mineral_id}: {e}")
        return None, None, None

    # Generate SVG to string buffer
    svg_string = None
    try:
        svg_buffer = io.BytesIO()
        # Import matplotlib with Agg backend
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        import numpy as np
        from crystal_renderer.data import HABIT_COLOURS
        from crystal_renderer.projection import (
            calculate_axis_origin,
            calculate_vertex_visibility,
            calculate_view_bounds,
        )
        from crystal_renderer.rendering import draw_crystallographic_axes

        # Create figure
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_proj_type('ortho')
        elev, azim = 30, -45
        ax.view_init(elev=elev, azim=azim)

        # Get colors based on crystal system
        default_colours = HABIT_COLOURS.get(description.system, HABIT_COLOURS['cubic'])

        # Draw faces
        face_vertices = [[geometry.vertices[i] for i in face] for face in geometry.faces]
        poly = Poly3DCollection(
            face_vertices,
            alpha=0.7,
            facecolor=default_colours['face'],
            edgecolor=default_colours['edge'],
            linewidth=1.5
        )
        ax.add_collection3d(poly)

        # Add vertices with depth-based visibility
        front_mask = calculate_vertex_visibility(geometry.vertices, geometry.faces, elev, azim)

        if np.any(front_mask):
            ax.scatter3D(
                geometry.vertices[front_mask, 0],
                geometry.vertices[front_mask, 1],
                geometry.vertices[front_mask, 2],
                color=default_colours['edge'], s=30, alpha=0.9, zorder=10
            )

        back_mask = ~front_mask
        if np.any(back_mask):
            ax.scatter3D(
                geometry.vertices[back_mask, 0],
                geometry.vertices[back_mask, 1],
                geometry.vertices[back_mask, 2],
                color=default_colours['edge'], s=30, alpha=0.3, zorder=5
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
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_zlabel('')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_zticklabels([])

        # Save to buffer
        plt.tight_layout()
        plt.savefig(svg_buffer, format='svg', dpi=100, bbox_inches='tight')
        plt.close(fig)

        svg_string = svg_buffer.getvalue().decode('utf-8')
        if verbose:
            print(f"  SVG: {len(svg_string)} bytes")
    except Exception as e:
        print(f"  Error generating SVG for {mineral_id}: {e}")

    # Generate STL
    stl_bytes = None
    try:
        stl_bytes = geometry_to_stl(geometry.vertices, geometry.faces, binary=True)
        if verbose:
            print(f"  STL: {len(stl_bytes)} bytes")
    except Exception as e:
        print(f"  Error generating STL for {mineral_id}: {e}")

    # Generate glTF
    gltf_string = None
    try:
        gltf_dict = geometry_to_gltf(geometry.vertices, geometry.faces, name=mineral_id)
        gltf_string = json.dumps(gltf_dict)
        if verbose:
            print(f"  glTF: {len(gltf_string)} bytes")
    except Exception as e:
        print(f"  Error generating glTF for {mineral_id}: {e}")

    return svg_string, stl_bytes, gltf_string


def generate_all_models(db_path: Path, verbose: bool = False) -> tuple[int, int]:
    """Generate models for all minerals in the database.

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

            svg, stl, gltf = generate_models_for_mineral(
                mineral.id, mineral.cdl, verbose=verbose
            )

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
        description='Generate 3D models for minerals in the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data/minerals.db
  %(prog)s data/minerals.db --verbose
  %(prog)s data/minerals.db --mineral diamond
        """
    )

    parser.add_argument('database', type=Path,
                        help='Path to minerals.db file')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-m', '--mineral', type=str,
                        help='Generate model for a specific mineral only')

    args = parser.parse_args()

    if not args.database.exists():
        print(f"Error: Database not found: {args.database}")
        sys.exit(1)

    if args.mineral:
        # Generate model for a single mineral
        with get_connection(args.database) as conn:
            from mineral_database.db import get_mineral_by_id
            mineral = get_mineral_by_id(conn, args.mineral)
            if not mineral:
                print(f"Error: Mineral not found: {args.mineral}")
                sys.exit(1)

            print(f"Generating models for {mineral.id}: {mineral.name}")
            svg, stl, gltf = generate_models_for_mineral(
                mineral.id, mineral.cdl, verbose=True
            )

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
    else:
        # Generate models for all minerals
        success, failure = generate_all_models(args.database, verbose=args.verbose)
        print(f"\nGeneration complete: {success} success, {failure} failures")

        if failure > 0:
            sys.exit(1)


if __name__ == '__main__':
    main()
