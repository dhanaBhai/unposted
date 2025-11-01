from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, cast
from dotenv import load_dotenv


def _get_env(name: str, default: str) -> str:
    return os.environ.get(f"UNPOSTED_{name}", default)


def _get_bool(name: str, default: bool) -> bool:
    value = os.environ.get(f"UNPOSTED_{name}")
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_list(name: str, default: list[str]) -> list[str]:
    value = os.environ.get(f"UNPOSTED_{name}")
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    """Minimal settings loader without external dependencies."""

    def __init__(self) -> None:
        # Load environment variables from the backend/.env file if present
        env_path = Path(__file__).parent / ".env"
        load_dotenv(env_path)
        self.app_name: str = _get_env("APP_NAME", "Unposted API")
        self.cors_origins: list[str] = _get_list("CORS_ORIGINS", ["http://localhost:5173"])
        strategy = _get_env("TRANSCRIPTION_STRATEGY", "mock")
        # Support mock, faster-whisper, and olama strategies
        if strategy not in {"mock", "faster-whisper", "olama"}:
            strategy = "mock"
        self.transcription_strategy: Literal["mock", "faster-whisper", "olama"] = cast(
            Literal["mock", "faster-whisper", "olama"], strategy
        )
        self.whisper_model: str = _get_env("WHISPER_MODEL", "base")
        self.whisper_compute_type: str = _get_env("WHISPER_COMPUTE_TYPE", "int8")
        self.temp_dir: Path = Path(_get_env("TEMP_DIR", "tmp"))
        # Olama (HTTP) settings
        # Example: UNPOSTED_OLAMA_URL=http://127.0.0.1:11434/transcribe
        self.olama_url: str = _get_env("OLAMA_URL", "")
        self.olama_api_key: str = _get_env("OLAMA_API_KEY", "")
        self.enable_encryption: bool = _get_bool("ENABLE_ENCRYPTION", False)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
