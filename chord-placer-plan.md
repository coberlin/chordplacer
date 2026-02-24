# Chord Sheet Annotator — Project Plan

## Overview

A web-based tool for placing chord names above syllables in PDF lyric sheets.
The user opens a PDF, clicks above a syllable, types a chord name, and exports
an annotated PDF. Annotations are saved as a JSON sidecar file.

---

## Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | React | Precise overlay rendering; easy absolute positioning |
| Frontend linting | ESLint + Prettier | Consistent code style and formatting |
| Backend | Python + FastAPI | Best PDF ecosystem; lightweight API |
| Backend tooling | uv + Ruff | Fast dependency management; fast linting and formatting |
| PDF rendering | PyMuPDF (`fitz`) | Fast, accurate page-to-image rendering |
| PDF parsing | pdfplumber | Character-level x/y coordinates |
| Syllable splitting | `hyphen` (JS) | Client-side splitting avoids round-trips; keeps UI responsive |
| PDF export | PyMuPDF drawing API | Write chord text at exact coordinates |
| Annotation storage | JSON sidecar file | Simple, no database needed |
| Integration testing | Playwright | Browser-based E2E tests; introduced at build step 5 |

---

## Architecture

```
PDF upload
    │
    ▼
FastAPI backend
    ├── PyMuPDF   → renders each page to PNG (for display)
    └── pdfplumber → extracts character x/y coords (per page, on demand)
            │
            ▼
        Returns page PNG + character bounding boxes + PDF dimensions
            │
            ▼
React frontend
    ├── Receives character data, runs syllable splitting client-side
    ├── Computes syllable x-ranges from character widths
    ├── Displays page PNG as background image
    ├── Coordinate transform layer maps display coords ↔ PDF coords
    ├── Transparent overlay div captures clicks
    ├── Click → find nearest syllable → place chord label
    ├── Chord labels = absolutely positioned divs
    └── Undo/redo stack tracks all placement actions
            │
            ▼
Save annotations → mysong.annotations.json
            │
            ▼
Export → FastAPI re-renders PDF with PyMuPDF drawing API
         writing chord names above each annotated line
```

---

## Coordinate System

The backend returns PDF-space coordinates (points, 72 dpi) alongside the
rendered PNG dimensions. The frontend maintains a **scale factor**:

```
scaleFactor = displayWidth / pdfPageWidth
```

- **Click → PDF coords:** divide click position by scaleFactor
- **PDF coords → display:** multiply by scaleFactor
- All annotation records store **PDF-space coordinates** so exports are exact
- The scale factor updates on window resize / zoom to keep overlays aligned

This is critical — without an explicit coordinate transform, chords will
export to the wrong positions.

---

## Data Model

### Annotation record
```json
{
  "id": "a1b2c3",
  "chord": "Am7",
  "page": 0,
  "x_pdf": 142.5,
  "y_pdf": 310.2,
  "word": "beau-ti-ful",
  "syllable_index": 1
}
```

Coordinates are stored in **PDF space** (points). The `id` field supports
undo/redo and individual deletion.

### Sidecar file
```
mysong.pdf
mysong.annotations.json   ← list of annotation records
```

---

## Key Components

### Backend

**`/upload` endpoint**
- Accepts PDF
- Runs PyMuPDF to render page 1 to PNG (other pages rendered on demand)
- Returns: first page image + PDF metadata (page count, page dimensions)

**`/page/{n}` endpoint**
- Renders page N to PNG via PyMuPDF
- Extracts character bounding boxes for page N via pdfplumber
- Returns: page image + character map (character → x/y/width/height)
- Lazy per-page loading avoids long waits on upload for large PDFs

**`/export` endpoint**
- Accepts original PDF + annotation JSON
- Uses PyMuPDF drawing API to write each chord name at its PDF-space x/y
  position above the correct line, in a monospace or chord-friendly font
- Returns annotated PDF

### Frontend

**Page viewer**
- Renders page PNG as `<img>` inside a positioned container
- Overlaid transparent `<div>` receives click events
- Coordinate transform layer converts between display and PDF space

**Syllable snap logic**
- Character data from backend is split into syllables client-side using `hyphen`
- On click, converts click position to PDF coords, finds the syllable whose
  x-range contains the click x
- Places chord label at left edge of that syllable

**Chord input**
- Plain text input field appears on click (MVP — fast to build, musicians
  know their chord names)
- Enter to confirm, Escape to cancel
- Post-MVP: autocomplete or dropdown for common chord names

**Chord labels**
- Absolutely positioned `<div>` elements above the page image
- Click to edit, right-click or X button to delete
- Draggable for fine adjustment (post-MVP enhancement)

**Undo / Redo**
- Simple action stack: each add/edit/delete pushes to undo history
- Ctrl+Z / Cmd+Z to undo, Ctrl+Shift+Z / Cmd+Shift+Z to redo
- Essential even for MVP — accidental clicks are inevitable

---

## Libraries

```
# Python (managed with uv)
fastapi
uvicorn
pymupdf          # PDF render + export
pdfplumber       # Character coordinates
python-multipart # File upload support
pytest           # Unit testing
pytest-cov       # Coverage reporting
httpx            # Async test client for FastAPI
ruff             # Linting + formatting (dev dependency)

# JavaScript / React
react
hyphen           # Client-side syllable splitting
@testing-library/react   # Component testing
@testing-library/jest-dom # DOM matchers
jest             # Test runner & coverage
eslint           # Linting (dev dependency)
prettier         # Code formatting (dev dependency)
@playwright/test # Integration / E2E testing (dev dependency)
```

---

## Testing Requirements

All code must maintain a **minimum of 80% unit test coverage** per user story.

- **Backend (Python):** use `pytest` with `pytest-cov` for coverage measurement
- **Frontend (React):** use Jest and React Testing Library with built-in coverage reporting
- Coverage is measured per story — each story's new/modified code must meet the 80% threshold before the story is considered complete
- Coverage reports should be generated as part of CI and reviewable locally via `pytest --cov` and `npm test -- --coverage`
- **Integration testing (Playwright):** deferred until build step 5 (Chord Placement),
  when the full upload → view → click → place flow is first testable end-to-end.
  Playwright tests are added incrementally in steps 5–8 to verify cross-layer
  behavior that unit tests alone cannot catch. Run via `npx playwright test`.

---

## Build Order

1. **PDF → PNG rendering** — get PyMuPDF serving page images via FastAPI
2. **Character extraction** — get pdfplumber returning x/y coords per page (lazy)
3. **React page viewer + coordinate transform** — display page image with correct scaling
4. **Syllable mapping** — integrate `hyphen` on frontend, compute syllable x-ranges
5. **Click → chord placement** — snap to syllable, show text input, place label
   - *Playwright setup + first integration tests:* upload PDF → click syllable → verify chord appears
6. **Undo/redo + edit/delete** — action stack, click-to-edit, delete
   - *Integration tests:* edit chord, delete chord, undo/redo sequences
7. **Save/load annotations** — persist to JSON sidecar file
   - *Integration tests:* save annotations, reload page, verify annotations restored
8. **PDF export** — write chord names into a new PDF with PyMuPDF
   - *Integration tests:* place chords → export → verify download completes

---

## Known Limitations

- **Scanned / image-based PDFs are not supported.** pdfplumber requires
  embedded text to extract character positions. If the PDF is a scanned image,
  character extraction will return nothing. OCR support (e.g. via Tesseract)
  could be added post-MVP.
- **Complex PDF layouts** (multi-column, text boxes, rotated text) may produce
  unexpected character coordinates. The tool is optimized for simple
  single-column lyric sheets.

---

## Notes

- Double-spaced lyric sheets provide the vertical room needed; the exported
  chord names are written into that gap above each lyric line.
- `hyphen` (JS) uses the same Hunspell/LibreOffice dictionaries as pyphen and
  supports multiple languages; English is the default but the language can be
  made configurable for non-English lyrics.
- For export font, a monospace font (e.g. Courier) makes chord alignment more
  predictable, but any embedded TTF works with PyMuPDF.
- All coordinates are stored in PDF space to ensure export fidelity regardless
  of the display zoom level used during annotation.
