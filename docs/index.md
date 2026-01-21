# Mineral Database

**Mineral Database** - A comprehensive database of mineral crystal habits with CDL notation and gemmological properties for visualization applications.

Part of the [Gemmology Project](https://gemmology.dev).

## Overview

The Mineral Database provides:

- **94+ mineral presets** with accurate crystallographic data
- **CDL notation** for crystal habit visualization
- **FGA-standard properties** (RI, SG, optical character, etc.)
- **SQLite backend** for fast queries
- **Full-text search** across mineral names and properties
- **Backwards compatible** with original `CRYSTAL_PRESETS` dict API

## Installation

```bash
pip install gemmology-mineral-database
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

## Backwards Compatibility

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

## Related Packages

- [cdl-parser](https://cdl-parser.gemmology.dev) - CDL notation parser
- [crystal-geometry](https://crystal-geometry.gemmology.dev) - 3D geometry from CDL
- [crystal-renderer](https://crystal-renderer.gemmology.dev) - SVG/3D rendering

## License

MIT License - see [LICENSE](https://github.com/gemmology-dev/mineral-database/blob/main/LICENSE) for details.
