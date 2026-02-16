"""
Mineral Database Models.

Data classes representing minerals and their properties.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Mineral:
    """A mineral preset with crystallographic and gemmological properties.

    Attributes:
        id: Unique preset identifier (e.g., 'diamond', 'ruby')
        name: Display name (e.g., 'Diamond', 'Ruby')
        cdl: Crystal Description Language notation
        system: Crystal system (cubic, hexagonal, etc.)
        point_group: Hermann-Mauguin point group symbol
        chemistry: Chemical formula
        hardness: Mohs hardness (can be range like '5-7')
        description: Crystal habit description
        localities: List of notable localities
        forms: List of crystal forms present

        # Optional gemmological properties
        sg: Specific gravity (may be range string)
        ri: Refractive index (may be range string)
        birefringence: Birefringence value or None for isotropic
        optical_character: Optical character (Uniaxial +/-, Biaxial +/-, Isotropic)
        dispersion: Dispersion coefficient
        lustre: Surface lustre
        cleavage: Cleavage description
        fracture: Fracture type
        pleochroism: Pleochroism description
        colors: List of possible colors
        treatments: List of known treatments
        inclusions: List of diagnostic inclusions

        # Optional special properties
        twin_law: Associated twin law name
        phenomenon: Optical phenomenon (e.g., 'Adularescence')
        note: Additional notes
    """

    # Required fields
    id: str
    name: str
    cdl: str
    system: str
    point_group: str
    chemistry: str
    hardness: int | float | str
    description: str

    # Common optional fields
    localities: list[str] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)

    # Gemmological properties
    sg: float | str | None = None
    ri: float | str | None = None
    birefringence: float | None = None
    optical_character: str | None = None
    dispersion: float | None = None
    lustre: str | None = None
    cleavage: str | None = None
    fracture: str | None = None
    pleochroism: str | None = None
    # Structured pleochroism data for dichroscope lookup
    pleochroism_strength: str | None = None  # none|weak|moderate|strong|very_strong
    pleochroism_color1: str | None = None
    pleochroism_color2: str | None = None
    pleochroism_color3: str | None = None  # For trichroic gems
    pleochroism_notes: str | None = None
    colors: list[str] = field(default_factory=list)
    treatments: list[str] = field(default_factory=list)
    inclusions: list[str] = field(default_factory=list)

    # Special properties
    twin_law: str | None = None
    phenomenon: str | None = None
    note: str | None = None

    # Calculator-optimized numeric fields (parsed from RI/SG ranges)
    ri_min: float | None = None
    ri_max: float | None = None
    sg_min: float | None = None
    sg_max: float | None = None

    # Heat treatment temperatures (Celsius, from GIA/GEM-A data)
    heat_treatment_temp_min: float | None = None
    heat_treatment_temp_max: float | None = None

    # Synthetic/simulant classification
    origin: str = "natural"  # natural|synthetic|simulant|composite
    growth_method: str | None = None
    natural_counterpart_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "cdl": self.cdl,
            "system": self.system,
            "point_group": self.point_group,
            "chemistry": self.chemistry,
            "hardness": self.hardness,
            "description": self.description,
            "origin": self.origin,
        }

        # Add non-empty lists
        if self.localities:
            result["localities"] = self.localities
        if self.forms:
            result["forms"] = self.forms
        if self.colors:
            result["colors"] = self.colors
        if self.treatments:
            result["treatments"] = self.treatments
        if self.inclusions:
            result["inclusions"] = self.inclusions

        # Add optional fields if set
        optional = [
            "sg",
            "ri",
            "birefringence",
            "optical_character",
            "dispersion",
            "lustre",
            "cleavage",
            "fracture",
            "pleochroism",
            "pleochroism_strength",
            "pleochroism_color1",
            "pleochroism_color2",
            "pleochroism_color3",
            "pleochroism_notes",
            "twin_law",
            "phenomenon",
            "note",
            "ri_min",
            "ri_max",
            "sg_min",
            "sg_max",
            "heat_treatment_temp_min",
            "heat_treatment_temp_max",
            "growth_method",
            "natural_counterpart_id",
        ]
        for key in optional:
            value = getattr(self, key)
            if value is not None:
                result[key] = value

        return result

    @classmethod
    def from_dict(cls, id: str, data: dict[str, Any]) -> "Mineral":
        """Create Mineral from dictionary.

        Args:
            id: The preset identifier
            data: Dictionary of mineral properties

        Returns:
            Mineral instance
        """
        return cls(
            id=id,
            name=data.get("name", id.replace("-", " ").title()),
            cdl=data["cdl"],
            system=data.get("system", "cubic"),
            point_group=data.get("point_group", "m3m"),
            chemistry=data.get("chemistry", ""),
            hardness=data.get("hardness", 0),
            description=data.get("description", ""),
            localities=data.get("localities", []),
            forms=data.get("forms", []),
            sg=data.get("sg"),
            ri=data.get("ri"),
            birefringence=data.get("birefringence"),
            optical_character=data.get("optical_character"),
            dispersion=data.get("dispersion"),
            lustre=data.get("lustre"),
            cleavage=data.get("cleavage"),
            fracture=data.get("fracture"),
            pleochroism=data.get("pleochroism"),
            pleochroism_strength=data.get("pleochroism_strength"),
            pleochroism_color1=data.get("pleochroism_color1"),
            pleochroism_color2=data.get("pleochroism_color2"),
            pleochroism_color3=data.get("pleochroism_color3"),
            pleochroism_notes=data.get("pleochroism_notes"),
            colors=data.get("colors", []),
            treatments=data.get("treatments", []),
            inclusions=data.get("inclusions", []),
            twin_law=data.get("twin_law"),
            phenomenon=data.get("phenomenon"),
            note=data.get("note"),
            ri_min=data.get("ri_min"),
            ri_max=data.get("ri_max"),
            sg_min=data.get("sg_min"),
            sg_max=data.get("sg_max"),
            heat_treatment_temp_min=data.get("heat_treatment_temp_min"),
            heat_treatment_temp_max=data.get("heat_treatment_temp_max"),
            origin=data.get("origin", "natural"),
            growth_method=data.get("growth_method"),
            natural_counterpart_id=data.get("natural_counterpart_id"),
        )


@dataclass
class MineralFamily:
    """A mineral family with shared gemmological properties.

    Families group multiple crystal expressions (e.g., fluorite-cube,
    fluorite-octahedron) that share identical gemmological properties
    but have different crystal morphologies.

    Attributes:
        id: Unique family identifier (e.g., 'fluorite', 'quartz')
        name: Display name (e.g., 'Fluorite', 'Quartz')
        crystal_system: Crystal system (cubic, hexagonal, etc.)
        point_group: Default Hermann-Mauguin point group symbol
        chemistry: Chemical formula
        category: Mineral category (silicates, halides, etc.)

        # Physical properties (shared across all expressions)
        hardness_min: Minimum Mohs hardness
        hardness_max: Maximum Mohs hardness
        sg_min: Minimum specific gravity
        sg_max: Maximum specific gravity

        # Optical properties
        ri_min: Minimum refractive index
        ri_max: Maximum refractive index
        birefringence: Birefringence value
        dispersion: Dispersion coefficient
        optical_character: Optical character (Uniaxial +/-, Biaxial +/-, Isotropic)
        pleochroism: Pleochroism description

        # Arrays
        localities: Notable localities
        colors: Possible colors
        treatments: Known treatments
        inclusions: Diagnostic inclusions
        forms: Crystal forms present in this family
    """

    # Required fields
    id: str
    name: str
    crystal_system: str

    # Common optional fields
    point_group: str | None = None
    chemistry: str | None = None
    category: str | None = None
    mineral_group: str | None = None

    # Physical properties
    hardness_min: float | None = None
    hardness_max: float | None = None
    sg_min: float | None = None
    sg_max: float | None = None

    # Optical properties
    ri_min: float | None = None
    ri_max: float | None = None
    birefringence: float | None = None
    dispersion: float | None = None
    optical_character: str | None = None
    pleochroism: str | None = None
    pleochroism_strength: str | None = None
    pleochroism_color1: str | None = None
    pleochroism_color2: str | None = None
    pleochroism_color3: str | None = None
    pleochroism_notes: str | None = None

    # Physical characteristics
    lustre: str | None = None
    cleavage: str | None = None
    fracture: str | None = None

    # Educational content
    description: str | None = None
    notes: str | None = None
    diagnostic_features: str | None = None
    common_inclusions: str | None = None

    # Arrays
    localities: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    treatments: list[str] = field(default_factory=list)
    inclusions: list[str] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)

    # Heat treatment
    heat_treatment_temp_min: float | None = None
    heat_treatment_temp_max: float | None = None

    # Special properties
    twin_law: str | None = None
    phenomenon: str | None = None
    fluorescence: str | None = None

    # Synthetic/simulant classification
    origin: str = "natural"  # natural|synthetic|simulant|composite
    growth_method: str | None = None
    natural_counterpart_id: str | None = None
    target_minerals: list[str] = field(default_factory=list)
    manufacturer: str | None = None
    year_first_produced: int | None = None
    diagnostic_synthetic_features: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "crystal_system": self.crystal_system,
            "origin": self.origin,
        }

        # Add optional scalar fields
        optional = [
            "point_group",
            "chemistry",
            "category",
            "mineral_group",
            "hardness_min",
            "hardness_max",
            "sg_min",
            "sg_max",
            "ri_min",
            "ri_max",
            "birefringence",
            "dispersion",
            "optical_character",
            "pleochroism",
            "pleochroism_strength",
            "pleochroism_color1",
            "pleochroism_color2",
            "pleochroism_color3",
            "pleochroism_notes",
            "lustre",
            "cleavage",
            "fracture",
            "description",
            "notes",
            "diagnostic_features",
            "common_inclusions",
            "heat_treatment_temp_min",
            "heat_treatment_temp_max",
            "twin_law",
            "phenomenon",
            "fluorescence",
            "growth_method",
            "natural_counterpart_id",
            "manufacturer",
            "year_first_produced",
            "diagnostic_synthetic_features",
        ]
        for key in optional:
            value = getattr(self, key)
            if value is not None:
                result[key] = value

        # Add non-empty lists
        for key in ["localities", "colors", "treatments", "inclusions", "forms", "target_minerals"]:
            value = getattr(self, key)
            if value:
                result[key] = value

        return result

    @classmethod
    def from_dict(cls, id: str, data: dict[str, Any]) -> "MineralFamily":
        """Create MineralFamily from dictionary.

        Args:
            id: The family identifier
            data: Dictionary of family properties

        Returns:
            MineralFamily instance
        """
        # Parse hardness range
        hardness = data.get("hardness")
        hardness_min, hardness_max = None, None
        if hardness is not None:
            if isinstance(hardness, (int, float)):
                hardness_min = hardness_max = float(hardness)
            elif isinstance(hardness, str) and "-" in hardness:
                parts = hardness.split("-")
                if len(parts) == 2:
                    try:
                        hardness_min = float(parts[0])
                        hardness_max = float(parts[1])
                    except ValueError:
                        pass

        # Parse SG range
        sg = data.get("sg")
        sg_min, sg_max = data.get("sg_min"), data.get("sg_max")
        if sg_min is None and sg is not None:
            if isinstance(sg, (int, float)):
                sg_min = sg_max = float(sg)
            elif isinstance(sg, str) and "-" in sg:
                parts = sg.split("-")
                if len(parts) == 2:
                    try:
                        sg_min = float(parts[0])
                        sg_max = float(parts[1])
                    except ValueError:
                        pass
            elif isinstance(sg, str):
                try:
                    sg_min = sg_max = float(sg)
                except ValueError:
                    pass

        # Parse RI range
        ri = data.get("ri")
        ri_min, ri_max = data.get("ri_min"), data.get("ri_max")
        if ri_min is None and ri is not None:
            if isinstance(ri, (int, float)):
                ri_min = ri_max = float(ri)
            elif isinstance(ri, str) and "-" in ri:
                parts = ri.split("-")
                if len(parts) == 2:
                    try:
                        ri_min = float(parts[0])
                        ri_max = float(parts[1])
                    except ValueError:
                        pass
            elif isinstance(ri, str):
                try:
                    ri_min = ri_max = float(ri)
                except ValueError:
                    pass

        return cls(
            id=id,
            name=data.get("name", id.replace("-", " ").title()),
            crystal_system=data.get("crystal_system", data.get("system", "cubic")),
            point_group=data.get("point_group"),
            chemistry=data.get("chemistry"),
            category=data.get("category"),
            mineral_group=data.get("mineral_group"),
            hardness_min=data.get("hardness_min", hardness_min),
            hardness_max=data.get("hardness_max", hardness_max),
            sg_min=sg_min,
            sg_max=sg_max,
            ri_min=ri_min,
            ri_max=ri_max,
            birefringence=data.get("birefringence"),
            dispersion=data.get("dispersion"),
            optical_character=data.get("optical_character"),
            pleochroism=data.get("pleochroism"),
            pleochroism_strength=data.get("pleochroism_strength"),
            pleochroism_color1=data.get("pleochroism_color1"),
            pleochroism_color2=data.get("pleochroism_color2"),
            pleochroism_color3=data.get("pleochroism_color3"),
            pleochroism_notes=data.get("pleochroism_notes"),
            lustre=data.get("lustre"),
            cleavage=data.get("cleavage"),
            fracture=data.get("fracture"),
            description=data.get("description"),
            notes=data.get("notes", data.get("note")),
            diagnostic_features=data.get("diagnostic_features"),
            common_inclusions=data.get("common_inclusions"),
            localities=data.get("localities", []),
            colors=data.get("colors", []),
            treatments=data.get("treatments", []),
            inclusions=data.get("inclusions", []),
            forms=data.get("forms", []),
            heat_treatment_temp_min=data.get("heat_treatment_temp_min"),
            heat_treatment_temp_max=data.get("heat_treatment_temp_max"),
            twin_law=data.get("twin_law"),
            phenomenon=data.get("phenomenon"),
            fluorescence=data.get("fluorescence"),
            origin=data.get("origin", "natural"),
            growth_method=data.get("growth_method"),
            natural_counterpart_id=data.get("natural_counterpart_id"),
            target_minerals=data.get("target_minerals", []),
            manufacturer=data.get("manufacturer"),
            year_first_produced=data.get("year_first_produced"),
            diagnostic_synthetic_features=data.get("diagnostic_synthetic_features"),
        )


@dataclass
class MineralExpression:
    """A crystal morphology expression within a mineral family.

    Expressions represent different crystal habits or forms of the same
    mineral species (e.g., fluorite cube vs fluorite octahedron).

    Attributes:
        id: Unique expression identifier (e.g., 'fluorite-octahedron')
        family_id: Parent family ID (e.g., 'fluorite')
        name: Display name (e.g., 'Octahedron')
        slug: URL-safe slug (e.g., 'octahedron')
        cdl: Crystal Description Language expression
        point_group: Override point group (if different from family)
        form_description: Description of this crystal form
        habit: Crystal habit description
        forms: List of crystal forms in this expression
        is_primary: Whether this is the primary/default form
        sort_order: Sort order within family
    """

    # Required fields
    id: str
    family_id: str
    name: str
    slug: str
    cdl: str

    # Crystal morphology
    point_group: str | None = None
    form_description: str | None = None
    habit: str | None = None
    forms: list[str] | None = None

    # Visual assets (paths)
    svg_path: str | None = None
    gltf_path: str | None = None
    stl_path: str | None = None
    thumbnail_path: str | None = None

    # Inline model data
    model_svg: str | None = None
    model_stl: bytes | None = None
    model_gltf: str | None = None
    models_generated_at: str | None = None

    # Metadata
    is_primary: bool = False
    sort_order: int = 0
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {
            "id": self.id,
            "family_id": self.family_id,
            "name": self.name,
            "slug": self.slug,
            "cdl": self.cdl,
        }

        # Add optional fields
        optional = [
            "point_group",
            "form_description",
            "habit",
            "svg_path",
            "gltf_path",
            "stl_path",
            "thumbnail_path",
            "model_svg",
            "model_gltf",
            "models_generated_at",
            "note",
        ]
        for key in optional:
            value = getattr(self, key)
            if value is not None:
                result[key] = value

        # Add forms list
        if self.forms:
            result["forms"] = self.forms

        # Add boolean/int fields
        result["is_primary"] = self.is_primary
        if self.sort_order != 0:
            result["sort_order"] = self.sort_order

        return result

    @classmethod
    def from_dict(
        cls, family_id: str, expression_data: dict[str, Any], expression_id: str | None = None
    ) -> "MineralExpression":
        """Create MineralExpression from dictionary.

        Args:
            family_id: Parent family ID
            expression_data: Dictionary of expression properties
            expression_id: Optional override for expression ID

        Returns:
            MineralExpression instance
        """
        slug = expression_data.get("slug", "default")
        if expression_id is None:
            expression_id = f"{family_id}-{slug}" if slug != "default" else family_id

        return cls(
            id=expression_id,
            family_id=family_id,
            name=expression_data.get("name", slug.replace("-", " ").title()),
            slug=slug,
            cdl=expression_data.get("cdl") or "",
            point_group=expression_data.get("point_group"),
            form_description=expression_data.get(
                "form_description", expression_data.get("description")
            ),
            habit=expression_data.get("habit"),
            forms=expression_data.get("forms"),
            svg_path=expression_data.get("svg_path"),
            gltf_path=expression_data.get("gltf_path"),
            stl_path=expression_data.get("stl_path"),
            thumbnail_path=expression_data.get("thumbnail_path"),
            is_primary=expression_data.get("is_primary", False),
            sort_order=expression_data.get("sort_order", 0),
            note=expression_data.get("note"),
        )


# Info panel property groups
INFO_GROUPS = {
    "basic": ["name", "chemistry", "system", "hardness"],
    "physical": ["sg", "cleavage", "fracture", "lustre"],
    "optical": ["ri", "birefringence", "optical_character", "dispersion", "pleochroism"],
    "gemological": ["colors", "treatments", "localities", "inclusions"],
    "crystal": ["point_group", "forms", "description"],
    "full": [
        "name",
        "chemistry",
        "system",
        "hardness",
        "sg",
        "ri",
        "optical_character",
        "cleavage",
    ],
    "fga": [
        "name",
        "ri",
        "sg",
        "hardness",
        "optical_character",
        "birefringence",
        "cleavage",
        "pleochroism",
    ],
    "classification": ["category", "mineral_group", "origin"],
    "synthetic": [
        "name",
        "origin",
        "growth_method",
        "natural_counterpart_id",
        "manufacturer",
        "year_first_produced",
        "diagnostic_synthetic_features",
    ],
}

# Property display labels
PROPERTY_LABELS = {
    "name": "Name",
    "chemistry": "Formula",
    "system": "System",
    "hardness": "Hardness",
    "sg": "SG",
    "ri": "RI",
    "birefringence": "Biref.",
    "optical_character": "Optical",
    "dispersion": "Dispersion",
    "pleochroism": "Pleochroism",
    "cleavage": "Cleavage",
    "fracture": "Fracture",
    "lustre": "Lustre",
    "colors": "Colors",
    "treatments": "Treatments",
    "localities": "Localities",
    "inclusions": "Inclusions",
    "point_group": "Point Group",
    "forms": "Forms",
    "description": "Habit",
    "ri_min": "RI Min",
    "ri_max": "RI Max",
    "sg_min": "SG Min",
    "sg_max": "SG Max",
    "heat_treatment_temp_min": "Heat Treat Min (°C)",
    "heat_treatment_temp_max": "Heat Treat Max (°C)",
    "origin": "Origin",
    "mineral_group": "Mineral Group",
    "growth_method": "Growth Method",
    "natural_counterpart_id": "Natural Counterpart",
    "target_minerals": "Target Minerals",
    "manufacturer": "Manufacturer",
    "year_first_produced": "Year First Produced",
    "diagnostic_synthetic_features": "Diagnostic Features (Synthetic)",
}


def get_property_label(key: str) -> str:
    """Get display label for a property key."""
    return PROPERTY_LABELS.get(key, key.replace("_", " ").title())


def format_property_value(key: str, value: Any) -> str:
    """Format a property value for display.

    Args:
        key: Property key
        value: Property value

    Returns:
        Formatted string for display
    """
    if value is None:
        return "None"
    if isinstance(value, list):
        if len(value) <= 3:
            return ", ".join(str(v) for v in value)
        return ", ".join(str(v) for v in value[:3]) + "..."
    if isinstance(value, tuple):
        return "-".join(str(v) for v in value)
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)
