# Control Mapping Application - Project Specification

## Overview

A full-stack application that maps compliance framework controls to cloud provider security checks using Claude Code CLI as the AI backend.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web UI        │────▶│   FastAPI       │────▶│  Claude Code    │
│   (HTML/JS)     │     │   Backend       │     │  CLI            │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                        │
                              ▼                        ▼
                        ┌───────────┐           ┌───────────┐
                        │  SQLite   │           │ providers/│
                        │  Database │           │ (checks)  │
                        └───────────┘           └───────────┘
```

## Key Components

### 1. Input Processing
- **Supported Formats**: PDF, CSV, Excel (.xlsx, .xls), JSON, TXT
- **Field Mapping**: User defines which fields contain:
  - Control ID
  - Control Name
  - Description
  - Section/SubSection
- **Max File Size**: 10MB

### 2. Claude Code Integration
- **Method**: Subprocess invocation of Claude Code CLI
- **Tools Allowed**: Read, Glob (for file access)
- **Timeout**: 10 minutes per job
- **Output**: Structured JSON mapping

### 3. Check Repository
- **Location**: `providers/` folder at project root
- **Structure**: `providers/{provider}/services/{service}/{check_id}/{check_id}_metadata.json`
- **Supported Providers**: aws, gcp, azure, kubernetes, m365, github

### 4. Output Formats

#### JSON Output
```json
{
  "Framework": "CIS AWS Foundations Benchmark",
  "Name": "CIS Amazon Web Services Foundations Benchmark",
  "Version": "1.4.0",
  "Provider": "aws",
  "Description": "Mapping of CIS AWS controls to security checks",
  "Requirements": [
    {
      "Id": "1.1",
      "Name": "Avoid the use of root account",
      "Description": "The root account has unrestricted access...",
      "Attributes": [
        {
          "ItemId": "1.1",
          "Section": "Identity and Access Management",
          "SubSection": "IAM Policies",
          "SubGroup": "",
          "Service": "iam"
        }
      ],
      "Checks": ["iam_root_user_no_access_keys", "iam_root_mfa_enabled"]
    }
  ]
}
```

#### Excel Output
| Control ID | Name | Description | Section | SubSection | Checks |
|------------|------|-------------|---------|------------|--------|
| 1.1 | Avoid root account | The root account... | IAM | IAM Policies | iam_root_user_no_access_keys, iam_root_mfa_enabled |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.10+, FastAPI |
| Database | SQLite with aiosqlite |
| AI Engine | Claude Code CLI (subprocess) |
| File Processing | pdfplumber, pandas, openpyxl |
| Frontend | HTML, CSS, JavaScript |
| Export | xlsxwriter (Excel), json (JSON) |

## Data Flow

```mermaid
flowchart LR
    A[Upload File] --> B[Extract Text]
    B --> C[Configure Mapping]
    C --> D[Build Prompt]
    D --> E[Claude Code CLI]
    E --> F[Parse JSON Output]
    F --> G[Generate Excel]
    G --> H[Download Files]
```

## Job States

| State | Description |
|-------|-------------|
| pending | Job created, waiting to start |
| running | Claude Code is processing |
| completed | Mapping finished successfully |
| failed | Error occurred during processing |

## File Structure

```
Control Mapping app/
├── app/                    # Python application
│   ├── api/               # FastAPI endpoints
│   ├── core/              # Claude integration, job manager
│   ├── services/          # Business logic
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   └── utils/             # Helpers
├── providers/             # Check definitions (user-provided)
├── prompts/               # Claude prompt templates
├── storage/               # Runtime data (uploads, outputs, db)
├── static/                # Web UI files
├── docs/                  # Documentation
└── tests/                 # Test suite
```

## Security Considerations

1. **File Validation**: Strict file type checking by content, not just extension
2. **Path Traversal**: Sanitized file names for uploads
3. **Claude Permissions**: Read-only tools (Read, Glob) only
4. **Upload Location**: Files stored outside web-accessible directories

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite connection string | `sqlite+aiosqlite:///./storage/jobs.db` |
| `UPLOAD_DIR` | Upload file storage | `./storage/uploads` |
| `OUTPUT_DIR` | Generated file storage | `./storage/outputs` |
| `PROVIDERS_DIR` | Check definitions path | `./providers` |
| `CLAUDE_TIMEOUT` | Max Claude execution time (sec) | `600` |
| `MAX_UPLOAD_SIZE` | Max upload file size (bytes) | `10485760` |

## Dependencies

See `requirements.txt` for full list. Key dependencies:
- fastapi >= 0.109.0
- uvicorn >= 0.27.0
- sqlalchemy >= 2.0.0
- pdfplumber >= 0.10.0
- pandas >= 2.0.0
- xlsxwriter >= 3.1.0
