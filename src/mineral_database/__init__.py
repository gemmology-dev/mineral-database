"""
Mineral Database - Crystal Presets for Gemmological Visualization.

A comprehensive database of mineral crystal habits with CDL notation,
physical and optical properties for gemmological applications.

Example:
    >>> from mineral_database import get_preset, list_presets
    >>> diamond = get_preset('diamond')
    >>> diamond['cdl']
    'cubic[m3m]:{111}@1.0 + {110}@0.2'
    >>> diamond['system']
    'cubic'

    >>> # List all cubic presets
    >>> cubic_presets = list_presets('cubic')
"""

__version__ = "2.1.2"
__author__ = "Fabian Schuh"
__email__ = "fabian@gemmology.dev"

# Core query functions
# Backwards compatibility: CRYSTAL_PRESETS dict-like access
from .compat import CRYSTAL_PRESETS, PRESET_CATEGORIES

# Database utilities (for advanced use)
from .db import (
    get_connection,
    init_database,
    insert_mineral,
    row_to_mineral,
)

# Data classes
from .models import (
    INFO_GROUPS,
    PROPERTY_LABELS,
    Mineral,
    MineralFamily,
    format_property_value,
    get_property_label,
)
from .queries import (
    classify,
    count_presets,
    ensure_reference_tables,
    filter_minerals,
    find_by_ri,
    find_by_sg,
    get_counterparts,
    get_family,
    get_info_properties,
    get_mineral,
    get_model_gltf,
    get_model_stl,
    get_model_svg,
    get_models_generated_at,
    get_preset,
    get_presets_by_form,
    get_systems,
    list_by_origin,
    list_families_by_group,
    list_heat_treatable,
    list_mineral_groups,
    list_preset_categories,
    list_presets,
    list_shape_factors,
    list_simulants,
    list_synthetics,
    list_thresholds,
    list_volume_factors,
    search_presets,
    set_database_path,
)

__all__ = [
    # Version
    "__version__",
    # Core functions
    "get_preset",
    "get_mineral",
    "list_presets",
    "list_preset_categories",
    "search_presets",
    "filter_minerals",
    "get_presets_by_form",
    "get_info_properties",
    "get_systems",
    "count_presets",
    "set_database_path",
    # Model functions
    "get_model_svg",
    "get_model_stl",
    "get_model_gltf",
    "get_models_generated_at",
    # Calculator functions (RI/SG lookup, shape factors, thresholds)
    "find_by_ri",
    "find_by_sg",
    "list_shape_factors",
    "list_volume_factors",
    "list_thresholds",
    "classify",
    "list_heat_treatable",
    "ensure_reference_tables",
    # Synthetic/simulant query functions
    "list_synthetics",
    "list_simulants",
    "get_counterparts",
    "list_by_origin",
    "list_mineral_groups",
    "list_families_by_group",
    "get_family",
    # Data classes
    "Mineral",
    "MineralFamily",
    "INFO_GROUPS",
    "PROPERTY_LABELS",
    "format_property_value",
    "get_property_label",
    # Database utilities
    "get_connection",
    "init_database",
    "insert_mineral",
    "row_to_mineral",
    # Backwards compatibility
    "CRYSTAL_PRESETS",
    "PRESET_CATEGORIES",
]
