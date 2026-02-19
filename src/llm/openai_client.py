from __future__ import annotations

import copy
import os
import time
from typing import Any, Dict, Optional

from openai import OpenAI


def get_client() -> OpenAI:
    # Official OpenAI SDK reads OPENAI_API_KEY
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def get_model(default: str = "gpt-4.1-mini") -> str:
    # You asked Step 5.1 to run on 4.1 mini
    return os.environ.get("OPENAI_MODEL", default)


def _sleep_backoff(attempt: int) -> None:
    # 1s, 2s, 4s (capped)
    time.sleep(min(8, 2**attempt))


def _enforce_required_all(schema: Any) -> Any:
    """
    Option A: For Structured Outputs strict mode, OpenAI requires that for any object schema
    that declares 'properties', the 'required' array must include *every* property key.
    We apply that rule recursively to the whole schema.
    """
    if not isinstance(schema, (dict, list)):
        return schema

    if isinstance(schema, list):
        return [_enforce_required_all(x) for x in schema]

    s = copy.deepcopy(schema)

    # Recurse into combinators if ever present
    for k in ("anyOf", "oneOf", "allOf"):
        if k in s and isinstance(s[k], list):
            s[k] = [_enforce_required_all(x) for x in s[k]]

    # Recurse into array items
    if s.get("type") == "array" and "items" in s:
        s["items"] = _enforce_required_all(s["items"])

    # If this is an object with properties, enforce required
    if s.get("type") == "object" and isinstance(s.get("properties"), dict):
        props = s["properties"]

        # First recurse into each property schema
        for pk, pv in list(props.items()):
            props[pk] = _enforce_required_all(pv)

        # Now enforce required = all property keys
        all_keys = list(props.keys())
        s["required"] = all_keys

    return s


def call_structured(
    *,
    instructions: str,
    user_input: str,
    schema: Dict[str, Any],
    model: Optional[str] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Calls OpenAI Responses API and requests a JSON object matching `schema`.
    Returns parsed JSON (dict). Retries on transient failures.

    Uses Responses API Structured Outputs via:
      text={ "format": { "type": "json_schema", "name": "...", "schema": ..., "strict": True } }
    """
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = get_client()
    m = model or get_model()

    # Option A: normalize schema for strict structured outputs
    strict_schema = _enforce_required_all(schema)

    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            resp = client.responses.create(
                model=m,
                instructions=instructions,
                input=user_input,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "locality_report_narratives",
                        "schema": strict_schema,
                        "strict": True,
                    }
                },
            )

            import json

            return json.loads(resp.output_text)

        except Exception as e:
            last_err = e
            _sleep_backoff(attempt)

    raise RuntimeError(f"OpenAI call failed after retries: {last_err}")