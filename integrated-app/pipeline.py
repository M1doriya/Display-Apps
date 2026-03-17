import importlib.util
import ast
import json
import logging
import os
import tempfile
from pathlib import Path
from copy import deepcopy
from typing import Any, Dict, Optional, Tuple, Iterable
import re

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
DEFAULT_ANTHROPIC_MAX_TOKENS = 16384
DEFAULT_STAGE2_INPUT_CHAR_BUDGET = 85000
REQUIRED_TOP_LEVEL_KEYS = {
    "_schema_info",
    "company_info",
    "statement_of_comprehensive_income",
    "statement_of_financial_position",
    "analysis_summary",
}

TOP_LEVEL_KEY_ALIASES = {
    "schema_info": "_schema_info",
    "income_statement": "statement_of_comprehensive_income",
    "statement_of_income": "statement_of_comprehensive_income",
    "balance_sheet": "statement_of_financial_position",
    "financial_position": "statement_of_financial_position",
    "summary": "analysis_summary",
}

ROOT_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT_DIR / "KreditLab_v7_9_updated.txt"
RENDERER_PATH = ROOT_DIR / "financial-statement-analysis" / "streamlit_financial_report_v7_7.py"


def _load_system_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise RuntimeError(f"Prompt file not found at {PROMPT_PATH}")
    # Keep prompt scope deterministic and small for lower token usage.
    return PROMPT_PATH.read_text(encoding="utf-8")


def _filter_relevant_lines(text: str, max_lines: int = 700) -> str:
    keywords = (
        "revenue",
        "profit",
        "loss",
        "income",
        "balance",
        "financial position",
        "cash flow",
        "audit",
        "audited",
        "management",
        "asset",
        "liability",
        "equity",
        "borrowings",
        "ebitda",
        "tax",
        "year",
        "202",
    )
    selected: list[str] = []
    for line in text.splitlines():
        compact = line.strip()
        if not compact:
            continue
        lower = compact.lower()
        if any(term in lower for term in keywords):
            selected.append(compact)
        if len(selected) >= max_lines:
            break
    return "\n".join(selected)


def _compact_tables_json(tables_json: Dict[str, Any], max_tables: int = 30, max_rows_per_table: int = 40) -> Dict[str, Any]:
    tables = tables_json.get("tables", []) if isinstance(tables_json, dict) else []
    compacted_tables: list[Dict[str, Any]] = []
    for table in tables[:max_tables]:
        if not isinstance(table, dict):
            continue
        compacted_tables.append(
            {
                "page": table.get("page"),
                "table_index": table.get("table_index"),
                "source_document": table.get("source_document"),
                "rows": (table.get("rows") or [])[:max_rows_per_table],
            }
        )
    return {"tables": compacted_tables}


def _prepare_stage2_payload(
    extraction_result: Dict[str, Any],
    combination_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    char_budget = int(os.environ.get("STAGE2_INPUT_CHAR_BUDGET", DEFAULT_STAGE2_INPUT_CHAR_BUDGET))
    original_text = extraction_result.get("full_text_with_tables", "")
    relevant_text = _filter_relevant_lines(original_text)
    if len(relevant_text) > char_budget:
        relevant_text = relevant_text[:char_budget]

    payload = {
        "full_text_with_tables": relevant_text,
        "tables_json": _compact_tables_json(extraction_result.get("tables_json", {})),
        "input_compaction": {
            "enabled": True,
            "char_budget": char_budget,
            "notes": "Preserve key accounting lines (including audit/management/profit & loss wording) and trim noise for lower token usage.",
        },
    }
    if combination_context:
        payload["combination_context"] = combination_context
    return payload


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


def _is_year_key(value: str) -> bool:
    lower = value.lower()
    return lower.startswith("year_") or lower.isdigit()


def _list_entry_identity(item: Dict[str, Any]) -> Optional[Tuple[Any, ...]]:
    if not isinstance(item, dict):
        return None

    for key in ("name", "label", "metric", "id", "period"):
        if key in item and item.get(key) not in (None, ""):
            return (key, item.get(key))

    if "note" in item and item.get("note") not in (None, ""):
        return ("note", item.get("note"))
    return None


def _merge_list(base: list[Any], incoming: list[Any]) -> list[Any]:
    merged = deepcopy(base)
    indexed: Dict[Tuple[Any, ...], int] = {}

    for idx, item in enumerate(merged):
        identity = _list_entry_identity(item)
        if identity is not None:
            indexed[identity] = idx

    for item in incoming:
        identity = _list_entry_identity(item)
        if identity is not None and identity in indexed and isinstance(merged[indexed[identity]], dict):
            merged[indexed[identity]] = _merge_structure(merged[indexed[identity]], item)
        else:
            merged.append(deepcopy(item))
            if identity is not None:
                indexed[identity] = len(merged) - 1

    return merged


def _merge_structure(base: Any, incoming: Any) -> Any:
    if isinstance(base, dict) and isinstance(incoming, dict):
        merged = deepcopy(base)
        for key, incoming_value in incoming.items():
            if key not in merged:
                merged[key] = deepcopy(incoming_value)
                continue

            current_value = merged[key]
            if isinstance(current_value, (dict, list)) and isinstance(incoming_value, type(current_value)):
                merged[key] = _merge_structure(current_value, incoming_value)
            elif _is_year_key(str(key)) or current_value in (None, "", [], {}):
                merged[key] = deepcopy(incoming_value)
        return merged

    if isinstance(base, list) and isinstance(incoming, list):
        return _merge_list(base, incoming)

    return deepcopy(incoming)


def merge_kreditlab_json_records(records: list[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        raise ValueError("At least one KreditLab JSON record is required")

    merged = deepcopy(records[0])
    for record in records[1:]:
        merged = _merge_structure(merged, record)

    return _limit_to_latest_periods(merged, max_periods=3)


def _extract_period_sort_key(period_key: str, label: str) -> Tuple[int, int, int, str]:
    raw = f"{period_key} {label}"
    years = re.findall(r"(20\d{2})", raw)
    year = int(years[-1]) if years else 0

    month = 12
    month_match = re.search(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b",
        label,
        re.IGNORECASE,
    )
    if month_match:
        month_map = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        month = month_map[month_match.group(1).lower()[:3]]

    label_lower = label.lower()
    if "ytd" in label_lower or "ma" in label_lower:
        source_rank = 2
    elif "audited" in label_lower or period_key.lower().startswith("fy"):
        source_rank = 1
    else:
        source_rank = 0

    return (year, month, source_rank, period_key)


def _prune_period_keys(value: Any, keep_periods: set[str], all_periods: set[str]) -> Any:
    if isinstance(value, dict):
        pruned: Dict[str, Any] = {}
        for key, child in value.items():
            if key in all_periods and key not in keep_periods:
                continue
            pruned[key] = _prune_period_keys(child, keep_periods, all_periods)
        return pruned
    if isinstance(value, list):
        return [_prune_period_keys(item, keep_periods, all_periods) for item in value]
    return value


def _limit_to_latest_periods(record: Dict[str, Any], max_periods: int = 3) -> Dict[str, Any]:
    company = record.get("company_info", {})
    periods = company.get("periods_analyzed", {})
    if not isinstance(periods, dict) or len(periods) <= max_periods:
        return record

    ranked = sorted(
        periods.items(),
        key=lambda kv: _extract_period_sort_key(kv[0], str(kv[1])),
        reverse=True,
    )
    keep_keys = [key for key, _ in ranked[:max_periods]]

    trimmed = deepcopy(record)
    trimmed["company_info"]["periods_analyzed"] = {key: periods[key] for key in keep_keys}

    keep_set = set(keep_keys)
    all_set = set(periods.keys())
    return _prune_period_keys(trimmed, keep_set, all_set)


def _combine_extraction_results(extraction_results: list[Dict[str, Any]]) -> Dict[str, Any]:
    if not extraction_results:
        raise ValueError("At least one extraction result is required")

    if len(extraction_results) == 1:
        return extraction_results[0]

    combined_text_parts: list[str] = []
    combined_tables: list[Dict[str, Any]] = []

    for idx, item in enumerate(extraction_results, start=1):
        combined_text_parts.append(f"\n\n===== SOURCE DOCUMENT {idx} =====\n")
        combined_text_parts.append(item.get("full_text_with_tables", ""))

        tables = item.get("tables_json", {}).get("tables", [])
        for table in tables:
            remapped = deepcopy(table)
            remapped["source_document"] = idx
            combined_tables.append(remapped)

    return {
        "full_text_output": "\n".join(combined_text_parts),
        "full_text_with_tables": "\n".join(combined_text_parts),
        "tables_json": {"tables": combined_tables},
    }


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

    try:
        parsed = ast.literal_eval(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, SyntaxError):
        pass

    last_error: Optional[Exception] = None
    for candidate in _json_object_candidates(cleaned):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            last_error = exc

        repaired = _repair_common_json_issues(candidate)
        if repaired != candidate:
            try:
                parsed = json.loads(repaired)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError as exc:
                last_error = exc

        try:
            parsed = ast.literal_eval(candidate)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, SyntaxError):
            pass

    if last_error:
        raise last_error
    raise json.JSONDecodeError("No JSON object found in response", cleaned, 0)


def _repair_common_json_issues(text: str) -> str:
    repaired = text
    repaired = re.sub(r"([\{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)", r'\1"\2"\3', repaired)
    repaired = repaired.replace("'", '"')
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    repaired = re.sub(r'([}\]"\d])\s*\n\s*("[A-Za-z_][A-Za-z0-9_]*"\s*:)', r'\1,\n\2', repaired)
    repaired = re.sub(r'([}\]"\d])\s+("[A-Za-z_][A-Za-z0-9_]*"\s*:)', r'\1, \2', repaired)
    repaired = re.sub(r"\bTrue\b", "true", repaired)
    repaired = re.sub(r"\bFalse\b", "false", repaired)
    repaired = re.sub(r"\bNone\b", "null", repaired)
    return repaired


def _validate_kreditlab_schema(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if not isinstance(data, dict):
        return False, f"Top-level JSON must be an object, received {type(data).__name__}"

    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(data.keys()))
    if missing:
        return False, f"Missing required top-level keys: {', '.join(missing)}"
    return True, None


def _normalize_top_level_aliases(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data

    normalized = dict(data)
    for alias, canonical in TOP_LEVEL_KEY_ALIASES.items():
        if canonical not in normalized and alias in normalized:
            normalized[canonical] = normalized[alias]
    return normalized


def _extract_schema_candidate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return the dict most likely to be the actual KreditLab payload.

    Claude occasionally wraps the target JSON in outer envelopes such as
    {"result": {...}} or {"kreditlab_json": {...}}. This helper walks nested
    dict/list values and returns the first object that satisfies required
    top-level keys, otherwise falls back to the original root object.
    """

    if isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                candidate = _extract_schema_candidate(item)
                valid, _ = _validate_kreditlab_schema(candidate)
                if valid:
                    return candidate
        return data

    if not isinstance(data, dict):
        if isinstance(data, str):
            try:
                parsed = _extract_json_object(data)
                return _extract_schema_candidate(parsed)
            except Exception:
                return data
        return data

    data = _normalize_top_level_aliases(data)

    valid, _ = _validate_kreditlab_schema(data)
    if valid:
        return data

    stack: list[Any] = [data]
    seen: set[int] = set()

    while stack:
        current = stack.pop()
        if not isinstance(current, (dict, list)):
            continue

        current_id = id(current)
        if current_id in seen:
            continue
        seen.add(current_id)

        if isinstance(current, dict):
            normalized = _normalize_top_level_aliases(current)
            valid, _ = _validate_kreditlab_schema(normalized)
            if valid:
                return normalized
            stack.extend(normalized.values())
        else:
            stack.extend(current)

    return data


def _call_anthropic(system_prompt: str, user_content: str, corrective: bool = False) -> str:
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is required")

    client = Anthropic(api_key=anthropic_api_key)
    required_key_list = ", ".join(sorted(REQUIRED_TOP_LEVEL_KEYS))
    assistant_instruction = (
        "Return ONLY valid minified JSON. No markdown fences, no explanations, no extra text. "
        f"The top-level object MUST contain these keys: {required_key_list}."
        if not corrective
        else (
            "Your previous output was invalid. Return ONLY corrected valid minified JSON matching the required schema. "
            f"The top-level object MUST contain these keys: {required_key_list}."
        )
    )

    requested_model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    max_tokens = int(os.environ.get("ANTHROPIC_MAX_TOKENS", DEFAULT_ANTHROPIC_MAX_TOKENS))
    model_candidates = [requested_model]
    if requested_model != FALLBACK_ANTHROPIC_MODEL:
        model_candidates.append(FALLBACK_ANTHROPIC_MODEL)

    last_error: Optional[Exception] = None
    message = None
    for model_name in model_candidates:
        try:
            message = client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"{assistant_instruction}\n\n"
                            "Important: Include terminology as found in source statements, including audit, management accounts, and profit and loss phrasing where applicable.\n\n"
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


def transform_to_kreditlab_json(
    extraction_result: Dict[str, Any],
    combination_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    system_prompt = _load_system_prompt()
    user_payload = _prepare_stage2_payload(
        extraction_result=extraction_result,
        combination_context=combination_context,
    )
    user_content = json.dumps(user_payload, ensure_ascii=False)

    response = _call_anthropic(system_prompt=system_prompt, user_content=user_content)

    parse_error: Optional[Exception] = None
    schema_error: Optional[str] = None

    for attempt in range(1, 4):
        try:
            parsed = _extract_json_object(response)
            candidate = _extract_schema_candidate(parsed)
            valid, error = _validate_kreditlab_schema(candidate)
            if valid:
                return _limit_to_latest_periods(candidate, max_periods=3)
            schema_error = error
            LOGGER.warning("Anthropic schema validation failed on attempt %s: %s", attempt, error)
        except Exception as exc:
            parse_error = exc
            LOGGER.warning("Failed to parse Anthropic response on attempt %s: %s", attempt, exc)

        if attempt == 3:
            break

        corrective_content = (
            "Your last output was invalid. Re-generate the complete JSON from source data. "
            "Return ONLY one valid JSON object with all required keys and no markdown fences.\n\n"
            f"PARSE_ERROR: {parse_error}\n"
            f"SCHEMA_ERROR: {schema_error}\n\n"
            "SOURCE_DATA:\n"
            f"{user_content}"
        )
        response = _call_anthropic(
            system_prompt=system_prompt,
            user_content=corrective_content,
            corrective=True,
        )

    if parse_error is not None:
        raise RuntimeError(f"Claude response is not valid JSON after retries: {parse_error}") from parse_error
    if schema_error is not None:
        raise RuntimeError(f"Claude response failed schema checks after retries: {schema_error}")
    raise RuntimeError("Claude response was invalid after retries")


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


def transform_multiple_extractions_to_kreditlab_json(
    extraction_results: list[Dict[str, Any]],
    source_filenames: Optional[list[str]] = None,
) -> Dict[str, Any]:
    if not extraction_results:
        raise ValueError("At least one extraction result is required")

    combined_extraction = _combine_extraction_results(extraction_results)
    combination_context: Dict[str, Any] = {
        "combine_documents": True,
        "total_source_documents": len(extraction_results),
        "instruction": (
            "All uploaded files belong to ONE case and must be transformed into ONE canonical KreditLab JSON object "
            "(schema version v7.9). Use all source documents together (do not prioritize only one file), "
            "apply source authority rules, and never default missing values to zero. "
            "If a label/parameter is not explicitly recognized, preserve it and map it to the closest relevant section "
            "with the original label retained in metadata."
        ),
    }
    if source_filenames:
        combination_context["source_filenames"] = source_filenames

    return transform_to_kreditlab_json(combined_extraction, combination_context=combination_context)
