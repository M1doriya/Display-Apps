# Display-Apps Integrated Railway Service

This repository provides a **single-service FastAPI app** for turning uploaded financial PDFs into KreditLab-style outputs.

At a high level, the app has three processing stages:

1. **Extraction (Tensorlake only)**
2. **Transformation (API/LLM logic = source of truth)**
3. **Rendering (HTML/PDF output only)**

The default end-to-end endpoint (`/process/pdf`) runs all three stages in sequence.

---

## How the app behaves (authoritative flow)

The intended business flow for one case is:

1. User uploads **one or more** financial PDFs.
2. Tensorlake extracts content from each file (**extraction only, not authoritative**).
3. The transform stage combines and maps extracted content into **one canonical case-level KreditLab JSON**.
4. The renderer produces HTML (and optional PDF) **from canonical JSON only**.

### Key behavior rules

- **Single source of truth:** all financial logic should live in the transform/API stage.
- **Renderer has no inference logic:** it should only format provided canonical data.
- **Missing is not zero:** unknown/missing values should remain missing (or flagged), not auto-filled with `0`.
- **Multi-file uploads are one case:** files should be reconciled together when producing the final case-level view.
- **Narrative must match data:** report commentary should not claim data is missing if fields are present.

---

## Current endpoint behavior

### 1) End-to-end processing

- `POST /process/pdf`
  - Input: single PDF (`file`)
  - Output options via `return=both|html_only|json_only`
  - Optional `include_pdf=true` to return base64 PDF output
  - Runs: extract -> transform -> render for that file

- `POST /process/pdfs`
  - Input: multiple PDFs (`files`)
  - Returns **per-file** processing results (`results[]`) today
  - Optional `include_pdf=true`

> Note: if you need strict **single-case, multi-file canonical output**, use staged processing and pass all extraction items together into `/stage/transform`.

### 2) Staged processing

- `POST /stage/tensorlake`
  - Input: one or many PDFs (`files`)
  - Output: extraction payload per file (`success` / `error`)

- `POST /stage/transform`
  - Input body: `{"items": [{"filename": "...", "extraction_result": {...}}]}`
  - With one item: returns transformed KreditLab JSON for that file
  - With multiple items: performs a **combined transform** and returns one `combined-report` JSON

- `POST /stage/render`
  - Input body: `{"items": [{"filename": "...", "kreditlab_json": {...}}], "include_pdf": false}`
  - Renders HTML (and optional PDF) for each provided JSON item

- `POST /stage/merge-render`
  - Input body: same structure as `/stage/render`
  - Merges multiple KreditLab JSON records and renders one merged report

### 3) Utility endpoints

- `GET /` -> Upload UI
- `GET /health` -> `{"status": "ok"}`
- `POST /render/html` -> render HTML from provided JSON payload

---

## Recommended production usage

For multi-document cases, prefer this pattern:

1. Upload all files to `/stage/tensorlake`
2. Send all extraction results together to `/stage/transform`
3. Render only the returned canonical JSON (`/stage/render` or `/render/html`)

This keeps one canonical case-level JSON and avoids mixing raw extraction with rendered logic.

---

## Deploy root

Deploy from repository root as one Railway service.

## Required environment variables

- `ANTHROPIC_API_KEY` (required)
- `TENSORLAKE_API_KEY` (required)
- `APP_TOKEN` (optional; if set, POST endpoints require `Authorization: Bearer <APP_TOKEN>`)
- `CORS_ALLOW_ORIGINS` (optional comma-separated allowlist; defaults to `*`)
- `ANTHROPIC_MODEL` (optional, default `claude-sonnet-4-6`; if invalid, app retries with `claude-opus-4-1-20250805`)

---

## Railway build/run

This repo includes:

- `requirements.txt` (consolidated dependencies)
- `Procfile` start command

Start command:

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

---

## curl examples

```bash
# Health
curl -s http://localhost:8000/health

# Process a single PDF end-to-end (token optional)
curl -X POST "http://localhost:8000/process/pdf?return=both" \
  -H "Authorization: Bearer $APP_TOKEN" \
  -F "file=@/path/to/file.pdf"

# Render HTML from an existing JSON payload
curl -X POST "http://localhost:8000/render/html" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $APP_TOKEN" \
  -d '{"data": {"_schema_info": {}, "company_info": {}, "statement_of_comprehensive_income": {}, "statement_of_financial_position": {}, "analysis_summary": {}}}'
```

---

## Security notes

- No API keys are hardcoded.
- Secrets are read from environment variables only.
- `.env` is gitignored for local development.
