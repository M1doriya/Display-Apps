import copy
import unittest
from pathlib import Path
import importlib.util


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_PATH = REPO_ROOT / "integrated-app" / "pipeline.py"

spec = importlib.util.spec_from_file_location("pipeline", PIPELINE_PATH)
pipeline = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(pipeline)


def _base_record():
    return {
        "_schema_info": {
            "version": "v7.9",
            "generated_by": "Kredit Lab",
            "generation_date": "2026-01-01",
            "currency_unit": "RM",
            "analysis_basis": "Company Standalone",
        },
        "company_info": {
            "name": "MTC Engineering",
            "financial_year_end": "31 December",
            "periods_analyzed": {"fy2024": "FY Dec 2024 (Audited)"},
        },
        "statement_of_comprehensive_income": {
            "revenue": {"line_items": {}, "total": {"display_name": "Total Revenue", "values": {"fy2024": 100}}},
            "net_profit_after_tax": {"display_name": "Net Profit After Tax", "formula": "", "values": {"fy2024": 10}},
        },
        "statement_of_financial_position": {
            "total_assets": {"display_name": "Total Assets", "values": {"fy2024": 500}},
            "total_liabilities": {"display_name": "Total Liabilities", "values": {"fy2024": 300}},
            "total_equity_and_liabilities": {"display_name": "Total Equity and Liabilities", "values": {"fy2024": 500}},
        },
        "analysis_summary": {},
    }


class TestMultiDocumentSupport(unittest.TestCase):
    def test_document_classification_and_period_context(self):
        extractions = [
            {"full_text_with_tables": "AFS audited financial statements year ended 31 December 2024"},
            {"full_text_with_tables": "Bank Statement for Sep 2025. Opening balance and closing balance. transaction date"},
            {"full_text_with_tables": "Profit & Loss for Sep 2025 gross profit and net profit"},
        ]
        names = [
            "AFS - MTC ENGINEERING SDN BHD. 31.12.24 (3).pdf",
            "MTCE BS Sept 2025.pdf",
            "MTCE P&L Sept 2025.pdf",
        ]

        context = pipeline.build_multi_document_context(extractions, names)

        self.assertEqual(len(context["documents"]), 3)
        self.assertEqual(context["documents"][0]["document_type"], "audit_report")
        self.assertEqual(context["documents"][1]["document_type"], "bank_statement")
        self.assertEqual(context["documents"][2]["document_type"], "profit_and_loss")
        self.assertEqual(context["primary_reporting_period"]["primary_year"], 2025)

    def test_mismatch_detection(self):
        extractions = [
            {"full_text_with_tables": "Bank Statement Sep 2025 opening balance closing balance"},
            {"full_text_with_tables": "Profit & Loss Sep 2025 net profit"},
            {"full_text_with_tables": "Audited financial statements year ended 31 December 2024"},
        ]
        context = pipeline.build_multi_document_context(extractions, None)
        mismatches = context["primary_reporting_period"]["mismatches"]
        self.assertTrue(any(item["document_type"] == "audit_report" for item in mismatches))

    def test_merge_preserves_secondary_values(self):
        record_audit = _base_record()
        record_pl = _base_record()
        record_bank = _base_record()

        record_pl["statement_of_comprehensive_income"]["revenue"]["line_items"]["contract_revenue"] = {"fy2024": 100}
        record_bank["analysis_summary"]["bank_statement_observations"] = [{"name": "Avg monthly credit", "value": 90000}]

        merged = pipeline.merge_kreditlab_json_records([record_audit, record_pl, record_bank])

        self.assertIn(
            "contract_revenue",
            merged["statement_of_comprehensive_income"]["revenue"]["line_items"],
        )
        self.assertIn("bank_statement_observations", merged["analysis_summary"])

    def test_schema_validation_v79(self):
        valid, error = pipeline._validate_kreditlab_schema(_base_record())
        self.assertTrue(valid)
        self.assertIsNone(error)

        wrong = copy.deepcopy(_base_record())
        wrong["_schema_info"]["version"] = "v7.8"
        valid, error = pipeline._validate_kreditlab_schema(wrong)
        self.assertFalse(valid)
        self.assertIn("v7.9", error)


if __name__ == "__main__":
    unittest.main()
