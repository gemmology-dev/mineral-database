"""
Mineral Database Connection.

SQLite database access layer for the mineral database.
"""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from .models import Mineral

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
        point_group TEXT NOT NULL,
        chemistry TEXT NOT NULL,
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
        heat_treatment_temp_max REAL   -- Max treatment temp (e.g., 1900)
    );

    -- Categories table for preset groupings
    CREATE TABLE IF NOT EXISTS categories (
        name TEXT PRIMARY KEY,
        presets_json TEXT NOT NULL
    );

    -- Full-text search index
    CREATE VIRTUAL TABLE IF NOT EXISTS minerals_fts USING fts5(
        id, name, chemistry, description, localities,
        content='minerals',
        content_rowid='rowid'
    );

    -- Triggers to keep FTS index in sync
    CREATE TRIGGER IF NOT EXISTS minerals_ai AFTER INSERT ON minerals BEGIN
        INSERT INTO minerals_fts(rowid, id, name, chemistry, description, localities)
        VALUES (new.rowid, new.id, new.name, new.chemistry, new.description, new.localities_json);
    END;

    CREATE TRIGGER IF NOT EXISTS minerals_ad AFTER DELETE ON minerals BEGIN
        INSERT INTO minerals_fts(minerals_fts, rowid, id, name, chemistry, description, localities)
        VALUES ('delete', old.rowid, old.id, old.name, old.chemistry, old.description, old.localities_json);
    END;

    CREATE TRIGGER IF NOT EXISTS minerals_au AFTER UPDATE ON minerals BEGIN
        INSERT INTO minerals_fts(minerals_fts, rowid, id, name, chemistry, description, localities)
        VALUES ('delete', old.rowid, old.id, old.name, old.chemistry, old.description, old.localities_json);
        INSERT INTO minerals_fts(rowid, id, name, chemistry, description, localities)
        VALUES (new.rowid, new.id, new.name, new.chemistry, new.description, new.localities_json);
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
        fracture, pleochroism, twin_law, phenomenon, note,
        localities_json, forms_json, colors_json, treatments_json, inclusions_json,
        ri_min, ri_max, sg_min, sg_max,
        heat_treatment_temp_min, heat_treatment_temp_max
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?
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
    cursor = conn.execute("SELECT id, name, factor, description FROM cut_shape_factors ORDER BY name")
    return [
        {"id": row["id"], "name": row["name"], "factor": row["factor"], "description": row["description"]}
        for row in cursor.fetchall()
    ]


def get_volume_shape_factors(conn: sqlite3.Connection) -> list[dict[str, str | float]]:
    """Get all volume shape factors.

    Returns:
        List of dicts with id, name, factor
    """
    cursor = conn.execute("SELECT id, name, factor FROM volume_shape_factors ORDER BY name")
    return [{"id": row["id"], "name": row["name"], "factor": row["factor"]} for row in cursor.fetchall()]


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
