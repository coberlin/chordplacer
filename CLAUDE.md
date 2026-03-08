# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chord Sheet Annotator: a web tool for placing chord names above syllables in PDF lyric sheets. Upload a PDF, click above a syllable, type a chord name, export an annotated PDF. Currently in early development (backend PDF rendering is implemented; frontend not yet started).

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, PyMuPDF (`fitz`), pdfplumber
- **Frontend:** React, Hyphen (syllable splitting) — not yet implemented
- **Backend tooling:** uv for dependency management, Ruff for linting/formatting
- **Frontend tooling:** ESLint, Prettier — not yet set up

## Common Commands

All backend commands run from `backend/`:

```bash
# Install dependencies (uses uv with the local .venv)
cd backend && uv pip install -e ".[dev]"

# Run tests
cd backend && python -m pytest

# Run tests with coverage
cd backend && python -m pytest --cov=app

# Run a single test
cd backend && python -m pytest tests/test_endpoints.py::test_upload_valid_pdf

# Lint
cd backend && ruff check .

# Format
cd backend && ruff format .

# Run dev server
cd backend && uvicorn app.main:app --reload
```

## Architecture

**Backend** (`backend/app/main.py`): Single FastAPI app with in-memory session tracking. Uploaded PDFs are saved to a temp directory keyed by session UUID.

- `POST /upload` — accepts PDF, validates, renders page 1 to PNG, returns PNG with session/page metadata in response headers (X-Session-Id, X-Page-Count, X-Page-Width, X-Page-Height)
- `GET /page/{page_num}?session_id=...` — renders requested page to PNG on demand (1-indexed)
- Planned: `/export` endpoint to write chords into PDF using PyMuPDF drawing API

**Coordinate system:** Backend returns PDF-space coordinates (points, 72 dpi). Frontend will maintain a scale factor (`displayWidth / pdfPageWidth`) for bidirectional coordinate conversion. All annotations store PDF-space coordinates for export fidelity.

**Annotation storage:** JSON sidecar files (no database). Each annotation record has chord name, page, PDF-space x/y, word, and syllable index.

## Testing Conventions

- pytest with `asyncio_mode = "auto"` — tests are `async def` using `@pytest.mark.asyncio`
- Test client uses `httpx.AsyncClient` with `ASGITransport` (no live server needed)
- Fixtures in `backend/tests/conftest.py` generate test PDFs programmatically via PyMuPDF
- Target: 80% coverage per user story

## Ruff Configuration

- Line length: 88
- Rules: E, F, I, N, W, UP (pycodestyle, pyflakes, isort, naming, warnings, pyupgrade)
- Target: Python 3.11

## Project Plan

See `chord-placer-plan.md` for full architecture and build order. See `chord-placer-tasks.md` for user stories and task breakdown.
