"""Factory for the vision classifier used by POST /assets/{id}/classify (FR2.2).

The provider choice lives in exactly this one place, per CLAUDE.md's "the call
lives in one place" convention (already applied to the image-generation tool
choice) — swapping MockVisionProvider for a real provider once PRD §14's
decision + a key land is a one-line change here, nothing in
app/routers/assets.py needs to change.

No vision-API key exists in this environment as of this sync (checked
VISION_API_KEY/ANTHROPIC_API_KEY/OPENAI_API_KEY/GOOGLE_API_KEY - none
present), and vision-ai-engineer's AnthropicVisionProvider is a deliberate
stub that raises NotImplementedError even when a key is present (PRD §14's
provider choice is still open) - so MockVisionProvider is the only provider
actually wired up today, not a placeholder standing in for something broken.
"""

from __future__ import annotations

from services.vision_classifier import VisionClassifierService
from services.vision_providers.mock import MockVisionProvider


def get_vision_classifier_service() -> VisionClassifierService:
    return VisionClassifierService(MockVisionProvider())
