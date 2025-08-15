"""
Text‑to‑speech (TTS) integration stub.

This module defines an interface for synthesising audio for Arabic
lemmas and examples.  The actual implementation is intentionally
pluggable so that one can integrate providers such as Google Cloud
Text‑to‑Speech or Azure Cognitive Services.  Currently it raises
``NotImplementedError`` because no provider is configured.
"""

from __future__ import annotations

from typing import Optional, Dict, Any


class TTSProvider:
    """Abstract base class for TTS providers."""

    def synthesize(self, text: str, dialect: str = "msa") -> Dict[str, Any]:
        """Synthesize the given text and return audio metadata.

        Args:
            text: The text to synthesise.
            dialect: The dialect code (e.g. 'msa', 'arz').

        Returns:
            A dictionary containing at least a URL or binary for the audio.
        """
        raise NotImplementedError


class DummyTTS(TTSProvider):
    """A no‑op TTS provider used when no real provider is configured."""

    def synthesize(self, text: str, dialect: str = "msa") -> Dict[str, Any]:
        # This dummy implementation just returns the input text for
        # demonstration.  Replace with calls to a real TTS API.
        return {
            "dialect": dialect,
            "text": text,
            "audio": None,
            "provider": "none",
        }
