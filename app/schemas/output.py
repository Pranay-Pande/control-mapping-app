"""
Pydantic schemas for mapping output format.
"""
from pydantic import BaseModel
from typing import Optional, List


class Attribute(BaseModel):
    """Control attribute within a requirement."""
    ItemId: str
    Section: str
    SubSection: Optional[str] = None
    SubGroup: Optional[str] = None
    Service: Optional[str] = None


class Requirement(BaseModel):
    """A single requirement/control in the mapping."""
    Id: str
    Name: str
    Description: Optional[str] = None
    Attributes: List[Attribute]
    Checks: List[str]


class MappingOutput(BaseModel):
    """Complete mapping output structure."""
    Framework: str
    Name: str
    Version: Optional[str] = None
    Provider: str
    Description: Optional[str] = None
    Requirements: List[Requirement]

    def get_summary(self) -> dict:
        """Generate summary statistics for the mapping."""
        total_controls = len(self.Requirements)
        controls_with_checks = sum(1 for r in self.Requirements if r.Checks)
        total_check_mappings = sum(len(r.Checks) for r in self.Requirements)
        unmapped_controls = total_controls - controls_with_checks

        return {
            "total_controls": total_controls,
            "controls_with_checks": controls_with_checks,
            "total_check_mappings": total_check_mappings,
            "unmapped_controls": unmapped_controls
        }
