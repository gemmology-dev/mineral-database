# API Reference

## Query Functions

### get_preset

Get a mineral preset dictionary by name.

```python
from mineral_database import get_preset

diamond = get_preset('diamond')
print(diamond['cdl'])      # CDL string
print(diamond['system'])   # Crystal system
print(diamond['hardness']) # Mohs hardness
```

::: mineral_database.get_preset

### get_mineral

Get a Mineral object by name.

```python
from mineral_database import get_mineral

mineral = get_mineral('ruby')
print(mineral.id)           # 'ruby'
print(mineral.name)         # 'Ruby'
print(mineral.system)       # 'trigonal'
print(mineral.chemistry)    # 'Al2O3:Cr'
print(mineral.hardness)     # 9
print(mineral.ri)           # '1.762-1.770'
print(mineral.localities)   # ['Myanmar', 'Mozambique', ...]
```

::: mineral_database.get_mineral

### list_presets

List preset names, optionally filtered by crystal system.

```python
from mineral_database import list_presets

# All presets
all_presets = list_presets()

# Filter by system
cubic_presets = list_presets('cubic')
trigonal_presets = list_presets('trigonal')
```

::: mineral_database.list_presets

### list_preset_categories

List all preset categories/tags.

```python
from mineral_database import list_preset_categories

categories = list_preset_categories()
# ['cubic', 'hexagonal', 'trigonal', 'twins', ...]
```

::: mineral_database.list_preset_categories

### search_presets

Full-text search across mineral names and properties.

```python
from mineral_database import search_presets

# Search by name
garnet_matches = search_presets('garnet')

# Search by property
red_gems = search_presets('red')
```

::: mineral_database.search_presets

### filter_minerals

Filter minerals by multiple criteria.

```python
from mineral_database import filter_minerals

# Filter by system and hardness
hard_cubic = filter_minerals(system='cubic', min_hardness=8)

# Filter by optical properties
birefringent = filter_minerals(has_birefringence=True)
```

::: mineral_database.filter_minerals

### get_presets_by_form

Get presets that include a specific crystal form.

```python
from mineral_database import get_presets_by_form

# Get all minerals with octahedral habit
octahedral = get_presets_by_form('octahedron')
```

::: mineral_database.get_presets_by_form

### count_presets

Get total count of presets.

```python
from mineral_database import count_presets

total = count_presets()
print(f"Database contains {total} presets")  # 94+
```

::: mineral_database.count_presets

## Data Classes

### Mineral

Full mineral data object.

```python
from mineral_database import Mineral

@dataclass
class Mineral:
    id: str
    name: str
    cdl: str
    system: str
    point_group: str
    chemistry: Optional[str]
    hardness: Optional[float]
    description: Optional[str]
    sg: Optional[float]
    ri: Optional[str]
    birefringence: Optional[float]
    optical_character: Optional[str]
    dispersion: Optional[float]
    lustre: Optional[str]
    cleavage: Optional[str]
    fracture: Optional[str]
    pleochroism: Optional[str]
    twin_law: Optional[str]
    phenomenon: Optional[str]
    localities: List[str]
    forms: List[str]
    colors: List[str]
    treatments: List[str]
    inclusions: List[str]
```

::: mineral_database.Mineral

## Property Formatting

### INFO_GROUPS

Property groups for display organization.

```python
from mineral_database import INFO_GROUPS

# Groups: 'identification', 'physical', 'optical', 'crystallographic'
for group, props in INFO_GROUPS.items():
    print(f"{group}: {props}")
```

### get_info_properties

Get formatted properties for display.

```python
from mineral_database import get_info_properties

# Get FGA-style properties
props = get_info_properties('ruby', 'fga')
# Returns: {'name': 'Ruby', 'ri': '1.762-1.770', 'sg': 4.0, ...}
```

::: mineral_database.get_info_properties

### get_property_label

Get display label for a property key.

```python
from mineral_database import get_property_label

label = get_property_label('sg')  # 'SG'
label = get_property_label('ri')  # 'RI'
```

::: mineral_database.get_property_label

### format_property_value

Format a property value for display.

```python
from mineral_database import format_property_value

value = format_property_value('sg', 4.0)       # '4.00'
value = format_property_value('hardness', 9)   # '9'
```

::: mineral_database.format_property_value

## Backwards Compatibility

### CRYSTAL_PRESETS

Dict-like interface for legacy code migration.

```python
from mineral_database import CRYSTAL_PRESETS

# Supports all dict operations
preset = CRYSTAL_PRESETS['diamond']
preset = CRYSTAL_PRESETS.get('ruby', None)
'garnet' in CRYSTAL_PRESETS
len(CRYSTAL_PRESETS)
list(CRYSTAL_PRESETS.keys())
list(CRYSTAL_PRESETS.values())
list(CRYSTAL_PRESETS.items())
```

::: mineral_database.CRYSTAL_PRESETS
