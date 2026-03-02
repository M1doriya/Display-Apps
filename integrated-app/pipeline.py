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
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
FALLBACK_ANTHROPIC_MODEL = "claude-opus-4-1-20250805"
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


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _json_object_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    stack = 0
    start: Optional[int] = None
    in_string = False
    escaping = False

    for idx, ch in enumerate(text):
        if in_string:
            if escaping:
                escaping = False
            elif ch == "\\":
                escaping = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            if stack == 0:
                start = idx
            stack += 1
        elif ch == "}" and stack > 0:
            stack -= 1
            if stack == 0 and start is not None:
                candidates.append(text[start : idx + 1])

    if not candidates:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidates.append(text[start : end + 1])

    candidates.sort(key=len, reverse=True)
    return candidates


def _extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = _strip_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    last_error: Optional[Exception] = None
    for candidate in _json_object_candidates(cleaned):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            last_error = exc

    if last_error:
        raise last_error
    raise json.JSONDecodeError("No JSON object found in response", cleaned, 0)


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

    requested_model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    model_candidates = [requested_model]
    if requested_model != FALLBACK_ANTHROPIC_MODEL:
        model_candidates.append(FALLBACK_ANTHROPIC_MODEL)

    last_error: Optional[Exception] = None
    message = None
    for model_name in model_candidates:
        try:
            message = client.messages.create(
                model=model_name,
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
            if model_name != requested_model:
                LOGGER.warning(
                    "Configured ANTHROPIC_MODEL '%s' failed. Fell back to '%s'.",
                    requested_model,
                    model_name,
                )
            break
        except Exception as exc:
            if "not_found_error" in str(exc) or "404" in str(exc):
                last_error = exc
                LOGGER.warning("Anthropic model '%s' is unavailable. Trying fallback.", model_name)
                continue
            raise

    if message is None:
        raise RuntimeError(
            "Unable to call Anthropic API: configured model is unavailable and fallback failed."
        ) from last_error

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
        "Your previous output was invalid JSON and/or failed required schema keys. "
        "Return ONLY a corrected JSON object. No markdown, no explanations.\n\n"
        f"INVALID_OUTPUT:\n{first_response}"
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
