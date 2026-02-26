# Display-Apps

## Integrated Railway App

This repo now includes a single deployable service in `integrated-app` that runs the full pipeline end-to-end:

1. PDF upload
2. Tensorlake extraction (`full_text_with_tables` + `tables_json`)
3. Anthropic Claude transform into KreditLab JSON using `KreditLab_v7_9_updated.txt` as system prompt
4. HTML rendering via `generate_full_html`
5. Optional PDF conversion and download

## Folder to deploy

- Deploy root: `integrated-app`
- App entrypoint: `main.py`
- Main dependency file: `integrated-app/requirements.txt`

## Required environment variables

- `ANTHROPIC_API_KEY` (required)
- `TENSORLAKE_API_KEY` (required)
- `APP_TOKEN` (optional; when set, POST endpoints require `Authorization: Bearer <APP_TOKEN>`)

> Do not commit secrets. Use Railway environment variables for production.

## Local run

```bash
cd integrated-app
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Railway setup (single service)

1. Create one Railway service from this repo.
2. Set **Root Directory** to `integrated-app`.
3. Configure environment variables:
   - `ANTHROPIC_API_KEY`
   - `TENSORLAKE_API_KEY`
   - optional `APP_TOKEN`
4. Start command:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```


### If Railway shows "railpack could not determine how to build the app"

This repo now includes root-level `requirements.txt`, `Procfile`, and `nixpacks.toml` so Railpack can detect Python automatically even if Root Directory is not set. The root requirements file is standalone (not a relative include), which avoids missing-path errors during build.

You can deploy in either mode:

1. **Recommended**: set Root Directory to `integrated-app`
2. **Fallback**: leave Root Directory blank (repo root). Railway will use root `requirements.txt` and start command that `cd`s into `integrated-app`.


If you still see an old path error like `/app/integrated-app/requirements.txt`:

- Ensure Railway is deploying the latest commit SHA (not an older cached build).
- Trigger a **Redeploy** with **Clear build cache**.
- The included `nixpacks.toml` now installs from `integrated-app/requirements.txt` when present, otherwise falls back to root `requirements.txt`.

## API endpoints

- `GET /health` → `{"status":"ok"}`
- `POST /process/pdf`
  - Multipart field: `file` (PDF)
  - Query params:
    - `return=html_only|json_only|both` (default `both`)
    - `include_pdf=true|false` (default `false`)
- `POST /render/html`
  - JSON body: `{"data": <kreditlab_json>}`

## curl examples

Health:

```bash
curl http://localhost:8000/health
```

Process PDF (both outputs):

```bash
curl -X POST "http://localhost:8000/process/pdf?return=both" \
  -H "Authorization: Bearer $APP_TOKEN" \
  -F "file=@/path/to/statement.pdf"
```

Render HTML from JSON:

```bash
curl -X POST "http://localhost:8000/render/html" \
  -H "Authorization: Bearer $APP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"_schema_info": {}, "company_info": {}, "statement_of_comprehensive_income": {}, "statement_of_financial_position": {}, "analysis_summary": {}}}'
```

## Minimal UI

Open `GET /` for a simple upload UI to:

- Upload a PDF
- Run full pipeline
- Preview rendered HTML
- Download `kreditlab.json`
- Download `report.html`
- Download `report.pdf` (when `include_pdf=true` is requested by API clients)

## Sample request script

```bash
python integrated-app/sample_request.py /path/to/file.pdf --base-url http://localhost:8000 --token "$APP_TOKEN"
```
