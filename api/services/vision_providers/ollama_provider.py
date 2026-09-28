"""
Local, free vision provider using Ollama (http://localhost:11434) — no API key,
no hosted-API cost. Added per explicit instruction: run a real (non-mocked)
classifier without paying for a hosted vision API.

Model choice: this environment has 15GB RAM with Postgres containers already
running (observed ~5.8GB available at the time this was wired up) — tight
enough that a larger vision model (llava:7b, ~4.7GB of weights) risks memory
pressure alongside those. Defaults to `moondream` (~828MB), the smallest
vision-capable Ollama model, which is safe within that budget. Override via
the OLLAMA_MODEL env var once more headroom exists or a larger pull is
confirmed to fit — see get_vision_classifier_service() in
app/services/vision.py for where the choice is actually made for the live app.

Local models are meaningfully less reliable at strict JSON-only output than a
hosted frontier model — they sometimes wrap the JSON answer in prose or
markdown code fences even when told not to. extract_json_object() below
recovers that before handing a dict up to VisionClassifierService, which still
does the real enum/type enforcement via ClassifierResult.model_validate() and
already degrades to an honest 'uncertain' result (never a fabricated guess) if
even this forgiving extraction fails — that behavior is untouched here.
"""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

import requests

from .base import VisionProvider, VisionProviderError

OLLAMA_BASE_URL_ENV_VAR = "OLLAMA_BASE_URL"
OLLAMA_MODEL_ENV_VAR = "OLLAMA_MODEL"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "moondream"
# Local CPU inference is slow (multi-second to tens-of-seconds per image on
# modest hardware) -- generous on purpose, this is an offline batch/manual-
# classify path, never a live request-path call (CLAUDE.md precompute-first).
REQUEST_TIMEOUT_S = 120

_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json_object(text: str) -> dict[str, Any]:
    """Recover a JSON object from text a local model may have wrapped in
    prose or a markdown code fence instead of returning bare JSON. Tries, in
    order: the whole text as-is, the contents of the first fenced code block,
    then the first balanced {...} block found anywhere (brace-depth matched,
    so a nested object inside e.g. "evidence" doesn't truncate the match).
    Raises json.JSONDecodeError if nothing in the text parses as a JSON
    object -- the caller wraps that as a VisionProviderError, which
    VisionClassifierService already treats as "never fabricate a guess,
    degrade to uncertain instead" (unchanged by this function existing)."""
    text = text.strip()
    candidates = [text]

    fence_match = _CODE_FENCE_RE.search(text)
    if fence_match:
        candidates.append(fence_match.group(1).strip())

    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start : i + 1])
                    break

    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if isinstance(parsed, dict):
            return parsed
        last_error = json.JSONDecodeError(f"parsed JSON was a {type(parsed).__name__}, not an object", candidate, 0)

    raise last_error or json.JSONDecodeError("no JSON object found in text", text, 0)


class OllamaVisionProvider(VisionProvider):
    name = "ollama"

    def __init__(self, model: str | None = None, base_url: str | None = None):
        self.model = model or os.environ.get(OLLAMA_MODEL_ENV_VAR, DEFAULT_MODEL)
        self.base_url = (base_url or os.environ.get(OLLAMA_BASE_URL_ENV_VAR, DEFAULT_BASE_URL)).rstrip("/")

    def classify_raw(
        self,
        image_path: Path,
        declared_category: str,
        declared_activity: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            image_bytes = Path(image_path).read_bytes()
        except OSError as exc:
            raise VisionProviderError(f"could not read image at {image_path}: {exc}") from exc
        image_b64 = base64.b64encode(image_bytes).decode("ascii")

        # Local import: services.vision_classifier imports services.vision_providers.base,
        # which (via this package's __init__.py) imports this module - a module-level
        # import here would be a circular import that breaks every import of
        # services.vision_providers, not just Ollama usage. By the time classify_raw()
        # actually runs, vision_classifier is fully initialized, so this is safe.
        from services.vision_classifier import build_classifier_prompt

        prompt = build_classifier_prompt(declared_category, declared_activity)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "format": "json",  # nudges Ollama toward valid JSON syntax; not a schema guarantee
            "stream": False,
            "options": {"temperature": 0},  # as deterministic as possible, no creative guessing
        }
        try:
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=REQUEST_TIMEOUT_S)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise VisionProviderError(
                f"Ollama request failed (model={self.model!r}, url={self.base_url!r}): {exc}. "
                f"Is `ollama serve` running, and has `ollama pull {self.model}` been run?"
            ) from exc

        try:
            body = resp.json()
        except ValueError as exc:
            raise VisionProviderError(f"Ollama returned a non-JSON HTTP response: {exc}") from exc

        raw_text = body.get("response", "")
        if not raw_text:
            raise VisionProviderError(f"Ollama returned an empty 'response' field: {body!r}")

        try:
            parsed = extract_json_object(raw_text)
        except json.JSONDecodeError as exc:
            raise VisionProviderError(
                f"could not extract a JSON object from Ollama's response text ({exc}). "
                f"Raw text (truncated): {raw_text[:300]!r}"
            ) from exc

        # moondream (and likely other small local models) reliably gets the
        # structured fields right but sometimes leaves "evidence" as "" -
        # ClassifierResult requires min_length=1 there. Discarding an
        # otherwise-valid, well-formed classification over one empty
        # supplementary field throws away real signal (predicted_category/
        # confidence/matches_declared) for no benefit - observed empirically:
        # this exact failure degraded 16/16 live classifications to a
        # fabricated-looking "uncertain, confidence=0.0" during the Reality
        # Pass reseed, when the model was very likely actually answering.
        # Coerce here (provider-specific quirk), not by loosening
        # ClassifierResult's schema for every provider.
        if isinstance(parsed.get("evidence"), str) and not parsed["evidence"].strip():
            parsed["evidence"] = "(model did not provide a text justification for this classification)"

        return parsed
