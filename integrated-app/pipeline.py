from dataclasses import dataclass
from typing import Any

from renderer import generate_full_html
from tensorlake_extractor import extract_pdf
from transformer import transform_to_kreditlab_json


@dataclass
class PipelineResult:
    kreditlab_json: dict[str, Any]
    html: str


def process_pdf(pdf_bytes: bytes) -> PipelineResult:
    extracted = extract_pdf(pdf_bytes)
    kreditlab_json = transform_to_kreditlab_json(
        full_text_with_tables=extracted.full_text_with_tables,
        tables_json=extracted.tables_json,
    )
    html = generate_full_html(kreditlab_json)
    return PipelineResult(kreditlab_json=kreditlab_json, html=html)
