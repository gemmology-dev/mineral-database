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
        models_generated_at TEXT  -- ISO timestamp
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

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_minerals_system ON minerals(system);
    CREATE INDEX IF NOT EXISTS idx_minerals_twin_law ON minerals(twin_law);
    """

    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def insert_mineral(conn: sqlite3.Connection, mineral: Mineral) -> None:
    """Insert a mineral into the database.

    Args:
        conn: Database connection
        mineral: Mineral to insert
    """
    sql = """
    INSERT OR REPLACE INTO minerals (
        id, name, cdl, system, point_group, chemistry, hardness, description,
        sg, ri, birefringence, optical_character, dispersion, lustre, cleavage,
        fracture, pleochroism, twin_law, phenomenon, note,
        localities_json, forms_json, colors_json, treatments_json, inclusions_json
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?
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
