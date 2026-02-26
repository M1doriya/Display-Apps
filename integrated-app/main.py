import base64
import json
import os
from typing import Literal

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from pipeline import process_pdf
from renderer import convert_html_to_pdf, generate_full_html

app = FastAPI(title="Display-Apps Integrated Pipeline", version="1.0.0")
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024


def require_auth(request: Request) -> None:
    app_token = os.getenv("APP_TOKEN")
    if not app_token:
        return

    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {app_token}"
    if auth != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class RenderRequest(BaseModel):
    data: dict


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html>
<head><meta charset='utf-8'><title>Display-Apps Pipeline</title></head>
<body style='font-family:Arial, sans-serif;max-width:900px;margin:30px auto;'>
  <h2>Display-Apps: PDF → KreditLab JSON → HTML</h2>
  <form id='uploadForm'>
    <input type='file' id='pdf' accept='application/pdf' required />
    <select id='mode'>
      <option value='both'>both</option>
      <option value='html_only'>html_only</option>
      <option value='json_only'>json_only</option>
    </select>
    <button type='submit'>Process PDF</button>
  </form>
  <p id='status'></p>
  <div id='downloads' style='display:none;gap:10px;'></div>
  <h3>HTML Preview</h3>
  <iframe id='preview' style='width:100%;height:500px;border:1px solid #ccc;'></iframe>
<script>
const statusEl = document.getElementById('status');
const downloadsEl = document.getElementById('downloads');
const previewEl = document.getElementById('preview');
function downloadLink(filename, content, mime) {
  const a = document.createElement('a');
  a.textContent = 'Download ' + filename;
  a.style.marginRight = '10px';
  const blob = new Blob([content], {type: mime});
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  return a;
}
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = 'Processing...';
  downloadsEl.innerHTML = '';
  downloadsEl.style.display = 'none';
  const file = document.getElementById('pdf').files[0];
  const mode = document.getElementById('mode').value;
  const form = new FormData();
  form.append('file', file);
  const response = await fetch('/process/pdf?return=' + encodeURIComponent(mode), {method: 'POST', body: form});
  const data = await response.json();
  if (!response.ok) {
    statusEl.textContent = 'Error: ' + (data.detail || 'unknown');
    return;
  }
  statusEl.textContent = 'Done';
  if (data.kreditlab_json) {
    downloadsEl.appendChild(downloadLink('kreditlab.json', JSON.stringify(data.kreditlab_json, null, 2), 'application/json'));
  }
  if (data.html) {
    downloadsEl.appendChild(downloadLink('report.html', data.html, 'text/html'));
    previewEl.srcdoc = data.html;
  }
  if (data.pdf_base64) {
    const raw = atob(data.pdf_base64);
    const arr = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
    downloadsEl.appendChild(downloadLink('report.pdf', arr, 'application/pdf'));
  }
  downloadsEl.style.display = 'block';
});
</script>
</body>
</html>"""


@app.post("/process/pdf")
async def process_pdf_endpoint(
    request: Request,
    file: UploadFile = File(...),
    return_mode: Literal["html_only", "json_only", "both"] = Query("both", alias="return"),
    include_pdf: bool = Query(False),
    _: None = Depends(require_auth),
):
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"PDF too large (max {MAX_UPLOAD_SIZE_BYTES} bytes)")

    try:
        result = process_pdf(pdf_bytes, render_html=return_mode in {"both", "html_only"})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc

    payload: dict[str, object] = {}
    if return_mode in {"both", "json_only"}:
        payload["kreditlab_json"] = result.kreditlab_json
    if return_mode in {"both", "html_only"}:
        payload["html"] = result.html
    if include_pdf and return_mode in {"both", "html_only"}:
        try:
            if result.html is None:
                raise ValueError("HTML output was not generated")
            pdf_bytes = convert_html_to_pdf(result.html)
            payload["pdf_base64"] = base64.b64encode(pdf_bytes).decode("utf-8")
        except Exception as exc:
            payload["pdf_error"] = str(exc)

    return JSONResponse(payload)


@app.post("/render/html")
def render_html_endpoint(
    body: RenderRequest,
    _: None = Depends(require_auth),
):
    try:
        html = generate_full_html(body.data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"HTML rendering failed: {exc}") from exc
    return {"html": html}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
