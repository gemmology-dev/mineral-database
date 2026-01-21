"""
Backwards Compatibility Layer.

Provides dict-like CRYSTAL_PRESETS and PRESET_CATEGORIES for
code migrating from the original crystal_presets.py module.
"""

from collections.abc import Iterator
from typing import Any

from .queries import get_preset, list_preset_categories, list_presets


class PresetDict:
    """Dict-like accessor for crystal presets.

    Provides backwards compatibility with code that uses:
        CRYSTAL_PRESETS['diamond']
        CRYSTAL_PRESETS.get('ruby')
        'garnet' in CRYSTAL_PRESETS
        for name in CRYSTAL_PRESETS:
    """

    def __getitem__(self, key: str) -> dict[str, Any]:
        """Get preset by key."""
        preset = get_preset(key)
        if preset is None:
            raise KeyError(key)
        return preset

    def get(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Get preset with default."""
        preset = get_preset(key)
        return preset if preset is not None else default

    def __contains__(self, key: str) -> bool:
        """Check if preset exists."""
        return get_preset(key) is not None

    def __iter__(self) -> Iterator[str]:
        """Iterate over preset names."""
        return iter(list_presets())

    def keys(self) -> list[str]:
        """Get all preset names."""
        return list_presets()

    def values(self) -> list[dict[str, Any]]:
        """Get all preset values."""
        return [preset for name in list_presets() if (preset := get_preset(name)) is not None]

    def items(self) -> list[tuple[str, dict[str, Any]]]:
        """Get all preset (name, value) pairs."""
        return [(name, preset) for name in list_presets() if (preset := get_preset(name)) is not None]

    def __len__(self) -> int:
        """Get number of presets."""
        return len(list_presets())


class CategoryDict:
    """Dict-like accessor for preset categories.

    Provides backwards compatibility with code that uses:
        PRESET_CATEGORIES['cubic']
        for category in PRESET_CATEGORIES:
    """

    def __getitem__(self, key: str) -> list[str]:
        """Get presets in category."""
        presets = list_presets(key)
        if not presets:
            raise KeyError(key)
        return presets

    def get(self, key: str, default: list[str] | None = None) -> list[str] | None:
        """Get category presets with default."""
        presets = list_presets(key)
        return presets if presets else default

    def __contains__(self, key: str) -> bool:
        """Check if category exists."""
        return key.lower() in [c.lower() for c in list_preset_categories()]

    def __iter__(self) -> Iterator[str]:
        """Iterate over category names."""
        return iter(list_preset_categories())

    def keys(self) -> list[str]:
        """Get all category names."""
        return list_preset_categories()

    def __len__(self) -> int:
        """Get number of categories."""
        return len(list_preset_categories())


# Singleton instances for backwards compatibility
CRYSTAL_PRESETS = PresetDict()
PRESET_CATEGORIES = CategoryDict()
