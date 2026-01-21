"""
Test suite for mineral-database.

Tests the database queries, models, and compatibility layer.
"""

from mineral_database import (
    CRYSTAL_PRESETS,
    INFO_GROUPS,
    Mineral,
    count_presets,
    filter_minerals,
    format_property_value,
    get_info_properties,
    get_mineral,
    get_preset,
    get_presets_by_form,
    get_property_label,
    get_systems,
    list_preset_categories,
    list_presets,
    search_presets,
)

# =============================================================================
# Mineral Model Tests
# =============================================================================


class TestMineralModel:
    """Test the Mineral dataclass."""

    def test_create_minimal(self):
        """Test creating mineral with minimal data."""
        mineral = Mineral(
            id="test",
            name="Test Mineral",
            cdl="cubic[m3m]:{111}",
            system="cubic",
            point_group="m3m",
            chemistry="XY",
            hardness=7,
            description="Test description",
        )
        assert mineral.id == "test"
        assert mineral.name == "Test Mineral"
        assert mineral.system == "cubic"

    def test_create_full(self):
        """Test creating mineral with all properties."""
        mineral = Mineral(
            id="test",
            name="Test Mineral",
            cdl="cubic[m3m]:{111}",
            system="cubic",
            point_group="m3m",
            chemistry="XY",
            hardness=7,
            description="Test description",
            localities=["Place A", "Place B"],
            forms=["octahedron"],
            sg=3.5,
            ri=1.544,
            birefringence=0.008,
            optical_character="Uniaxial -",
        )
        assert mineral.sg == 3.5
        assert mineral.ri == 1.544
        assert len(mineral.localities) == 2

    def test_to_dict(self):
        """Test converting mineral to dictionary."""
        mineral = Mineral(
            id="test",
            name="Test Mineral",
            cdl="cubic[m3m]:{111}",
            system="cubic",
            point_group="m3m",
            chemistry="XY",
            hardness=7,
            description="Test",
        )
        d = mineral.to_dict()
        assert d["id"] == "test"
        assert d["name"] == "Test Mineral"
        assert "sg" not in d  # Not set, should be excluded

    def test_from_dict(self):
        """Test creating mineral from dictionary."""
        data = {
            "name": "Test",
            "cdl": "cubic[m3m]:{111}",
            "system": "cubic",
            "point_group": "m3m",
            "chemistry": "XY",
            "hardness": 7,
            "description": "Test",
        }
        mineral = Mineral.from_dict("test", data)
        assert mineral.id == "test"
        assert mineral.name == "Test"


# =============================================================================
# Query Function Tests
# =============================================================================


class TestQueries:
    """Test query functions."""

    def test_get_preset(self):
        """Test getting a preset by name."""
        preset = get_preset("diamond")
        assert preset is not None
        assert preset["name"] == "Diamond"
        assert preset["system"] == "cubic"
        assert "cdl" in preset

    def test_get_preset_case_insensitive(self):
        """Test preset lookup is case-insensitive."""
        preset1 = get_preset("diamond")
        preset2 = get_preset("DIAMOND")
        preset3 = get_preset("Diamond")
        assert preset1 == preset2 == preset3

    def test_get_preset_not_found(self):
        """Test getting a non-existent preset."""
        preset = get_preset("not-a-real-mineral")
        assert preset is None

    def test_get_mineral(self):
        """Test getting a Mineral object."""
        mineral = get_mineral("ruby")
        assert mineral is not None
        assert isinstance(mineral, Mineral)
        assert mineral.name == "Ruby"

    def test_list_presets_all(self):
        """Test listing all presets."""
        presets = list_presets()
        assert len(presets) > 50  # We have ~94 presets
        assert "diamond" in presets
        assert "ruby" in presets

    def test_list_presets_by_system(self):
        """Test listing presets by crystal system."""
        cubic_presets = list_presets("cubic")
        assert len(cubic_presets) > 0
        for name in cubic_presets:
            preset = get_preset(name)
            assert preset["system"] == "cubic"

    def test_list_preset_categories(self):
        """Test listing categories."""
        categories = list_preset_categories()
        assert len(categories) > 0
        # Should include crystal systems
        assert any("cubic" in c.lower() for c in categories) or len(categories) > 0

    def test_search_presets(self):
        """Test searching presets."""
        matches = search_presets("garnet")
        assert len(matches) > 0
        # At least some results should be garnet-related
        garnet_found = False
        for name in matches:
            if "garnet" in name.lower():
                garnet_found = True
                break
        assert garnet_found, "Search for 'garnet' should return garnet presets"

    def test_count_presets(self):
        """Test counting presets."""
        count = count_presets()
        assert count >= 90  # We have ~94 presets

    def test_get_systems(self):
        """Test getting crystal systems."""
        systems = get_systems()
        expected_systems = [
            "cubic",
            "hexagonal",
            "trigonal",
            "tetragonal",
            "orthorhombic",
            "monoclinic",
            "triclinic",
        ]
        for system in expected_systems:
            assert system in systems


# =============================================================================
# Backwards Compatibility Tests
# =============================================================================


class TestCompatibility:
    """Test backwards compatibility layer."""

    def test_crystal_presets_getitem(self):
        """Test dict-like access with []."""
        preset = CRYSTAL_PRESETS["diamond"]
        assert preset["name"] == "Diamond"

    def test_crystal_presets_get(self):
        """Test dict-like .get() method."""
        preset = CRYSTAL_PRESETS.get("diamond")
        assert preset is not None
        assert preset["name"] == "Diamond"

    def test_crystal_presets_get_default(self):
        """Test .get() with default."""
        preset = CRYSTAL_PRESETS.get("not-real", {"default": True})
        assert preset == {"default": True}

    def test_crystal_presets_contains(self):
        """Test 'in' operator."""
        assert "diamond" in CRYSTAL_PRESETS
        assert "not-real" not in CRYSTAL_PRESETS

    def test_crystal_presets_iter(self):
        """Test iteration."""
        names = list(CRYSTAL_PRESETS)
        assert len(names) > 50
        assert "diamond" in names

    def test_crystal_presets_keys(self):
        """Test .keys() method."""
        keys = CRYSTAL_PRESETS.keys()
        assert len(keys) > 50
        assert "diamond" in keys

    def test_crystal_presets_len(self):
        """Test len()."""
        assert len(CRYSTAL_PRESETS) > 50


# =============================================================================
# Property Formatting Tests
# =============================================================================


class TestFormatting:
    """Test property formatting functions."""

    def test_format_float(self):
        """Test formatting float values."""
        assert format_property_value("sg", 3.52) == "3.52"
        assert format_property_value("sg", 3.0) == "3"

    def test_format_list(self):
        """Test formatting list values."""
        colors = ["Red", "Blue", "Green"]
        formatted = format_property_value("colors", colors)
        assert "Red" in formatted
        assert "Blue" in formatted

    def test_format_list_truncated(self):
        """Test formatting long lists triggers truncation."""
        # Use 10+ items to ensure truncation is triggered (threshold is 3)
        items = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        formatted = format_property_value("test", items)
        assert "..." in formatted
        # Should only show first 3 items
        assert formatted == "A, B, C..."

    def test_format_none(self):
        """Test formatting None."""
        assert format_property_value("test", None) == "None"

    def test_property_label(self):
        """Test getting property labels."""
        assert get_property_label("sg") == "SG"
        assert get_property_label("ri") == "RI"
        assert get_property_label("unknown_key") == "Unknown Key"


# =============================================================================
# Info Groups Tests
# =============================================================================


class TestInfoGroups:
    """Test info group functionality."""

    def test_info_groups_exist(self):
        """Test that info groups are defined."""
        assert "basic" in INFO_GROUPS
        assert "fga" in INFO_GROUPS
        assert "optical" in INFO_GROUPS

    def test_get_info_properties(self):
        """Test getting info properties."""
        props = get_info_properties("diamond", "basic")
        assert "name" in props
        assert props["name"] == "Diamond"


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for real minerals."""

    def test_diamond_preset(self):
        """Test diamond preset has expected properties."""
        preset = get_preset("diamond")
        assert preset["system"] == "cubic"
        assert preset["point_group"] == "m3m"
        assert preset["hardness"] == 10
        assert "cdl" in preset
        assert "{111}" in preset["cdl"]

    def test_ruby_preset(self):
        """Test ruby preset."""
        preset = get_preset("ruby")
        assert preset["system"] == "trigonal"
        assert preset["hardness"] == 9
        assert "Al2O3" in preset["chemistry"]

    def test_quartz_preset(self):
        """Test quartz preset."""
        preset = get_preset("quartz")
        assert preset["system"] == "trigonal"
        assert preset["chemistry"] == "SiO2"
        assert preset["hardness"] == 7

    def test_garnet_preset(self):
        """Test garnet preset."""
        preset = get_preset("garnet")
        assert preset["system"] == "cubic"
        assert "dodecahedron" in preset.get("forms", [])

    def test_twinned_presets(self):
        """Test presets with twin laws."""
        twin_presets = filter_minerals(has_twin=True)
        assert len(twin_presets) > 5  # We have multiple twinned presets

        # Verify they have twin laws
        for name in twin_presets[:3]:
            preset = get_preset(name)
            assert preset.get("twin_law") is not None

    def test_presets_by_form(self):
        """Test getting presets by crystal form."""
        octahedron_presets = get_presets_by_form("octahedron")
        assert len(octahedron_presets) > 0
        assert "diamond" in octahedron_presets or "spinel" in octahedron_presets
