# Unposted – Private Audio Journaling POC

Unposted is a minimal proof-of-concept journaling experience built to respect privacy and keep every entry on-device. The app walks you through recording short voice notes, transcribing them with a local FastAPI backend, and reviewing your thoughts in a card-based dashboard.

- **Frontend:** React (Vite), TypeScript, TailwindCSS, Zustand
- **Backend:** FastAPI, Python 3.11, Whisper / faster-whisper (CPU inference), `cryptography` (optional Fernet encryption)
- **Storage:** Audio blobs and transcripts stay in the browser (IndexedDB via Dexie). Backend keeps nothing after responding.

> Private by default. No cloud persistence. You own the recordings.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [User Flows](#user-flows)
3. [Repository Layout](#repository-layout)
4. [Prerequisites](#prerequisites)
5. [Quickstart](#quickstart)
6. [Frontend App](#frontend-app)
7. [Backend API](#backend-api)
8. [Transcription Pipeline](#transcription-pipeline)
9. [Local Storage Layer](#local-storage-layer)
10. [Testing & Linting](#testing--linting)
11. [Stretch Ideas](#stretch-ideas)
12. [FAQ](#faq)

---

## System Overview

| Slice      | Purpose                                             | Tech                                                         |
|------------|-----------------------------------------------------|--------------------------------------------------------------|
| Frontend   | Recording UI, waveform, journal cards, settings     | Vite + React, Tailwind, Zustand, Dexie (IndexedDB)           |
| Backend    | Receives audio, runs Whisper, returns transcript    | FastAPI, Uvicorn, Whisper / faster-whisper                   |
| Security   | Local-only persistence, optional AES-256 encryption | Fernet (from `cryptography`), HTTPS via dev proxy            |
| Tooling    | Type checking, testing, linting                     | Vitest, ESLint, Prettier, Pytest, Ruff                       |

The default developer workflow spins up both Vite and Uvicorn. Audio blobs stay local (browser memory/IndexedDB) until you hit **Save**, then a single POST hits `/api/transcribe`. The backend writes a temp file, transcribes, returns JSON, and deletes the temp file.

---

## User Flows

### 1. Landing & Empty State
- Visit `/journals` (default route). App loads existing entries from IndexedDB.
- If no journals exist, show empty-state card with “Tell us how you feel today” and **Start Recording** button.
- Sidebar lists `Journals`, `Streaks`, `Settings`. Footer banner: “Private by default — stored locally in your browser.”

### 2. Recording
- Click **Start Recording** → prompt for microphone permission.
- Once granted, switch to recording UI with waveform, timer, and controls (`Pause`, `Stop`).
- On `Stop`, show preview player and options: `Save`, `Discard`.

### 3. Transcribing
- `Save` uploads the blob via `POST /api/transcribe`.
- UI shows “Transcribing your entry…” spinner while waiting.
- FastAPI stores the blob temporarily, calls Whisper/faster-whisper, and responds with `{ transcript, duration }`.
- Frontend creates a journal object:
  ```json
  {
    "id": "uuid-v4",
    "createdAt": "2025-11-01T10:31:00Z",
    "audioUrl": "blob:...",
    "transcript": "I felt more centered today after the walk...",
    "duration": 87.2
  }
  ```
- Entry is pushed into IndexedDB and state store; toast confirms success.

### 4. Dashboard & Streaks
- `/journals` displays cards sorted newest → oldest.
- Card contents: title (timestamp or first 5 words), snippet, recorded date, duration.
- Streak badge appears under the grid if entries exist for consecutive days.

### 5. Detail View
- Click card → `/journals/:id`.
- Show transcript, audio playback, `Delete`, `Download Audio`, `Export Transcript`, `Append to Note` (disabled placeholder), “Private by default” banner.
- Delete removes IndexedDB record and audio blob reference.
- Download triggers a `.webm` or `.wav` file save; export creates `.txt`.

### 6. Settings
- Controls for storage mode (Plaintext vs Encrypted prototype toggle).
- “Clear All Journals” button with confirm dialog.
- App build info and privacy reminder.

---

## Repository Layout

```
unposted/
├── README.md                # You are here
├── frontend/                # Vite + React app
│   ├── package.json
│   └── src/
│       ├── components/
│       ├── pages/
│       └── store/
└── backend/                 # FastAPI service
    ├── main.py
    ├── asr.py
    └── requirements.txt
```

---

## Prerequisites

- macOS/Linux (WSL ok) with recent audio drivers
- Node.js 18+ (use `fnm`/`nvm` to match `.nvmrc` once added)
- pnpm 8+ (preferred) or npm 9+
- Python 3.11 with `pipx` or virtualenv
- FFmpeg installed (`brew install ffmpeg` or `apt install ffmpeg`)
- (Optional) GPU drivers + CUDA/cuDNN if you plan to run Whisper on GPU

---

## Quickstart

```bash
git clone <repo>
cd unposted

# Backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload

# Frontend (new terminal)
cd frontend
pnpm install
pnpm dev
```

Visit http://localhost:5173 and ensure the frontend proxy sends API calls to http://127.0.0.1:8000.

---

## Frontend App

- **Scaffolding:** Vite + React + TypeScript with TailwindCSS pre-configured.
- **State:** Zustand store under `src/store/journals.ts` manages journal list, streaks, and persistence sync with IndexedDB.
- **Persistence:** Dexie wrapper to read/write entries; fallback to localStorage for demo.
- **Key Components:**
  - `Recorder.tsx`: MediaRecorder hook, waveform, recording controls.
  - `JournalCard.tsx`: Card UI for dashboard.
  - `JournalDetail.tsx`: Full entry view with export/delete actions.
- **Routing:** React Router (`/journals`, `/journals/:id`, `/settings`, `/streaks`).
- **Styling:** Tailwind + CSS variables for light/dark palette inspired by mockups.

### Planned Frontend Scripts

| Script         | Command            | Description                        |
|----------------|--------------------|------------------------------------|
| `pnpm dev`     | Vite dev server    | Runs frontend with hot reload      |
| `pnpm build`   | `vite build`       | Production bundle                  |
| `pnpm test`    | `vitest`           | Unit/component tests               |
| `pnpm lint`    | `eslint`           | Lints React code                   |
| `pnpm format`  | `prettier --write` | Formats TSX/TS/JSON                |

---

## Backend API

- `backend/main.py` exposes:
  - `GET /api/health` → `{ "status": "ok" }`
  - `POST /api/transcribe` → accepts audio `UploadFile`, returns `{ transcript, duration }`
- `backend/asr.py` wraps Whisper or faster-whisper; supports CPU by default.
- Temp files saved under `./tmp/` and deleted after inference.
- CORS enabled for `http://localhost:5173`.
- Settings driven by `backend/config.py` (to be added) with Pydantic `BaseSettings` for toggles like model size, encryption, temp dir, feature flags.

### Planned Backend Commands

| Command                            | Description                              |
|------------------------------------|------------------------------------------|
| `uvicorn backend.main:app --reload`| Run API with auto-reload                 |
| `python -m backend.asr --download` | (Future) Pre-download Whisper models     |
| `pytest`                           | Backend tests                            |
| `ruff check backend`               | Linting                                  |

---

## Transcription Pipeline

1. Frontend captures audio via `MediaRecorder` (`audio/webm;codecs=opus` default).
2. Blob posted as multipart form-data to FastAPI.
3. FastAPI writes blob to disk (`tempfile.NamedTemporaryFile`).
4. `asr.py` loads Whisper model once (singleton), runs transcription, returns text + duration.
5. Temp audio deleted; only transcript string leaves backend.
6. Frontend stores transcript + metadata locally; backend forgets everything.

For faster prototypes, set `TRANSCRIBE_STRATEGY=mock` to return lorem ipsum text without hitting Whisper.

---

## Local Storage Layer

- **IndexedDB via Dexie**: `journals` table keyed by UUID.
- **Schema:** `{ id, createdAt, audioBlob, transcript, duration, encrypted }`.
- **Encryption (optional):**
  - Ask user for passphrase in Settings.
  - Derive Fernet key via PBKDF2; encrypt transcript before writing to IndexedDB.
  - Audio blobs remain unencrypted unless future stretch goal implemented.
- **Exports:** Use `URL.createObjectURL` for audio, `Blob` for text downloads.

---

## Testing & Linting

- Frontend: Vitest + React Testing Library for store, recorder hook, and component rendering.
- Backend: Pytest for `/api/transcribe` (use fixture audio), integration tests using `httpx.AsyncClient`.
- CI recommendation: GitHub Actions matrix (Node 18, Python 3.11) running lint + test + type-check.

---

## Stretch Ideas

1. Emotion inference (valence × arousal) using simple classifier.
2. AI-generated reflection prompts based on recent entries.
3. Summaries (“You sounded energized today…”).
4. Offline-first PWA support (service worker + caching).
5. Multi-device sync via end-to-end encrypted blob sync (future research).

---

## FAQ

**Why Whisper/faster-whisper?**  
Open-sourced, high-quality ASR that can run locally on CPU/GPU without sending data to third parties.

**Can we skip the backend?**  
You can bring in [`@xenova/transformers`](https://github.com/xenova/transformers.js/) for pure client-side Whisper, but device compatibility and bundle size suffer. The FastAPI hop keeps the browser light.

**What about mobile browsers?**  
Works best on Chrome/Safari desktop. Mobile Safari’s MediaRecorder support is limited; treat it as a future enhancement.

**Will recordings survive refresh?**  
Yes, transcripts/audio stay in IndexedDB. Clearing browser storage wipes them.

---

Happy building! Ping the README with updates as you flesh out components, backend routes, and encryption setup.

