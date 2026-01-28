# Control Mapping Application - Prompt Templates

This document describes the prompt templates used to interact with Claude Code CLI for control mapping.

## Overview

The application uses two prompts:
1. **System Prompt**: Sets Claude's role and rules
2. **Mapping Instruction**: Contains the actual task with context

## File Locations

- System Prompt: `prompts/system_prompt.txt`
- Mapping Instruction: `prompts/mapping_instruction.txt`
- Output Format: `prompts/output_format.json`

## System Prompt

```
You are an expert compliance mapping assistant. Your task is to analyze
compliance framework controls and map them to cloud provider security checks.

RULES:
1. Only use check IDs from the provided list - never invent IDs
2. A control may map to multiple checks for complete coverage
3. If no suitable check exists, leave the Checks array empty
4. Extract control metadata exactly as written in the source
5. Preserve original control IDs and hierarchy
6. Output ONLY valid JSON - no explanatory text before or after

You have access to Read and Glob tools to examine files if needed.
```

## Mapping Instruction Template

The mapping instruction is dynamically generated with the following placeholders:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{provider}` | Target cloud provider | `aws` |
| `{framework_name}` | Name of compliance framework | `CIS AWS Foundations Benchmark` |
| `{framework_version}` | Framework version | `1.4.0` |
| `{file_path}` | Path to uploaded document | `storage/uploads/abc123.pdf` |
| `{field_mappings}` | User-defined field mappings | See below |
| `{custom_instructions}` | Additional user instructions | `Focus on Level 1 controls` |
| `{output_format}` | JSON structure template | See output_format.json |

### Field Mappings Format

The `{field_mappings}` placeholder is replaced with user-configured mappings:

```
The document uses the following field structure:
- Control ID is in the field/column: "Recommendation #"
- Control Name is in the field/column: "Title"
- Description is in the field/column: "Description"
- Section is in the field/column: "Section"
- SubSection is in the field/column: "Sub-Section"
```

## Full Prompt Example

When executed, Claude receives a prompt like this:

```
# Control Mapping Task

## Objective
Map compliance controls from the framework document to aws security checks.

## Framework Information
- Name: CIS AWS Foundations Benchmark
- Version: 1.4.0
- Provider Target: aws

## Source Document
The framework document is located at: storage/uploads/550e8400.pdf
Please read and analyze this file to extract all controls.

## Field Mapping Instructions
The document uses the following field structure:
- Control ID is in the field/column: "Recommendation #"
- Control Name is in the field/column: "Title"
- Description is in the field/column: "Description"
- Section is in the field/column: "Section"

## Available Security Checks
The checks are stored in: providers/aws/services/
Browse this folder recursively to find all *_metadata.json files.

Each check metadata file contains:
- CheckID: The identifier to use in the "Checks" array
- CheckTitle: Human-readable check name
- Description: What the check verifies
- ServiceName: Target cloud service
- Severity: Check severity level
- Categories: Grouping categories

## Additional Instructions
Focus on Level 1 controls only. Skip informational sections.

## Required Output Format
Return a JSON object with this exact structure:

{
  "Framework": "CIS AWS Foundations Benchmark",
  "Name": "Full framework name",
  "Version": "1.4.0",
  "Provider": "aws",
  "Description": "Brief description of this mapping",
  "Requirements": [
    {
      "Id": "control_id",
      "Name": "Control Name with full description",
      "Description": "Detailed description from the framework",
      "Attributes": [
        {
          "ItemId": "control_id",
          "Section": "Section Name (XX)",
          "SubSection": "SubSection Name (XX-X)",
          "SubGroup": "Optional grouping",
          "Service": "service_name"
        }
      ],
      "Checks": ["check_id_1", "check_id_2"]
    }
  ]
}

IMPORTANT: In the "Checks" array, use the exact "CheckID" values from the metadata files.

Begin by reading the framework document, then browse the providers/aws/services/
folder recursively, and finally output the mapping JSON.
```

## Claude Code CLI Invocation

The prompt is sent to Claude Code CLI with these flags:

```bash
claude --print --output-format json --allowedTools "Read,Glob" "PROMPT_HERE"
```

| Flag | Purpose |
|------|---------|
| `--print` | Output to stdout instead of interactive mode |
| `--output-format json` | Request JSON-formatted response |
| `--allowedTools "Read,Glob"` | Restrict to read-only file operations |

## Prompt Builder Code

The prompt is built in `app/core/prompt_builder.py`:

```python
class PromptBuilder:
    def build_prompt(
        self,
        framework_name: str,
        framework_version: str,
        provider: str,
        file_path: str,
        field_mappings: dict,
        custom_instructions: str = ""
    ) -> tuple[str, str]:
        """
        Returns (system_prompt, user_prompt)
        """
        # Load templates
        system_prompt = self._load_template("system_prompt.txt")
        mapping_template = self._load_template("mapping_instruction.txt")
        output_format = self._load_template("output_format.json")

        # Format field mappings
        field_text = self._format_field_mappings(field_mappings)

        # Build user prompt
        user_prompt = mapping_template.format(
            provider=provider,
            framework_name=framework_name,
            framework_version=framework_version,
            file_path=file_path,
            field_mappings=field_text,
            custom_instructions=custom_instructions or "None provided.",
            output_format=output_format
        )

        return system_prompt, user_prompt
```

## Customization

### Adding Custom Instructions

Users can provide additional instructions via the API:

```json
{
  "custom_instructions": "Focus on Level 1 controls only. Ignore any controls marked as 'optional'. Map storage-related controls to S3 checks where applicable."
}
```

### Modifying Templates

To modify the default behavior, edit the files in `prompts/`:

1. `system_prompt.txt` - Change Claude's role or add rules
2. `mapping_instruction.txt` - Modify the task structure
3. `output_format.json` - Change the output JSON structure

**Warning**: Changing `output_format.json` may require updates to the export service to handle the new structure.
