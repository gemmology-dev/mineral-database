"""
Mineral Database Connection.

SQLite database access layer for the mineral database.
"""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from .models import Mineral, MineralExpression, MineralFamily

# Path to the compiled database
_DB_PATH = Path(__file__).parent / "data" / "minerals.db"


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection.

    Args:
        db_path: Optional path to database file. Uses default if not provided.

    Yields:
        SQLite connection
    """
    path = db_path or _DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database(db_path: Path | None = None) -> None:
    """Initialize the database schema.

    Args:
        db_path: Optional path to database file.
    """
    schema_sql = """
    -- Minerals table
    CREATE TABLE IF NOT EXISTS minerals (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        cdl TEXT NOT NULL,
        system TEXT NOT NULL,
        point_group TEXT,
        chemistry TEXT,
        hardness TEXT,
        description TEXT,
        sg TEXT,
        ri TEXT,
        birefringence REAL,
        optical_character TEXT,
        dispersion REAL,
        lustre TEXT,
        cleavage TEXT,
        fracture TEXT,
        pleochroism TEXT,
        -- Structured pleochroism data for dichroscope lookup
        pleochroism_strength TEXT,    -- none|weak|moderate|strong|very_strong
        pleochroism_color1 TEXT,
        pleochroism_color2 TEXT,
        pleochroism_color3 TEXT,      -- For trichroic gems
        pleochroism_notes TEXT,
        twin_law TEXT,
        phenomenon TEXT,
        note TEXT,
        localities_json TEXT,
        forms_json TEXT,
        colors_json TEXT,
        treatments_json TEXT,
        inclusions_json TEXT,
        -- Pre-generated 3D model data
        model_svg TEXT,           -- SVG markup (~2-10 KB)
        model_stl BLOB,           -- Binary STL (~4-8 KB)
        model_gltf TEXT,          -- glTF JSON (~6-10 KB)
        models_generated_at TEXT, -- ISO timestamp
        -- Calculator-optimized numeric columns (split from TEXT)
        ri_min REAL,              -- Minimum RI (e.g., 1.762)
        ri_max REAL,              -- Maximum RI (e.g., 1.770)
        sg_min REAL,              -- Minimum SG (e.g., 3.99)
        sg_max REAL,              -- Maximum SG (e.g., 4.01)
        -- Heat treatment temperatures (Celsius)
        heat_treatment_temp_min REAL,  -- Min treatment temp (e.g., 800)
        heat_treatment_temp_max REAL,  -- Max treatment temp (e.g., 1900)
        -- Synthetic/simulant classification
        origin TEXT NOT NULL DEFAULT 'natural',
        growth_method TEXT,
        natural_counterpart_id TEXT
    );

    -- Categories table for preset groupings
    CREATE TABLE IF NOT EXISTS categories (
        name TEXT PRIMARY KEY,
        presets_json TEXT NOT NULL
    );

    -- Full-text search index
    CREATE VIRTUAL TABLE IF NOT EXISTS minerals_fts USING fts5(
        id, name, chemistry, description, localities, origin, growth_method,
        content='minerals',
        content_rowid='rowid'
    );

    -- Triggers to keep FTS index in sync
    CREATE TRIGGER IF NOT EXISTS minerals_ai AFTER INSERT ON minerals BEGIN
        INSERT INTO minerals_fts(rowid, id, name, chemistry, description, localities, origin, growth_method)
        VALUES (new.rowid, new.id, new.name, new.chemistry, new.description, new.localities_json, new.origin, new.growth_method);
    END;

    CREATE TRIGGER IF NOT EXISTS minerals_ad AFTER DELETE ON minerals BEGIN
        INSERT INTO minerals_fts(minerals_fts, rowid, id, name, chemistry, description, localities, origin, growth_method)
        VALUES ('delete', old.rowid, old.id, old.name, old.chemistry, old.description, old.localities_json, old.origin, old.growth_method);
    END;

    CREATE TRIGGER IF NOT EXISTS minerals_au AFTER UPDATE ON minerals BEGIN
        INSERT INTO minerals_fts(minerals_fts, rowid, id, name, chemistry, description, localities, origin, growth_method)
        VALUES ('delete', old.rowid, old.id, old.name, old.chemistry, old.description, old.localities_json, old.origin, old.growth_method);
        INSERT INTO minerals_fts(rowid, id, name, chemistry, description, localities, origin, growth_method)
        VALUES (new.rowid, new.id, new.name, new.chemistry, new.description, new.localities_json, new.origin, new.growth_method);
    END;

    -- Cut shape factors for carat estimation
    CREATE TABLE IF NOT EXISTS cut_shape_factors (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        factor REAL NOT NULL,
        description TEXT
    );

    -- Volume shape factors for rough estimation
    CREATE TABLE IF NOT EXISTS volume_shape_factors (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        factor REAL NOT NULL
    );

    -- Gemmological classification thresholds
    CREATE TABLE IF NOT EXISTS gemmological_thresholds (
        category TEXT NOT NULL,
        level TEXT NOT NULL,
        min_value REAL,
        max_value REAL,
        description TEXT,
        PRIMARY KEY (category, level)
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_minerals_system ON minerals(system);
    CREATE INDEX IF NOT EXISTS idx_minerals_twin_law ON minerals(twin_law);
    CREATE INDEX IF NOT EXISTS idx_minerals_ri_min ON minerals(ri_min);
    CREATE INDEX IF NOT EXISTS idx_minerals_ri_max ON minerals(ri_max);
    CREATE INDEX IF NOT EXISTS idx_minerals_sg_min ON minerals(sg_min);
    CREATE INDEX IF NOT EXISTS idx_minerals_sg_max ON minerals(sg_max);

    -- =========================================================================
    -- Family + Expression Tables (normalized structure)
    -- =========================================================================

    -- Core family table (shared gemmological properties)
    CREATE TABLE IF NOT EXISTS mineral_families (
        id TEXT PRIMARY KEY,           -- 'fluorite', 'quartz', 'diamond'
        name TEXT NOT NULL,            -- 'Fluorite', 'Quartz', 'Diamond'
        crystal_system TEXT NOT NULL,  -- 'cubic', 'trigonal', etc.
        point_group TEXT,              -- Hermann-Mauguin notation
        chemistry TEXT,
        category TEXT,

        -- Physical properties (shared across all expressions)
        hardness_min REAL,
        hardness_max REAL,
        sg_min REAL,
        sg_max REAL,

        -- Optical properties
        ri_min REAL,
        ri_max REAL,
        birefringence REAL,
        dispersion REAL,
        optical_character TEXT,
        pleochroism TEXT,
        pleochroism_strength TEXT,     -- none|weak|moderate|strong|very_strong
        pleochroism_color1 TEXT,
        pleochroism_color2 TEXT,
        pleochroism_color3 TEXT,
        pleochroism_notes TEXT,

        -- Physical characteristics
        lustre TEXT,
        cleavage TEXT,
        fracture TEXT,

        -- Educational content
        description TEXT,
        notes TEXT,
        diagnostic_features TEXT,
        common_inclusions TEXT,

        -- JSON arrays
        localities_json TEXT,          -- JSON array of localities
        colors_json TEXT,              -- JSON array of colors
        treatments_json TEXT,          -- JSON array of treatments
        inclusions_json TEXT,          -- JSON array of inclusions
        forms_json TEXT,               -- JSON array of crystal forms

        -- Heat treatment temperatures
        heat_treatment_temp_min REAL,
        heat_treatment_temp_max REAL,

        -- Special properties
        twin_law TEXT,
        phenomenon TEXT,
        fluorescence TEXT,

        -- Synthetic/simulant classification
        origin TEXT NOT NULL DEFAULT 'natural',    -- natural|synthetic|simulant|composite
        growth_method TEXT,                        -- flame_fusion|flux|hydrothermal|cvd|hpht|czochralski|skull_melting|gilson
        natural_counterpart_id TEXT,               -- FK to natural family this imitates/replicates
        target_minerals_json TEXT,                 -- JSON array of family IDs (for simulants targeting multiple gems)
        manufacturer TEXT,                         -- e.g. 'Chatham', 'Kashan', 'Element Six'
        year_first_produced INTEGER,               -- e.g. 1902
        diagnostic_synthetic_features TEXT,         -- key identification features

        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- Expression table (CDL variants linked to families)
    CREATE TABLE IF NOT EXISTS mineral_expressions (
        id TEXT PRIMARY KEY,           -- 'fluorite-octahedron'
        family_id TEXT NOT NULL REFERENCES mineral_families(id),
        name TEXT NOT NULL,            -- 'Octahedron' (display name)
        slug TEXT NOT NULL,            -- 'octahedron' (URL-safe)

        -- Crystal morphology
        cdl TEXT NOT NULL,             -- CDL expression
        point_group TEXT,              -- Override if different from family
        form_description TEXT,         -- 'Regular octahedron bounded by {111} faces'
        habit TEXT,                    -- 'octahedral', 'cubic', 'tabular'
        forms_json TEXT,               -- JSON array of forms for this expression

        -- Visual assets
        svg_path TEXT,
        gltf_path TEXT,
        stl_path TEXT,
        thumbnail_path TEXT,

        -- Pre-generated model data (inline)
        model_svg TEXT,
        model_stl BLOB,
        model_gltf TEXT,
        models_generated_at TEXT,

        -- Metadata
        is_primary BOOLEAN DEFAULT FALSE,  -- Primary form for family display
        sort_order INTEGER DEFAULT 0,
        note TEXT,                     -- Expression-specific notes

        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- Indexes for family/expression tables
    CREATE INDEX IF NOT EXISTS idx_expressions_family ON mineral_expressions(family_id);
    CREATE INDEX IF NOT EXISTS idx_families_system ON mineral_families(crystal_system);
    CREATE INDEX IF NOT EXISTS idx_expressions_primary ON mineral_expressions(is_primary);
    CREATE INDEX IF NOT EXISTS idx_families_ri_min ON mineral_families(ri_min);
    CREATE INDEX IF NOT EXISTS idx_families_ri_max ON mineral_families(ri_max);
    CREATE INDEX IF NOT EXISTS idx_families_sg_min ON mineral_families(sg_min);
    CREATE INDEX IF NOT EXISTS idx_families_sg_max ON mineral_families(sg_max);
    CREATE INDEX IF NOT EXISTS idx_families_origin ON mineral_families(origin);
    CREATE INDEX IF NOT EXISTS idx_families_growth_method ON mineral_families(growth_method);

    -- Backwards compatibility view (maintains existing API)
    -- This view makes family+expression data look like the flat minerals table
    CREATE VIEW IF NOT EXISTS minerals_view AS
    SELECT
        e.id,
        f.name || CASE WHEN e.slug != 'default' AND e.slug != f.id THEN ' (' || e.name || ')' ELSE '' END AS name,
        e.cdl,
        f.crystal_system AS system,
        COALESCE(e.point_group, f.point_group) AS point_group,
        f.chemistry,
        CASE
            WHEN f.hardness_min = f.hardness_max THEN CAST(f.hardness_min AS TEXT)
            ELSE CAST(f.hardness_min AS TEXT) || '-' || CAST(f.hardness_max AS TEXT)
        END AS hardness,
        COALESCE(e.form_description, f.description) AS description,
        CASE
            WHEN f.sg_min = f.sg_max THEN CAST(f.sg_min AS TEXT)
            ELSE CAST(f.sg_min AS TEXT) || '-' || CAST(f.sg_max AS TEXT)
        END AS sg,
        CASE
            WHEN f.ri_min = f.ri_max THEN CAST(f.ri_min AS TEXT)
            ELSE CAST(f.ri_min AS TEXT) || '-' || CAST(f.ri_max AS TEXT)
        END AS ri,
        f.birefringence,
        f.optical_character,
        f.dispersion,
        f.lustre,
        f.cleavage,
        f.fracture,
        f.pleochroism,
        f.pleochroism_strength,
        f.pleochroism_color1,
        f.pleochroism_color2,
        f.pleochroism_color3,
        f.pleochroism_notes,
        f.twin_law,
        f.phenomenon,
        COALESCE(e.note, f.notes) AS note,
        f.localities_json,
        COALESCE(e.forms_json, f.forms_json) AS forms_json,
        f.colors_json,
        f.treatments_json,
        f.inclusions_json,
        e.model_svg,
        e.model_stl,
        e.model_gltf,
        e.models_generated_at,
        f.ri_min,
        f.ri_max,
        f.sg_min,
        f.sg_max,
        f.heat_treatment_temp_min,
        f.heat_treatment_temp_max,
        e.family_id,
        f.origin,
        f.growth_method,
        f.natural_counterpart_id,
        f.diagnostic_synthetic_features
    FROM mineral_expressions e
    JOIN mineral_families f ON e.family_id = f.id;
    """

    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def _parse_range(value: float | str | None) -> tuple[float | None, float | None]:
    """Parse a range string like '1.762-1.770' into (min, max) floats.

    Args:
        value: Single number, range string, or None

    Returns:
        Tuple of (min_value, max_value). For single values, both are the same.
    """
    if value is None:
        return None, None

    if isinstance(value, (int, float)):
        return float(value), float(value)

    value_str = str(value).strip()

    # Skip metallic/opaque or clearly non-numeric
    if not value_str or value_str.lower() in ("metallic", "opaque", "n/a", "none"):
        return None, None

    # Handle range format: "1.762-1.770"
    if "-" in value_str:
        parts = value_str.split("-")
        # Handle negative numbers (e.g., "-3m" point group shouldn't be parsed)
        if len(parts) == 2 and parts[0]:
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                return None, None
        # Could be just a negative number
        try:
            val = float(value_str)
            return val, val
        except ValueError:
            return None, None

    # Single value
    try:
        val = float(value_str)
        return val, val
    except ValueError:
        return None, None


def insert_mineral(conn: sqlite3.Connection, mineral: Mineral) -> None:
    """Insert a mineral into the database.

    Args:
        conn: Database connection
        mineral: Mineral to insert
    """
    # Parse RI and SG ranges
    ri_min, ri_max = _parse_range(mineral.ri)
    sg_min, sg_max = _parse_range(mineral.sg)

    sql = """
    INSERT OR REPLACE INTO minerals (
        id, name, cdl, system, point_group, chemistry, hardness, description,
        sg, ri, birefringence, optical_character, dispersion, lustre, cleavage,
        fracture, pleochroism,
        pleochroism_strength, pleochroism_color1, pleochroism_color2,
        pleochroism_color3, pleochroism_notes,
        twin_law, phenomenon, note,
        localities_json, forms_json, colors_json, treatments_json, inclusions_json,
        ri_min, ri_max, sg_min, sg_max,
        heat_treatment_temp_min, heat_treatment_temp_max,
        origin, growth_method, natural_counterpart_id
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?,
        ?, ?, ?
    )
    """

    conn.execute(
        sql,
        (
            mineral.id,
            mineral.name,
            mineral.cdl,
            mineral.system,
            mineral.point_group,
            mineral.chemistry,
            str(mineral.hardness),
            mineral.description,
            str(mineral.sg) if mineral.sg else None,
            str(mineral.ri) if mineral.ri else None,
            mineral.birefringence,
            mineral.optical_character,
            mineral.dispersion,
            mineral.lustre,
            mineral.cleavage,
            mineral.fracture,
            mineral.pleochroism,
            mineral.pleochroism_strength,
            mineral.pleochroism_color1,
            mineral.pleochroism_color2,
            mineral.pleochroism_color3,
            mineral.pleochroism_notes,
            mineral.twin_law,
            mineral.phenomenon,
            mineral.note,
            json.dumps(mineral.localities) if mineral.localities else "[]",
            json.dumps(mineral.forms) if mineral.forms else "[]",
            json.dumps(mineral.colors) if mineral.colors else "[]",
            json.dumps(mineral.treatments) if mineral.treatments else "[]",
            json.dumps(mineral.inclusions) if mineral.inclusions else "[]",
            ri_min,
            ri_max,
            sg_min,
            sg_max,
            mineral.heat_treatment_temp_min,
            mineral.heat_treatment_temp_max,
            mineral.origin,
            mineral.growth_method,
            mineral.natural_counterpart_id,
        ),
    )


def row_to_mineral(row: sqlite3.Row) -> Mineral:
    """Convert a database row to a Mineral object.

    Args:
        row: Database row

    Returns:
        Mineral instance
    """
    # Parse hardness (may be int, float, or range string)
    hardness_str = row["hardness"]
    try:
        if "." in str(hardness_str):
            hardness = float(hardness_str)
        else:
            hardness = int(hardness_str)
    except (ValueError, TypeError):
        hardness = hardness_str

    # Parse SG
    sg_str = row["sg"]
    if sg_str:
        try:
            sg: float | str | None = float(sg_str)
        except ValueError:
            sg = sg_str
    else:
        sg = None

    # Parse RI
    ri_str = row["ri"]
    if ri_str:
        try:
            ri: float | str | None = float(ri_str)
        except ValueError:
            ri = ri_str
    else:
        ri = None

    # Extract new numeric columns (may not exist in older databases)
    ri_min = row["ri_min"] if "ri_min" in row.keys() else None
    ri_max = row["ri_max"] if "ri_max" in row.keys() else None
    sg_min = row["sg_min"] if "sg_min" in row.keys() else None
    sg_max = row["sg_max"] if "sg_max" in row.keys() else None
    heat_min = row["heat_treatment_temp_min"] if "heat_treatment_temp_min" in row.keys() else None
    heat_max = row["heat_treatment_temp_max"] if "heat_treatment_temp_max" in row.keys() else None

    # Extract pleochroism columns (may not exist in older databases)
    pleochroism_strength = (
        row["pleochroism_strength"] if "pleochroism_strength" in row.keys() else None
    )
    pleochroism_color1 = row["pleochroism_color1"] if "pleochroism_color1" in row.keys() else None
    pleochroism_color2 = row["pleochroism_color2"] if "pleochroism_color2" in row.keys() else None
    pleochroism_color3 = row["pleochroism_color3"] if "pleochroism_color3" in row.keys() else None
    pleochroism_notes = row["pleochroism_notes"] if "pleochroism_notes" in row.keys() else None

    # Extract synthetic/simulant columns (may not exist in older databases)
    origin = row["origin"] if "origin" in row.keys() else "natural"
    growth_method = row["growth_method"] if "growth_method" in row.keys() else None
    natural_counterpart_id = (
        row["natural_counterpart_id"] if "natural_counterpart_id" in row.keys() else None
    )

    return Mineral(
        id=row["id"],
        name=row["name"],
        cdl=row["cdl"],
        system=row["system"],
        point_group=row["point_group"],
        chemistry=row["chemistry"],
        hardness=hardness,
        description=row["description"] or "",
        localities=json.loads(row["localities_json"] or "[]"),
        forms=json.loads(row["forms_json"] or "[]"),
        sg=sg,
        ri=ri,
        birefringence=row["birefringence"],
        optical_character=row["optical_character"],
        dispersion=row["dispersion"],
        lustre=row["lustre"],
        cleavage=row["cleavage"],
        fracture=row["fracture"],
        pleochroism=row["pleochroism"],
        pleochroism_strength=pleochroism_strength,
        pleochroism_color1=pleochroism_color1,
        pleochroism_color2=pleochroism_color2,
        pleochroism_color3=pleochroism_color3,
        pleochroism_notes=pleochroism_notes,
        colors=json.loads(row["colors_json"] or "[]"),
        treatments=json.loads(row["treatments_json"] or "[]"),
        inclusions=json.loads(row["inclusions_json"] or "[]"),
        twin_law=row["twin_law"],
        phenomenon=row["phenomenon"],
        note=row["note"],
        ri_min=ri_min,
        ri_max=ri_max,
        sg_min=sg_min,
        sg_max=sg_max,
        heat_treatment_temp_min=heat_min,
        heat_treatment_temp_max=heat_max,
        origin=origin,
        growth_method=growth_method,
        natural_counterpart_id=natural_counterpart_id,
    )


def get_mineral_by_id(conn: sqlite3.Connection, mineral_id: str) -> Mineral | None:
    """Get a mineral by its ID.

    Args:
        conn: Database connection
        mineral_id: Mineral ID

    Returns:
        Mineral or None if not found
    """
    cursor = conn.execute("SELECT * FROM minerals WHERE id = ?", (mineral_id.lower(),))
    row = cursor.fetchone()
    if row:
        return row_to_mineral(row)
    return None


def get_all_minerals(conn: sqlite3.Connection) -> list[Mineral]:
    """Get all minerals from the database.

    Args:
        conn: Database connection

    Returns:
        List of all minerals
    """
    cursor = conn.execute("SELECT * FROM minerals ORDER BY id")
    return [row_to_mineral(row) for row in cursor.fetchall()]


def get_minerals_by_system(conn: sqlite3.Connection, system: str) -> list[Mineral]:
    """Get minerals by crystal system.

    Args:
        conn: Database connection
        system: Crystal system name

    Returns:
        List of minerals in that system
    """
    cursor = conn.execute("SELECT * FROM minerals WHERE system = ? ORDER BY id", (system.lower(),))
    return [row_to_mineral(row) for row in cursor.fetchall()]


def search_minerals(conn: sqlite3.Connection, query: str) -> list[Mineral]:
    """Search minerals using full-text search.

    Args:
        conn: Database connection
        query: Search query

    Returns:
        List of matching minerals
    """
    # Use FTS5 search
    cursor = conn.execute(
        """
        SELECT m.* FROM minerals m
        JOIN minerals_fts fts ON m.id = fts.id
        WHERE minerals_fts MATCH ?
        ORDER BY rank
    """,
        (query,),
    )
    return [row_to_mineral(row) for row in cursor.fetchall()]


def insert_category(conn: sqlite3.Connection, name: str, presets: list[str]) -> None:
    """Insert or update a category.

    Args:
        conn: Database connection
        name: Category name
        presets: List of preset IDs in this category
    """
    conn.execute(
        "INSERT OR REPLACE INTO categories (name, presets_json) VALUES (?, ?)",
        (name, json.dumps(presets)),
    )


def update_mineral_models(
    conn: sqlite3.Connection,
    mineral_id: str,
    svg: str | None = None,
    stl: bytes | None = None,
    gltf: str | None = None,
    generated_at: str | None = None,
) -> None:
    """Update the 3D model data for a mineral.

    Args:
        conn: Database connection
        mineral_id: Mineral ID
        svg: SVG markup string
        stl: Binary STL data
        gltf: glTF JSON string
        generated_at: ISO timestamp when models were generated
    """
    conn.execute(
        """
        UPDATE minerals SET
            model_svg = ?,
            model_stl = ?,
            model_gltf = ?,
            models_generated_at = ?
        WHERE id = ?
        """,
        (svg, stl, gltf, generated_at, mineral_id.lower()),
    )


def get_mineral_models(conn: sqlite3.Connection, mineral_id: str) -> dict[str, str | bytes | None]:
    """Get the 3D model data for a mineral.

    Args:
        conn: Database connection
        mineral_id: Mineral ID

    Returns:
        Dictionary with model_svg, model_stl, model_gltf, models_generated_at
    """
    cursor = conn.execute(
        """
        SELECT model_svg, model_stl, model_gltf, models_generated_at
        FROM minerals WHERE id = ?
        """,
        (mineral_id.lower(),),
    )
    row = cursor.fetchone()
    if row:
        return {
            "model_svg": row["model_svg"],
            "model_stl": row["model_stl"],
            "model_gltf": row["model_gltf"],
            "models_generated_at": row["models_generated_at"],
        }
    return {
        "model_svg": None,
        "model_stl": None,
        "model_gltf": None,
        "models_generated_at": None,
    }


def get_category_presets(conn: sqlite3.Connection, name: str) -> list[str]:
    """Get preset IDs for a category.

    Args:
        conn: Database connection
        name: Category name

    Returns:
        List of preset IDs
    """
    cursor = conn.execute("SELECT presets_json FROM categories WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return list(json.loads(row["presets_json"]))
    return []


def get_all_categories(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Get all categories and their presets.

    Args:
        conn: Database connection

    Returns:
        Dict mapping category name to list of preset IDs
    """
    cursor = conn.execute("SELECT name, presets_json FROM categories")
    return {row["name"]: json.loads(row["presets_json"]) for row in cursor.fetchall()}


# =============================================================================
# Reference Table Population
# =============================================================================

# Cut shape factors for carat weight estimation (gem trade standards)
CUT_SHAPE_FACTORS = [
    ("round-brilliant", "Round Brilliant", 0.0061, "Most common cut, 57-58 facets"),
    ("oval", "Oval", 0.0062, "Elongated round, good finger coverage"),
    ("pear", "Pear", 0.0059, "Teardrop shape, pointed end"),
    ("marquise", "Marquise", 0.0058, "Boat-shaped, elongated with points"),
    ("emerald-cut", "Emerald Cut", 0.0083, "Step cut rectangle, open table"),
    ("cushion", "Cushion", 0.0080, "Rounded square/rectangle, vintage style"),
    ("princess", "Princess", 0.0083, "Square brilliant cut"),
    ("heart", "Heart", 0.0059, "Romantic shape, requires skill to cut"),
    ("radiant", "Radiant", 0.0081, "Brilliant-cut corners on emerald shape"),
]

# Volume shape factors for rough estimation
VOLUME_SHAPE_FACTORS = [
    ("sphere", "Sphere", 0.5236),
    ("cube", "Cube", 1.0),
    ("irregular", "Irregular", 0.65),
]

# Gemmological classification thresholds
GEMMOLOGICAL_THRESHOLDS = [
    # Birefringence thresholds (GIA/GEM-A classification)
    ("birefringence", "none", None, 0.0001, "Isotropic (singly refractive)"),
    ("birefringence", "low", 0.0001, 0.01, "Weak doubling, hard to see"),
    ("birefringence", "medium", 0.01, 0.02, "Moderate doubling visible under loupe"),
    ("birefringence", "high", 0.02, 0.05, "Strong doubling, visible with naked eye (e.g., zircon)"),
    ("birefringence", "very_high", 0.05, None, "Extreme doubling (e.g., calcite)"),
    # Dispersion thresholds (fire classification)
    ("dispersion", "low", None, 0.020, "Minimal fire, subtle"),
    ("dispersion", "moderate", 0.020, 0.030, "Noticeable fire under good lighting"),
    ("dispersion", "high", 0.030, 0.040, "Strong fire, attractive play of colors"),
    ("dispersion", "very_high", 0.040, None, "Exceptional fire (e.g., diamond, demantoid)"),
    # Critical angle thresholds (brilliance/light return)
    ("critical_angle", "very_small", None, 25.0, "Excellent light return (e.g., diamond at 24.4°)"),
    ("critical_angle", "small", 25.0, 35.0, "Good light return (e.g., zircon, demantoid)"),
    ("critical_angle", "moderate", 35.0, 45.0, "Average light return (e.g., corundum, spinel)"),
    ("critical_angle", "large", 45.0, None, "Lower light return (e.g., quartz, feldspar)"),
]


def init_reference_tables(conn: sqlite3.Connection) -> None:
    """Populate reference tables with standard gemmological data.

    Args:
        conn: Database connection
    """
    # Insert cut shape factors
    conn.executemany(
        "INSERT OR REPLACE INTO cut_shape_factors (id, name, factor, description) VALUES (?, ?, ?, ?)",
        CUT_SHAPE_FACTORS,
    )

    # Insert volume shape factors
    conn.executemany(
        "INSERT OR REPLACE INTO volume_shape_factors (id, name, factor) VALUES (?, ?, ?)",
        VOLUME_SHAPE_FACTORS,
    )

    # Insert gemmological thresholds
    conn.executemany(
        "INSERT OR REPLACE INTO gemmological_thresholds (category, level, min_value, max_value, description) VALUES (?, ?, ?, ?, ?)",
        GEMMOLOGICAL_THRESHOLDS,
    )

    conn.commit()


def get_cut_shape_factors(conn: sqlite3.Connection) -> list[dict[str, str | float | None]]:
    """Get all cut shape factors.

    Returns:
        List of dicts with id, name, factor, description
    """
    cursor = conn.execute(
        "SELECT id, name, factor, description FROM cut_shape_factors ORDER BY name"
    )
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "factor": row["factor"],
            "description": row["description"],
        }
        for row in cursor.fetchall()
    ]


def get_volume_shape_factors(conn: sqlite3.Connection) -> list[dict[str, str | float]]:
    """Get all volume shape factors.

    Returns:
        List of dicts with id, name, factor
    """
    cursor = conn.execute("SELECT id, name, factor FROM volume_shape_factors ORDER BY name")
    return [
        {"id": row["id"], "name": row["name"], "factor": row["factor"]} for row in cursor.fetchall()
    ]


def get_thresholds(conn: sqlite3.Connection, category: str) -> list[dict[str, str | float | None]]:
    """Get thresholds for a specific category.

    Args:
        category: Threshold category (birefringence, dispersion, critical_angle)

    Returns:
        List of threshold dicts ordered by min_value
    """
    cursor = conn.execute(
        """
        SELECT level, min_value, max_value, description
        FROM gemmological_thresholds
        WHERE category = ?
        ORDER BY COALESCE(min_value, -999999)
        """,
        (category,),
    )
    return [
        {
            "level": row["level"],
            "min_value": row["min_value"],
            "max_value": row["max_value"],
            "description": row["description"],
        }
        for row in cursor.fetchall()
    ]


def classify_value(conn: sqlite3.Connection, category: str, value: float) -> str | None:
    """Classify a value based on gemmological thresholds.

    Args:
        category: Threshold category (birefringence, dispersion, critical_angle)
        value: The value to classify

    Returns:
        Classification level (e.g., 'low', 'medium', 'high') or None if not found
    """
    cursor = conn.execute(
        """
        SELECT level FROM gemmological_thresholds
        WHERE category = ?
          AND (min_value IS NULL OR min_value <= ?)
          AND (max_value IS NULL OR max_value > ?)
        LIMIT 1
        """,
        (category, value, value),
    )
    row = cursor.fetchone()
    return row["level"] if row else None


def find_minerals_by_ri(
    conn: sqlite3.Connection, ri: float, tolerance: float = 0.01
) -> list[Mineral]:
    """Find minerals matching an RI value within tolerance.

    Args:
        conn: Database connection
        ri: Refractive index value to match
        tolerance: Acceptable tolerance (default 0.01)

    Returns:
        List of matching Mineral objects
    """
    cursor = conn.execute(
        """
        SELECT * FROM minerals
        WHERE ri_min IS NOT NULL
          AND ri_max IS NOT NULL
          AND (ri_min - ? <= ? AND ri_max + ? >= ?)
        ORDER BY ABS((ri_min + ri_max) / 2 - ?) ASC
        """,
        (tolerance, ri, tolerance, ri, ri),
    )
    return [row_to_mineral(row) for row in cursor.fetchall()]


def find_minerals_by_sg(
    conn: sqlite3.Connection, sg: float, tolerance: float = 0.05
) -> list[Mineral]:
    """Find minerals matching an SG value within tolerance.

    Args:
        conn: Database connection
        sg: Specific gravity value to match
        tolerance: Acceptable tolerance (default 0.05)

    Returns:
        List of matching Mineral objects
    """
    cursor = conn.execute(
        """
        SELECT * FROM minerals
        WHERE sg_min IS NOT NULL
          AND sg_max IS NOT NULL
          AND (sg_min - ? <= ? AND sg_max + ? >= ?)
        ORDER BY ABS((sg_min + sg_max) / 2 - ?) ASC
        """,
        (tolerance, sg, tolerance, sg, sg),
    )
    return [row_to_mineral(row) for row in cursor.fetchall()]


def get_minerals_with_heat_treatment(conn: sqlite3.Connection) -> list[Mineral]:
    """Get minerals that have heat treatment temperature data.

    Returns:
        List of Mineral objects with heat treatment data
    """
    cursor = conn.execute(
        """
        SELECT * FROM minerals
        WHERE heat_treatment_temp_min IS NOT NULL
          OR heat_treatment_temp_max IS NOT NULL
        ORDER BY name
        """
    )
    return [row_to_mineral(row) for row in cursor.fetchall()]


# =============================================================================
# Family + Expression Functions (normalized structure)
# =============================================================================


def insert_family(conn: sqlite3.Connection, family: MineralFamily) -> None:
    """Insert a mineral family into the database.

    Args:
        conn: Database connection
        family: MineralFamily to insert
    """
    sql = """
    INSERT OR REPLACE INTO mineral_families (
        id, name, crystal_system, point_group, chemistry, category,
        hardness_min, hardness_max, sg_min, sg_max,
        ri_min, ri_max, birefringence, dispersion, optical_character,
        pleochroism, pleochroism_strength, pleochroism_color1, pleochroism_color2,
        pleochroism_color3, pleochroism_notes,
        lustre, cleavage, fracture,
        description, notes, diagnostic_features, common_inclusions,
        localities_json, colors_json, treatments_json, inclusions_json, forms_json,
        heat_treatment_temp_min, heat_treatment_temp_max,
        twin_law, phenomenon, fluorescence,
        origin, growth_method, natural_counterpart_id, target_minerals_json,
        manufacturer, year_first_produced, diagnostic_synthetic_features,
        updated_at
    ) VALUES (
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?,
        CURRENT_TIMESTAMP
    )
    """

    conn.execute(
        sql,
        (
            family.id,
            family.name,
            family.crystal_system,
            family.point_group,
            family.chemistry,
            family.category,
            family.hardness_min,
            family.hardness_max,
            family.sg_min,
            family.sg_max,
            family.ri_min,
            family.ri_max,
            family.birefringence,
            family.dispersion,
            family.optical_character,
            family.pleochroism,
            family.pleochroism_strength,
            family.pleochroism_color1,
            family.pleochroism_color2,
            family.pleochroism_color3,
            family.pleochroism_notes,
            family.lustre,
            family.cleavage,
            family.fracture,
            family.description,
            family.notes,
            family.diagnostic_features,
            family.common_inclusions,
            json.dumps(family.localities) if family.localities else "[]",
            json.dumps(family.colors) if family.colors else "[]",
            json.dumps(family.treatments) if family.treatments else "[]",
            json.dumps(family.inclusions) if family.inclusions else "[]",
            json.dumps(family.forms) if family.forms else "[]",
            family.heat_treatment_temp_min,
            family.heat_treatment_temp_max,
            family.twin_law,
            family.phenomenon,
            family.fluorescence,
            family.origin,
            family.growth_method,
            family.natural_counterpart_id,
            json.dumps(family.target_minerals) if family.target_minerals else None,
            family.manufacturer,
            family.year_first_produced,
            family.diagnostic_synthetic_features,
        ),
    )


def insert_expression(conn: sqlite3.Connection, expression: MineralExpression) -> None:
    """Insert a mineral expression into the database.

    Args:
        conn: Database connection
        expression: MineralExpression to insert
    """
    sql = """
    INSERT OR REPLACE INTO mineral_expressions (
        id, family_id, name, slug,
        cdl, point_group, form_description, habit, forms_json,
        svg_path, gltf_path, stl_path, thumbnail_path,
        model_svg, model_stl, model_gltf, models_generated_at,
        is_primary, sort_order, note
    ) VALUES (
        ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?
    )
    """

    conn.execute(
        sql,
        (
            expression.id,
            expression.family_id,
            expression.name,
            expression.slug,
            expression.cdl,
            expression.point_group,
            expression.form_description,
            expression.habit,
            json.dumps(expression.forms) if expression.forms else None,
            expression.svg_path,
            expression.gltf_path,
            expression.stl_path,
            expression.thumbnail_path,
            expression.model_svg,
            expression.model_stl,
            expression.model_gltf,
            expression.models_generated_at,
            expression.is_primary,
            expression.sort_order,
            expression.note,
        ),
    )


def row_to_family(row: sqlite3.Row) -> MineralFamily:
    """Convert a database row to a MineralFamily object.

    Args:
        row: Database row

    Returns:
        MineralFamily instance
    """
    return MineralFamily(
        id=row["id"],
        name=row["name"],
        crystal_system=row["crystal_system"],
        point_group=row["point_group"],
        chemistry=row["chemistry"],
        category=row["category"],
        hardness_min=row["hardness_min"],
        hardness_max=row["hardness_max"],
        sg_min=row["sg_min"],
        sg_max=row["sg_max"],
        ri_min=row["ri_min"],
        ri_max=row["ri_max"],
        birefringence=row["birefringence"],
        dispersion=row["dispersion"],
        optical_character=row["optical_character"],
        pleochroism=row["pleochroism"],
        pleochroism_strength=row["pleochroism_strength"],
        pleochroism_color1=row["pleochroism_color1"],
        pleochroism_color2=row["pleochroism_color2"],
        pleochroism_color3=row["pleochroism_color3"],
        pleochroism_notes=row["pleochroism_notes"],
        lustre=row["lustre"],
        cleavage=row["cleavage"],
        fracture=row["fracture"],
        description=row["description"],
        notes=row["notes"],
        diagnostic_features=row["diagnostic_features"],
        common_inclusions=row["common_inclusions"],
        localities=json.loads(row["localities_json"] or "[]"),
        colors=json.loads(row["colors_json"] or "[]"),
        treatments=json.loads(row["treatments_json"] or "[]"),
        inclusions=json.loads(row["inclusions_json"] or "[]"),
        forms=json.loads(row["forms_json"] or "[]"),
        heat_treatment_temp_min=row["heat_treatment_temp_min"],
        heat_treatment_temp_max=row["heat_treatment_temp_max"],
        twin_law=row["twin_law"],
        phenomenon=row["phenomenon"],
        fluorescence=row["fluorescence"],
        origin=row["origin"] if "origin" in row.keys() else "natural",
        growth_method=row["growth_method"] if "growth_method" in row.keys() else None,
        natural_counterpart_id=row["natural_counterpart_id"]
        if "natural_counterpart_id" in row.keys()
        else None,
        target_minerals=json.loads(row["target_minerals_json"] or "[]")
        if "target_minerals_json" in row.keys()
        else [],
        manufacturer=row["manufacturer"] if "manufacturer" in row.keys() else None,
        year_first_produced=row["year_first_produced"]
        if "year_first_produced" in row.keys()
        else None,
        diagnostic_synthetic_features=row["diagnostic_synthetic_features"]
        if "diagnostic_synthetic_features" in row.keys()
        else None,
    )


def row_to_expression(row: sqlite3.Row) -> MineralExpression:
    """Convert a database row to a MineralExpression object.

    Args:
        row: Database row

    Returns:
        MineralExpression instance
    """
    return MineralExpression(
        id=row["id"],
        family_id=row["family_id"],
        name=row["name"],
        slug=row["slug"],
        cdl=row["cdl"],
        point_group=row["point_group"],
        form_description=row["form_description"],
        habit=row["habit"],
        forms=json.loads(row["forms_json"]) if row["forms_json"] else None,
        svg_path=row["svg_path"],
        gltf_path=row["gltf_path"],
        stl_path=row["stl_path"],
        thumbnail_path=row["thumbnail_path"],
        model_svg=row["model_svg"],
        model_stl=row["model_stl"],
        model_gltf=row["model_gltf"],
        models_generated_at=row["models_generated_at"],
        is_primary=bool(row["is_primary"]),
        sort_order=row["sort_order"] or 0,
        note=row["note"],
    )


def get_family_by_id(conn: sqlite3.Connection, family_id: str) -> MineralFamily | None:
    """Get a mineral family by its ID.

    Args:
        conn: Database connection
        family_id: Family ID

    Returns:
        MineralFamily or None if not found
    """
    cursor = conn.execute("SELECT * FROM mineral_families WHERE id = ?", (family_id.lower(),))
    row = cursor.fetchone()
    if row:
        return row_to_family(row)
    return None


def get_all_families(conn: sqlite3.Connection) -> list[MineralFamily]:
    """Get all mineral families from the database.

    Args:
        conn: Database connection

    Returns:
        List of all mineral families
    """
    cursor = conn.execute("SELECT * FROM mineral_families ORDER BY name")
    return [row_to_family(row) for row in cursor.fetchall()]


def get_families_by_system(conn: sqlite3.Connection, system: str) -> list[MineralFamily]:
    """Get mineral families by crystal system.

    Args:
        conn: Database connection
        system: Crystal system name

    Returns:
        List of families in that system
    """
    cursor = conn.execute(
        "SELECT * FROM mineral_families WHERE crystal_system = ? ORDER BY name",
        (system.lower(),),
    )
    return [row_to_family(row) for row in cursor.fetchall()]


def get_expressions_for_family(conn: sqlite3.Connection, family_id: str) -> list[MineralExpression]:
    """Get all expressions for a mineral family.

    Args:
        conn: Database connection
        family_id: Family ID

    Returns:
        List of expressions ordered by is_primary DESC, sort_order
    """
    cursor = conn.execute(
        """
        SELECT * FROM mineral_expressions
        WHERE family_id = ?
        ORDER BY is_primary DESC, sort_order
        """,
        (family_id.lower(),),
    )
    return [row_to_expression(row) for row in cursor.fetchall()]


def get_expression_by_id(conn: sqlite3.Connection, expression_id: str) -> MineralExpression | None:
    """Get a mineral expression by its ID.

    Args:
        conn: Database connection
        expression_id: Expression ID

    Returns:
        MineralExpression or None if not found
    """
    cursor = conn.execute(
        "SELECT * FROM mineral_expressions WHERE id = ?", (expression_id.lower(),)
    )
    row = cursor.fetchone()
    if row:
        return row_to_expression(row)
    return None


def get_family_count(conn: sqlite3.Connection) -> int:
    """Get the total number of mineral families.

    Args:
        conn: Database connection

    Returns:
        Number of families
    """
    cursor = conn.execute("SELECT COUNT(*) FROM mineral_families")
    return cursor.fetchone()[0]


def get_expression_count(conn: sqlite3.Connection) -> int:
    """Get the total number of mineral expressions.

    Args:
        conn: Database connection

    Returns:
        Number of expressions
    """
    cursor = conn.execute("SELECT COUNT(*) FROM mineral_expressions")
    return cursor.fetchone()[0]


def get_families_with_expression_counts(
    conn: sqlite3.Connection,
) -> list[tuple[MineralFamily, int]]:
    """Get all families with their expression counts.

    Args:
        conn: Database connection

    Returns:
        List of (family, expression_count) tuples
    """
    cursor = conn.execute(
        """
        SELECT f.*, COUNT(e.id) as expression_count
        FROM mineral_families f
        LEFT JOIN mineral_expressions e ON f.id = e.family_id
        GROUP BY f.id
        ORDER BY f.name
        """
    )
    results = []
    for row in cursor.fetchall():
        family = row_to_family(row)
        results.append((family, row["expression_count"]))
    return results


def find_families_by_ri(
    conn: sqlite3.Connection, ri: float, tolerance: float = 0.01
) -> list[MineralFamily]:
    """Find mineral families matching an RI value within tolerance.

    Args:
        conn: Database connection
        ri: Refractive index value to match
        tolerance: Acceptable tolerance (default 0.01)

    Returns:
        List of matching MineralFamily objects (no duplicates)
    """
    cursor = conn.execute(
        """
        SELECT * FROM mineral_families
        WHERE ri_min IS NOT NULL
          AND ri_max IS NOT NULL
          AND (ri_min - ? <= ? AND ri_max + ? >= ?)
        ORDER BY ABS((ri_min + ri_max) / 2 - ?) ASC
        """,
        (tolerance, ri, tolerance, ri, ri),
    )
    return [row_to_family(row) for row in cursor.fetchall()]


def find_families_by_sg(
    conn: sqlite3.Connection, sg: float, tolerance: float = 0.05
) -> list[MineralFamily]:
    """Find mineral families matching an SG value within tolerance.

    Args:
        conn: Database connection
        sg: Specific gravity value to match
        tolerance: Acceptable tolerance (default 0.05)

    Returns:
        List of matching MineralFamily objects (no duplicates)
    """
    cursor = conn.execute(
        """
        SELECT * FROM mineral_families
        WHERE sg_min IS NOT NULL
          AND sg_max IS NOT NULL
          AND (sg_min - ? <= ? AND sg_max + ? >= ?)
        ORDER BY ABS((sg_min + sg_max) / 2 - ?) ASC
        """,
        (tolerance, sg, tolerance, sg, sg),
    )
    return [row_to_family(row) for row in cursor.fetchall()]


def update_expression_models(
    conn: sqlite3.Connection,
    expression_id: str,
    svg: str | None = None,
    stl: bytes | None = None,
    gltf: str | None = None,
    generated_at: str | None = None,
) -> None:
    """Update the 3D model data for an expression.

    Args:
        conn: Database connection
        expression_id: Expression ID
        svg: SVG markup string
        stl: Binary STL data
        gltf: glTF JSON string
        generated_at: ISO timestamp when models were generated
    """
    conn.execute(
        """
        UPDATE mineral_expressions SET
            model_svg = ?,
            model_stl = ?,
            model_gltf = ?,
            models_generated_at = ?
        WHERE id = ?
        """,
        (svg, stl, gltf, generated_at, expression_id.lower()),
    )


def get_all_expressions(conn: sqlite3.Connection) -> list[MineralExpression]:
    """Get all mineral expressions from the database.

    Args:
        conn: Database connection

    Returns:
        List of all mineral expressions
    """
    cursor = conn.execute(
        """
        SELECT * FROM mineral_expressions
        ORDER BY family_id, is_primary DESC, sort_order
        """
    )
    return [row_to_expression(row) for row in cursor.fetchall()]


# =============================================================================
# Synthetic / Simulant Query Functions
# =============================================================================


def get_families_by_origin(conn: sqlite3.Connection, origin: str) -> list[MineralFamily]:
    """Get mineral families filtered by origin.

    Args:
        conn: Database connection
        origin: Origin type (natural, synthetic, simulant, composite)

    Returns:
        List of matching MineralFamily objects
    """
    cursor = conn.execute(
        "SELECT * FROM mineral_families WHERE origin = ? ORDER BY name",
        (origin.lower(),),
    )
    return [row_to_family(row) for row in cursor.fetchall()]


def get_synthetics_for_natural(conn: sqlite3.Connection, natural_id: str) -> list[MineralFamily]:
    """Get all synthetic versions of a natural mineral.

    Args:
        conn: Database connection
        natural_id: ID of the natural mineral family

    Returns:
        List of synthetic MineralFamily objects
    """
    cursor = conn.execute(
        """
        SELECT * FROM mineral_families
        WHERE origin = 'synthetic' AND natural_counterpart_id = ?
        ORDER BY name
        """,
        (natural_id.lower(),),
    )
    return [row_to_family(row) for row in cursor.fetchall()]


def get_simulants_for_natural(conn: sqlite3.Connection, natural_id: str) -> list[MineralFamily]:
    """Get all simulants that imitate a natural mineral.

    Args:
        conn: Database connection
        natural_id: ID of the natural mineral family

    Returns:
        List of simulant MineralFamily objects
    """
    cursor = conn.execute(
        """
        SELECT * FROM mineral_families
        WHERE (origin = 'simulant' OR origin = 'composite')
          AND (natural_counterpart_id = ?
               OR target_minerals_json LIKE ?)
        ORDER BY name
        """,
        (natural_id.lower(), f'%"{natural_id.lower()}"%'),
    )
    return [row_to_family(row) for row in cursor.fetchall()]


def get_natural_counterpart(conn: sqlite3.Connection, family_id: str) -> MineralFamily | None:
    """Get the natural counterpart for a synthetic or simulant.

    Args:
        conn: Database connection
        family_id: ID of the synthetic/simulant family

    Returns:
        Natural MineralFamily or None
    """
    cursor = conn.execute(
        "SELECT natural_counterpart_id FROM mineral_families WHERE id = ?",
        (family_id.lower(),),
    )
    row = cursor.fetchone()
    if row and row["natural_counterpart_id"]:
        return get_family_by_id(conn, row["natural_counterpart_id"])
    return None


def get_families_by_growth_method(conn: sqlite3.Connection, method: str) -> list[MineralFamily]:
    """Get mineral families by growth method.

    Args:
        conn: Database connection
        method: Growth method (flame_fusion, flux, hydrothermal, cvd, hpht, etc.)

    Returns:
        List of matching MineralFamily objects
    """
    cursor = conn.execute(
        "SELECT * FROM mineral_families WHERE growth_method = ? ORDER BY name",
        (method.lower(),),
    )
    return [row_to_family(row) for row in cursor.fetchall()]
