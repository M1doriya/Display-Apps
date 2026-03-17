import sys
import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path("integrated-app").resolve()))


def load_module(name: str, rel_path: str):
    path = Path(rel_path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


pipeline = load_module("pipeline", "integrated-app/pipeline.py")
renderer = load_module("renderer", "financial-statement-analysis/streamlit_financial_report_v7_7.py")
app_module = load_module("integrated_app", "integrated-app/app.py")


def minimal_payload(version: str = "v7.9"):
    return {
        "_schema_info": {"version": version},
        "company_info": {"periods_analyzed": {"fy2024": "FY 2024 (Audited)"}},
        "statement_of_comprehensive_income": {},
        "statement_of_financial_position": {},
        "analysis_summary": {},
    }


def test_schema_enforces_v79_only():
    ok, err = pipeline._validate_kreditlab_schema(minimal_payload("v7.9"))
    assert ok and err is None

    ok, err = pipeline._validate_kreditlab_schema(minimal_payload("v7.7"))
    assert not ok
    assert "v7.9" in err


def test_canonical_case_has_quality_flags_and_period_reconciliation():
    records = [minimal_payload("v7.9"), minimal_payload("v7.9")]
    metadata = [
        {
            "filename": "pl.pdf",
            "document_class": "profit_and_loss",
            "period_signals": {"years": ["2024"]},
        },
        {
            "filename": "old-bs.pdf",
            "document_class": "balance_sheet",
            "period_signals": {"years": ["2022"]},
        },
    ]
    merged = pipeline._build_canonical_case_json(records, metadata)
    assert merged["_schema_info"]["version"] == "v7.9"
    assert merged["data_quality"]["source_documents_used"][0]["filename"] == "pl.pdf"
    assert merged["data_quality"]["source_documents_excluded"][0]["filename"] == "old-bs.pdf"
    assert merged["data_quality"]["period_mismatch"][0]["filename"] == "old-bs.pdf"


def test_transform_multiple_builds_one_case(monkeypatch):
    def fake_transform(extraction, combination_context=None):
        payload = minimal_payload("v7.9")
        payload["analysis_summary"] = {
            "doc": combination_context.get("source_document_index"),
            "class": combination_context.get("document_class"),
        }
        return payload

    monkeypatch.setattr(pipeline, "transform_to_kreditlab_json", fake_transform)

    merged = pipeline.transform_multiple_extractions_to_kreditlab_json(
        [
            {"full_text_with_tables": "Balance Sheet 2024 assets liabilities"},
            {"full_text_with_tables": "Profit and Loss 2024 revenue cost"},
        ],
        source_filenames=["bs.pdf", "pl.pdf"],
    )
    assert merged["_schema_info"]["version"] == "v7.9"
    assert len(merged["case_metadata"]["documents"]) == 2
    assert len(merged["data_quality"]["source_documents_used"]) == 2


def test_none_safe_benchmark_helper():
    assert renderer.check_benchmark_status(None, ">= 1.25x", "x") == ""


def test_process_pdfs_keeps_partial_success(monkeypatch):
    app = app_module.app

    def fake_extract(payload: bytes):
        if payload == b"bad":
            raise RuntimeError("boom")
        return {"full_text_with_tables": "Profit and Loss 2024 revenue", "tables_json": {"tables": []}}

    monkeypatch.setattr(app_module, "extract_with_tensorlake", fake_extract)
    monkeypatch.setattr(app_module, "transform_multiple_extractions_to_kreditlab_json", lambda results, source_filenames=None: minimal_payload("v7.9"))
    monkeypatch.setattr(app_module, "generate_full_html", lambda data: "<html>ok</html>")

    client = TestClient(app)
    files = [
        ("files", ("good.pdf", b"good", "application/pdf")),
        ("files", ("bad.pdf", b"bad", "application/pdf")),
    ]
    response = client.post("/process/pdfs", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert any(item["status"] == "error" for item in body["file_statuses"])
    assert body["kreditlab_json"]["_schema_info"]["version"] == "v7.9"
