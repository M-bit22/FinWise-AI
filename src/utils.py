import json
import re
from typing import Any


REQUIRED_FIELDS = {
    "financial_summary": "",
    "key_findings": [],
    "financial_health_score": 50,
    "spending_analysis": [],
    "risk_level": "MEDIUM",
    "top_priorities": [],
    "budget_recommendations": [],
    "savings_strategy": [],
    "next_month_action_plan": [],
}


def _content_to_text(raw_text: Any) -> str:
    """Normalize Gemini/LangChain content, which may be text or a list of parts."""
    if raw_text is None:
        return ""
    if isinstance(raw_text, str):
        return raw_text.strip()
    if isinstance(raw_text, list):
        parts = []
        for part in raw_text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text")
                if text:
                    parts.append(str(text))
            else:
                text = getattr(part, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return str(raw_text).strip()


def _extract_json_object(text: str):
    """Find the first complete JSON object, tolerating prose and Markdown fences."""
    cleaned = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```", "", cleaned).strip()
    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except (json.JSONDecodeError, TypeError):
        pass

    # Scan for a balanced {...} while respecting quoted strings and escaped quotes.
    start = cleaned.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(cleaned)):
            char = cleaned[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start:index + 1]
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        break
        start = cleaned.find("{", start + 1)
    return None


def parse_llm_json(raw_text: Any) -> dict:
    """Parse and normalize the FinWise response without silently hiding parse failures."""
    text = _content_to_text(raw_text)
    parsed = _extract_json_object(text)
    if not isinstance(parsed, dict) and text:
        # Optional tolerant repair for common model output defects (trailing commas,
        # unquoted keys, or truncated-ish JSON). The dependency is optional at runtime.
        try:
            from json_repair import repair_json
            repaired = repair_json(text, return_objects=True)
            if isinstance(repaired, dict):
                parsed = repaired
            elif isinstance(repaired, str):
                parsed = _extract_json_object(repaired)
        except Exception:
            pass
    if not isinstance(parsed, dict):
        result = dict(REQUIRED_FIELDS)
        result["_parse_error"] = True
        result["_raw_response"] = text[:3000]
        result["_parse_message"] = (
            "Gemini returned text that could not be parsed as a JSON object. "
            "Check the raw response in the app's technical details."
        )
        return result

    result = dict(REQUIRED_FIELDS)
    result.update(parsed)
    result["_parse_error"] = False

    # Normalize list fields and ignore null/empty model values.
    for key in (
        "key_findings", "spending_analysis", "top_priorities",
        "budget_recommendations", "savings_strategy", "next_month_action_plan",
    ):
        value = result.get(key)
        if not isinstance(value, list):
            result[key] = [str(value)] if value not in (None, "") else []
        result[key] = [item for item in result[key] if item not in (None, "")]
    # Spending-analysis entries should be objects; convert accidental scalar entries
    # into a safe, renderable object instead of failing in the dashboard.
    normalized_spending = []
    for item in result.get("spending_analysis", []):
        if isinstance(item, dict):
            normalized_spending.append({
                "category": str(item.get("category", "General")),
                "observation": str(item.get("observation", "")),
                "recommendation": str(item.get("recommendation", "")),
            })
        else:
            normalized_spending.append({
                "category": "General",
                "observation": str(item),
                "recommendation": "Review this item against your monthly budget.",
            })
    result["spending_analysis"] = normalized_spending
    try:
        result["financial_health_score"] = max(
            0, min(100, int(float(result.get("financial_health_score", 50))))
        )
    except (TypeError, ValueError):
        result["financial_health_score"] = 50
    risk = str(result.get("risk_level", "MEDIUM")).upper().strip()
    result["risk_level"] = risk if risk in {"LOW", "MEDIUM", "HIGH"} else "MEDIUM"
    if not isinstance(result.get("financial_summary"), str):
        result["financial_summary"] = str(result.get("financial_summary", ""))
    return result
