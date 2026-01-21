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

__version__ = "1.0.0"
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
    format_property_value,
    get_property_label,
)
from .queries import (
    count_presets,
    filter_minerals,
    get_info_properties,
    get_mineral,
    get_preset,
    get_presets_by_form,
    get_systems,
    list_preset_categories,
    list_presets,
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
    # Data classes
    "Mineral",
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
