"""
Tests for the Mineral Database CLI.
"""

import json

import pytest

from mineral_database.cli import create_parser, main


class TestCLIParser:
    """Tests for CLI argument parsing."""

    def test_create_parser(self):
        """Parser should be created successfully."""
        parser = create_parser()
        assert parser.prog == "mineral-db"

    def test_parser_help(self, capsys):
        """Parser should include help information."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])
        captured = capsys.readouterr()
        assert "Mineral Database" in captured.out


class TestCountCommand:
    """Tests for --count command."""

    def test_count_presets(self, capsys):
        """Count command should return total presets."""
        result = main(["--count"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Total presets:" in captured.out
        # Should have at least some presets
        assert int(captured.out.split(":")[1].strip()) > 0


class TestCategoriesCommand:
    """Tests for --categories command."""

    def test_list_categories(self, capsys):
        """Categories command should list all categories."""
        result = main(["--categories"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Preset Categories:" in captured.out
        # Should include crystal systems
        assert "cubic" in captured.out.lower()


class TestListCommand:
    """Tests for --list command."""

    def test_list_all(self, capsys):
        """List all presets."""
        result = main(["--list"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Crystal Presets" in captured.out

    def test_list_by_category(self, capsys):
        """List presets by category."""
        result = main(["--list", "cubic"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Cubic Presets:" in captured.out
        # Should include diamond
        assert "diamond" in captured.out.lower()

    def test_list_invalid_category(self, capsys):
        """List with invalid category returns message."""
        result = main(["--list", "nonexistent"])
        assert result == 0
        captured = capsys.readouterr()
        assert "No presets found" in captured.out


class TestInfoCommand:
    """Tests for --info command."""

    def test_info_valid_preset(self, capsys):
        """Info command shows preset details."""
        result = main(["--info", "diamond-octahedron"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Preset: diamond-octahedron" in captured.out
        assert "Name:" in captured.out
        assert "CDL:" in captured.out
        assert "System:" in captured.out
        assert "cubic" in captured.out.lower()

    def test_info_invalid_preset(self, capsys):
        """Info command with invalid preset returns error."""
        result = main(["--info", "nonexistent"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Preset not found" in captured.out


class TestSearchCommand:
    """Tests for --search command."""

    def test_search_matches(self, capsys):
        """Search command finds matching presets."""
        result = main(["--search", "garnet"])
        assert result == 0
        captured = capsys.readouterr()
        assert "matching" in captured.out.lower()

    def test_search_no_matches(self, capsys):
        """Search with no matches returns message."""
        result = main(["--search", "xyznonexistent123"])
        assert result == 0
        captured = capsys.readouterr()
        assert "No presets found" in captured.out


class TestJsonCommand:
    """Tests for --json command."""

    def test_json_valid_preset(self, capsys):
        """JSON command outputs valid JSON."""
        result = main(["--json", "diamond-octahedron"])
        assert result == 0
        captured = capsys.readouterr()
        # Should be valid JSON
        data = json.loads(captured.out)
        assert "name" in data
        assert "cdl" in data
        assert "system" in data

    def test_json_invalid_preset(self, capsys):
        """JSON command with invalid preset returns error JSON."""
        result = main(["--json", "nonexistent"])
        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "error" in data


class TestDefaultBehavior:
    """Tests for default CLI behavior."""

    def test_no_args_shows_help(self, capsys):
        """No arguments shows help."""
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "Mineral Database" in captured.out
