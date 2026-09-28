"""Factory for the vision classifier used by POST /assets/{id}/classify (FR2.2).

The provider choice lives in exactly this one place, per CLAUDE.md's "the call
lives in one place" convention (already applied to the image-generation tool
choice) — swapping providers is a one-line change here, nothing in
app/routers/assets.py needs to change.

No hosted vision-API key exists in this environment (checked VISION_API_KEY/
ANTHROPIC_API_KEY/OPENAI_API_KEY/GOOGLE_API_KEY — none present), and
vision-ai-engineer's AnthropicVisionProvider is a deliberate stub that raises
NotImplementedError even when a key is present (PRD §14's hosted-provider
choice is still open). Per explicit instruction, the real default is now a
local, free Ollama model (see vision_providers/ollama_provider.py) instead of
a hosted API — `moondream` was pulled and is running locally as of this sync.
MockVisionProvider is kept for what it's already used for: fast/deterministic
unit tests (api/tests/test_vision_classifier.py), not as the production
stand-in anymore now that a real local option exists.
"""

from __future__ import annotations

from services.vision_classifier import VisionClassifierService
from services.vision_providers.ollama_provider import OllamaVisionProvider


def get_vision_classifier_service() -> VisionClassifierService:
    return VisionClassifierService(OllamaVisionProvider())
