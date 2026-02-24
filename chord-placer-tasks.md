# Chord Sheet Annotator — User Stories & Tasks

> **Testing requirement:** Every story must achieve a minimum of **80% unit test
> coverage** on new/modified code. Backend tests use pytest + pytest-cov; frontend
> tests use Jest + React Testing Library. A story is not complete until coverage
> is verified.
>
> **Tooling:** Backend uses **uv** for dependency management and **Ruff** for
> linting/formatting. Frontend uses **ESLint** for linting and **Prettier** for
> formatting. All code must pass linting before a story is considered complete.

---

## Story 1: PDF Page Rendering

**As a** musician, **I want to** upload a PDF lyric sheet and see it displayed as an image, **so that** I can visually identify where to place chords.

### Tasks

- [ ] 1.1 Set up FastAPI project using `uv` with uvicorn, pymupdf, pdfplumber, and python-multipart dependencies
- [ ] 1.1a Configure Ruff for linting and formatting; add `ruff.toml` or `[tool.ruff]` section in `pyproject.toml`
- [ ] 1.2 Create `/upload` endpoint that accepts a PDF file upload
- [ ] 1.3 Store the uploaded PDF in a temp/session directory for later use
- [ ] 1.4 Render page 1 to PNG using PyMuPDF on upload; return the image, page count, and page dimensions (width/height in PDF points)
- [ ] 1.5 Create `/page/{n}` endpoint that renders page N to PNG on demand (lazy rendering)
- [ ] 1.6 Return PDF metadata (page dimensions in points) alongside each page image so the frontend can compute scale factors
- [ ] 1.7 Add CORS middleware so the React frontend can call the API
- [ ] 1.8 Write unit tests for `/upload` and `/page/{n}` endpoints (valid PDF, invalid file, out-of-range page)
- [ ] 1.9 Verify ≥ 80% test coverage for all Story 1 code

### Acceptance Criteria

- Uploading a PDF returns a PNG of page 1 plus metadata (page count, page width, page height)
- Requesting `/page/2` returns a PNG of page 2
- Invalid page numbers return a 404
- Unit test coverage ≥ 80% for all backend code introduced in this story

---

## Story 2: Character Coordinate Extraction

**As a** developer, **I want** the backend to extract character-level bounding boxes from each PDF page, **so that** the frontend can map click positions to specific characters and syllables.

### Tasks

- [ ] 2.1 Integrate pdfplumber to extract character data (char, x0, y0, x1, y1) for a given page
- [ ] 2.2 Add character map to the `/page/{n}` response: list of `{char, x0, y0, x1, y1}` in PDF-point coordinates
- [ ] 2.3 Group characters into words based on spatial proximity (gap threshold between characters)
- [ ] 2.4 Include line-level grouping (y-coordinate clustering) so the frontend knows which line each word belongs to
- [ ] 2.5 Handle edge cases: ligatures, whitespace-only regions, non-ASCII characters
- [ ] 2.6 Write unit tests for character extraction, word grouping, and line clustering logic
- [ ] 2.7 Verify ≥ 80% test coverage for all Story 2 code

### Acceptance Criteria

- `/page/{n}` returns a character map with bounding boxes in PDF-point coordinates
- Characters are grouped into words and lines
- A sample lyric sheet PDF produces correct character positions when spot-checked
- Unit test coverage ≥ 80% for all backend code introduced in this story

---

## Story 3: Page Viewer with Coordinate Transform

**As a** musician, **I want to** see the PDF page displayed in my browser with correct scaling, **so that** chords I place visually align with the underlying PDF coordinates.

### Tasks

- [ ] 3.1 Set up React project (create-react-app or Vite)
- [ ] 3.1a Configure ESLint and Prettier; add `.eslintrc` and `.prettierrc` config files
- [ ] 3.2 Build an upload form that sends the PDF to `/upload` and stores the response (page image URL, page count, dimensions)
- [ ] 3.3 Create a `PageViewer` component that displays the page PNG inside a positioned container
- [ ] 3.4 Implement coordinate transform layer: compute `scaleFactor = displayWidth / pdfPageWidth`
- [ ] 3.5 Add helper functions: `displayToPdf(x, y)` and `pdfToDisplay(x, y)`
- [ ] 3.6 Recalculate scale factor on window resize to keep overlays aligned
- [ ] 3.7 Add page navigation (previous/next) that fetches pages lazily from `/page/{n}`
- [ ] 3.8 Overlay a transparent `<div>` on the page image to capture click events
- [ ] 3.9 Write unit tests for coordinate transform functions (round-trip accuracy, edge cases)
- [ ] 3.10 Write component tests for PageViewer (renders image, handles resize, page navigation)
- [ ] 3.11 Verify ≥ 80% test coverage for all Story 3 code

### Acceptance Criteria

- The page image scales to fit the browser window
- Coordinate transforms round-trip correctly: `pdfToDisplay(displayToPdf(x, y))` returns the original values (within rounding)
- Resizing the window updates the overlay positions
- Page navigation loads new pages on demand
- Unit test coverage ≥ 80% for all frontend code introduced in this story

---

## Story 4: Syllable Mapping

**As a** musician, **I want** clicks to snap to syllable boundaries, **so that** chords align precisely above the syllable I intend.

### Tasks

- [ ] 4.1 Install and configure the `hyphen` library with an English dictionary
- [ ] 4.2 When character data arrives from the backend, reconstruct words from character groups
- [ ] 4.3 Run each word through `hyphen` to split it into syllables
- [ ] 4.4 Compute each syllable's x-range by summing the widths of its constituent characters
- [ ] 4.5 Store syllable data per line: `{word, syllableIndex, xStart, xEnd, yLine}` in PDF coordinates
- [ ] 4.6 Build a lookup function: given a PDF-space (x, y), find the nearest syllable on the closest line
- [ ] 4.7 Write unit tests for syllable splitting, x-range computation, and nearest-syllable lookup
- [ ] 4.8 Verify ≥ 80% test coverage for all Story 4 code

### Acceptance Criteria

- "beautiful" splits into "beau-ti-ful" (3 syllables) with correct x-ranges
- Clicking between two syllables snaps to the nearest one
- Single-syllable words are handled correctly (no splitting)
- Unit test coverage ≥ 80% for all frontend code introduced in this story

---

## Story 5: Chord Placement

**As a** musician, **I want to** click above a syllable and type a chord name, **so that** I can annotate my lyric sheet with chords.

### Tasks

- [ ] 5.1 On overlay click, convert click position to PDF coordinates and find the nearest syllable
- [ ] 5.2 Show a text input field at the click position (positioned in display coordinates)
- [ ] 5.3 On Enter, create an annotation record: `{id, chord, page, x_pdf, y_pdf, word, syllable_index}`
- [ ] 5.4 On Escape, cancel the input without creating an annotation
- [ ] 5.5 Render placed chords as absolutely positioned `<div>` elements above the page image
- [ ] 5.6 Position chord labels at the left edge of the snapped syllable, offset above the lyric line
- [ ] 5.7 Maintain an in-memory list of annotations per page
- [ ] 5.8 Style chord labels to be visually distinct (e.g., bold, contrasting color)
- [ ] 5.9 Write unit tests for annotation record creation and chord label positioning logic
- [ ] 5.10 Write component tests for chord input (Enter confirms, Escape cancels) and label rendering
- [ ] 5.11 Install Playwright and configure `playwright.config.ts` (base URL, browser list, webServer start commands for backend + frontend)
- [ ] 5.12 Write Playwright integration test: upload a PDF → click above a syllable → type chord → verify chord label appears at the correct position
- [ ] 5.13 Write Playwright integration test: place multiple chords on a page and verify all are visible
- [ ] 5.14 Verify ≥ 80% unit test coverage for all Story 5 code

### Acceptance Criteria

- Clicking above a word opens a text input
- Typing "Am7" and pressing Enter places "Am7" above the correct syllable
- Pressing Escape dismisses the input with no annotation created
- Multiple chords can be placed on the same page without interfering
- Unit test coverage ≥ 80% for all frontend code introduced in this story
- Playwright integration tests pass for the chord placement flow

---

## Story 6: Edit, Delete, and Undo/Redo

**As a** musician, **I want to** edit, delete, and undo chord placements, **so that** I can correct mistakes without starting over.

### Tasks

- [ ] 6.1 Click on an existing chord label to open it for editing (pre-filled text input)
- [ ] 6.2 Add a delete action: right-click or X button on a chord label removes it
- [ ] 6.3 Implement an undo/redo action stack that tracks add, edit, and delete operations
- [ ] 6.4 Wire Ctrl+Z / Cmd+Z to undo and Ctrl+Shift+Z / Cmd+Shift+Z to redo
- [ ] 6.5 Ensure undo of a delete restores the chord label at its original position
- [ ] 6.6 Ensure undo of an edit reverts to the previous chord name
- [ ] 6.7 Write unit tests for the undo/redo action stack (add, edit, delete, sequential operations)
- [ ] 6.8 Write component tests for edit and delete interactions
- [ ] 6.9 Write Playwright integration test: place chord → click to edit → change name → verify updated label
- [ ] 6.10 Write Playwright integration test: place chord → delete → verify removed; undo → verify restored
- [ ] 6.11 Verify ≥ 80% unit test coverage for all Story 6 code

### Acceptance Criteria

- Clicking a placed chord opens it for editing; Enter confirms, Escape cancels
- Deleting a chord removes it from the display and the annotation list
- Ctrl+Z undoes the last action (add, edit, or delete)
- Ctrl+Shift+Z redoes an undone action
- Undo/redo works correctly across multiple sequential operations
- Unit test coverage ≥ 80% for all frontend code introduced in this story
- Playwright integration tests pass for edit, delete, and undo/redo flows

---

## Story 7: Save and Load Annotations

**As a** musician, **I want to** save my chord annotations and reload them later, **so that** I can work on a lyric sheet across multiple sessions.

### Tasks

- [ ] 7.1 Create a `/save` endpoint that accepts the annotation JSON array and the PDF filename; writes `{filename}.annotations.json` to disk
- [ ] 7.2 Create a `/load` endpoint that accepts a PDF filename and returns the matching `.annotations.json` if it exists
- [ ] 7.3 Add a Save button in the frontend that posts the current annotations to `/save`
- [ ] 7.4 On PDF upload, automatically check for an existing annotations file and load it
- [ ] 7.5 Render loaded annotations as chord labels at their stored PDF-space positions
- [ ] 7.6 Show a visual indicator when there are unsaved changes
- [ ] 7.7 Prompt before navigating away if there are unsaved changes (beforeunload)
- [ ] 7.8 Write unit tests for `/save` and `/load` endpoints (save, load, missing file)
- [ ] 7.9 Write component tests for save button, unsaved-changes indicator, and auto-load on upload
- [ ] 7.10 Write Playwright integration test: place chords → save → reload page → verify annotations are restored
- [ ] 7.11 Verify ≥ 80% unit test coverage for all Story 7 code

### Acceptance Criteria

- Clicking Save persists annotations to a JSON sidecar file
- Re-uploading the same PDF restores previously saved annotations
- Unsaved changes trigger a warning before page unload
- The sidecar file format matches the data model in the plan
- Unit test coverage ≥ 80% for all code introduced in this story
- Playwright integration tests pass for the save/load round-trip

---

## Story 8: PDF Export

**As a** musician, **I want to** export an annotated PDF with chord names printed above the lyrics, **so that** I can print or share the finished chord sheet.

### Tasks

- [ ] 8.1 Create an `/export` endpoint that accepts the original PDF path and annotation JSON
- [ ] 8.2 Open the original PDF with PyMuPDF and iterate over annotations grouped by page
- [ ] 8.3 For each annotation, draw the chord name at its `(x_pdf, y_pdf)` position using PyMuPDF's text drawing API
- [ ] 8.4 Choose an appropriate font (e.g., Courier or Helvetica-Bold) and size for chord labels
- [ ] 8.5 Offset chord text vertically above the lyric line so it doesn't overlap the lyrics
- [ ] 8.6 Save and return the annotated PDF as a downloadable file
- [ ] 8.7 Add an Export button in the frontend that triggers the download
- [ ] 8.8 Verify exported chord positions match the on-screen placement by spot-checking coordinates
- [ ] 8.9 Write unit tests for `/export` endpoint (valid annotations, empty annotations, coordinate accuracy)
- [ ] 8.10 Write component tests for the Export button and download trigger
- [ ] 8.11 Write Playwright integration test: place chords → click Export → verify PDF download completes
- [ ] 8.12 Verify ≥ 80% unit test coverage for all Story 8 code

### Acceptance Criteria

- Clicking Export downloads a new PDF with chord names printed above the lyrics
- Chord positions in the exported PDF match the on-screen placement
- The original PDF is not modified
- Chords are legible and do not overlap lyric text
- Unit test coverage ≥ 80% for all code introduced in this story
- Playwright integration tests pass for the export flow
