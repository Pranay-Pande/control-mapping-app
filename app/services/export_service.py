"""
Service for exporting mapping results to JSON and Excel formats.
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
import xlsxwriter
from app.schemas.output import MappingOutput


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use in filename."""
    # Replace spaces and special characters with underscores
    name = re.sub(r'[^\w\-]', '_', name)
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    return name.strip('_')


class ExportService:
    """Service for exporting mapping outputs."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_filename(
        self,
        job_id: str,
        extension: str,
        framework_name: Optional[str] = None,
        provider: Optional[str] = None
    ) -> str:
        """
        Generate filename for output file.

        If framework_name and provider are provided, uses format:
        {framework}_{provider}.{ext}

        Otherwise uses job_id.
        """
        if framework_name and provider:
            safe_framework = sanitize_filename(framework_name)
            safe_provider = sanitize_filename(provider)
            return f"{safe_framework}_{safe_provider}.{extension}"
        return f"{job_id}.{extension}"

    async def export_json(
        self,
        job_id: str,
        mapping_result: Dict[str, Any],
        framework_name: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Path:
        """
        Export mapping result to JSON file.

        Args:
            job_id: Unique job identifier
            mapping_result: The mapping output dictionary
            framework_name: Optional framework name for filename
            provider: Optional provider name for filename

        Returns:
            Path to the created JSON file
        """
        filename = self._get_filename(job_id, "json", framework_name, provider)
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_result, f, indent=2, ensure_ascii=False)

        return output_path

    async def export_excel(
        self,
        job_id: str,
        mapping_result: Dict[str, Any],
        framework_name: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Path:
        """
        Export mapping result to Excel file.

        Args:
            job_id: Unique job identifier
            mapping_result: The mapping output dictionary
            framework_name: Optional framework name for filename
            provider: Optional provider name for filename

        Returns:
            Path to the created Excel file
        """
        filename = self._get_filename(job_id, "xlsx", framework_name, provider)
        output_path = self.output_dir / filename

        workbook = xlsxwriter.Workbook(str(output_path))

        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        cell_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'top'
        })

        # Summary sheet
        summary_sheet = workbook.add_worksheet("Summary")
        summary_data = [
            ("Framework", mapping_result.get("Framework", "")),
            ("Name", mapping_result.get("Name", "")),
            ("Version", mapping_result.get("Version", "")),
            ("Provider", mapping_result.get("Provider", "")),
            ("Description", mapping_result.get("Description", "")),
            ("Total Requirements", len(mapping_result.get("Requirements", []))),
        ]

        for row, (label, value) in enumerate(summary_data):
            summary_sheet.write(row, 0, label, header_format)
            summary_sheet.write(row, 1, str(value), cell_format)

        summary_sheet.set_column(0, 0, 20)
        summary_sheet.set_column(1, 1, 60)

        # Requirements sheet
        req_sheet = workbook.add_worksheet("Requirements")

        headers = ["Control ID", "Name", "Description", "Section", "SubSection", "Service", "Checks"]
        for col, header in enumerate(headers):
            req_sheet.write(0, col, header, header_format)

        row = 1
        for req in mapping_result.get("Requirements", []):
            req_sheet.write(row, 0, req.get("Id", ""), cell_format)
            req_sheet.write(row, 1, req.get("Name", ""), cell_format)
            req_sheet.write(row, 2, req.get("Description", ""), cell_format)

            # Extract attributes (use first if multiple)
            attrs = req.get("Attributes", [{}])
            attr = attrs[0] if attrs else {}

            req_sheet.write(row, 3, attr.get("Section", ""), cell_format)
            req_sheet.write(row, 4, attr.get("SubSection", ""), cell_format)
            req_sheet.write(row, 5, attr.get("Service", ""), cell_format)

            # Join checks with comma
            checks = ", ".join(req.get("Checks", []))
            req_sheet.write(row, 6, checks, cell_format)

            row += 1

        # Set column widths
        req_sheet.set_column(0, 0, 15)  # Control ID
        req_sheet.set_column(1, 1, 40)  # Name
        req_sheet.set_column(2, 2, 50)  # Description
        req_sheet.set_column(3, 3, 25)  # Section
        req_sheet.set_column(4, 4, 25)  # SubSection
        req_sheet.set_column(5, 5, 15)  # Service
        req_sheet.set_column(6, 6, 50)  # Checks

        # Checks sheet (detailed)
        checks_sheet = workbook.add_worksheet("Check Mappings")

        check_headers = ["Control ID", "Control Name", "Check ID"]
        for col, header in enumerate(check_headers):
            checks_sheet.write(0, col, header, header_format)

        row = 1
        for req in mapping_result.get("Requirements", []):
            control_id = req.get("Id", "")
            control_name = req.get("Name", "")

            for check_id in req.get("Checks", []):
                checks_sheet.write(row, 0, control_id, cell_format)
                checks_sheet.write(row, 1, control_name, cell_format)
                checks_sheet.write(row, 2, check_id, cell_format)
                row += 1

        checks_sheet.set_column(0, 0, 15)
        checks_sheet.set_column(1, 1, 50)
        checks_sheet.set_column(2, 2, 40)

        workbook.close()
        return output_path


# Singleton instance
_export_service: ExportService = None


def get_export_service() -> ExportService:
    """Get the singleton export service instance."""
    global _export_service
    if _export_service is None:
        from app.config import get_settings
        settings = get_settings()
        _export_service = ExportService(settings.output_dir)
    return _export_service
