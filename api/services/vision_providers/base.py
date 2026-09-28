"""
Provider interface for SAKSHYA's AI Image Interpreter (PRD Phase 2, FR2.1).

The vision-LLM vendor is intentionally not locked in here — PRD.md §14 still
lists it as an open decision ("Vision LLM provider for Phase 2 — decide by cost/
quota available on demo day"). This ABC is the seam: swap providers by passing a
different VisionProvider into VisionClassifierService, same principle CLAUDE.md
already applies to the image-generation tool choice ("the call lives in one
place").
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class VisionProviderError(Exception):
    """Raised on a transport/parse failure calling a vision provider (network
    error, non-JSON response, HTTP error, etc). Distinct from a *validation*
    failure of a structurally-parseable-but-schema-invalid response — that's
    handled one layer up, by ClassifierResult.model_validate in
    VisionClassifierService, so both failure modes go through the same
    retry-then-degrade-to-uncertain path."""


class VisionProviderNotConfigured(VisionProviderError):
    """Raised when a provider needs credentials that aren't present in the
    environment (e.g. no vision API key). Never caught and silently
    worked around — it's meant to surface as a hard stop. A provider that
    quietly fell back to fabricated data instead of raising this would violate
    CLAUDE.md's 'never fabricate a number' rule."""


class VisionProvider(ABC):
    """Common interface every vision backend (mock, or a real vision LLM)
    implements. `name` is recorded into ai_result.provider for traceability —
    the dashboard/report must always be able to show which provider produced
    a given classification, especially while the real provider is a stub and
    everything running is MockVisionProvider."""

    name: str = "base"

    @abstractmethod
    def classify_raw(
        self,
        image_path: Path,
        declared_category: str,
        declared_activity: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return the raw parsed JSON dict describing the photo, in the shape
        ClassifierResult expects (see vision_classifier.py). Must raise
        VisionProviderError (or VisionProviderNotConfigured) on failure rather
        than returning a best-guess dict — schema/enum validation of a
        successfully-returned dict is the caller's job, not this method's."""
        raise NotImplementedError
