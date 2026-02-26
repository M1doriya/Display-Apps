from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

RENDERER_FILE = Path(__file__).resolve().parents[1] / "financial-statement-analysis" / "streamlit_financial_report_v7_7.py"

_spec = spec_from_file_location("financial_renderer", RENDERER_FILE)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load renderer from {RENDERER_FILE}")
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)


def generate_full_html(data: dict[str, Any]) -> str:
    return _module.generate_full_html(data)


def convert_html_to_pdf(html: str) -> bytes:
    return _module.convert_html_to_pdf(html)
