# Display-Apps Integrated Railway Service

This repository now supports a **single-service Railway deployment** that runs the full pipeline end-to-end:

1. Upload one or multiple PDFs
2. Extract text/tables via Tensorlake
3. Transform to KreditLab JSON via Anthropic Claude (system prompt loaded from KreditLab `.txt` instruction files in repo root)
4. Render report HTML
5. Download JSON/HTML (and optional PDF)

## Deploy Root
Deploy from repository root as one Railway service.

## Required environment variables
- `ANTHROPIC_API_KEY` (required)
- `TENSORLAKE_API_KEY` (required)
- `APP_TOKEN` (optional, if set then POST endpoints require `Authorization: Bearer <APP_TOKEN>`)
- `CORS_ALLOW_ORIGINS` (optional comma-separated allowlist; defaults to `*`)
- `ANTHROPIC_MODEL` (optional, default `claude-3-5-sonnet-20241022`; if invalid, app retries with `claude-opus-4-1-20250805`)

## Railway build/run
This repo includes:
- `requirements.txt` (consolidated dependencies)
- `Procfile` start command

Start command used:
```bash
uvicorn app:app --app-dir integrated-app --host 0.0.0.0 --port ${PORT}
```

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --app-dir integrated-app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` for upload UI.

## API endpoints
- `GET /health` -> `{"status":"ok"}`
- `POST /process/pdf`
  - multipart form with `file` (PDF)
  - query params:
    - `return=both|html_only|json_only` (default `both`)
    - `include_pdf=true|false` (default false)
- `POST /process/pdfs`
  - multipart form with `files` (one or many PDFs)
  - query params:
    - `include_pdf=true|false` (default false)
  - returns array with per-file success/error entries
- `POST /render/html`
  - body: `{"data": <kreditlab_json>}`
- `POST /stage/tensorlake`
  - multipart form with `files` (one or many PDFs)
  - returns extraction output per file (`success`/`error`)
- `POST /stage/transform`
  - body: `{"items": [{"filename": "...", "extraction_result": {...}}]}`
  - transforms extracted data to KreditLab JSON per file
- `POST /stage/render`
  - body: `{"items": [{"filename": "...", "kreditlab_json": {...}}], "include_pdf": false}`
  - renders HTML (and optional PDF) per file

## curl examples
```bash
# Health
curl -s http://localhost:8000/health

# Process PDF (token optional, include header only if APP_TOKEN is configured)
curl -X POST "http://localhost:8000/process/pdf?return=both" \
  -H "Authorization: Bearer $APP_TOKEN" \
  -F "file=@/path/to/file.pdf"

# Render HTML from existing JSON
curl -X POST "http://localhost:8000/render/html" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $APP_TOKEN" \
  -d '{"data": {"_schema_info": {}, "company_info": {}, "statement_of_comprehensive_income": {}, "statement_of_financial_position": {}, "analysis_summary": {}}}'
```

## Security notes
- No API keys are hardcoded.
- Secrets are read from environment variables only.
- `.env` is gitignored for local development.
