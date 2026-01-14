"""Mock tests for data exporters."""

import csv
import json
from io import StringIO

import pytest

from utils.exporters.csv_exporter import CSVExporter
from utils.exporters.json_exporter import JSONExporter


class TestCSVExporter:
    """Test CSV exporter functionality."""

    def test_export_empty_data(self):
        """Test exporting empty data returns empty string."""
        data = []
        result = CSVExporter.export(data)

        assert result == ""

    def test_export_single_record(self):
        """Test exporting single record."""
        data = [
            {
                "date": "2026-01-13",
                "sleep_start": "2026-01-13 22:00:00",
                "sleep_end": "2026-01-14 06:00:00",
                "duration_hours": 8.0,
                "quality_rating": 8.5,
                "note": "Good sleep",
            }
        ]

        result = CSVExporter.export(data)

        assert result != ""
        assert "date,sleep_start,sleep_end,duration_hours,quality_rating,note" in result
        assert "2026-01-13" in result
        assert "8.0" in result
        assert "Good sleep" in result

    def test_export_multiple_records(self):
        """Test exporting multiple records."""
        data = [
            {
                "date": "2026-01-13",
                "duration_hours": 8.0,
                "quality_rating": 8.5,
            },
            {
                "date": "2026-01-14",
                "duration_hours": 7.5,
                "quality_rating": 7.0,
            },
        ]

        result = CSVExporter.export(data)

        # Parse CSV to verify structure
        csv_file = StringIO(result)
        reader = csv.DictReader(csv_file)
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["date"] == "2026-01-13"
        assert rows[0]["duration_hours"] == "8.0"
        assert rows[1]["date"] == "2026-01-14"

    def test_export_with_special_characters(self):
        """Test exporting data with special characters in notes."""
        data = [
            {
                "date": "2026-01-13",
                "note": 'Had "great" sleep, felt amazing!',
            }
        ]

        result = CSVExporter.export(data)

        assert result != ""
        # CSV should properly escape quotes
        assert "great" in result

    def test_export_with_unicode(self):
        """Test exporting data with unicode characters."""
        data = [
            {
                "date": "2026-01-13",
                "note": "Отличный сон 😴",
            }
        ]

        result = CSVExporter.export(data)

        assert result != ""
        assert "Отличный сон" in result

    def test_export_to_bytes_empty(self):
        """Test converting empty CSV to bytes."""
        data = []
        result = CSVExporter.export_to_bytes(data)

        assert isinstance(result, bytes)
        assert result == b""

    def test_export_to_bytes_with_data(self):
        """Test converting CSV to bytes."""
        data = [
            {
                "date": "2026-01-13",
                "duration_hours": 8.0,
            }
        ]

        result = CSVExporter.export_to_bytes(data)

        assert isinstance(result, bytes)
        assert b"date,duration_hours" in result
        assert b"2026-01-13" in result

    def test_export_preserves_field_order(self):
        """Test that export preserves field order from first record."""
        data = [
            {
                "date": "2026-01-13",
                "duration_hours": 8.0,
                "quality_rating": 8.5,
            }
        ]

        result = CSVExporter.export(data)

        # Check that header matches the order of keys in dict
        lines = result.strip().split("\n")
        header = lines[0]
        assert header.startswith("date")


class TestJSONExporter:
    """Test JSON exporter functionality."""

    def test_export_empty_data(self):
        """Test exporting empty data returns empty array."""
        data = []
        result = JSONExporter.export(data)

        assert result == "[]"

    def test_export_single_record(self):
        """Test exporting single record."""
        data = [
            {
                "date": "2026-01-13",
                "sleep_start": "2026-01-13 22:00:00",
                "sleep_end": "2026-01-14 06:00:00",
                "duration_hours": 8.0,
                "quality_rating": 8.5,
                "note": "Good sleep",
            }
        ]

        result = JSONExporter.export(data)

        # Parse JSON to verify structure
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["date"] == "2026-01-13"
        assert parsed[0]["duration_hours"] == 8.0
        assert parsed[0]["quality_rating"] == 8.5
        assert parsed[0]["note"] == "Good sleep"

    def test_export_multiple_records(self):
        """Test exporting multiple records."""
        data = [
            {
                "date": "2026-01-13",
                "duration_hours": 8.0,
            },
            {
                "date": "2026-01-14",
                "duration_hours": 7.5,
            },
        ]

        result = JSONExporter.export(data)

        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["date"] == "2026-01-13"
        assert parsed[1]["date"] == "2026-01-14"

    def test_export_with_unicode(self):
        """Test exporting data with unicode characters."""
        data = [
            {
                "date": "2026-01-13",
                "note": "Отличный сон 😴 中文",
            }
        ]

        result = JSONExporter.export(data)

        parsed = json.loads(result)
        assert parsed[0]["note"] == "Отличный сон 😴 中文"

    def test_export_with_custom_indent(self):
        """Test exporting with custom indentation."""
        data = [{"date": "2026-01-13"}]

        result_2 = JSONExporter.export(data, indent=2)
        result_4 = JSONExporter.export(data, indent=4)

        # Both should be valid JSON
        json.loads(result_2)
        json.loads(result_4)

        # Different indentation should produce different lengths
        assert len(result_2) != len(result_4)

    def test_export_to_bytes_empty(self):
        """Test converting empty JSON to bytes."""
        data = []
        result = JSONExporter.export_to_bytes(data)

        assert isinstance(result, bytes)
        assert result == b"[]"

    def test_export_to_bytes_with_data(self):
        """Test converting JSON to bytes."""
        data = [
            {
                "date": "2026-01-13",
                "duration_hours": 8.0,
            }
        ]

        result = JSONExporter.export_to_bytes(data)

        assert isinstance(result, bytes)
        assert b'"date"' in result
        assert b"2026-01-13" in result

    def test_export_handles_special_types(self):
        """Test that export handles various data types correctly."""
        data = [
            {
                "string": "text",
                "integer": 42,
                "float": 3.14,
                "boolean": True,
                "null": None,
            }
        ]

        result = JSONExporter.export(data)

        parsed = json.loads(result)
        assert parsed[0]["string"] == "text"
        assert parsed[0]["integer"] == 42
        assert parsed[0]["float"] == 3.14
        assert parsed[0]["boolean"] is True
        assert parsed[0]["null"] is None

    def test_export_preserves_dict_structure(self):
        """Test that nested structures are preserved (if any)."""
        data = [
            {
                "date": "2026-01-13",
                "metadata": {
                    "source": "mobile",
                    "version": "1.0",
                },
            }
        ]

        result = JSONExporter.export(data)

        parsed = json.loads(result)
        assert "metadata" in parsed[0]
        assert parsed[0]["metadata"]["source"] == "mobile"
