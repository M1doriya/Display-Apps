import importlib.util
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
from anthropic import Anthropic
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

LOGGER = logging.getLogger(__name__)
REQUIRED_TOP_LEVEL_KEYS = {
    "_schema_info",
    "company_info",
    "statement_of_comprehensive_income",
    "statement_of_financial_position",
    "analysis_summary",
}

ROOT_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT_DIR / "KreditLab_v7_9_updated.txt"
RENDERER_PATH = ROOT_DIR / "financial-statement-analysis" / "streamlit_financial_report_v7_7.py"


def _load_system_prompt() -> str:
    instruction_files = sorted(
        p for p in ROOT_DIR.glob("*.txt") if "kreditlab" in p.stem.lower()
    )
    if not instruction_files:
        if not PROMPT_PATH.exists():
            raise RuntimeError(f"Prompt file not found at {PROMPT_PATH}")
        instruction_files = [PROMPT_PATH]

    sections = []
    for path in instruction_files:
        sections.append(f"# Instructions from {path.name}\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(sections)


def _load_renderer_module():
    spec = importlib.util.spec_from_file_location("kreditlab_renderer", RENDERER_PATH)
    if not spec or not spec.loader:
        raise RuntimeError(f"Unable to load renderer module from {RENDERER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_RENDERER = _load_renderer_module()
generate_full_html = _RENDERER.generate_full_html
convert_html_to_pdf = _RENDERER.convert_html_to_pdf


def upload_file_v2(path: str, api_key: str) -> str:
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
        raise RuntimeError(f"Tensorlake upload failed ({response.status_code}): {response.text}")
    return response.json()["file_id"]


def _clean_number(value: str) -> Any:
    try:
        return int(value.replace(",", ""))
    except Exception:
        return value


def _html_table_to_matrix(table):
    rows = table.find_all("tr")
    return [[cell.get_text(strip=True) for cell in row.find_all(["td", "th"])] for row in rows]


def _html_table_to_objects(table):
    matrix = _html_table_to_matrix(table)
    if not matrix or len(matrix) < 2:
        return []

    header = matrix[0]
    objects = []
    for row in matrix[1:]:
        entry = {}
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


def extract_with_tensorlake(pdf_bytes: bytes) -> Dict[str, Any]:
    tensorlake_api_key = os.environ.get("TENSORLAKE_API_KEY")
    if not tensorlake_api_key:
        raise RuntimeError("TENSORLAKE_API_KEY environment variable is required")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        temp_pdf_path = tmp.name

    try:
        file_id = upload_file_v2(temp_pdf_path, tensorlake_api_key)
        doc_ai = DocumentAI(api_key=tensorlake_api_key)

        parsing_options = ParsingOptions(
            chunking_strategy=ChunkingStrategy.PAGE,
            table_output_mode=TableOutputMode.MARKDOWN,
            table_parsing_format=TableParsingFormat.TSR,
            ocr_model=OcrPipelineProvider.TENSORLAKE02,
            skew_detection=True,
        )
        enrichment_options = EnrichmentOptions(figure_summarization=False, table_summarization=False)
        result = doc_ai.parse_and_wait(
            file_id=file_id,
            parsing_options=parsing_options,
            enrichment_options=enrichment_options,
        )
        if result.status != ParseStatus.SUCCESSFUL:
            raise RuntimeError(f"Tensorlake parsing failed with status: {result.status}")

        full_text_output = ""
        full_text_with_tables = ""
        all_tables_json = {"tables": []}

        for i, chunk in enumerate(result.chunks, start=1):
            raw_markdown = chunk.content
            soup = BeautifulSoup(raw_markdown, "html.parser")
            tables = soup.find_all("table")
            for t in tables:
                t.extract()

            text_plain = soup.get_text("\n", strip=True)
            full_text_output += f"\n\n===== PAGE {i} =====\n\n{text_plain}\n\n"
            full_text_with_tables += f"\n\n===== PAGE {i} =====\n\n{text_plain}\n\n"

            for t_index, table in enumerate(tables, start=1):
                matrix = _html_table_to_matrix(table)
                if not matrix or len(matrix) < 2:
                    continue
                headers = matrix[0]
                rows = matrix[1:]
                readable = tabulate(rows, headers=headers, tablefmt="grid")
                full_text_with_tables += readable + "\n\n"
                all_tables_json["tables"].append(
                    {
                        "page": i,
                        "table_index": t_index,
                        "rows": _html_table_to_objects(table),
                    }
                )

        return {
            "full_text_output": full_text_output,
            "full_text_with_tables": full_text_with_tables,
            "tables_json": all_tables_json,
        }
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


def _extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _validate_kreditlab_schema(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(data.keys()))
    if missing:
        return False, f"Missing required top-level keys: {', '.join(missing)}"
    return True, None


def _call_anthropic(system_prompt: str, user_content: str, corrective: bool = False) -> str:
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is required")

    client = Anthropic(api_key=anthropic_api_key)
    assistant_instruction = (
        "Return ONLY valid JSON. No markdown fences, no explanations, no extra text."
        if not corrective
        else "Your previous output was invalid. Return ONLY corrected valid JSON matching the required schema."
    )

    message = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        max_tokens=8192,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    f"{assistant_instruction}\n\n"
                    "Transform this extracted financial data into KreditLab JSON format:\n\n"
                    f"FULL_TEXT_WITH_TABLES:\n{user_content}"
                ),
            }
        ],
    )

    chunks = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            chunks.append(block.text)
    return "\n".join(chunks).strip()


def transform_to_kreditlab_json(extraction_result: Dict[str, Any]) -> Dict[str, Any]:
    system_prompt = _load_system_prompt()
    user_payload = {
        "full_text_with_tables": extraction_result["full_text_with_tables"],
        "tables_json": extraction_result.get("tables_json", {}),
    }
    user_content = json.dumps(user_payload, ensure_ascii=False)

    first_response = _call_anthropic(system_prompt=system_prompt, user_content=user_content)

    try:
        parsed = _extract_json_object(first_response)
        valid, error = _validate_kreditlab_schema(parsed)
        if valid:
            return parsed
        LOGGER.warning("Anthropic schema validation failed on first attempt: %s", error)
    except Exception as exc:
        LOGGER.warning("Failed to parse Anthropic response on first attempt: %s", exc)

    corrective_content = (
        f"Original extracted input:\n{user_content}\n\n"
        f"Previous invalid output:\n{first_response}\n\n"
        "Return JSON only; fix schema/JSON."
    )
    second_response = _call_anthropic(system_prompt=system_prompt, user_content=corrective_content, corrective=True)

    try:
        parsed = _extract_json_object(second_response)
    except Exception as exc:
        raise RuntimeError(f"Claude response is not valid JSON after retry: {exc}") from exc

    valid, error = _validate_kreditlab_schema(parsed)
    if not valid:
        raise RuntimeError(f"Claude response failed schema checks after retry: {error}")

    return parsed


def process_pdf(pdf_bytes: bytes, include_pdf: bool = False) -> Dict[str, Any]:
    extraction_result = extract_with_tensorlake(pdf_bytes)
    kreditlab_json = transform_to_kreditlab_json(extraction_result)
    html = generate_full_html(kreditlab_json)

    result: Dict[str, Any] = {
        "kreditlab_json": kreditlab_json,
        "html": html,
    }

    if include_pdf:
        try:
            result["pdf_bytes"] = convert_html_to_pdf(html)
        except Exception as exc:
            LOGGER.warning("PDF conversion failed: %s", exc)

    return result
