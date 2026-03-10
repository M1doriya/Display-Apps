import base64
import os
import secrets
from pathlib import Path
from typing import Literal, Optional

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from pipeline import (
    convert_html_to_pdf,
    extract_with_tensorlake,
    generate_full_html,
    process_pdf,
    transform_to_kreditlab_json,
    transform_multiple_extractions_to_kreditlab_json,
    merge_kreditlab_json_records,
)

app = FastAPI(title="Display-Apps Integrated Pipeline", version="1.0.0")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/assets", StaticFiles(directory=str(BASE_DIR.parent)), name="assets")

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


class StageTransformItem(BaseModel):
    filename: str
    extraction_result: dict


class StageTransformRequest(BaseModel):
    items: list[StageTransformItem]


class StageRenderItem(BaseModel):
    filename: str
    kreditlab_json: dict


class StageRenderRequest(BaseModel):
    items: list[StageRenderItem]
    include_pdf: bool = False


class StageMergeRequest(BaseModel):
    items: list[StageRenderItem]
    include_pdf: bool = False


AUTH_USERNAME = "admin"
AUTH_PASSWORD = "xs2admin"
AUTH_COOKIE_NAME = "display_apps_auth"
AUTH_COOKIE_VALUE = "authenticated"


def _is_valid_basic_auth(authorization: Optional[str]) -> bool:
    if not authorization or not authorization.startswith("Basic "):
        return False
    try:
        encoded = authorization.split(" ", 1)[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return False
    return secrets.compare_digest(username, AUTH_USERNAME) and secrets.compare_digest(password, AUTH_PASSWORD)


def _is_authenticated(request: Request, authorization: Optional[str] = None) -> bool:
    cookie_ok = secrets.compare_digest(request.cookies.get(AUTH_COOKIE_NAME, ""), AUTH_COOKIE_VALUE)
    return cookie_ok or _is_valid_basic_auth(authorization)


def require_authenticated_user(request: Request, authorization: Optional[str] = Header(default=None)) -> None:
    if not _is_authenticated(request, authorization):
        raise HTTPException(status_code=401, detail="Authentication required")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    valid_username = secrets.compare_digest(username, AUTH_USERNAME)
    valid_password = secrets.compare_digest(password, AUTH_PASSWORD)

    if not (valid_username and valid_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=401,
        )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(AUTH_COOKIE_NAME, AUTH_COOKIE_VALUE, httponly=True, samesite="lax")
    return response


@app.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response


@app.get("/", response_class=HTMLResponse)
def index(request: Request, _: None = Depends(require_authenticated_user)):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process/pdf")
async def process_pdf_endpoint(
    return_mode: Literal["html_only", "json_only", "both"] = Query("both", alias="return"),
    include_pdf: bool = Query(False),
    file: UploadFile = File(...),
    _: None = Depends(require_authenticated_user),
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
    _: None = Depends(require_authenticated_user),
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
def render_html_endpoint(body: RenderHTMLRequest, _: None = Depends(require_authenticated_user)):
    try:
        html = generate_full_html(body.data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to render HTML: {exc}") from exc
    return {"html": html}


@app.post("/stage/tensorlake")
async def stage_tensorlake_endpoint(
    files: list[UploadFile] = File(...),
    _: None = Depends(require_authenticated_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one PDF")

    results = []
    for upload in files:
        try:
            payload = await _read_validated_pdf(upload)
            extraction_result = extract_with_tensorlake(payload)
            results.append(
                {
                    "filename": upload.filename,
                    "status": "success",
                    "extraction_result": extraction_result,
                }
            )
        except HTTPException as exc:
            results.append({"filename": upload.filename, "status": "error", "error": exc.detail})
        except Exception as exc:
            results.append({"filename": upload.filename, "status": "error", "error": f"Tensorlake failed: {exc}"})

    return {"results": results}


@app.post("/stage/transform")
def stage_transform_endpoint(body: StageTransformRequest, _: None = Depends(require_authenticated_user)):
    if not body.items:
        raise HTTPException(status_code=400, detail="No stage payload supplied")

    if len(body.items) == 1:
        item = body.items[0]
        try:
            kreditlab_json = transform_to_kreditlab_json(item.extraction_result)
            return {
                "results": [
                    {
                        "filename": item.filename,
                        "status": "success",
                        "kreditlab_json": kreditlab_json,
                    }
                ]
            }
        except Exception as exc:
            return {
                "results": [
                    {
                        "filename": item.filename,
                        "status": "error",
                        "error": f"Anthropic transform failed: {exc}",
                    }
                ]
            }

    try:
        combined_json = transform_multiple_extractions_to_kreditlab_json(
            [item.extraction_result for item in body.items],
            source_filenames=[item.filename for item in body.items],
        )
        return {
            "results": [
                {
                    "filename": "combined-report",
                    "source_filenames": [item.filename for item in body.items],
                    "status": "success",
                    "kreditlab_json": combined_json,
                }
            ]
        }
    except Exception as exc:
        return {
            "results": [
                {
                    "filename": "combined-report",
                    "source_filenames": [item.filename for item in body.items],
                    "status": "error",
                    "error": f"Anthropic combined transform failed: {exc}",
                }
            ]
        }


@app.post("/stage/render")
def stage_render_endpoint(body: StageRenderRequest, _: None = Depends(require_authenticated_user)):
    if not body.items:
        raise HTTPException(status_code=400, detail="No stage payload supplied")

    results = []
    for item in body.items:
        try:
            html = generate_full_html(item.kreditlab_json)
            entry = {
                "filename": item.filename,
                "status": "success",
                "kreditlab_json": item.kreditlab_json,
                "html": html,
            }
            if body.include_pdf:
                try:
                    entry["pdf_base64"] = base64.b64encode(convert_html_to_pdf(html)).decode("utf-8")
                except Exception:
                    pass
            results.append(entry)
        except Exception as exc:
            results.append(
                {
                    "filename": item.filename,
                    "status": "error",
                    "error": f"HTML render failed: {exc}",
                }
            )

    return {"results": results}


@app.post("/stage/merge-render")
def stage_merge_render_endpoint(body: StageMergeRequest, _: None = Depends(require_authenticated_user)):
    if not body.items:
        raise HTTPException(status_code=400, detail="No stage payload supplied")

    try:
        merged_json = merge_kreditlab_json_records([item.kreditlab_json for item in body.items])
        html = generate_full_html(merged_json)

        entry = {
            "filename": "merged-report",
            "source_filenames": [item.filename for item in body.items],
            "status": "success",
            "kreditlab_json": merged_json,
            "html": html,
        }
        if body.include_pdf:
            try:
                entry["pdf_base64"] = base64.b64encode(convert_html_to_pdf(html)).decode("utf-8")
            except Exception:
                pass

        return {"result": entry}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Merge render failed: {exc}") from exc


async def _process_single_upload(file: UploadFile, include_pdf: bool):
    payload = await _read_validated_pdf(file)

    try:
        return process_pdf(payload, include_pdf=include_pdf)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc


async def _read_validated_pdf(file: UploadFile) -> bytes:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    payload = await file.read()
    if len(payload) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max supported size is 20MB")
    return payload
