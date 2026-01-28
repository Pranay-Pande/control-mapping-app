# Control Mapping Application - API Reference

## Base URL

```
http://localhost:8000
```

## Endpoints

### Upload

#### POST /upload

Upload a compliance framework document.

**Request**
```
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | The compliance document (PDF, CSV, Excel, JSON, TXT) |

**Response** `200 OK`
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "CIS_AWS_Benchmark_v1.4.pdf",
  "file_type": "pdf",
  "size_bytes": 245678,
  "preview": "First 500 characters of extracted text..."
}
```

**Errors**
- `400 Bad Request`: Invalid file type or empty file
- `413 Payload Too Large`: File exceeds maximum size

---

### Configure

#### POST /configure

Configure field mappings and provider for a mapping job.

**Request**
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "framework_name": "CIS AWS Foundations Benchmark",
  "framework_version": "1.4.0",
  "provider": "aws",
  "field_mappings": {
    "id_field": "Recommendation #",
    "name_field": "Title",
    "description_field": "Description",
    "section_field": "Section",
    "subsection_field": "Sub-Section"
  },
  "custom_instructions": "Focus on Level 1 controls only. Skip informational sections."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| upload_id | string | Yes | UUID from /upload response |
| framework_name | string | Yes | Name of the compliance framework |
| framework_version | string | No | Version of the framework |
| provider | string | Yes | Target cloud provider (aws, gcp, azure, kubernetes, m365, github) |
| field_mappings | object | Yes | Mapping of field names in the document |
| custom_instructions | string | No | Additional instructions for Claude |

**Response** `200 OK`
```json
{
  "configuration_id": "660e8400-e29b-41d4-a716-446655440001",
  "provider_valid": true,
  "available_checks": 156
}
```

**Errors**
- `404 Not Found`: Upload ID not found
- `400 Bad Request`: Invalid provider or missing required fields

---

### Mapping

#### POST /map

Start a control mapping job.

**Request**
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "configuration_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**Response** `202 Accepted`
```json
{
  "job_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors**
- `404 Not Found`: Upload or configuration ID not found
- `409 Conflict`: A job is already running for this configuration

---

#### GET /status/{job_id}

Check the status of a mapping job.

**Path Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | string | UUID of the mapping job |

**Response (Pending)** `200 OK`
```json
{
  "job_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "pending",
  "progress_percentage": 0,
  "progress_message": "Waiting to start...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Response (Running)** `200 OK`
```json
{
  "job_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "running",
  "progress_percentage": 45,
  "progress_message": "Processing controls...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:15Z"
}
```

**Response (Completed)** `200 OK`
```json
{
  "job_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "completed",
  "progress_percentage": 100,
  "progress_message": "Mapping completed successfully",
  "summary": {
    "total_controls": 50,
    "controls_with_checks": 47,
    "total_check_mappings": 89,
    "unmapped_controls": 3
  },
  "download_links": {
    "json": "/download/770e8400-e29b-41d4-a716-446655440002/json",
    "excel": "/download/770e8400-e29b-41d4-a716-446655440002/excel"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:22Z"
}
```

**Response (Failed)** `200 OK`
```json
{
  "job_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "failed",
  "progress_percentage": 25,
  "progress_message": "Error during processing",
  "error_message": "Claude Code execution timed out after 600 seconds",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:40:00Z"
}
```

**Errors**
- `404 Not Found`: Job ID not found

---

### Download

#### GET /download/{job_id}/{file_type}

Download the mapping output file.

**Path Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | string | UUID of the completed mapping job |
| file_type | string | Output format: `json` or `excel` |

**Response** `200 OK`
- For `json`: `application/json` file download
- For `excel`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` file download

**Errors**
- `404 Not Found`: Job ID not found or job not completed
- `400 Bad Request`: Invalid file type (must be `json` or `excel`)

---

### Providers

#### GET /providers

List all available cloud providers.

**Response** `200 OK`
```json
{
  "providers": [
    {
      "name": "aws",
      "display_name": "Amazon Web Services",
      "check_count": 156
    },
    {
      "name": "gcp",
      "display_name": "Google Cloud Platform",
      "check_count": 98
    },
    {
      "name": "azure",
      "display_name": "Microsoft Azure",
      "check_count": 124
    },
    {
      "name": "kubernetes",
      "display_name": "Kubernetes",
      "check_count": 45
    }
  ]
}
```

---

#### GET /checks/{provider}

List all security checks for a provider.

**Path Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| provider | string | Provider name (aws, gcp, azure, etc.) |

**Query Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Filter checks by name or description |
| service | string | Filter by service name |
| limit | integer | Max results (default: 100) |
| offset | integer | Pagination offset (default: 0) |

**Response** `200 OK`
```json
{
  "provider": "aws",
  "total": 156,
  "checks": [
    {
      "CheckID": "iam_root_mfa_enabled",
      "CheckTitle": "Ensure MFA is enabled for the root account",
      "ServiceName": "iam",
      "Severity": "critical",
      "Description": "The root account has unrestricted access..."
    },
    {
      "CheckID": "s3_bucket_encryption",
      "CheckTitle": "Ensure S3 buckets have default encryption enabled",
      "ServiceName": "s3",
      "Severity": "high",
      "Description": "S3 buckets should have default encryption..."
    }
  ]
}
```

**Errors**
- `404 Not Found`: Provider not found

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limits

No rate limits are currently implemented for local development. For production deployments, consider adding rate limiting middleware.

## Health Check

#### GET /health

Check application health.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```
