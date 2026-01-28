"""
Builds prompts for Claude Code mapping operations.
"""
from pathlib import Path
from typing import Optional

from app.core.constants import get_provider_display_name


class PromptBuilder:
    """Constructs prompts for Claude Code with proper context injection."""

    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self._load_templates()

    def _load_templates(self):
        """Load prompt templates from files."""
        system_file = self.prompts_dir / "system_prompt.txt"
        mapping_file = self.prompts_dir / "mapping_instruction.txt"
        output_file = self.prompts_dir / "output_format.json"

        self.system_template = system_file.read_text(encoding='utf-8') if system_file.exists() else ""
        self.mapping_template = mapping_file.read_text(encoding='utf-8') if mapping_file.exists() else ""
        self.output_format = output_file.read_text(encoding='utf-8') if output_file.exists() else "{}"

    def _format_field_mappings(self, field_mappings: dict, enable_subgroup: bool = True) -> str:
        """Format field mappings for prompt inclusion."""
        if not field_mappings:
            return "Use your best judgment to identify control fields in the document."

        lines = ["The document uses the following field structure:"]

        # Map field keys to their labels and corresponding format example keys
        field_config = {
            "id_field": ("Control ID", "id_format_example"),
            "name_field": ("Control Name", "name_format_example"),
            "description_field": ("Description", "description_format_example"),
            "section_field": ("Section", "section_format_example"),
            "subsection_field": ("SubSection", "subsection_format_example"),
            "subgroup_field": ("SubGroup", "subgroup_format_example"),
            "service_field": ("Service", None)
        }

        for field_key, (label, format_key) in field_config.items():
            # Skip SubGroup if disabled
            if field_key == "subgroup_field" and not enable_subgroup:
                continue

            value = field_mappings.get(field_key)
            if value:
                line = f"- {label} is in the field/column: \"{value}\""
                # Add format example if provided
                if format_key:
                    format_example = field_mappings.get(format_key)
                    if format_example:
                        line += f". IMPORTANT: Follow this exact format pattern: \"{format_example}\" (preserve numbering, prefixes, and exact formatting)"
                lines.append(line)

        return "\n".join(lines)

    def build_prompt(
        self,
        framework_name: str,
        framework_version: str,
        provider: str,
        file_path: str,
        field_mappings: dict,
        custom_instructions: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Build system prompt and user prompt for mapping.

        Args:
            framework_name: Name of the compliance framework
            framework_version: Version of the framework
            provider: Target cloud provider
            file_path: Path to the uploaded framework document
            field_mappings: Dictionary of field mappings
            custom_instructions: Optional additional instructions

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Format field mappings
        field_text = self._format_field_mappings(field_mappings)

        # Build user prompt from template
        user_prompt = self.mapping_template.format(
            provider=provider,
            framework_name=framework_name,
            framework_version=framework_version or "Not specified",
            file_path=file_path,
            field_mappings=field_text,
            custom_instructions=custom_instructions or "None provided.",
            output_format=self.output_format
        )

        return self.system_template, user_prompt

    def build_simple_prompt(
        self,
        framework_name: str,
        framework_version: str,
        provider: str,
        framework_content: str,
        checks_list: str,
        field_mappings: dict,
        custom_instructions: Optional[str] = None,
        framework_full_name: Optional[str] = None,
        framework_description: Optional[str] = None,
        enable_subgroup: bool = True
    ) -> str:
        """
        Build a single comprehensive prompt (alternative approach).

        This version embeds the content directly rather than asking Claude
        to read files. Useful for smaller documents.

        Returns:
            Single prompt string
        """
        field_text = self._format_field_mappings(field_mappings, enable_subgroup)
        # Get standardized provider display name
        provider_display = get_provider_display_name(provider)

        # Build framework info section
        framework_info = f"""- Framework (short name): {framework_name}
- Version: {framework_version or "Not specified"}
- Provider Target: {provider_display}"""

        if framework_full_name:
            framework_info += f"\n- Full Name: {framework_full_name}"

        # Build the Name field instruction
        name_instruction = ""
        if framework_full_name:
            name_instruction = f'8. The "Name" field in the output JSON MUST be exactly: "{framework_full_name}"'
        else:
            name_instruction = '8. The "Name" field should be a full descriptive name of the framework extracted from the document'

        # Build SubGroup instruction based on enable_subgroup setting
        if enable_subgroup:
            subgroup_instruction = '9. Include the "SubGroup" field for sub-sections (e.g., 4.1, 4.2, 4.3 under a parent section 4). Each sub-section should be a separate entry in the Requirements array.'
        else:
            subgroup_instruction = '''9. DO NOT include the "SubGroup" field in the output JSON - omit it entirely from each requirement object.
10. IMPORTANT: Do NOT create separate entries for sub-sections (like 4.1, 4.2, 4.3). Instead, merge all sub-sections into their parent control (e.g., section 4). Combine all checks from sub-sections into the parent control's Checks array.'''

        # Build Description instruction
        if framework_description:
            description_instruction = f'11. The "Description" field in the output JSON MUST be exactly: "{framework_description}"'
        else:
            description_instruction = '11. The "Description" field should be a concise description of this mapping generated from the document context'

        prompt = f"""# Control Mapping Task

## Objective
Map compliance controls from the framework document to {provider_display} security checks.

## Framework Information
{framework_info}

## Framework Document Content
```
{framework_content[:50000]}
```

## Field Mapping Instructions
{field_text}

## Available Security Checks for {provider_display}
{checks_list}

## Additional Instructions
{custom_instructions or "None provided."}

## Required Output Format
Return a JSON object with this exact structure:

{self.output_format}

CRITICAL INSTRUCTIONS:
1. In the "Checks" array, use the exact CheckID values from the list above
2. Output ONLY valid JSON - no explanatory text before or after
3. If no suitable check exists for a control, leave the Checks array empty
4. PRESERVE EXACT FORMAT: For Section, SubSection, Id, and Name fields, copy the EXACT text from the document INCLUDING:
   - Number prefixes (e.g., "2.0 Security Domain Policies" NOT just "Security Domain Policies")
   - Original punctuation and formatting
   - Full hierarchy indicators (e.g., "2.1.1" not just the text)
5. The Id field should be the control identifier exactly as it appears in the document
6. Section and SubSection should include their full identifiers/numbers as shown in the document
7. The "Provider" field in the output JSON MUST be exactly: "{provider_display}"
{name_instruction}
{subgroup_instruction}
{description_instruction}

Analyze the framework and output the mapping JSON:
"""
        return prompt


# Singleton instance
_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """Get the singleton prompt builder instance."""
    global _builder
    if _builder is None:
        from app.config import get_settings
        settings = get_settings()
        _builder = PromptBuilder(settings.prompts_dir)
    return _builder
