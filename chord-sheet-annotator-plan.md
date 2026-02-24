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
| Backend | Python + FastAPI | Best PDF ecosystem; lightweight API |
| PDF rendering | PyMuPDF (`fitz`) | Fast, accurate page-to-image rendering |
| PDF parsing | pdfplumber | Character-level x/y coordinates |
| Syllable splitting | pyphen | LibreOffice-quality hyphenation dictionaries |
| PDF export | PyMuPDF drawing API | Write chord text at exact coordinates |
| Annotation storage | JSON sidecar file | Simple, no database needed |

---

## Architecture

```
PDF upload
    │
    ▼
FastAPI backend
    ├── PyMuPDF   → renders each page to PNG (for display)
    └── pdfplumber → extracts character x/y coords per page
            │
            ▼
        pyphen splits each word into syllables
        syllable x-ranges computed from character widths
            │
            ▼
React frontend
    ├── Displays page PNG as background image
    ├── Transparent overlay div captures clicks
    ├── Click → find nearest syllable → place chord label
    └── Chord labels = absolutely positioned divs
            │
            ▼
Save annotations → mysong.annotations.json
            │
            ▼
Export → FastAPI re-renders PDF with PyMuPDF drawing API
         writing chord names above each annotated line
```

---

## Data Model

### Annotation record
```json
{
  "chord": "Am7",
  "page": 0,
  "x": 142.5,
  "y": 310.2,
  "word": "beau-ti-ful",
  "syllable_index": 1
}
```

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
- Runs PyMuPDF to render all pages to PNG
- Runs pdfplumber to extract all character bounding boxes
- Runs pyphen to split words into syllables
- Returns: page images + syllable map (page → syllable → x/y range)

**`/export` endpoint**
- Accepts original PDF + annotation JSON
- Uses PyMuPDF drawing API to write each chord name at its x/y position
  above the correct line, in a monospace or chord-friendly font
- Returns annotated PDF

### Frontend

**Page viewer**
- Renders page PNG as `<img>` inside a positioned container
- Overlaid transparent `<div>` receives click events

**Syllable snap logic**
- On click, finds the syllable whose x-range contains the click x
- Places chord label at left edge of that syllable

**Chord input**
- Small popup or inline text field on click
- Searchable dropdown via react-select with common chord names
- Also accepts free-text input (for slash chords, sus4, etc.)

**Chord labels**
- Absolutely positioned `<div>` elements above the page image
- Draggable for fine adjustment (optional enhancement)

---

## Libraries

```
# Python
fastapi
uvicorn
pymupdf          # PDF render + export
pdfplumber       # Character coordinates
pyphen           # Syllable splitting
python-multipart # File upload support

# JavaScript / React
react
react-select     # Chord name picker
```

---

## Build Order

1. **PDF → PNG rendering** — get PyMuPDF serving page images via FastAPI
2. **Character extraction** — get pdfplumber returning x/y coords for all characters
3. **Syllable mapping** — integrate pyphen, compute syllable x-ranges
4. **React overlay UI** — display page image, capture clicks, snap to syllable
5. **Chord placement & storage** — place labels, save/load annotation JSON
6. **PDF export** — write chord names into a new PDF with PyMuPDF

---

## Notes

- Double-spaced lyric sheets provide the vertical room needed; the exported
  chord names are written into that gap above each lyric line.
- pyphen supports multiple languages; English is the default but the language
  can be made configurable for non-English lyrics.
- For export font, a monospace font (e.g. Courier) makes chord alignment more
  predictable, but any embedded TTF works with PyMuPDF.
