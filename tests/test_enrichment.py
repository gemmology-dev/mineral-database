"""
Test suite for v2.1 database enrichment.

Tests fluorescence, diagnostic features, new minerals,
mineral group assignments, and category population.
"""

from mineral_database import get_family
from mineral_database.queries import list_families_by_group

# =============================================================================
# Fluorescence Tests
# =============================================================================


class TestFluorescence:
    """Test fluorescence data on key minerals."""

    def test_diamond_fluorescence(self):
        """Test diamond has fluorescence data."""
        family = get_family("diamond")
        assert family is not None
        assert family.fluorescence is not None
        assert "blue" in family.fluorescence.lower() or "LWUV" in family.fluorescence

    def test_ruby_fluorescence(self):
        """Test ruby has fluorescence data."""
        family = get_family("ruby")
        assert family is not None
        assert family.fluorescence is not None
        assert "red" in family.fluorescence.lower()

    def test_fluorite_fluorescence(self):
        """Test fluorite still has fluorescence data."""
        family = get_family("fluorite")
        assert family is not None
        assert family.fluorescence is not None

    def test_kunzite_fluorescence(self):
        """Test kunzite has fluorescence data."""
        family = get_family("kunzite")
        assert family is not None
        assert family.fluorescence is not None
        assert "phosphorescence" in family.fluorescence.lower()

    def test_sodalite_fluorescence(self):
        """Test sodalite has fluorescence data."""
        family = get_family("sodalite")
        assert family is not None
        assert family.fluorescence is not None
        assert "orange" in family.fluorescence.lower()


# =============================================================================
# Diagnostic Features Tests
# =============================================================================


class TestDiagnosticFeatures:
    """Test diagnostic features on key minerals."""

    def test_diamond_diagnostic(self):
        """Test diamond has diagnostic features."""
        family = get_family("diamond")
        assert family is not None
        assert family.diagnostic_features is not None
        assert "adamantine" in family.diagnostic_features.lower()

    def test_quartz_diagnostic(self):
        """Test quartz has diagnostic features."""
        family = get_family("quartz")
        assert family is not None
        assert family.diagnostic_features is not None

    def test_tourmaline_diagnostic(self):
        """Test tourmaline has diagnostic features."""
        family = get_family("tourmaline")
        assert family is not None
        assert family.diagnostic_features is not None
        assert "triangular" in family.diagnostic_features.lower()


# =============================================================================
# New Mineral Tests (v2.1 additions)
# =============================================================================


class TestNewMinerals:
    """Test all 25 new minerals exist with correct properties."""

    def test_almandine_exists(self):
        """Test almandine garnet exists."""
        family = get_family("almandine")
        assert family is not None
        assert family.crystal_system == "cubic"
        assert family.mineral_group == "Garnet Group"

    def test_pyrope_exists(self):
        """Test pyrope garnet exists."""
        family = get_family("pyrope")
        assert family is not None
        assert family.crystal_system == "cubic"
        assert family.mineral_group == "Garnet Group"

    def test_grossular_exists(self):
        """Test grossular garnet exists."""
        family = get_family("grossular")
        assert family is not None
        assert family.crystal_system == "cubic"

    def test_andradite_exists(self):
        """Test andradite garnet exists."""
        family = get_family("andradite")
        assert family is not None
        assert family.crystal_system == "cubic"

    def test_hessonite_exists(self):
        """Test hessonite exists."""
        family = get_family("hessonite")
        assert family is not None
        assert family.mineral_group == "Garnet Group"

    def test_uvarovite_exists(self):
        """Test uvarovite exists."""
        family = get_family("uvarovite")
        assert family is not None
        assert family.mineral_group == "Garnet Group"

    def test_colour_change_garnet_exists(self):
        """Test colour-change garnet exists."""
        family = get_family("colour-change-garnet")
        assert family is not None
        assert family.mineral_group == "Garnet Group"

    def test_rose_quartz_exists(self):
        """Test rose quartz exists."""
        family = get_family("rose-quartz")
        assert family is not None
        assert family.mineral_group == "Quartz Group"

    def test_smoky_quartz_exists(self):
        """Test smoky quartz exists."""
        family = get_family("smoky-quartz")
        assert family is not None
        assert family.mineral_group == "Quartz Group"

    def test_chalcedony_exists(self):
        """Test chalcedony exists."""
        family = get_family("chalcedony")
        assert family is not None
        assert family.mineral_group == "Quartz Group"

    def test_jadeite_exists(self):
        """Test jadeite exists."""
        family = get_family("jadeite")
        assert family is not None
        assert family.mineral_group == "Pyroxene Group"
        assert family.category == "Inosilicates"

    def test_nephrite_exists(self):
        """Test nephrite exists."""
        family = get_family("nephrite")
        assert family is not None
        assert family.mineral_group == "Amphibole Group"

    def test_elbaite_exists(self):
        """Test elbaite exists."""
        family = get_family("elbaite")
        assert family is not None
        assert family.mineral_group == "Tourmaline Group"

    def test_schorl_exists(self):
        """Test schorl exists."""
        family = get_family("schorl")
        assert family is not None
        assert family.mineral_group == "Tourmaline Group"

    def test_dravite_exists(self):
        """Test dravite exists."""
        family = get_family("dravite")
        assert family is not None
        assert family.mineral_group == "Tourmaline Group"

    def test_padparadscha_exists(self):
        """Test padparadscha sapphire exists."""
        family = get_family("padparadscha")
        assert family is not None
        assert family.mineral_group == "Corundum Group"

    def test_pink_sapphire_exists(self):
        """Test pink sapphire exists."""
        family = get_family("pink-sapphire")
        assert family is not None
        assert family.mineral_group == "Corundum Group"

    def test_spodumene_exists(self):
        """Test spodumene exists."""
        family = get_family("spodumene")
        assert family is not None
        assert family.mineral_group == "Spodumene Group"

    def test_enstatite_exists(self):
        """Test enstatite exists."""
        family = get_family("enstatite")
        assert family is not None
        assert family.mineral_group == "Pyroxene Group"

    def test_augite_exists(self):
        """Test augite exists."""
        family = get_family("augite")
        assert family is not None
        assert family.mineral_group == "Pyroxene Group"

    def test_actinolite_exists(self):
        """Test actinolite exists."""
        family = get_family("actinolite")
        assert family is not None
        assert family.mineral_group == "Amphibole Group"

    def test_tremolite_exists(self):
        """Test tremolite exists."""
        family = get_family("tremolite")
        assert family is not None
        assert family.mineral_group == "Amphibole Group"

    def test_andesine_exists(self):
        """Test andesine exists."""
        family = get_family("andesine")
        assert family is not None
        assert family.mineral_group == "Feldspar Group"

    def test_bytownite_exists(self):
        """Test bytownite exists."""
        family = get_family("bytownite")
        assert family is not None
        assert family.mineral_group == "Feldspar Group"

    def test_sanidine_exists(self):
        """Test sanidine exists."""
        family = get_family("sanidine")
        assert family is not None
        assert family.mineral_group == "Feldspar Group"


# =============================================================================
# Group Count Tests
# =============================================================================


class TestGroupCounts:
    """Test mineral group member counts."""

    def test_garnet_group_count(self):
        """Test garnet group has enough members."""
        families = list_families_by_group("Garnet Group")
        # garnet, demantoid, rhodolite, spessartine, tsavorite,
        # almandine, pyrope, grossular, andradite, hessonite, uvarovite, colour-change-garnet
        assert len(families) >= 11

    def test_feldspar_group_count(self):
        """Test feldspar group has enough members."""
        families = list_families_by_group("Feldspar Group")
        # orthoclase, moonstone, labradorite, sunstone, amazonite, plagioclase-albite,
        # andesine, bytownite, sanidine
        assert len(families) >= 9

    def test_tourmaline_group_count(self):
        """Test tourmaline group has enough members."""
        families = list_families_by_group("Tourmaline Group")
        # tourmaline, elbaite, schorl, dravite
        assert len(families) >= 4

    def test_corundum_group_count(self):
        """Test corundum group has enough members."""
        families = list_families_by_group("Corundum Group")
        # corundum, ruby, sapphire, padparadscha, pink-sapphire
        assert len(families) >= 5

    def test_quartz_group_count(self):
        """Test quartz group has enough members."""
        families = list_families_by_group("Quartz Group")
        # quartz, amethyst, citrine, rose-quartz, smoky-quartz, chalcedony
        assert len(families) >= 6


# =============================================================================
# Category Tests
# =============================================================================


class TestCategories:
    """Test Dana category assignments."""

    def test_diamond_category(self):
        """Test diamond is classified as Native Elements."""
        family = get_family("diamond")
        assert family is not None
        assert family.category == "Native Elements"

    def test_ruby_category(self):
        """Test ruby is classified as Oxides."""
        family = get_family("ruby")
        assert family is not None
        assert family.category == "Oxides"

    def test_quartz_category(self):
        """Test quartz is classified as Tectosilicates."""
        family = get_family("quartz")
        assert family is not None
        assert family.category == "Tectosilicates"

    def test_garnet_category(self):
        """Test garnet is classified as Nesosilicates."""
        family = get_family("garnet")
        assert family is not None
        assert family.category == "Nesosilicates"

    def test_calcite_category(self):
        """Test calcite is classified as Carbonates."""
        family = get_family("calcite")
        assert family is not None
        assert family.category == "Carbonates"

    def test_fluorite_category(self):
        """Test fluorite is classified as Halides."""
        family = get_family("fluorite")
        assert family is not None
        assert family.category == "Halides"

    def test_opal_category(self):
        """Test opal is classified as Mineraloid."""
        family = get_family("opal")
        assert family is not None
        assert family.category == "Mineraloid"

    def test_all_families_have_category(self):
        """Test that all natural mineral families have a category."""
        from mineral_database.queries import list_by_origin

        natural_ids = list_by_origin("natural")
        missing = []
        for fid in natural_ids:
            family = get_family(fid)
            if family and not family.category:
                missing.append(fid)
        assert len(missing) == 0, f"Families missing category: {missing}"
