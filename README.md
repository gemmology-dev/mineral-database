# mineral-database

[![PyPI version](https://badge.fury.io/py/mineral-database.svg)](https://badge.fury.io/py/mineral-database)
[![Python](https://img.shields.io/pypi/pyversions/mineral-database.svg)](https://pypi.org/project/mineral-database/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mineral Database** - A comprehensive database of mineral crystal habits with CDL notation and gemmological properties for visualization applications.

Part of the [Gemmology Project](https://gemmology.dev).

## Installation

```bash
pip install mineral-database
```

## Quick Start

```python
from mineral_database import get_preset, list_presets, search_presets

# Get a specific mineral preset
diamond = get_preset('diamond')
print(diamond['cdl'])      # 'cubic[m3m]:{111}@1.0 + {110}@0.2'
print(diamond['system'])   # 'cubic'
print(diamond['hardness']) # 10

# List all presets
all_presets = list_presets()

# List presets by crystal system
cubic_presets = list_presets('cubic')

# Search presets
garnet_matches = search_presets('garnet')
```

## Features

- **94+ mineral presets** with accurate crystallographic data
- **CDL notation** for crystal habit visualization
- **FGA-standard properties** (RI, SG, optical character, etc.)
- **SQLite backend** for fast queries
- **Full-text search** across mineral names and properties
- **Backwards compatible** with original `CRYSTAL_PRESETS` dict API

## Database Contents

The database includes presets for all major crystal systems:

| System | Count | Examples |
|--------|-------|----------|
| Cubic | ~25 | Diamond, Garnet, Fluorite, Pyrite |
| Hexagonal | ~8 | Beryl, Emerald, Aquamarine, Apatite |
| Trigonal | ~15 | Quartz, Ruby, Sapphire, Tourmaline |
| Tetragonal | ~5 | Zircon, Rutile, Cassiterite |
| Orthorhombic | ~10 | Topaz, Peridot, Tanzanite |
| Monoclinic | ~10 | Kunzite, Epidote, Gypsum |
| Triclinic | ~5 | Turquoise, Kyanite, Labradorite |
| **Twins** | ~15 | Japan Law, Spinel Macle, Iron Cross |

## API Reference

### Query Functions

```python
from mineral_database import (
    get_preset,           # Get preset dict by name
    get_mineral,          # Get Mineral object by name
    list_presets,         # List preset names
    list_preset_categories,  # List categories
    search_presets,       # Full-text search
    filter_minerals,      # Filter by criteria
    get_presets_by_form,  # Get by crystal form
    count_presets,        # Total count
)
```

### Backwards Compatibility

The package provides dict-like `CRYSTAL_PRESETS` for code migration:

```python
from mineral_database import CRYSTAL_PRESETS

# All dict operations work
preset = CRYSTAL_PRESETS['diamond']
preset = CRYSTAL_PRESETS.get('ruby')
'garnet' in CRYSTAL_PRESETS
for name in CRYSTAL_PRESETS:
    print(name)
```

### Mineral Object

```python
from mineral_database import get_mineral, Mineral

mineral = get_mineral('ruby')
print(mineral.id)           # 'ruby'
print(mineral.name)         # 'Ruby'
print(mineral.system)       # 'trigonal'
print(mineral.chemistry)    # 'Al2O3:Cr'
print(mineral.hardness)     # 9
print(mineral.ri)           # '1.762-1.770'
print(mineral.localities)   # ['Myanmar', 'Mozambique', ...]
```

### Property Formatting

```python
from mineral_database import (
    INFO_GROUPS,
    get_info_properties,
    get_property_label,
    format_property_value,
)

# Get FGA-style properties
props = get_info_properties('ruby', 'fga')
# Returns: {'name': 'Ruby', 'ri': '1.762-1.770', 'sg': 4.0, ...}

# Format for display
label = get_property_label('sg')  # 'SG'
value = format_property_value('sg', 4.0)  # '4'
```

## CLI Usage

```bash
# List all presets
mineral-db --list

# List by crystal system
mineral-db --list cubic

# Show preset details
mineral-db --info diamond

# Search presets
mineral-db --search garnet

# Output as JSON
mineral-db --json ruby

# Show categories
mineral-db --categories
```

## Database Schema

The SQLite database stores minerals with full gemmological properties:

```python
# Core fields (all minerals)
id, name, cdl, system, point_group, chemistry, hardness, description

# Optional gemmological properties
sg, ri, birefringence, optical_character, dispersion, lustre,
cleavage, fracture, pleochroism, twin_law, phenomenon

# List fields (JSON-encoded)
localities, forms, colors, treatments, inclusions
```

## Building the Database

For development, you can rebuild the database from source:

```bash
# From legacy Python dict
python scripts/build_db.py --from-legacy crystal_presets.py -o minerals.db

# From YAML files
python scripts/build_db.py --from-yaml data/source/minerals -o minerals.db

# Export to YAML for editing
python scripts/build_db.py --export-yaml minerals.db -o data/source/minerals
```

## Development

```bash
# Clone and install
git clone https://github.com/gemmology-dev/mineral-database.git
cd mineral-database
pip install -e ".[dev]"

# Run tests
pytest

# Build database
python scripts/build_db.py --from-legacy /path/to/crystal_presets.py -o src/mineral_database/data/minerals.db
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [cdl-parser](https://github.com/gemmology-dev/cdl-parser) - CDL notation parser
- [crystal-geometry](https://github.com/gemmology-dev/crystal-geometry) - 3D geometry from CDL
- [crystal-renderer](https://github.com/gemmology-dev/crystal-renderer) - SVG/3D rendering
- [gemmology-plugin](https://github.com/gemmology-dev/gemmology-plugin) - Claude Code plugin
