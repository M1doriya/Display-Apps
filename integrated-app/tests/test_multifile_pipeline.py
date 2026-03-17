import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402
import app as integrated_app  # noqa: E402


def _base_record():
    return {
        "_schema_info": {"version": "v7.9"},
        "company_info": {"periods_analyzed": {"year_2024": "FY Dec 2024 (Audited)"}},
        "statement_of_comprehensive_income": {},
        "statement_of_financial_position": {},
        "analysis_summary": {},
    }


def test_case_context_classifies_documents_and_flags_period_mismatch():
    extraction_results = [
        {"full_text_with_tables": "Independent auditors report for financial statements year ended 31 Dec 2024", "tables_json": {"tables": []}},
        {"full_text_with_tables": "Statement of Financial Position current assets non-current liabilities at 31 Dec 2024", "tables_json": {"tables": []}},
        {"full_text_with_tables": "Profit and loss statement turnover cost of sales finance costs for Sep 2025", "tables_json": {"tables": []}},
    ]

    context = pipeline._build_case_reconciliation_context(extraction_results, ["audit.pdf", "bs.pdf", "pnl.pdf"])
    assert context["documents"][0]["document_class"] == "audit_report"
    assert context["documents"][1]["document_class"] == "balance_sheet"
    assert context["documents"][2]["document_class"] == "profit_and_loss"
    assert context["documents"][2]["period_reconciliation_status"] == "mismatched"
    assert context["dominant_reporting_year"] in {2024, 2025}


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Independent auditors report and audited financial statements", "audit_report"),
        ("Statement of financial position current assets current liabilities", "balance_sheet"),
        ("Profit and loss turnover and gross profit net profit", "profit_and_loss"),
        ("Bank statement opening balance debit credit closing balance", "bank_statement"),
        ("Random supporting schedule without accounting headings", "other_supporting_document"),
    ],
)
def test_document_classifier_supports_required_classes(text, expected):
    assert pipeline._classify_document_type({"full_text_with_tables": text}) == expected


def test_apply_case_metadata_sets_source_documents_and_version():
    case_context = {
        "dominant_reporting_year": 2024,
        "reconciliation_flags": [{"source_filename": "pnl.pdf", "status": "mismatched"}],
        "documents": [
            {"source_filename": "audit.pdf", "document_class": "audit_report", "period_reconciliation_status": "matched"},
            {"source_filename": "pnl.pdf", "document_class": "profit_and_loss", "period_reconciliation_status": "mismatched"},
        ],
    }

    output = pipeline._apply_case_metadata(_base_record(), case_context)
    assert output["_schema_info"]["version"] == "v7.9"
    assert len(output["notes"]["source_documents"]) == 2
    assert output["notes"]["period_reconciliation"]["dominant_reporting_year"] == 2024


def test_schema_validation_requires_v79_and_object_shape():
    ok, err = pipeline._validate_kreditlab_schema(_base_record())
    assert ok is True
    assert err is None

    bad = _base_record()
    bad["_schema_info"]["version"] = "v7.8"
    ok, err = pipeline._validate_kreditlab_schema(bad)
    assert ok is False
    assert "v7.9" in err


def test_transform_multiple_merges_all_records_and_preserves_complementary_fields(monkeypatch):
    extraction_results = [{"full_text_with_tables": "statement of financial position 2024", "tables_json": {"tables": []}}, {"full_text_with_tables": "profit and loss revenue finance costs 2024", "tables_json": {"tables": []}}]

    def fake_transform(extraction, combination_context=None):
        idx = combination_context["source_document_index"]
        base = _base_record()
        if idx == 1:
            base["statement_of_financial_position"] = {"assets": {"year_2024": 1000}}
            base["statement_of_comprehensive_income"] = {"revenue": {"year_2024": None}}
        else:
            base["statement_of_comprehensive_income"] = {
                "revenue": {"year_2024": 2000},
                "finance_costs": {"year_2024": -120},
            }
        return base

    monkeypatch.setattr(pipeline, "transform_to_kreditlab_json", fake_transform)

    merged = pipeline.transform_multiple_extractions_to_kreditlab_json(extraction_results, ["bs.pdf", "pnl.pdf"])
    assert merged["statement_of_financial_position"]["assets"]["year_2024"] == 1000
    assert merged["statement_of_comprehensive_income"]["revenue"]["year_2024"] == 2000
    assert merged["statement_of_comprehensive_income"]["finance_costs"]["year_2024"] == -120
    assert merged["notes"]["source_documents"][0]["filename"] == "bs.pdf"


def test_process_pdfs_endpoint_returns_combined_case_output(monkeypatch):
    client = TestClient(integrated_app.app)

    monkeypatch.setattr(integrated_app, "extract_with_tensorlake", lambda payload: {"full_text_with_tables": "profit and loss 2024", "tables_json": {"tables": []}})
    monkeypatch.setattr(
        integrated_app,
        "transform_multiple_extractions_to_kreditlab_json",
        lambda extraction_results, source_filenames=None: {
            "_schema_info": {"version": "v7.9"},
            "company_info": {"periods_analyzed": {"year_2024": "FY Dec 2024 (Audited)"}},
            "statement_of_comprehensive_income": {"revenue": {"year_2024": 100}},
            "statement_of_financial_position": {},
            "analysis_summary": {},
            "notes": {"source_documents": [{"filename": fn} for fn in (source_filenames or [])]},
        },
    )
    monkeypatch.setattr(integrated_app, "generate_full_html", lambda data: "<html>combined</html>")

    files = [
        ("files", ("audit.pdf", b"%PDF-1.4 mock", "application/pdf")),
        ("files", ("pnl.pdf", b"%PDF-1.4 mock", "application/pdf")),
    ]

    response = client.post("/process/pdfs", files=files)
    assert response.status_code == 200
    body = response.json()
    assert "result" in body
    assert body["result"]["filename"] == "combined-report"
    assert body["result"]["source_filenames"] == ["audit.pdf", "pnl.pdf"]
    assert body["result"]["html"] == "<html>combined</html>"


def test_negative_value_preserved_in_merge():
    rec1 = _base_record()
    rec2 = _base_record()
    rec1["statement_of_comprehensive_income"] = {"finance_costs": {"year_2024": -45}}
    rec2["statement_of_comprehensive_income"] = {"revenue": {"year_2024": 500}}
    merged = pipeline.merge_kreditlab_json_records([rec1, rec2])
    assert merged["statement_of_comprehensive_income"]["finance_costs"]["year_2024"] == -45


def test_unknown_parameter_is_not_dropped_on_merge():
    rec1 = _base_record()
    rec2 = _base_record()
    rec1["statement_of_financial_position"] = {"other_assets": [{"name": "Restricted cash / sinking fund", "year_2024": 80}]}
    rec2["statement_of_comprehensive_income"] = {"revenue": {"year_2024": 500}}
    merged = pipeline.merge_kreditlab_json_records([rec1, rec2])
    assert merged["statement_of_financial_position"]["other_assets"][0]["name"] == "Restricted cash / sinking fund"


def test_period_mismatch_multi_file_case_has_flag():
    extraction_results = [
        {"full_text_with_tables": "statement of financial position 31 Dec 2024", "tables_json": {"tables": []}},
        {"full_text_with_tables": "profit and loss for month ended Sep 2025", "tables_json": {"tables": []}},
    ]
    context = pipeline._build_case_reconciliation_context(extraction_results, ["bs.pdf", "pnl.pdf"])
    statuses = [d["period_reconciliation_status"] for d in context["documents"]]
    assert "mismatched" in statuses
