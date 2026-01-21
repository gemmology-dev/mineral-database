# Examples

## Basic Usage

### Querying Presets

```python
from mineral_database import get_preset, list_presets

# Get a specific preset
diamond = get_preset('diamond')
print(f"CDL: {diamond['cdl']}")
print(f"System: {diamond['system']}")
print(f"Hardness: {diamond['hardness']}")

# List all available presets
all_presets = list_presets()
print(f"Total presets: {len(all_presets)}")
```

### Using Mineral Objects

```python
from mineral_database import get_mineral

# Get full mineral data
ruby = get_mineral('ruby')
print(f"Name: {ruby.name}")
print(f"Chemistry: {ruby.chemistry}")
print(f"RI: {ruby.ri}")
print(f"Localities: {', '.join(ruby.localities)}")
```

### Searching

```python
from mineral_database import search_presets

# Search by name
garnets = search_presets('garnet')
print(f"Found {len(garnets)} garnet varieties")

# Search by property
red_gems = search_presets('red')
myanmar_gems = search_presets('Myanmar')
```

## Working with Crystal Systems

### Listing by System

```python
from mineral_database import list_presets

# Get presets for each system
cubic = list_presets('cubic')
trigonal = list_presets('trigonal')
hexagonal = list_presets('hexagonal')

print(f"Cubic minerals: {len(cubic)}")
print(f"Trigonal minerals: {len(trigonal)}")
print(f"Hexagonal minerals: {len(hexagonal)}")
```

### Crystal System Examples

```python
from mineral_database import get_preset

# Cubic system
diamond = get_preset('diamond')    # {111} + {110}
garnet = get_preset('garnet')      # {110} + {211}
fluorite = get_preset('fluorite')  # {100}
pyrite = get_preset('pyrite')      # {210}

# Trigonal system
quartz = get_preset('quartz')      # {10-10} + {10-11}
ruby = get_preset('ruby')          # {10-10} + {10-11}
tourmaline = get_preset('tourmaline')

# Hexagonal system
beryl = get_preset('beryl')        # {10-10} + {0001}
emerald = get_preset('emerald')
apatite = get_preset('apatite')
```

## Filtering and Advanced Queries

### Filter by Criteria

```python
from mineral_database import filter_minerals

# Find hard cubic minerals
hard_cubic = filter_minerals(system='cubic', min_hardness=8)
for m in hard_cubic:
    print(f"{m.name}: hardness {m.hardness}")

# Find minerals with high RI
high_ri = filter_minerals(min_ri=1.7)
```

### Filter by Crystal Form

```python
from mineral_database import get_presets_by_form

# Find minerals with octahedral habit
octahedral = get_presets_by_form('octahedron')
print("Octahedral minerals:")
for preset_id in octahedral:
    print(f"  - {preset_id}")

# Find minerals with prismatic habit
prismatic = get_presets_by_form('prism')
```

## Gemmological Properties

### FGA-Style Properties

```python
from mineral_database import get_info_properties, get_mineral

# Get formatted properties for display
props = get_info_properties('ruby', 'fga')
print("Ruby - FGA Properties:")
for key, value in props.items():
    print(f"  {key}: {value}")
```

### Property Formatting

```python
from mineral_database import (
    get_property_label,
    format_property_value,
    INFO_GROUPS
)

# Get display labels
print(get_property_label('sg'))     # 'SG'
print(get_property_label('ri'))     # 'RI'

# Format values
print(format_property_value('sg', 4.0))        # '4.00'
print(format_property_value('hardness', 9))    # '9'

# Property groups
for group, props in INFO_GROUPS.items():
    print(f"\n{group.upper()}:")
    for prop in props:
        print(f"  - {prop}")
```

## Backwards Compatibility

### Using CRYSTAL_PRESETS

```python
from mineral_database import CRYSTAL_PRESETS

# Dict-like access
diamond = CRYSTAL_PRESETS['diamond']
ruby = CRYSTAL_PRESETS.get('ruby')

# Checking existence
if 'garnet' in CRYSTAL_PRESETS:
    print("Garnet preset exists")

# Iteration
for name in CRYSTAL_PRESETS:
    preset = CRYSTAL_PRESETS[name]
    print(f"{name}: {preset['cdl']}")

# Length
print(f"Total presets: {len(CRYSTAL_PRESETS)}")
```

### Migration from Legacy Code

```python
# Old code using dict
# from my_module import CRYSTAL_PRESETS
# preset = CRYSTAL_PRESETS['diamond']

# New code - drop-in replacement
from mineral_database import CRYSTAL_PRESETS
preset = CRYSTAL_PRESETS['diamond']

# Or use the new API for more features
from mineral_database import get_preset, get_mineral
preset = get_preset('diamond')      # Same dict format
mineral = get_mineral('diamond')    # Full Mineral object
```

## Integration Examples

### With cdl-parser

```python
from mineral_database import get_preset
from cdl_parser import parse_cdl

# Get CDL string from database
diamond = get_preset('diamond')
cdl_string = diamond['cdl']

# Parse it
desc = parse_cdl(cdl_string)
print(f"System: {desc.system}")
print(f"Forms: {len(desc.forms)}")
```

### With crystal-geometry

```python
from mineral_database import get_preset
from crystal_geometry import cdl_string_to_geometry

# Get CDL and generate geometry
preset = get_preset('garnet')
geom = cdl_string_to_geometry(preset['cdl'])

print(f"Garnet geometry:")
print(f"  Vertices: {len(geom.vertices)}")
print(f"  Faces: {len(geom.faces)}")
```

### With crystal-renderer

```python
from mineral_database import get_preset, get_info_properties
from crystal_renderer import generate_cdl_svg

# Get preset with properties
preset = get_preset('ruby')
props = get_info_properties('ruby', 'fga')

# Render with info panel
generate_cdl_svg(
    preset['cdl'],
    "ruby.svg",
    show_axes=True,
    info_panel=props
)
```

### Full Pipeline Example

```python
from mineral_database import get_preset, get_mineral
from cdl_parser import parse_cdl
from crystal_geometry import cdl_to_geometry
from crystal_renderer import generate_geometry_svg

# Get mineral data
mineral = get_mineral('diamond')
print(f"Rendering {mineral.name}")
print(f"  Chemistry: {mineral.chemistry}")
print(f"  Hardness: {mineral.hardness}")
print(f"  RI: {mineral.ri}")

# Parse CDL
desc = parse_cdl(mineral.cdl)

# Generate geometry
geom = cdl_to_geometry(desc)

# Render
generate_geometry_svg(
    geom.vertices,
    geom.faces,
    f"{mineral.id}.svg",
    face_color='#E8F5E9'
)
print(f"Saved to {mineral.id}.svg")
```

## Database Operations

### Counting Presets

```python
from mineral_database import count_presets, list_preset_categories

# Total count
total = count_presets()
print(f"Database contains {total} presets")

# Count by category
categories = list_preset_categories()
for cat in categories:
    presets = list_presets(cat) if cat != 'all' else list_presets()
    print(f"  {cat}: {len(presets)}")
```

### Exporting Data

```python
from mineral_database import list_presets, get_preset
import json

# Export all presets to JSON
all_data = {}
for preset_id in list_presets():
    all_data[preset_id] = get_preset(preset_id)

with open('minerals.json', 'w') as f:
    json.dump(all_data, f, indent=2)

print(f"Exported {len(all_data)} presets")
```
