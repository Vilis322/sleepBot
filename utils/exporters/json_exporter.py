import json
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


class JSONExporter:
    """Exporter for sleep data to JSON format."""

    @staticmethod
    def export(data: list[dict[str, Any]], indent: int = 2) -> str:
        """Export sleep data to JSON string.

        Args:
            data: List of sleep session dictionaries
            indent: JSON indentation level

        Returns:
            JSON string

        Example:
            >>> data = [{"date": "2026-01-01", "duration_hours": 8.5}]
            >>> json_string = JSONExporter.export(data)
        """
        if not data:
            logger.warning("json_export_empty_data")
            return "[]"

        try:
            json_string = json.dumps(data, indent=indent, ensure_ascii=False)
            logger.info("json_export_completed", rows=len(data))
            return json_string
        except Exception as e:
            logger.error("json_export_failed", error=str(e))
            raise

    @staticmethod
    def export_to_bytes(data: list[dict[str, Any]], indent: int = 2) -> bytes:
        """Export sleep data to JSON bytes (for file sending).

        Args:
            data: List of sleep session dictionaries
            indent: JSON indentation level

        Returns:
            JSON data as bytes
        """
        json_string = JSONExporter.export(data, indent=indent)
        return json_string.encode("utf-8")
