import base64
import json
import os
from pathlib import Path
from typing import Literal, Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from pipeline import generate_full_html, process_pdf

app = FastAPI(title="Display-Apps Integrated Pipeline", version="1.0.0")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

cors_origins = [origin.strip() for origin in os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RenderHTMLRequest(BaseModel):
    data: dict


def require_optional_token(authorization: Optional[str] = Header(default=None)) -> None:
    expected = os.environ.get("APP_TOKEN")
    if not expected:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process/pdf")
async def process_pdf_endpoint(
    return_mode: Literal["html_only", "json_only", "both"] = Query("both", alias="return"),
    include_pdf: bool = Query(False),
    file: UploadFile = File(...),
    _: None = Depends(require_optional_token),
):
    result = await _process_single_upload(file, include_pdf=include_pdf)

    response = {}
    if return_mode in {"both", "json_only"}:
        response["kreditlab_json"] = result["kreditlab_json"]
    if return_mode in {"both", "html_only"}:
        response["html"] = result["html"]

    if include_pdf and result.get("pdf_bytes"):
        response["pdf_base64"] = base64.b64encode(result["pdf_bytes"]).decode("utf-8")

    return JSONResponse(response)


@app.post("/process/pdfs")
async def process_pdfs_endpoint(
    include_pdf: bool = Query(False),
    files: list[UploadFile] = File(...),
    _: None = Depends(require_optional_token),
):
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one PDF")

    results = []
    for upload in files:
        try:
            result = await _process_single_upload(upload, include_pdf=include_pdf)
            entry = {
                "filename": upload.filename,
                "kreditlab_json": result["kreditlab_json"],
                "html": result["html"],
            }
            if include_pdf and result.get("pdf_bytes"):
                entry["pdf_base64"] = base64.b64encode(result["pdf_bytes"]).decode("utf-8")
            results.append(entry)
        except HTTPException as exc:
            results.append({"filename": upload.filename, "error": exc.detail})

    return {"results": results}


@app.post("/render/html")
def render_html_endpoint(body: RenderHTMLRequest, _: None = Depends(require_optional_token)):
    try:
        html = generate_full_html(body.data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to render HTML: {exc}") from exc
    return {"html": html}


async def _process_single_upload(file: UploadFile, include_pdf: bool):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    payload = await file.read()
    if len(payload) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max supported size is 20MB")

    try:
        return process_pdf(payload, include_pdf=include_pdf)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc
