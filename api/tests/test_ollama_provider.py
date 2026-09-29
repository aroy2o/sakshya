"""
Tests for OllamaVisionProvider: the forgiving JSON-extraction step (local
models often wrap JSON in prose or markdown fences) and the provider's error
handling. These mock requests.post — no live Ollama server or pulled model is
required, so they run fast and deterministically in CI, same as every other
test in this file's neighbors. Actually classifying real images against a live
Ollama server is exercised separately by `scripts/batch_classify.py --provider
ollama` (manual/offline, not part of the automated pytest suite — real
local-model inference is slow and environment-dependent, not something to
gate CI on).
"""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest
import requests

from services.vision_providers.base import VisionProviderError
from services.vision_providers.ollama_provider import OllamaVisionProvider, extract_json_object

VALID_RESULT = {
    "predicted_category": "SM",
    "predicted_activity": "check dam",
    "construction_stage": "completed",
    "water_visible": "yes",
    "vegetation_cover": "medium",
    "matches_declared": "yes",
    "confidence": 0.8,
    "evidence": "a concrete dam wall is visible",
}


# ---------------------------------------------------------------------------
# extract_json_object -- the forgiving parse step
# ---------------------------------------------------------------------------


def test_extract_bare_json():
    text = json.dumps(VALID_RESULT)
    assert extract_json_object(text) == VALID_RESULT


def test_extract_json_wrapped_in_markdown_fence():
    text = f"```json\n{json.dumps(VALID_RESULT)}\n```"
    assert extract_json_object(text) == VALID_RESULT


def test_extract_json_wrapped_in_plain_fence_no_language_tag():
    text = f"```\n{json.dumps(VALID_RESULT)}\n```"
    assert extract_json_object(text) == VALID_RESULT


def test_extract_json_wrapped_in_prose():
    text = f"Sure, here is my analysis:\n\n{json.dumps(VALID_RESULT)}\n\nLet me know if you need more detail."
    assert extract_json_object(text) == VALID_RESULT


def test_extract_json_with_nested_braces_in_evidence_field():
    """A naive first-'{'-to-last-'}' scan would work here too, but a naive
    first-'{'-to-first-'}' scan would truncate mid-object -- this asserts the
    brace-depth-matched scan handles a value that itself contains braces."""
    payload = dict(VALID_RESULT)
    payload["evidence"] = "the {dam} wall is visible with a spillway"
    text = f"Here you go: {json.dumps(payload)} -- hope that helps!"
    assert extract_json_object(text) == payload


def test_extract_raises_on_no_json_present():
    with pytest.raises(json.JSONDecodeError):
        extract_json_object("I cannot analyze this image, sorry.")


def test_extract_raises_on_json_array_not_object():
    with pytest.raises(json.JSONDecodeError):
        extract_json_object("[1, 2, 3]")


# ---------------------------------------------------------------------------
# OllamaVisionProvider -- request building and error handling, requests.post mocked
# ---------------------------------------------------------------------------


def _mock_response(json_body: dict) -> Mock:
    resp = Mock()
    resp.raise_for_status = Mock()
    resp.json = Mock(return_value=json_body)
    return resp


def test_provider_sends_expected_payload_shape(tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"fake-jpeg-bytes")

    with patch("services.vision_providers.ollama_provider.requests.post") as mock_post:
        mock_post.return_value = _mock_response({"response": json.dumps(VALID_RESULT)})
        provider = OllamaVisionProvider(model="moondream", base_url="http://localhost:11434")
        result = provider.classify_raw(image_path, "SM", "Check Dam")

    assert result == VALID_RESULT
    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["model"] == "moondream"
    assert call_kwargs.kwargs["json"]["stream"] is False
    assert call_kwargs.kwargs["json"]["format"] == "json"
    assert len(call_kwargs.kwargs["json"]["images"]) == 1
    assert "Check Dam" in call_kwargs.kwargs["json"]["prompt"]


def test_provider_raises_vision_provider_error_on_connection_failure(tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"fake-jpeg-bytes")

    with patch("services.vision_providers.ollama_provider.requests.post") as mock_post:
        mock_post.side_effect = requests.ConnectionError("connection refused")
        provider = OllamaVisionProvider()
        with pytest.raises(VisionProviderError, match="Ollama request failed"):
            provider.classify_raw(image_path, "SM", "Check Dam")


def test_provider_raises_vision_provider_error_on_empty_response(tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"fake-jpeg-bytes")

    with patch("services.vision_providers.ollama_provider.requests.post") as mock_post:
        mock_post.return_value = _mock_response({"response": ""})
        provider = OllamaVisionProvider()
        with pytest.raises(VisionProviderError, match="empty"):
            provider.classify_raw(image_path, "SM", "Check Dam")


def test_provider_raises_vision_provider_error_on_unparseable_response(tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"fake-jpeg-bytes")

    with patch("services.vision_providers.ollama_provider.requests.post") as mock_post:
        mock_post.return_value = _mock_response({"response": "I really cannot say anything useful here."})
        provider = OllamaVisionProvider()
        with pytest.raises(VisionProviderError, match="could not extract"):
            provider.classify_raw(image_path, "SM", "Check Dam")


def test_provider_raises_vision_provider_error_on_missing_image_file():
    provider = OllamaVisionProvider()
    with pytest.raises(VisionProviderError, match="could not read image"):
        provider.classify_raw("/nonexistent/path.jpg", "SM", "Check Dam")


def test_provider_extracts_json_wrapped_in_prose_end_to_end(tmp_path):
    """Integration of extract_json_object into the provider's actual flow --
    the exact failure mode this whole feature exists to recover from."""
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"fake-jpeg-bytes")
    prose_wrapped = f"Looking at this image, here's what I see:\n{json.dumps(VALID_RESULT)}\nHope this helps."

    with patch("services.vision_providers.ollama_provider.requests.post") as mock_post:
        mock_post.return_value = _mock_response({"response": prose_wrapped})
        provider = OllamaVisionProvider()
        result = provider.classify_raw(image_path, "SM", "Check Dam")

    assert result == VALID_RESULT


def test_provider_defaults_to_moondream_and_localhost():
    provider = OllamaVisionProvider()
    assert provider.model == "moondream"
    assert provider.base_url == "http://localhost:11434"


def test_provider_respects_env_var_overrides(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "llava:7b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://example.internal:9999")
    provider = OllamaVisionProvider()
    assert provider.model == "llava:7b"
    assert provider.base_url == "http://example.internal:9999"
