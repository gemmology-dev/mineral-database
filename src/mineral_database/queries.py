"""
Mineral Database Query API.

High-level query functions for the mineral database.
"""

from pathlib import Path
from typing import Any

from .db import (
    classify_value,
    find_minerals_by_ri,
    find_minerals_by_sg,
    get_all_minerals,
    get_category_presets,
    get_connection,
    get_cut_shape_factors,
    get_families_by_growth_method,
    get_families_by_origin,
    get_family_by_id,
    get_mineral_by_id,
    get_mineral_models,
    get_minerals_by_system,
    get_minerals_with_heat_treatment,
    get_simulants_for_natural,
    get_synthetics_for_natural,
    get_thresholds,
    get_volume_shape_factors,
    init_reference_tables,
    search_minerals,
)
from .models import INFO_GROUPS, Mineral, MineralFamily

# Module-level database path (can be overridden)
_db_path: Path | None = None


def set_database_path(path: Path) -> None:
    """Set the database path for all queries.

    Args:
        path: Path to the SQLite database file
    """
    global _db_path
    _db_path = path


def get_preset(name: str) -> dict[str, Any] | None:
    """Get a crystal preset by name.

    This is the primary compatibility function matching the original API.

    Args:
        name: Preset name (case-insensitive)

    Returns:
        Preset dictionary or None if not found
    """
    with get_connection(_db_path) as conn:
        mineral = get_mineral_by_id(conn, name.lower())
        if mineral:
            return mineral.to_dict()
    return None


def get_mineral(name: str) -> Mineral | None:
    """Get a Mineral object by name.

    Args:
        name: Preset name (case-insensitive)

    Returns:
        Mineral object or None if not found
    """
    with get_connection(_db_path) as conn:
        return get_mineral_by_id(conn, name.lower())


def list_presets(category: str | None = None) -> list[str]:
    """List available preset names.

    Args:
        category: Optional crystal system or category to filter by

    Returns:
        List of preset names
    """
    with get_connection(_db_path) as conn:
        if category:
            category = category.lower()
            # Check if it's a category
            presets = get_category_presets(conn, category)
            if presets:
                return presets
            # Check if it's a crystal system
            minerals = get_minerals_by_system(conn, category)
            return [m.id for m in minerals]
        # Return all presets
        minerals = get_all_minerals(conn)
        return sorted([m.id for m in minerals])


def list_preset_categories() -> list[str]:
    """List available preset categories (crystal systems)."""
    with get_connection(_db_path) as conn:
        cursor = conn.execute(
            "SELECT DISTINCT system FROM minerals WHERE system IS NOT NULL ORDER BY system"
        )
        return [row[0] for row in cursor.fetchall()]


def search_presets(query: str) -> list[str]:
    """Search presets by name, mineral name, or chemistry.

    Args:
        query: Search term

    Returns:
        List of matching preset names
    """
    query = query.lower()
    results = []

    with get_connection(_db_path) as conn:
        # Try FTS search first
        try:
            minerals = search_minerals(conn, query)
            results = [m.id for m in minerals]
        except Exception:
            # Fallback to simple LIKE search
            pass

        if not results:
            # Simple fallback search
            all_minerals = get_all_minerals(conn)
            for mineral in all_minerals:
                if (
                    query in mineral.id.lower()
                    or query in mineral.name.lower()
                    or query in mineral.chemistry.lower()
                    or query in mineral.description.lower()
                ):
                    results.append(mineral.id)

    return results


def filter_minerals(
    system: str | None = None,
    min_hardness: float | None = None,
    max_hardness: float | None = None,
    has_twin: bool = False,
) -> list[str]:
    """Filter minerals by various criteria.

    Args:
        system: Filter by crystal system
        min_hardness: Minimum Mohs hardness
        max_hardness: Maximum Mohs hardness
        has_twin: Only return minerals with twin laws

    Returns:
        List of matching preset names
    """
    results = []

    with get_connection(_db_path) as conn:
        if system:
            minerals = get_minerals_by_system(conn, system)
        else:
            minerals = get_all_minerals(conn)

        for mineral in minerals:
            # Check hardness
            try:
                hardness = float(str(mineral.hardness).split("-")[0])
                if min_hardness and hardness < min_hardness:
                    continue
                if max_hardness and hardness > max_hardness:
                    continue
            except (ValueError, TypeError):
                pass

            # Check twin
            if has_twin and not mineral.twin_law:
                continue

            results.append(mineral.id)

    return results


def get_presets_by_form(form_name: str) -> list[str]:
    """Get presets that include a specific crystal form.

    Args:
        form_name: Form name (e.g., 'octahedron', 'cube')

    Returns:
        List of preset names
    """
    form_name = form_name.lower()
    results = []

    with get_connection(_db_path) as conn:
        minerals = get_all_minerals(conn)
        for mineral in minerals:
            if form_name in [f.lower() for f in mineral.forms]:
                results.append(mineral.id)

    return results


def get_info_properties(preset_name: str, group_or_keys: str) -> dict[str, Any]:
    """Get specific properties from a preset for info panel display.

    Args:
        preset_name: Name of the preset
        group_or_keys: Either a group name ('basic', 'full', 'fga', etc.)
                      or comma-separated property keys

    Returns:
        Dictionary of property key -> value for display
    """
    mineral = get_mineral(preset_name)
    if not mineral:
        return {}

    # Determine which keys to extract
    if group_or_keys in INFO_GROUPS:
        keys = INFO_GROUPS[group_or_keys]
    else:
        keys = [k.strip() for k in group_or_keys.split(",")]

    # Extract properties
    result = {}
    mineral_dict = mineral.to_dict()
    for key in keys:
        if key in mineral_dict:
            result[key] = mineral_dict[key]

    return result


def get_systems() -> list[str]:
    """Get list of crystal systems with presets.

    Returns:
        List of crystal system names
    """
    systems = set()
    with get_connection(_db_path) as conn:
        minerals = get_all_minerals(conn)
        for mineral in minerals:
            systems.add(mineral.system)
    return sorted(systems)


def count_presets() -> int:
    """Get total number of presets in database.

    Returns:
        Number of presets
    """
    with get_connection(_db_path) as conn:
        minerals = get_all_minerals(conn)
        return len(minerals)


# Model query functions for pre-generated 3D visualizations


def get_model_svg(mineral_id: str) -> str | None:
    """Get the pre-generated SVG for a mineral.

    Args:
        mineral_id: Mineral preset ID (case-insensitive)

    Returns:
        SVG markup string or None if not generated
    """
    with get_connection(_db_path) as conn:
        models = get_mineral_models(conn, mineral_id)
        value = models.get("model_svg")
        return str(value) if value is not None else None


def get_model_stl(mineral_id: str) -> bytes | None:
    """Get the pre-generated STL binary for a mineral.

    Args:
        mineral_id: Mineral preset ID (case-insensitive)

    Returns:
        Binary STL data or None if not generated
    """
    with get_connection(_db_path) as conn:
        models = get_mineral_models(conn, mineral_id)
        value = models.get("model_stl")
        if isinstance(value, bytes):
            return value
        return None


def get_model_gltf(mineral_id: str) -> dict[str, object] | None:
    """Get the pre-generated glTF for a mineral.

    Args:
        mineral_id: Mineral preset ID (case-insensitive)

    Returns:
        glTF dictionary or None if not generated
    """
    import json

    with get_connection(_db_path) as conn:
        models = get_mineral_models(conn, mineral_id)
        gltf_str = models.get("model_gltf")
        if gltf_str and isinstance(gltf_str, str):
            result: dict[str, object] = json.loads(gltf_str)
            return result
        return None


def get_models_generated_at(mineral_id: str) -> str | None:
    """Get the timestamp when models were generated for a mineral.

    Args:
        mineral_id: Mineral preset ID (case-insensitive)

    Returns:
        ISO timestamp string or None if not generated
    """
    with get_connection(_db_path) as conn:
        models = get_mineral_models(conn, mineral_id)
        value = models.get("models_generated_at")
        return str(value) if value is not None else None


# =============================================================================
# Calculator-optimized query functions
# =============================================================================


def find_by_ri(ri: float, tolerance: float = 0.01) -> list[Mineral]:
    """Find minerals matching an RI value within tolerance.

    Args:
        ri: Refractive index value to match
        tolerance: Acceptable tolerance (default 0.01)

    Returns:
        List of matching Mineral objects, sorted by closest match
    """
    with get_connection(_db_path) as conn:
        return find_minerals_by_ri(conn, ri, tolerance)


def find_by_sg(sg: float, tolerance: float = 0.05) -> list[Mineral]:
    """Find minerals matching an SG value within tolerance.

    Args:
        sg: Specific gravity value to match
        tolerance: Acceptable tolerance (default 0.05)

    Returns:
        List of matching Mineral objects, sorted by closest match
    """
    with get_connection(_db_path) as conn:
        return find_minerals_by_sg(conn, sg, tolerance)


def list_shape_factors() -> list[dict[str, Any]]:
    """Get all cut shape factors for carat estimation.

    Returns:
        List of dicts with id, name, factor, description
    """
    with get_connection(_db_path) as conn:
        return get_cut_shape_factors(conn)


def list_volume_factors() -> list[dict[str, Any]]:
    """Get all volume shape factors for rough estimation.

    Returns:
        List of dicts with id, name, factor
    """
    with get_connection(_db_path) as conn:
        return get_volume_shape_factors(conn)


def list_thresholds(category: str) -> list[dict[str, Any]]:
    """Get classification thresholds for a category.

    Args:
        category: One of 'birefringence', 'dispersion', 'critical_angle'

    Returns:
        List of threshold dicts with level, min_value, max_value, description
    """
    with get_connection(_db_path) as conn:
        return get_thresholds(conn, category)


def classify(category: str, value: float) -> str | None:
    """Classify a value based on gemmological thresholds.

    Args:
        category: One of 'birefringence', 'dispersion', 'critical_angle'
        value: The value to classify

    Returns:
        Classification level (e.g., 'low', 'medium', 'high') or None
    """
    with get_connection(_db_path) as conn:
        return classify_value(conn, category, value)


def list_heat_treatable() -> list[Mineral]:
    """Get minerals with heat treatment temperature data.

    Returns:
        List of Mineral objects with heat treatment info
    """
    with get_connection(_db_path) as conn:
        return get_minerals_with_heat_treatment(conn)


def ensure_reference_tables() -> None:
    """Initialize reference tables if they're empty.

    Call this after database creation to populate shape factors and thresholds.
    """
    with get_connection(_db_path) as conn:
        init_reference_tables(conn)


# =============================================================================
# Synthetic / Simulant Query Functions
# =============================================================================


def list_synthetics(growth_method: str | None = None) -> list[str]:
    """List all synthetic mineral family IDs.

    Args:
        growth_method: Optional filter by growth method
            (flame_fusion, flux, hydrothermal, cvd, hpht, czochralski, etc.)

    Returns:
        List of synthetic family IDs
    """
    with get_connection(_db_path) as conn:
        if growth_method:
            families = get_families_by_growth_method(conn, growth_method)
        else:
            families = get_families_by_origin(conn, "synthetic")
        return [f.id for f in families]


def list_simulants(target: str | None = None) -> list[str]:
    """List all simulant mineral family IDs.

    Args:
        target: Optional natural mineral to find simulants for

    Returns:
        List of simulant family IDs
    """
    with get_connection(_db_path) as conn:
        if target:
            families = get_simulants_for_natural(conn, target)
        else:
            families = get_families_by_origin(conn, "simulant")
        return [f.id for f in families]


def get_counterparts(name: str) -> dict[str, list[str]]:
    """Get all synthetic and simulant counterparts for a natural mineral.

    Args:
        name: Natural mineral family ID

    Returns:
        Dict with 'synthetics' and 'simulants' keys, each containing
        a list of family IDs
    """
    with get_connection(_db_path) as conn:
        synthetics = get_synthetics_for_natural(conn, name)
        simulants = get_simulants_for_natural(conn, name)
        return {
            "synthetics": [f.id for f in synthetics],
            "simulants": [f.id for f in simulants],
        }


def list_by_origin(origin: str) -> list[str]:
    """List all mineral family IDs filtered by origin.

    Args:
        origin: Origin type (natural, synthetic, simulant, composite)

    Returns:
        List of family IDs
    """
    with get_connection(_db_path) as conn:
        families = get_families_by_origin(conn, origin)
        return [f.id for f in families]


def get_family(name: str) -> MineralFamily | None:
    """Get a MineralFamily object by ID.

    Args:
        name: Family ID (case-insensitive)

    Returns:
        MineralFamily object or None
    """
    with get_connection(_db_path) as conn:
        return get_family_by_id(conn, name.lower())
