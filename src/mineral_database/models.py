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
    colors: list[str] = field(default_factory=list)
    treatments: list[str] = field(default_factory=list)
    inclusions: list[str] = field(default_factory=list)

    # Special properties
    twin_law: str | None = None
    phenomenon: str | None = None
    note: str | None = None

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
            "twin_law",
            "phenomenon",
            "note",
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
            colors=data.get("colors", []),
            treatments=data.get("treatments", []),
            inclusions=data.get("inclusions", []),
            twin_law=data.get("twin_law"),
            phenomenon=data.get("phenomenon"),
            note=data.get("note"),
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
