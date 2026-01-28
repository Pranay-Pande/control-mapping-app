"""
Multi-format file processing for compliance documents.
"""
from pathlib import Path
from typing import Protocol, Optional
import json
import pdfplumber
import pandas as pd
from app.models.enums import FileType


class FileProcessor(Protocol):
    """Protocol for file processors."""

    def extract_text(self, file_path: Path) -> str:
        """Extract text content from file."""
        ...

    def get_structure(self, file_path: Path) -> dict:
        """Get structural information about the file."""
        ...


class PDFProcessor:
    """Processor for PDF files."""

    def extract_text(self, file_path: Path) -> str:
        """Extract text from all pages of a PDF."""
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def get_structure(self, file_path: Path) -> dict:
        """Get PDF structure information."""
        with pdfplumber.open(file_path) as pdf:
            return {
                "pages": len(pdf.pages),
                "has_tables": any(p.extract_tables() for p in pdf.pages[:5])  # Check first 5 pages
            }


class CSVProcessor:
    """Processor for CSV files."""

    def extract_text(self, file_path: Path) -> str:
        """Extract text from CSV as formatted table."""
        df = pd.read_csv(file_path)
        return df.to_string(index=False)

    def get_structure(self, file_path: Path) -> dict:
        """Get CSV structure information."""
        df = pd.read_csv(file_path)
        return {
            "columns": list(df.columns),
            "row_count": len(df),
            "sample_rows": df.head(3).to_dict(orient="records")
        }


class ExcelProcessor:
    """Processor for Excel files (.xlsx, .xls)."""

    def extract_text(self, file_path: Path) -> str:
        """Extract text from all sheets in Excel file."""
        dfs = pd.read_excel(file_path, sheet_name=None)
        parts = []
        for sheet_name, df in dfs.items():
            parts.append(f"=== Sheet: {sheet_name} ===\n{df.to_string(index=False)}")
        return "\n\n".join(parts)

    def get_structure(self, file_path: Path) -> dict:
        """Get Excel structure information."""
        dfs = pd.read_excel(file_path, sheet_name=None)
        sheets = {}
        for sheet_name, df in dfs.items():
            sheets[sheet_name] = {
                "columns": list(df.columns),
                "row_count": len(df)
            }
        return {"sheets": sheets}


class JSONProcessor:
    """Processor for JSON files."""

    def extract_text(self, file_path: Path) -> str:
        """Extract text from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, indent=2)

    def get_structure(self, file_path: Path) -> dict:
        """Get JSON structure information."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return {"type": "array", "length": len(data)}
        elif isinstance(data, dict):
            return {"type": "object", "keys": list(data.keys())[:20]}
        else:
            return {"type": type(data).__name__}


class TextProcessor:
    """Processor for plain text files."""

    def extract_text(self, file_path: Path) -> str:
        """Extract text from text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_structure(self, file_path: Path) -> dict:
        """Get text file structure information."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        return {
            "line_count": len(lines),
            "char_count": len(content)
        }


class FileProcessorFactory:
    """Factory for creating file processors based on file type."""

    _processors = {
        FileType.PDF: PDFProcessor,
        FileType.CSV: CSVProcessor,
        FileType.XLSX: ExcelProcessor,
        FileType.XLS: ExcelProcessor,
        FileType.JSON: JSONProcessor,
        FileType.TXT: TextProcessor,
    }

    _extension_map = {
        ".pdf": FileType.PDF,
        ".csv": FileType.CSV,
        ".xlsx": FileType.XLSX,
        ".xls": FileType.XLS,
        ".json": FileType.JSON,
        ".txt": FileType.TXT,
    }

    @classmethod
    def get_file_type(cls, file_path: Path) -> FileType:
        """Determine file type from extension."""
        suffix = file_path.suffix.lower()
        if suffix not in cls._extension_map:
            raise ValueError(f"Unsupported file type: {suffix}")
        return cls._extension_map[suffix]

    @classmethod
    def get_processor(cls, file_path: Path) -> FileProcessor:
        """Get appropriate processor for file type."""
        file_type = cls.get_file_type(file_path)
        processor_class = cls._processors.get(file_type)
        if not processor_class:
            raise ValueError(f"No processor for file type: {file_type}")
        return processor_class()

    @classmethod
    def process_file(cls, file_path: Path) -> tuple[str, str, dict]:
        """
        Process a file and return extracted content.

        Returns:
            (extracted_text, preview, structure)
        """
        processor = cls.get_processor(file_path)

        # Extract text
        text = processor.extract_text(file_path)

        # Create preview (first 500 chars)
        preview = text[:500] + "..." if len(text) > 500 else text

        # Get structure
        structure = processor.get_structure(file_path)

        return text, preview, structure
