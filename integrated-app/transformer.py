import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic

PROMPT_FILE = Path(__file__).resolve().parents[1] / "KreditLab_v7_9_updated.txt"
REQUIRED_KEYS = {
    "_schema_info",
    "company_info",
    "statement_of_comprehensive_income",
    "statement_of_financial_position",
    "analysis_summary",
}


def _extract_json_block(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in Claude response")
    return stripped[start : end + 1]


def _parse_and_validate(text: str) -> dict[str, Any]:
    content = _extract_json_block(text)
    parsed = json.loads(content)

    missing = [key for key in REQUIRED_KEYS if key not in parsed]
    if missing:
        raise ValueError(f"Missing required top-level keys: {', '.join(sorted(missing))}")
    return parsed


def _call_claude(client: Anthropic, system_prompt: str, user_content: str) -> str:
    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=8192,
        temperature=0,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": user_content,
            }
        ],
    )

    parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "\n".join(parts).strip()


def transform_to_kreditlab_json(full_text_with_tables: str, tables_json: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required")

    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    client = Anthropic(api_key=api_key)

    base_user_prompt = (
        "Convert the following extracted financial statement content to KreditLab JSON. "
        "Return ONLY valid JSON with no markdown, no backticks, and no commentary.\n\n"
        f"full_text_with_tables:\n{full_text_with_tables}\n\n"
        f"tables_json:\n{json.dumps(tables_json, ensure_ascii=False)}"
    )

    first = _call_claude(client, system_prompt, base_user_prompt)
    try:
        return _parse_and_validate(first)
    except Exception as first_err:
        corrective_prompt = (
            f"The previous response was invalid: {first_err}. "
            "Return JSON only and fix schema/JSON issues. Do not include markdown or explanation.\n\n"
            f"Source data:\n{base_user_prompt}"
        )
        second = _call_claude(client, system_prompt, corrective_prompt)
        try:
            return _parse_and_validate(second)
        except Exception as second_err:
            raise RuntimeError(f"Claude JSON parse/validation failed after retry: {second_err}") from second_err
