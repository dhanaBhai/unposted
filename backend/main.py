from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .asr import TranscriptionResult, transcriber
from .config import settings


class TranscriptionResponse(BaseModel):
    transcript: str
    duration: float


ACCEPTED_MIME_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/x-m4a",
}


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Lightweight welcome to confirm the service is running."""
    return {"message": "Unposted backend is running", "docs": "/docs"}


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _persist_upload(file: UploadFile, destination: Path) -> None:
    """Persist the incoming UploadFile to disk in chunks."""
    chunk_size = 1024 * 1024  # 1 MiB
    with destination.open("wb") as buffer:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            buffer.write(chunk)


@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)) -> TranscriptionResponse:
    if file.content_type not in ACCEPTED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported media type: {file.content_type}")

    suffix = Path(file.filename or "recording.webm").suffix or ".webm"
    temp_dir = settings.temp_dir

    with NamedTemporaryFile(dir=temp_dir, suffix=suffix, delete=False) as tmp:
        temp_path = Path(tmp.name)

    try:
        await _persist_upload(file, temp_path)
        result: TranscriptionResult = transcriber.transcribe(temp_path)
        return TranscriptionResponse.model_validate(result.__dict__)
    except Exception as exc:  # pragma: no cover - surface unexpected errors with message
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            # Swallow cleanup errors; failing to delete is non-critical.
            pass
