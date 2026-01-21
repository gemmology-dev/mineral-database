# Mineral-Database Optimizations & Improvements

**Status**: Pending Implementation
**Priority**: Medium (no blockers, but quality improvements needed)
**Date**: January 2026

---

## Critical Issues

### 1. Type Errors (9 mypy errors)

**Impact**: Blocks strict typing environments, breaks type-aware IDEs.

**Errors by Location**:

| File | Line | Issue |
|------|------|-------|
| `models.py` | 94-102 | List[str] assigned to Union[int, float, str] in to_dict() |
| `db.py` | 326 | Missing return type annotation on get_all_categories() |
| `compat.py` | 49, 51 | List comprehension with potential None values |
| `cli.py` | 83 | Missing type parameter for generic list |

**Proposed Fixes**:

```python
# models.py - Fix to_dict() return type annotation
def to_dict(self) -> dict[str, Any]:
    """Convert to dictionary, excluding None and empty lists."""
    result: dict[str, Any] = {
        'name': self.name,
        'cdl': self.cdl,
        # ... other fields
    }
    # List fields - assign directly without type issues
    if self.localities:
        result['localities'] = self.localities
    return result

# compat.py - Add None filtering
def values(self) -> Iterator[dict[str, Any]]:
    """Return all preset values."""
    return (p for p in (get_preset(k) for k in list_presets()) if p is not None)

# cli.py - Modern type annotation
def main(args: list[str] | None = None) -> int:
```

---

### 2. Ruff Style Issues (77 errors, 77 auto-fixable)

**Categories**:
- 59 errors: Deprecated typing imports (`List` → `list`, `Dict` → `dict`, `Optional[X]` → `X | None`)
- 4 errors: Unsorted/unused imports
- 14 errors: Other modernization issues

**Fix Command**:
```bash
cd workspace/mineral-database
ruff check . --fix
```

---

### 3. CLI Untested (0% coverage)

**Current State**: 94 lines, 0 tests, 0% coverage.

**Proposed Tests**:
```python
# tests/test_cli.py
import pytest
from click.testing import CliRunner
from mineral_database.cli import main

class TestCLI:
    def test_list_all(self):
        runner = CliRunner()
        result = runner.invoke(main, ['list'])
        assert result.exit_code == 0
        assert 'diamond' in result.output

    def test_show_mineral(self):
        runner = CliRunner()
        result = runner.invoke(main, ['show', 'diamond'])
        assert result.exit_code == 0
        assert 'Diamond' in result.output

    def test_search(self):
        runner = CliRunner()
        result = runner.invoke(main, ['search', 'garnet'])
        assert result.exit_code == 0

    def test_show_missing(self):
        runner = CliRunner()
        result = runner.invoke(main, ['show', 'nonexistent'])
        assert result.exit_code == 1
```

---

## Code Quality Improvements

### 4. Category Distinction Issue (compat.py)

**Issue**: Cannot distinguish "empty category" from "missing category".

```python
# Current behavior
presets = PRESET_CATEGORIES.get('nonexistent')  # Returns []
presets = PRESET_CATEGORIES.get('habits')       # Returns [] if empty

# Proposed fix
def get(self, key: str, default: list[str] | None = None) -> list[str] | None:
    """Get presets in category with proper None handling."""
    if key not in self._get_categories():
        return default
    return list_presets(key)

def _get_categories(self) -> set[str]:
    """Get all valid category names."""
    return set(list_preset_categories())
```

---

### 5. Duplicate Hardness Parsing

**Issue**: Hardness parsing appears in two places.

**Locations**:
- `db.py:174-181` - In insert_mineral
- `queries.py:160-166` - In filter_minerals

**Proposed Fix**:
```python
# models.py or new utils.py
def parse_hardness(value: int | float | str) -> float:
    """Extract minimum hardness from value.

    Handles:
    - int/float: return as-is
    - str range: "5-7" → 5.0
    - str single: "6.5" → 6.5
    """
    if isinstance(value, (int, float)):
        return float(value)
    try:
        # Try parsing as range first
        if '-' in value:
            return float(value.split('-')[0])
        return float(value)
    except (ValueError, AttributeError):
        return 0.0
```

---

### 6. Error Handling & Logging

**Issue**: Silent failures, no logging.

**Proposed Improvements**:
```python
import logging

logger = logging.getLogger(__name__)

def search_presets(query: str) -> list[str]:
    """Search presets with logging."""
    try:
        # FTS5 search
        results = _fts_search(query)
        logger.debug(f"FTS5 search for '{query}' returned {len(results)} results")
        return results
    except Exception as e:
        logger.warning(f"FTS5 search failed, falling back to LIKE: {e}")
        return _like_search(query)
```

---

### 7. Query Performance Optimizations

**Issue**: Some queries do unnecessary full scans.

**Current**:
```python
def count_presets() -> int:
    minerals = list(get_all_minerals())
    return len(minerals)

def get_systems() -> list[str]:
    minerals = get_all_minerals()
    return sorted({m.system for m in minerals})
```

**Proposed**:
```python
def count_presets() -> int:
    """Count presets using SQL COUNT."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM minerals")
        return cursor.fetchone()[0]

def get_systems() -> list[str]:
    """Get distinct systems using SQL DISTINCT."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT DISTINCT system FROM minerals ORDER BY system"
        )
        return [row[0] for row in cursor.fetchall()]
```

---

## Data Validation

### 8. CDL Validation Integration

**Issue**: CDL notation not validated against cdl-parser.

**Proposed**:
```python
# Optional validation during database build
def validate_mineral_data(mineral: Mineral) -> list[str]:
    """Validate mineral data, return list of issues."""
    issues = []

    # Validate CDL if parser available
    try:
        from cdl_parser import parse_cdl
        try:
            parse_cdl(mineral.cdl)
        except Exception as e:
            issues.append(f"Invalid CDL: {e}")
    except ImportError:
        pass  # cdl-parser not installed, skip validation

    # Validate point group
    VALID_POINT_GROUPS = {'m3m', '-43m', '432', ...}  # 32 groups
    if mineral.point_group not in VALID_POINT_GROUPS:
        issues.append(f"Invalid point group: {mineral.point_group}")

    return issues
```

---

## Test Coverage Improvements

### 9. Missing Test Categories

**Current Coverage**: 61% (380 statements, 131 missed)

**Recommended Additional Tests**:

| Category | Tests Needed |
|----------|--------------|
| CLI | Full command coverage |
| Error Conditions | Invalid inputs, missing files |
| Database Schema | Schema integrity, FTS5 triggers |
| Edge Cases | Empty results, special characters |
| Performance | Benchmark queries on full dataset |

**Example Error Condition Tests**:
```python
class TestErrorConditions:
    def test_get_preset_none(self):
        """Test getting non-existent preset returns None."""
        result = get_preset('nonexistent_mineral')
        assert result is None

    def test_search_special_characters(self):
        """Test search with SQL injection attempt."""
        results = search_presets("'; DROP TABLE minerals; --")
        assert isinstance(results, list)  # Should not raise

    def test_filter_invalid_hardness(self):
        """Test filtering with invalid hardness values."""
        results = filter_minerals(min_hardness=-1, max_hardness=100)
        assert isinstance(results, list)
```

---

## Documentation Gaps

### 10. Missing Documentation

| Document | Purpose | Priority |
|----------|---------|----------|
| `ARCHITECTURE.md` | Data model and design decisions | Medium |
| `MIGRATION.md` | Guide for crystal_presets.py users | High |
| `TROUBLESHOOTING.md` | Common issues and solutions | Low |
| API reference | Generated from docstrings | Medium |

**Proposed MIGRATION.md Structure**:
```markdown
# Migrating from crystal_presets.py

## Quick Migration

Replace:
```python
from crystal_presets import CRYSTAL_PRESETS, PRESET_CATEGORIES
```

With:
```python
from mineral_database.compat import CRYSTAL_PRESETS, PRESET_CATEGORIES
```

## Full Migration (Recommended)

Use the new query API:
```python
from mineral_database import get_preset, list_presets, search_presets
```
```

---

## CDL v2 Preparation

### 11. Support for Amorphous Materials

**Current State**: Database has 1 amorphous preset (opal).

**Needed for CDL v2**:
- Add more amorphous materials (obsidian, amber, tektite, moldavite)
- Add `form_type` column: 'crystalline', 'amorphous', 'cryptocrystalline'
- Update schema for amorphous-specific properties (void percentage, etc.)

---

### 12. Twin Law Enhancements

**Current**: 12 twin laws as simple strings.

**Proposed Schema Extension**:
```sql
CREATE TABLE twin_laws (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    axis TEXT,           -- e.g., '[111]', '[001]'
    angle REAL,          -- rotation angle in degrees
    type TEXT,           -- 'contact', 'penetration', 'polysynthetic'
    systems TEXT         -- JSON array of valid crystal systems
);
```

---

### 13. Growth Habit Support

**For CDL v2 Features** (scepter, phantom, skeletal, etc.):

**Proposed Schema Extension**:
```sql
ALTER TABLE minerals ADD COLUMN habit_type TEXT;
-- Values: 'normal', 'scepter', 'phantom', 'skeletal', 'elestial', 'faden'

ALTER TABLE minerals ADD COLUMN growth_pattern TEXT;
-- JSON describing growth zones, phantom layers, etc.
```

---

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| P0 | Fix 9 mypy errors | 2 hours | Unblocks strict typing |
| P0 | Run `ruff check --fix` | 10 min | Code style compliance |
| P1 | Add CLI tests | 2 hours | 100% test coverage |
| P1 | Consolidate hardness parsing | 1 hour | Code quality |
| P2 | Add logging | 1 hour | Debuggability |
| P2 | Optimize count/systems queries | 30 min | Performance |
| P2 | Create MIGRATION.md | 2 hours | User adoption |
| P3 | CDL v2 schema extensions | 1 week | Future features |

---

## Verification Checklist

After implementing fixes:

- [ ] All 34 existing tests pass
- [ ] mypy passes with zero errors
- [ ] ruff check passes with zero errors
- [ ] CLI tests added and passing
- [ ] Coverage > 80%
- [ ] MIGRATION.md created
- [ ] No performance regression

---

*Document created: 2026-01-20*
