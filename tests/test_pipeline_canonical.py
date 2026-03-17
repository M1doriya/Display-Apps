import importlib.util
from pathlib import Path
import unittest


PIPELINE_PATH = Path(__file__).resolve().parents[1] / "integrated-app" / "pipeline.py"
spec = importlib.util.spec_from_file_location("pipeline", PIPELINE_PATH)
pipeline = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(pipeline)


class CanonicalPipelineTests(unittest.TestCase):
    def _base_json(self):
        return {
            "_schema_info": {"version": "v7.7"},
            "company_info": {"periods_analyzed": {"year_2024": "FY2024"}},
            "statement_of_comprehensive_income": {"revenue": {"year_2024": 1200}},
            "statement_of_financial_position": {"assets": {"year_2024": 3000}},
            "analysis_summary": {
                "notes": ["P&L missing", "Balance sheet missing"],
            },
        }

    def test_schema_version_enforced_to_v79(self):
        data = self._base_json()
        processed = pipeline._post_process_canonical_json(data, extraction_results=[], source_filenames=None)
        self.assertEqual(processed["_schema_info"]["version"], "v7.9")

    def test_validate_schema_rejects_non_v79(self):
        ok, error = pipeline._validate_kreditlab_schema(self._base_json())
        self.assertFalse(ok)
        self.assertIn("v7.9", error)

    def test_missing_not_zero_blocks_derived_metrics(self):
        data = self._base_json()
        data["statement_of_financial_position"] = {}
        processed = pipeline._post_process_canonical_json(data, extraction_results=[], source_filenames=None)
        flags = processed["analysis_summary"]["data_quality_flags"]
        self.assertIn("statement_of_financial_position", flags["missing_required_inputs"])
        self.assertIn("ratios", flags["blocked_derived_metrics"])

    def test_synonyms_and_unknown_parameters_preserved(self):
        extraction = {
            "full_text_with_tables": "Sales and turnover grew with bank charges",
            "tables_json": {
                "tables": [
                    {
                        "table_index": 1,
                        "source_document": 1,
                        "rows": [
                            {"name": "Custom Deferred Income Bucket", "year_2024": 10},
                            {"name": "Sales", "year_2024": 100},
                        ],
                    }
                ]
            },
        }
        processed = pipeline._post_process_canonical_json(
            self._base_json(),
            extraction_results=[extraction],
            source_filenames=["pnl.pdf"],
        )
        flags = processed["analysis_summary"]["data_quality_flags"]
        mapped = flags["synonym_mapped_fields"]
        self.assertTrue(any(entry["canonical"] == "revenue" for entry in mapped))
        unknown = flags["unknown_parameters_preserved"]
        self.assertTrue(any(item["label"] == "Custom Deferred Income Bucket" for item in unknown))

    def test_document_classification_and_period_reconciliation(self):
        pnl = {
            "full_text_with_tables": "Statement of Profit and Loss for year ended 31.12.2024 turnover",
            "tables_json": {"tables": []},
        }
        bs = {
            "full_text_with_tables": "Statement of Financial Position as at 31.12.2024 total assets",
            "tables_json": {"tables": []},
        }

        processed = pipeline._post_process_canonical_json(
            self._base_json(),
            extraction_results=[pnl, bs],
            source_filenames=["pnl.pdf", "bs.pdf"],
        )
        docs = processed["_case_metadata"]["documents"]
        self.assertEqual(docs[0]["document_type"], "profit_and_loss")
        self.assertEqual(docs[1]["document_type"], "balance_sheet")
        self.assertEqual(processed["analysis_summary"]["data_quality_flags"]["period_mismatch"], False)

    def test_narrative_consistency_no_false_missing(self):
        processed = pipeline._post_process_canonical_json(self._base_json(), extraction_results=[], source_filenames=None)
        notes = processed["analysis_summary"]["notes"]
        self.assertTrue(all("missing" not in str(item).lower() for item in notes))


if __name__ == "__main__":
    unittest.main()
