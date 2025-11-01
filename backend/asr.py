from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import settings

try:
    from faster_whisper import WhisperModel  # type: ignore
except ImportError:  # pragma: no cover - optional dependency in mock mode
    WhisperModel = None  # type: ignore[assignment]

import httpx


@dataclass
class TranscriptionResult:
    transcript: str
    duration: float


class Transcriber:
    """Simple strategy wrapper that defers model loading until needed."""

    def __init__(
        self,
        strategy: str = settings.transcription_strategy,
        model_name: str = settings.whisper_model,
        compute_type: str = settings.whisper_compute_type,
    ) -> None:
        self.strategy = strategy
        self.model_name = model_name
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    def _ensure_model(self) -> None:
        if self.strategy == "mock":
            return
        if self._model is not None:
            return
        if WhisperModel is None:
            raise RuntimeError(
                "faster-whisper is not installed. Install optional dependencies or set "
                "UNPOSTED_TRANSCRIPTION_STRATEGY=mock.",
            )
        self._model = WhisperModel(self.model_name, compute_type=self.compute_type)

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        if self.strategy == "mock":
            return TranscriptionResult(
                transcript="This is a placeholder transcript. Configure faster-whisper to enable real ASR.",
                duration=0.0,
            )

        audio_path = audio_path.resolve()
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file missing: {audio_path}")

        # Olama (HTTP) strategy: POST audio file to configured Olama endpoint
        if self.strategy == "olama":
            olama_url = settings.olama_url or ""
            if not olama_url:
                raise RuntimeError(
                    "Olama transcription selected but UNPOSTED_OLAMA_URL is not set."
                    " Set UNPOSTED_OLAMA_URL to your Olama HTTP endpoint."
                )

            headers = {}
            if settings.olama_api_key:
                headers["Authorization"] = f"Bearer {settings.olama_api_key}"

            # Send file as multipart/form-data under 'file' key. Adjust as needed for your Olama endpoint.
            with audio_path.open("rb") as fh:
                files = {"file": (audio_path.name, fh, "application/octet-stream")}
                try:
                    resp = httpx.post(olama_url, headers=headers, files=files, timeout=60.0)
                except httpx.HTTPError as exc:
                    raise RuntimeError(f"Failed to contact Olama endpoint: {exc}") from exc

            if resp.status_code != 200:
                raise RuntimeError(f"Olama request failed: {resp.status_code} {resp.text}")

            try:
                data = resp.json()
            except ValueError:
                raise RuntimeError("Olama response was not valid JSON")

            # Accept either 'transcript' or 'text' fields from Olama response
            transcript = data.get("transcript") or data.get("text")
            if not transcript:
                raise RuntimeError("Olama response did not contain a transcript field")

            duration = float(data.get("duration", 0.0))
            return TranscriptionResult(transcript=str(transcript).strip(), duration=duration)

        # Default: faster-whisper
        self._ensure_model()
        assert self._model is not None  # mypy hint

        segments, info = self._model.transcribe(str(audio_path))
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        return TranscriptionResult(transcript=transcript, duration=float(getattr(info, "duration", 0.0)))


transcriber = Transcriber()
