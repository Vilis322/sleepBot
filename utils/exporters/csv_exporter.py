import csv
from io import StringIO
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


class CSVExporter:
    """Exporter for sleep data to CSV format."""

    @staticmethod
    def export(data: list[dict[str, Any]]) -> str:
        """Export sleep data to CSV string.

        Args:
            data: List of sleep session dictionaries

        Returns:
            CSV string

        Example:
            >>> data = [{"date": "2026-01-01", "duration_hours": 8.5}]
            >>> csv_string = CSVExporter.export(data)
        """
        if not data:
            logger.warning("csv_export_empty_data")
            return ""

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())

        # Write header
        writer.writeheader()

        # Write rows
        for row in data:
            writer.writerow(row)

        csv_string = output.getvalue()
        output.close()

        logger.info("csv_export_completed", rows=len(data))
        return csv_string

    @staticmethod
    def export_to_bytes(data: list[dict[str, Any]]) -> bytes:
        """Export sleep data to CSV bytes (for file sending).

        Args:
            data: List of sleep session dictionaries

        Returns:
            CSV data as bytes
        """
        csv_string = CSVExporter.export(data)
        return csv_string.encode("utf-8")
