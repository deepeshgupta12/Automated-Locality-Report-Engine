from __future__ import annotations

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

    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            resp = client.responses.create(
                model=m,
                instructions=instructions,
                input=user_input,
                # Structured Outputs (JSON Schema) for Responses API
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "locality_report_narratives",
                        "schema": schema,
                        "strict": True,
                    }
                },
            )

            # output_text will be JSON string due to text.format=json_schema
            import json

            return json.loads(resp.output_text)

        except Exception as e:
            last_err = e
            _sleep_backoff(attempt)

    raise RuntimeError(f"OpenAI call failed after retries: {last_err}")