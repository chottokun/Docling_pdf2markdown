# API Reference

Language: [English](API_REFERENCE.md) | [日本語](../API_REFERENCE.md)

API specifications for the Docling Markdown Conversion Server powered by FastAPI, along with usage guides for various programming languages.

---

## 📌 Table of Contents
1. [Overview & Configuration](#1-overview--configuration)
2. [Document Conversion Endpoint (`POST /convert/`)](#2-document-conversion-endpoint-post-convert)
3. [File Download Endpoint (`GET /download/{request_id}/{filename}`)](#3-file-download-endpoint-get-downloadrequest_idfilename)
4. [Health Check Endpoint (`GET /`)](#4-health-check-endpoint-get-)
5. [Prometheus Metrics Endpoint (`GET /metrics`)](#5-prometheus-metrics-endpoint-get-metrics)
6. [Client Usage Examples (cURL / Python / JavaScript)](#6-client-usage-examples-curl--python--javascript)
7. [Error Responses](#7-error-responses)
8. [Security & Concurrency Control](#8-security--concurrency-control)

---

## 1. Overview & Configuration

This API server allows users to upload various documents such as PDF, Word, Excel, and PowerPoint, converting them into RAG-optimized structured Markdown, extracted images, and table data (HTML/Markdown).

### Base URL
- **Local Direct (uvicorn)**: `http://localhost:8000`
- **Docker Compose**: `http://localhost:8090` *(mapped via port 8090:8000 in docker-compose.yml)*

### Authentication
When the server environment variable `DOCLING_API_KEY` is configured, all requests require the following HTTP header:
```http
X-API-Key: your_configured_api_key
```

---

## 2. Document Conversion Endpoint (`POST /convert/`)

Submits a document file along with conversion option parameters to execute the Markdown conversion pipeline.

- **Method**: `POST`
- **Path**: `/convert/`
- **Content-Type**: `multipart/form-data`
- **Headers**:
  - `X-API-Key` (Optional / Required if configured): API key

### Request Parameters (Form Data)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `file` **(Required)** | File | - | Input file (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.html`, etc.) |
| `table_format` | string | `"html"` | Output format for tables (`html` or `markdown`) |
| `include_page_breaks` | boolean | `false` | Insert page break markers `<!-- PAGE_BREAK: Page N -->` |
| `include_kv_extraction` | boolean | `false` | Include key-value extraction metadata section |
| `vlm_enabled` | boolean | `false` | Enable automated caption generation via Vision-Language Model (VLM) |
| `vlm_provider` | string | `"ollama"` | VLM provider (`ollama`, `openai`, `gemini`, `anthropic`, `vllm`, etc.) |
| `vlm_api_key` | string | `""` | VLM API Key (when using authenticated providers) |
| `vlm_model` | string | `"qwen2-vl:2b"` | Name of the VLM model to use |
| `vlm_prompt` | string | *Default prompt* | Prompt instructions for image captioning |
| `vlm_max_concurrent` | integer | `5` | Maximum concurrent request limit for VLM API |
| `num_threads` | integer | `4` | CPU threads for computation |
| `cuda_use_flash_attention` | boolean | `false` | Enable FlashAttention2 (supported GPU environments only) |
| `math_inline_delim` | string | `"auto"` | Inline LaTeX math delimiter (`"auto"`, `"$"`, `"\("`, etc.) |
| `math_block_delim` | string | `"auto"` | Block LaTeX math delimiter (`"auto"`, `"$$"`, `"\["`, etc.) |
| `math_block_newline` | string | `"auto"` | Control inner newlines in math blocks (`"auto"`, `"true"`, `"false"`) |

### Success Response (200 OK)
```json
{
  "message": "Conversion successful",
  "markdown_file": "processed_document.md",
  "output_id": "8f3b2a1c9d4e5f60",
  "download_url": "/download/8f3b2a1c9d4e5f60/processed_document.md"
}
```

---

## 3. File Download Endpoint (`GET /download/{request_id}/{filename}`)

Retrieves converted assets (Markdown files or extracted image files).

- **Method**: `GET`
- **Path**: `/download/{request_id}/{filename}`
- **Path Parameters**:
  - `request_id`: Unique string ID (`output_id`) returned in the `/convert/` response
  - `filename`: Target filename to retrieve (`processed_document.md` or `images/picture_1.png`, etc.)

### Success Response (200 OK)
Returns binary or text stream of the requested file.

---

## 4. Health Check Endpoint (`GET /`)

Checks server status.

- **Method**: `GET`
- **Path**: `/`

### Success Response (200 OK)
```json
{
  "message": "Welcome to the Docling Markdown Conversion Server"
}
```

---

## 5. Prometheus Metrics Endpoint (`GET /metrics`)

Returns system and performance metrics in plain text format compatible with Prometheus.

- **Method**: `GET`
- **Path**: `/metrics`

### Main Metrics
- `docling_conversions_total{status="success|error"}`: Total document conversion request count
- `docling_active_conversions`: Currently active conversion worker processes
- `docling_conversion_duration_seconds_count` / `_sum`: Conversion duration histogram
- `docling_vlm_requests_total{provider="...", status="..."}`: VLM image caption request count
- `docling_vlm_retry_total{provider="..."}`: VLM API retry attempts during transient failures

---

## 6. Client Usage Examples (cURL / Python / JavaScript)

### cURL Example

#### Basic Conversion Request
```bash
curl -X POST "http://localhost:8090/convert/" \
  -F "file=@/path/to/document.pdf"
```

#### Authenticated Request with Options
```bash
curl -X POST "http://localhost:8090/convert/" \
  -H "X-API-Key: your_secret_key" \
  -F "file=@/path/to/financial_report.xlsx" \
  -F "table_format=html" \
  -F "include_page_breaks=true" \
  -F "math_block_newline=true"
```

#### Downloading Results
```bash
curl -H "X-API-Key: your_secret_key" \
  -o result.md \
  "http://localhost:8090/download/8f3b2a1c9d4e5f60/processed_document.md"
```

---

### Python (httpx) Example

```python
import httpx

API_BASE_URL = "http://localhost:8090"
API_KEY = "your_secret_key"  # Set to None if unauthenticated

headers = {}
if API_KEY:
    headers["X-API-Key"] = API_KEY

# 1. Conversion Request
with open("sample.pdf", "rb") as f:
    files = {"file": ("sample.pdf", f, "application/pdf")}
    data = {
        "table_format": "html",
        "include_page_breaks": "true",
    }
    response = httpx.post(f"{API_BASE_URL}/convert/", headers=headers, files=files, data=data)
    response.raise_for_status()

result = response.json()
print("Conversion Response:", result)

# 2. Markdown Download
download_url = f"{API_BASE_URL}{result['download_url']}"
dl_response = httpx.get(download_url, headers=headers)
dl_response.raise_for_status()

with open(result["markdown_file"], "w", encoding="utf-8") as out_f:
    out_f.write(dl_response.text)

print(f"Saved to {result['markdown_file']}")
```

---

### JavaScript (Fetch / Node.js) Example

```javascript
const fs = require('fs');
const FormData = require('form-data');
const fetch = require('node-fetch');

async function convertDocument() {
  const form = new FormData();
  form.append('file', fs.createReadStream('sample.pdf'));
  form.append('table_format', 'html');

  // 1. Conversion Request
  const res = await fetch('http://localhost:8090/convert/', {
    method: 'POST',
    body: form,
    headers: {
      ...form.getHeaders(),
      // 'X-API-Key': 'your_secret_key'
    }
  });

  if (!res.ok) {
    throw new Error(`HTTP Error: ${res.status}`);
  }

  const result = await res.json();
  console.log('Result:', result);

  // 2. Download
  const dlRes = await fetch(`http://localhost:8090${result.download_url}`);
  const markdownText = await dlRes.text();
  fs.writeFileSync(result.markdown_file, markdownText);
}

convertDocument().catch(console.error);
```

---

## 7. Error Responses

| HTTP Status | Error Description | Example Response | Resolution |
|---|---|---|---|
| **400 Bad Request** | Unsupported extension / Invalid argument | `{"detail": "Unsupported file format. Supported: ['.pdf', '.docx', ...]"}` | Upload file with an allowed file extension |
| **401 Unauthorized** | Missing or invalid API key | `{"detail": "Invalid or missing API Key."}` | Provide correct `X-API-Key` in request header |
| **404 Not Found** | File does not exist / Path traversal attempt | `{"detail": "File not found."}` | Verify `request_id` and `filename` |
| **413 Payload Too Large** | File size exceeds maximum threshold | `{"detail": "Payload Too Large. Maximum size is 52428800 bytes."}` | Upload file within `MAX_UPLOAD_SIZE` (default 20MB) |
| **429 Too Many Requests** | Rate limit exceeded | `{"detail": "Too Many Requests. Please try again later."}` | Wait for window reset (1 minute) before retrying |
| **500 Internal Server Error** | Server internal processing error | `{"detail": "An internal error occurred during conversion."}` | Inspect server application logs |

---

## 8. Security & Concurrency Control

- **Path Traversal Protection**: Traversal characters (`../`) in `request_id` and `filename` are automatically rejected using absolute path verification (`is_relative_to`).
- **Dynamic Semaphore Control**: Dynamically limits concurrent heavy worker processes based on available system RAM to prevent Out-of-Memory (OOM) crashes.
- **IP Spoofing Mitigation**: Evaluates `X-Forwarded-For` proxy chains only when requests originate from verified trusted proxies (`TRUSTED_PROXIES`).
- **Prometheus Observability**: Promotes monitoring of conversion counts, active process gauges, latencies, and VLM retries via `/metrics`.
