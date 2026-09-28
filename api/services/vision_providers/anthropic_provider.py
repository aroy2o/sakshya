"""
STUB — not callable in this environment.

No vision-capable API key is configured (checked VISION_API_KEY,
ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY as of 2026-09-28 — none
present; logged to PROGRESS.md's "Needs your attention"). PRD.md §14 also still
lists the vision-LLM provider itself as an open decision, so this file is named
for the most likely candidate, not a locked-in choice.

Left unimplemented rather than faked: a stub that silently returned canned JSON
would look like a working integration, which violates CLAUDE.md's "never
fabricate a number." The prompt template (build_classifier_prompt, in
vision_classifier.py) and the strict response schema (ClassifierResult) are
already built and pytest-covered against MockVisionProvider — wiring up the
actual API call here is the only piece left once a provider + key are chosen.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .base import VisionProvider, VisionProviderNotConfigured

# Checked in priority order: a generic override first, then the provider-specific name.
VISION_API_KEY_ENV_VARS = ("VISION_API_KEY", "ANTHROPIC_API_KEY")


class AnthropicVisionProvider(VisionProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-5"):
        self.model = model
        self.api_key = api_key or next(
            (os.environ[var] for var in VISION_API_KEY_ENV_VARS if os.environ.get(var)),
            None,
        )

    def classify_raw(
        self,
        image_path: Path,
        declared_category: str,
        declared_activity: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise VisionProviderNotConfigured(
                f"No vision API key found (checked {', '.join(VISION_API_KEY_ENV_VARS)}). "
                "Use MockVisionProvider until a provider + key are chosen (PRD §14)."
            )
        # TODO(vision-ai-engineer, once PRD §14 is resolved with a key available):
        # send image_path's bytes as a base64 image content block alongside
        # build_classifier_prompt(declared_category, declared_activity) to the
        # chosen vision-capable model, parse its JSON text response, and return
        # the parsed dict. Raise VisionProviderError on any transport/parse
        # failure so VisionClassifierService's retry/fallback path handles it.
        raise NotImplementedError(
            "Live vision-LLM call not yet implemented — provider choice is still open "
            "per PRD §14 and no key is available to test against in this session."
        )
