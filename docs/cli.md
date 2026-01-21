# CLI Usage

The `mineral-db` command-line tool provides access to the mineral database.

## Installation

The CLI is installed automatically with the package:

```bash
pip install gemmology-mineral-database
```

## Commands

### List Presets

List all mineral presets:

```bash
mineral-db --list
```

Output:
```
Available Presets (94):
  diamond
  ruby
  sapphire
  emerald
  garnet
  ...
```

List presets by crystal system:

```bash
mineral-db --list cubic
```

Output:
```
Cubic Presets (25):
  diamond
  garnet
  fluorite
  pyrite
  spinel
  ...
```

### Show Preset Info

Display detailed information about a preset:

```bash
mineral-db --info diamond
```

Output:
```
Diamond
=======
CDL: cubic[m3m]:{111}@1.0 + {110}@0.2
System: cubic
Point Group: m3m
Chemistry: C
Hardness: 10

Physical Properties:
  SG: 3.52
  Lustre: adamantine
  Cleavage: perfect {111}

Optical Properties:
  RI: 2.417
  Dispersion: 0.044

Localities:
  - South Africa
  - Russia
  - Botswana
  - Australia
```

### Search Presets

Search presets by keyword:

```bash
mineral-db --search garnet
```

Output:
```
Search Results for 'garnet' (6):
  garnet        - Garnet group (general)
  pyrope        - Pyrope garnet
  almandine     - Almandine garnet
  spessartine   - Spessartine garnet
  grossular     - Grossular garnet
  andradite     - Andradite garnet
```

### JSON Output

Output preset data as JSON:

```bash
mineral-db --json ruby
```

Output:
```json
{
  "id": "ruby",
  "name": "Ruby",
  "cdl": "trigonal[-3m]:{10-10}@1.0 + {10-11}@0.8",
  "system": "trigonal",
  "point_group": "-3m",
  "chemistry": "Al2O3:Cr",
  "hardness": 9,
  "sg": 4.0,
  "ri": "1.762-1.770",
  "birefringence": 0.008,
  "optical_character": "uniaxial negative",
  "localities": ["Myanmar", "Mozambique", "Thailand", "Sri Lanka"]
}
```

### Show Categories

List all preset categories:

```bash
mineral-db --categories
```

Output:
```
Categories:
  cubic (25)
  hexagonal (8)
  trigonal (15)
  tetragonal (5)
  orthorhombic (10)
  monoclinic (10)
  triclinic (5)
  twins (15)
```

## Examples

### Filtering by System

```bash
# List all trigonal minerals
mineral-db --list trigonal

# Get info on quartz
mineral-db --info quartz
```

### Searching for Properties

```bash
# Find minerals with asterism
mineral-db --search asterism

# Find minerals from Myanmar
mineral-db --search Myanmar
```

### Scripting

Use with shell scripting:

```bash
# Export all presets to JSON
for preset in $(mineral-db --list | tail -n +2); do
    mineral-db --json "$preset" > "presets/${preset}.json"
done
```

Process JSON output with jq:

```bash
# Get all CDL strings for cubic minerals
mineral-db --list cubic | tail -n +2 | while read preset; do
    mineral-db --json "$preset" | jq -r '.cdl'
done
```

### Integration with Other Tools

Use CDL strings with crystal-renderer:

```bash
# Get CDL and render
cdl=$(mineral-db --json diamond | jq -r '.cdl')
echo "CDL: $cdl"
# Use with crystal-renderer Python API
```
