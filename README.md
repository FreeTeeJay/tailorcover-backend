# TailorCover — Backend (FastAPI)

Public API for generating tailored cover letters (local template by default; optional LLM).

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Health check: http://localhost:8000/healthz → `{"ok": true}`

## Deploy (Render)
- Build: `pip install -r backend/requirements.txt`
- Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Env (optional): `ENABLE_LLM=0` (or set `OPENAI_API_KEY` + `ENABLE_LLM=1`)

## Endpoints
- `POST /generate` → `{ cover_letter, mode }`
- `GET /healthz` → `{ ok: true }`