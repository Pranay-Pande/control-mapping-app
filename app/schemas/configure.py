"""
Pydantic schemas for configuration operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class FieldMappings(BaseModel):
    """Field mappings for document parsing."""
    # Field/column names
    id_field: Optional[str] = Field(None, description="Column/field containing control ID")
    name_field: Optional[str] = Field(None, description="Column/field containing control name")
    description_field: Optional[str] = Field(None, description="Column/field containing description")
    section_field: Optional[str] = Field(None, description="Column/field containing section")
    subsection_field: Optional[str] = Field(None, description="Column/field containing subsection")
    subgroup_field: Optional[str] = Field(None, description="Column/field containing subgroup")
    service_field: Optional[str] = Field(None, description="Column/field containing service name")

    # Format examples - show Claude the exact format pattern to follow
    id_format_example: Optional[str] = Field(None, description="Example format: 'irdai_2_1' or 'AC-2.1'")
    name_format_example: Optional[str] = Field(None, description="Example format for control names")
    section_format_example: Optional[str] = Field(None, description="Example format: '2.0 Security Domain Policies'")
    subsection_format_example: Optional[str] = Field(None, description="Example format: '2.1 Data Classification'")
    subgroup_format_example: Optional[str] = Field(None, description="Example format: '2.1.1 Password Requirements'")
    description_format_example: Optional[str] = Field(None, description="Example format for descriptions")


class ConfigureRequest(BaseModel):
    """Request to configure a mapping job."""
    upload_id: str = Field(..., description="UUID of the uploaded file")
    framework_name: str = Field(..., description="Short name of the compliance framework (e.g., IRDAI, CIS_AWS)")
    framework_version: Optional[str] = Field(None, description="Version of the framework")
    framework_full_name: Optional[str] = Field(None, description="Full descriptive name of the framework")
    framework_description: Optional[str] = Field(None, description="Custom description for this mapping")
    providers: List[str] = Field(..., description="Target cloud providers (aws, gcp, azure, etc.)")
    enable_subgroup: bool = Field(True, description="Whether to include SubGroup field in output")
    field_mappings: FieldMappings = Field(default_factory=FieldMappings)
    custom_instructions: Optional[str] = Field(None, description="Additional instructions for Claude")


class ProviderInfo(BaseModel):
    """Information about a configured provider."""
    name: str
    check_count: int


class ConfigureResponse(BaseModel):
    """Response after successful configuration."""
    configuration_id: str
    providers: List[ProviderInfo]
    total_checks: int

    class Config:
        from_attributes = True
