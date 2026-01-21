# Pre-generated 3D Models

The mineral database includes pre-generated 3D visualizations for each mineral preset. These models are stored directly in the SQLite database for instant access without requiring the full rendering pipeline.

## Available Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **SVG** | Scalable Vector Graphics | Web display, documentation, print |
| **STL** | Binary stereolithography | 3D printing, CAD software |
| **glTF** | GL Transmission Format | WebGL, Three.js, game engines |

## Retrieving Pre-generated Models

### SVG Visualization

```python
from mineral_database import get_model_svg

# Get SVG markup for a mineral
svg = get_model_svg('diamond')
if svg:
    # Save to file
    with open('diamond.svg', 'w') as f:
        f.write(svg)

    # Or display in Jupyter notebook
    from IPython.display import SVG, display
    display(SVG(svg))
```

### STL for 3D Printing

```python
from mineral_database import get_model_stl

# Get binary STL data
stl_data = get_model_stl('quartz')
if stl_data:
    # Save to file
    with open('quartz.stl', 'wb') as f:
        f.write(stl_data)

    # Ready for 3D printing software
    print(f"STL size: {len(stl_data)} bytes")
```

### glTF for Web Display

```python
from mineral_database import get_model_gltf
import json

# Get glTF dictionary
gltf = get_model_gltf('ruby')
if gltf:
    # Save as .gltf file
    with open('ruby.gltf', 'w') as f:
        json.dump(gltf, f, indent=2)

    # Or use directly with Three.js loader
    print(f"glTF has {len(gltf.get('meshes', []))} meshes")
```

### Check Generation Timestamp

```python
from mineral_database import get_models_generated_at

# Check when models were generated
timestamp = get_models_generated_at('emerald')
if timestamp:
    print(f"Models generated at: {timestamp}")
else:
    print("Models not yet generated")
```

---

## Generating Models

Models are generated using the companion packages (`cdl-parser`, `crystal-geometry`, `crystal-renderer`) and stored in the database.

### Using the Generation Script

```bash
# Generate models for all minerals
python scripts/generate_models.py data/minerals.db

# Verbose output showing generation details
python scripts/generate_models.py data/minerals.db --verbose

# Generate for a specific mineral only
python scripts/generate_models.py data/minerals.db --mineral diamond
```

### Programmatic Generation

For custom generation workflows:

```python
from cdl_parser import parse_cdl
from crystal_geometry import cdl_to_geometry
from crystal_renderer.formats import geometry_to_stl, geometry_to_gltf

# Parse CDL and generate geometry
cdl = "cubic[m3m]:{111}@1.0 + {100}@1.3"
description = parse_cdl(cdl)
geometry = cdl_to_geometry(description)

# Generate STL
stl_binary = geometry_to_stl(geometry.vertices, geometry.faces, binary=True)

# Generate glTF
gltf_dict = geometry_to_gltf(geometry.vertices, geometry.faces, name="custom")
```

---

## Web Integration

### Embedding SVG in HTML

```html
<!-- Direct embedding -->
<div class="crystal-viewer">
  {{ mineral_svg | safe }}
</div>

<!-- Via JavaScript -->
<script>
fetch('/api/mineral/diamond/svg')
  .then(r => r.text())
  .then(svg => {
    document.getElementById('viewer').innerHTML = svg;
  });
</script>
```

### Three.js with glTF

```javascript
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const loader = new GLTFLoader();

// Load from URL
loader.load('/api/mineral/quartz/gltf', (gltf) => {
  scene.add(gltf.scene);
});

// Or load from JSON string
const gltfData = await fetch('/api/mineral/quartz/gltf').then(r => r.json());
loader.parse(JSON.stringify(gltfData), '', (gltf) => {
  scene.add(gltf.scene);
});
```

### 3D Printing Workflow

```python
from mineral_database import get_model_stl, get_preset

def prepare_for_printing(mineral_id: str, scale_mm: float = 50):
    """Prepare a mineral model for 3D printing.

    Args:
        mineral_id: Mineral preset name
        scale_mm: Desired size in millimeters
    """
    # Get preset info
    preset = get_preset(mineral_id)
    if not preset:
        raise ValueError(f"Mineral not found: {mineral_id}")

    # Get STL data
    stl_data = get_model_stl(mineral_id)
    if not stl_data:
        raise ValueError(f"No STL model for: {mineral_id}")

    # Save with descriptive filename
    filename = f"{mineral_id}_{preset['system']}_{scale_mm}mm.stl"
    with open(filename, 'wb') as f:
        f.write(stl_data)

    print(f"Saved: {filename}")
    print(f"Crystal system: {preset['system']}")
    print(f"Point group: {preset['point_group']}")
    print(f"Note: Scale to {scale_mm}mm in slicer software")

    return filename

# Example: Prepare diamond for printing
prepare_for_printing('diamond', scale_mm=30)
```

---

## Database Schema

Pre-generated models are stored in the `mineral_models` table:

```sql
CREATE TABLE mineral_models (
    mineral_id TEXT PRIMARY KEY,
    model_svg TEXT,           -- SVG markup string
    model_stl BLOB,           -- Binary STL data
    model_gltf TEXT,          -- JSON-encoded glTF
    models_generated_at TEXT, -- ISO timestamp
    FOREIGN KEY (mineral_id) REFERENCES minerals(id)
);
```

### Querying Directly

```python
from mineral_database import get_connection

with get_connection() as conn:
    cursor = conn.execute("""
        SELECT mineral_id,
               LENGTH(model_svg) as svg_size,
               LENGTH(model_stl) as stl_size,
               LENGTH(model_gltf) as gltf_size,
               models_generated_at
        FROM mineral_models
        WHERE model_svg IS NOT NULL
        ORDER BY models_generated_at DESC
        LIMIT 10
    """)

    for row in cursor:
        print(f"{row['mineral_id']}: SVG={row['svg_size']}, STL={row['stl_size']}, glTF={row['gltf_size']}")
```

---

## Batch Operations

### Export All Models to Files

```python
from mineral_database import list_presets, get_model_svg, get_model_stl, get_model_gltf
from pathlib import Path
import json

def export_all_models(output_dir: str):
    """Export all pre-generated models to files."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    (output / 'svg').mkdir(exist_ok=True)
    (output / 'stl').mkdir(exist_ok=True)
    (output / 'gltf').mkdir(exist_ok=True)

    for mineral_id in list_presets():
        # SVG
        svg = get_model_svg(mineral_id)
        if svg:
            (output / 'svg' / f'{mineral_id}.svg').write_text(svg)

        # STL
        stl = get_model_stl(mineral_id)
        if stl:
            (output / 'stl' / f'{mineral_id}.stl').write_bytes(stl)

        # glTF
        gltf = get_model_gltf(mineral_id)
        if gltf:
            (output / 'gltf' / f'{mineral_id}.gltf').write_text(json.dumps(gltf))

        print(f"Exported: {mineral_id}")

# Export all models
export_all_models('./crystal_models')
```

### Generate Missing Models

```python
from mineral_database import (
    list_presets,
    get_preset,
    get_models_generated_at,
    get_connection,
)
from mineral_database.db import update_mineral_models
from datetime import datetime, timezone

def regenerate_missing():
    """Regenerate models for minerals missing them."""
    from cdl_parser import parse_cdl
    from crystal_geometry import cdl_to_geometry
    from crystal_renderer.formats import geometry_to_stl, geometry_to_gltf

    missing = []
    for mineral_id in list_presets():
        if not get_models_generated_at(mineral_id):
            missing.append(mineral_id)

    print(f"Found {len(missing)} minerals without models")

    with get_connection() as conn:
        for mineral_id in missing:
            preset = get_preset(mineral_id)
            try:
                desc = parse_cdl(preset['cdl'])
                geom = cdl_to_geometry(desc)

                stl = geometry_to_stl(geom.vertices, geom.faces, binary=True)
                gltf = geometry_to_gltf(geom.vertices, geom.faces, name=mineral_id)

                update_mineral_models(
                    conn, mineral_id,
                    stl=stl,
                    gltf=json.dumps(gltf),
                    generated_at=datetime.now(timezone.utc).isoformat()
                )
                print(f"Generated: {mineral_id}")
            except Exception as e:
                print(f"Failed: {mineral_id} - {e}")

        conn.commit()
```

---

## Troubleshooting

### "No model found for mineral"

Models may not be generated yet:

```python
from mineral_database import get_model_svg, get_preset

mineral_id = 'diamond'
svg = get_model_svg(mineral_id)

if svg is None:
    preset = get_preset(mineral_id)
    if preset:
        print(f"Mineral exists but model not generated")
        print(f"Run: python scripts/generate_models.py db.db -m {mineral_id}")
    else:
        print(f"Mineral not found: {mineral_id}")
```

### Large Database Size

Pre-generated models significantly increase database size:

| Content | Approximate Size |
|---------|-----------------|
| Mineral data only | ~100 KB |
| With SVG models | ~5-10 MB |
| With all formats | ~15-25 MB |

To reduce size, you can strip unused formats:

```python
# Keep only SVG, remove STL and glTF
with get_connection(db_path) as conn:
    conn.execute("UPDATE mineral_models SET model_stl = NULL, model_gltf = NULL")
    conn.execute("VACUUM")
    conn.commit()
```

### Model Quality Issues

Models are generated at standard settings. For higher quality:

```python
from crystal_renderer.formats import geometry_to_stl

# Higher subdivision for smoother STL
stl = geometry_to_stl(
    geometry.vertices,
    geometry.faces,
    binary=True,
    subdivisions=2  # Increase for smoother surfaces
)
```
