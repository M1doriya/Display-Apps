import json
import os
import tempfile
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup
from tabulate import tabulate
from tensorlake.documentai import (
    ChunkingStrategy,
    DocumentAI,
    EnrichmentOptions,
    OcrPipelineProvider,
    ParseStatus,
    ParsingOptions,
    TableOutputMode,
    TableParsingFormat,
)


@dataclass
class ExtractionResult:
    full_text_with_tables: str
    tables_json: dict[str, Any]


def _upload_file_v2(path: str, api_key: str) -> str:
    url = "https://api.tensorlake.ai/documents/v2/files"
    with open(path, "rb") as f:
        files = {"file_bytes": ("file.pdf", f, "application/pdf")}
        data = {"labels": json.dumps({"source": "integrated_app"})}
        response = httpx.put(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data=data,
            timeout=60,
        )

    if response.status_code != 200:
        raise RuntimeError(f"Tensorlake upload failed {response.status_code}: {response.text}")

    payload = response.json()
    file_id = payload.get("file_id")
    if not file_id:
        raise RuntimeError("Tensorlake upload response missing file_id")
    return file_id


def _clean_number(value: str) -> int | str:
    try:
        return int(value.replace(",", ""))
    except Exception:
        return value


def _html_table_to_matrix(table: Any) -> list[list[str]]:
    rows = table.find_all("tr")
    return [[cell.get_text(strip=True) for cell in row.find_all(["td", "th"])] for row in rows]


def _html_table_to_objects(table: Any) -> list[dict[str, Any]]:
    matrix = _html_table_to_matrix(table)
    if not matrix or len(matrix) < 2:
        return []

    header = matrix[0]
    objects: list[dict[str, Any]] = []
    for row in matrix[1:]:
        entry: dict[str, Any] = {}
        for h, v in zip(header, row):
            h_low = h.lower().strip()
            if h_low in ["2024", "year_2024"]:
                entry["year_2024"] = _clean_number(v)
            elif h_low in ["2023", "as restated 2023", "year_2023"]:
                entry["year_2023"] = _clean_number(v)
            elif h_low == "note":
                entry["note"] = _clean_number(v) if v else None
            else:
                entry["name"] = v
        objects.append(entry)

    return objects


def extract_pdf(pdf_bytes: bytes) -> ExtractionResult:
    api_key = os.getenv("TENSORLAKE_API_KEY")
    if not api_key:
        raise RuntimeError("TENSORLAKE_API_KEY is required")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        temp_pdf_path = tmp.name

    try:
        file_id = _upload_file_v2(temp_pdf_path, api_key)
        doc_ai = DocumentAI(api_key=api_key)

        parsing_options = ParsingOptions(
            chunking_strategy=ChunkingStrategy.PAGE,
            table_output_mode=TableOutputMode.MARKDOWN,
            table_parsing_format=TableParsingFormat.TSR,
            ocr_model=OcrPipelineProvider.TENSORLAKE02,
            skew_detection=True,
        )
        enrichment_options = EnrichmentOptions(
            figure_summarization=False,
            table_summarization=False,
        )

        result = doc_ai.parse_and_wait(
            file_id=file_id,
            parsing_options=parsing_options,
            enrichment_options=enrichment_options,
        )

        if result.status != ParseStatus.SUCCESSFUL:
            raise RuntimeError(f"Tensorlake parse failed: {result.status}")

        full_text_with_tables = ""
        all_tables_json: dict[str, Any] = {"tables": []}

        for i, chunk in enumerate(result.chunks, start=1):
            raw_markdown = chunk.content
            soup = BeautifulSoup(raw_markdown, "html.parser")
            tables = soup.find_all("table")
            for t in tables:
                t.extract()

            text_plain = soup.get_text("\n", strip=True)
            full_text_with_tables += f"\n\n===== PAGE {i} =====\n\n{text_plain}\n\n"

            for t_index, table in enumerate(tables, start=1):
                matrix = _html_table_to_matrix(table)
                if not matrix or len(matrix) < 2:
                    continue

                headers = matrix[0]
                rows = matrix[1:]
                full_text_with_tables += tabulate(rows, headers=headers, tablefmt="grid") + "\n\n"

                all_tables_json["tables"].append(
                    {
                        "page": i,
                        "table_index": t_index,
                        "rows": _html_table_to_objects(table),
                    }
                )

        return ExtractionResult(
            full_text_with_tables=full_text_with_tables,
            tables_json=all_tables_json,
        )
    finally:
        try:
            os.remove(temp_pdf_path)
        except OSError:
            pass
