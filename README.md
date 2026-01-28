# Control Mapping Application

A full-stack application that maps compliance framework controls to cloud provider security checks using Claude Code CLI as the AI backend.

## Features

### Core Features
- **Multi-format Input**: Upload compliance documents in PDF, CSV, Excel, JSON, or TXT format (max 10MB)
- **Intelligent AI Mapping**: Uses Claude Code to analyze controls and map them to security checks
- **Multiple Providers**: Supports AWS, GCP, Azure, Kubernetes, M365, GitHub, OracleCloud, NHN, and AlibabaCloud
- **Multi-Provider Selection**: Select multiple providers at once to generate separate mappings for each
- **Batch Processing**: One mapping job per provider, executed sequentially
- **Dual Output Formats**: Download mappings in JSON or Excel format
- **ZIP Download**: Download all provider mappings at once as a ZIP archive

### Configuration Options
- **Framework Full Name**: Custom full name for the framework (or let Claude generate one)
- **Framework Description**: Custom description for the mapping output
- **Field Mappings**: Tell Claude which columns/fields contain your control data
- **Format Examples**: Provide example formats for each field to ensure Claude follows exact patterns
- **SubGroup Toggle**: Enable/disable SubGroup field - when disabled, sub-sections are merged into parent controls
- **Custom Instructions**: Additional guidance for Claude during mapping

### Interface
- **Web UI**: Simple 4-step wizard interface
- **REST API**: Full API for programmatic access

## Prerequisites

- Python 3.10+
- Claude Code CLI installed and configured (`claude` command available in PATH)
- Your provider check definitions in the `providers/` folder

## Installation

1. Clone or download this repository

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Copy and configure the environment file:
   ```bash
   cp .env.example .env
   ```
   The `.env` file is optional - the application uses sensible defaults.

5. Add your check definitions to the `providers/` folder (see structure below)

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```

Or run directly:
```bash
python -m app.main
```

Then open http://localhost:8000 in your browser.

## Usage Guide (4-Step Wizard)

### Step 1: Upload
- Drag and drop your compliance framework document
- Supported formats: PDF, CSV, Excel (.xlsx, .xls), JSON, TXT
- Maximum file size: 10MB
- A preview of the extracted content will be shown

### Step 2: Configure
Configure your mapping settings:

| Field | Required | Description |
|-------|----------|-------------|
| Framework Name | Yes | Short identifier (e.g., "IRDAI", "CIS_AWS") |
| Version | No | Framework version (e.g., "1.4.0") |
| Framework Full Name | No | Descriptive name for output. If not provided, Claude generates one |
| Framework Description | No | Custom description for the mapping output |
| Target Providers | Yes | Select one or more cloud providers (use "Select All" for all) |
| Enable SubGroup | Yes | Toggle to include/exclude SubGroup field in output |

**Field Mappings** (all optional):
- Control ID Field + ID Format Example
- Control Name Field + Name Format Example
- Section Field + Section Format Example
- SubSection Field + SubSection Format Example
- SubGroup Field + SubGroup Format Example (only if SubGroup enabled)
- Description Field + Description Format Example
- Service Field
- Additional Instructions

### Step 3: Map
- Review your configuration summary
- Click "Start Mapping" to begin
- Watch real-time progress for each provider
- Jobs run sequentially (one provider at a time)

### Step 4: Download
- View mapping statistics (total controls, controls with checks, providers)
- **Download All (ZIP)**: Get all provider mappings in a single archive
- **Download by Provider**: Download individual JSON or Excel files

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload compliance document (multipart/form-data) |
| `/configure` | POST | Configure field mappings and providers |
| `/map` | POST | Start mapping jobs (returns batch_id) |
| `/batch/{batch_id}/status` | GET | Check batch status (all providers) |
| `/status/{job_id}` | GET | Check individual job status |
| `/download/{job_id}/json` | GET | Download JSON output for a job |
| `/download/{job_id}/excel` | GET | Download Excel output for a job |
| `/download/batch/{batch_id}/zip` | GET | Download all outputs as ZIP |
| `/providers` | GET | List available providers with check counts |
| `/checks/{provider}` | GET | List checks for a provider |

### API Usage Example

```bash
# 1. Upload file
curl -X POST -F "file=@compliance_framework.pdf" http://localhost:8000/upload
# Returns: {"upload_id": "...", "filename": "...", "preview": "..."}

# 2. Configure mapping
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "upload_id": "YOUR_UPLOAD_ID",
    "framework_name": "CIS_AWS",
    "framework_version": "1.4.0",
    "framework_full_name": "CIS Amazon Web Services Foundations Benchmark",
    "framework_description": "Mapping of CIS AWS controls to security checks",
    "providers": ["aws", "gcp"],
    "enable_subgroup": true,
    "field_mappings": {
      "id_field": "Control ID",
      "id_format_example": "1.1.1",
      "section_field": "Section",
      "section_format_example": "1. Identity and Access Management"
    }
  }' \
  http://localhost:8000/configure
# Returns: {"configuration_id": "...", "providers": [...], "total_checks": 500}

# 3. Start mapping
curl -X POST -H "Content-Type: application/json" \
  -d '{"upload_id": "YOUR_UPLOAD_ID", "configuration_id": "YOUR_CONFIG_ID"}' \
  http://localhost:8000/map
# Returns: {"batch_id": "...", "job_ids": [...], "jobs": [...]}

# 4. Check batch status
curl http://localhost:8000/batch/YOUR_BATCH_ID/status
# Returns: {"status": "completed", "overall_progress": 100, "jobs": [...]}

# 5. Download outputs
curl -O http://localhost:8000/download/batch/YOUR_BATCH_ID/zip
# Or individual files:
curl -O http://localhost:8000/download/YOUR_JOB_ID/json
curl -O http://localhost:8000/download/YOUR_JOB_ID/excel
```

## Output JSON Format

```json
{
  "Framework": "CIS_AWS",
  "Name": "CIS Amazon Web Services Foundations Benchmark",
  "Version": "1.4.0",
  "Provider": "AWS",
  "Description": "Mapping of CIS AWS controls to security checks",
  "Requirements": [
    {
      "Id": "1.1",
      "Name": "Avoid the use of root account",
      "Description": "The root account has unrestricted access to all resources...",
      "Attributes": [
        {
          "ItemId": "1.1",
          "Section": "1. Identity and Access Management",
          "SubSection": "1.1 IAM Policies",
          "SubGroup": "1.1.1 Root Account",
          "Service": "iam"
        }
      ],
      "Checks": ["iam_root_user_no_access_keys", "iam_root_mfa_enabled"]
    }
  ]
}
```

**Note**: The `SubGroup` field is only included when "Enable SubGroup" is checked during configuration.

## Check File Structure

```
providers/
├── aws/
│   └── services/
│       ├── iam/
│       │   └── iam_root_mfa_enabled/
│       │       └── iam_root_mfa_enabled_metadata.json
│       └── s3/
│           └── s3_bucket_encryption/
│               └── s3_bucket_encryption_metadata.json
├── gcp/
│   └── services/
│       └── ...
├── azure/
│   └── services/
│       └── ...
└── kubernetes/
    └── services/
        └── ...
```

Each check file (`*.metadata.json`) should have this format:
```json
{
  "Provider": "aws",
  "CheckID": "iam_root_mfa_enabled",
  "CheckTitle": "Ensure MFA is enabled for root account",
  "ServiceName": "iam",
  "Severity": "critical",
  "Description": "The root account has unrestricted access..."
}
```

## Project Structure

```
Control Mapping app/
├── app/                        # Python application
│   ├── api/                    # FastAPI endpoints
│   │   └── endpoints/          # Individual endpoint modules
│   │       ├── upload.py       # File upload handling
│   │       ├── configure.py    # Configuration management
│   │       ├── mapping.py      # Job creation and status
│   │       ├── download.py     # File downloads (incl. ZIP)
│   │       └── providers.py    # Provider/check listing
│   ├── core/                   # Core functionality
│   │   ├── claude_runner.py    # Claude Code CLI integration
│   │   ├── job_manager.py      # Background job execution
│   │   ├── prompt_builder.py   # AI prompt construction
│   │   └── constants.py        # Provider display names
│   ├── services/               # Business logic
│   │   ├── check_repository.py # Check file discovery
│   │   ├── export_service.py   # JSON/Excel generation
│   │   └── file_processor.py   # Document text extraction
│   ├── models/                 # Database models (SQLAlchemy)
│   │   ├── job.py              # Upload, Configuration, Batch, Job
│   │   ├── database.py         # Database connection
│   │   └── enums.py            # Status enums
│   └── schemas/                # Pydantic schemas (API contracts)
├── providers/                  # Check definitions (add your own)
├── prompts/                    # Claude prompt templates
│   └── output_format.json      # Expected output structure
├── storage/                    # Runtime data (auto-created)
│   ├── uploads/                # Uploaded files
│   ├── outputs/                # Generated JSON/Excel files
│   └── jobs.db                 # SQLite database
├── static/                     # Web UI files
│   ├── index.html              # Main HTML page
│   ├── css/styles.css          # Styling
│   └── js/app.js               # Frontend JavaScript
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
└── .env.example                # Environment variables template
```

## Troubleshooting

### Claude Code CLI not found
Ensure Claude Code CLI is installed and the `claude` command is available in your PATH:
```bash
claude --version
```

### Database errors after code updates
If you see errors about missing columns, delete the database and restart:
```bash
rm storage/jobs.db  # On Windows: del storage\jobs.db
uvicorn app.main:app --reload
```

### File upload fails
- Check file size is under 10MB
- Ensure file format is supported (PDF, CSV, Excel, JSON, TXT)
- Check the `storage/uploads/` directory has write permissions

### No providers available
- Ensure check definition files exist in `providers/` folder
- Check files follow the `*_metadata.json` naming pattern
- Verify JSON format is valid

### Mapping produces no checks
- Review Claude's output in the generated JSON file
- Ensure check definitions exist for the selected provider
- Try providing more specific field mappings and format examples
- Add custom instructions to guide Claude better

### Job stuck in "running" state
- Check Claude Code CLI is responding: `claude --version`
- Check server logs for errors
- Restart the server to clear the job manager state

## Environment Variables

All variables are optional with sensible defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVIDERS_DIR` | `providers` | Directory containing check definitions |
| `PROMPTS_DIR` | `prompts` | Directory containing prompt templates |
| `STORAGE_DIR` | `storage` | Directory for uploads, outputs, database |
| `DATABASE_URL` | `sqlite+aiosqlite:///storage/jobs.db` | Database connection string |

## Documentation

- [PROJECT_SPEC.md](docs/PROJECT_SPEC.md) - Full requirements specification
- [API_REFERENCE.md](docs/API_REFERENCE.md) - Detailed API documentation
- [PROMPT_TEMPLATE.md](docs/PROMPT_TEMPLATE.md) - Claude prompt templates

## License

MIT
