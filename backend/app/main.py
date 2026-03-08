import tempfile
import uuid
from pathlib import Path

import fitz
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI(title="Chord Sheet Annotator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(tempfile.gettempdir()) / "chordplacer_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Map session_id -> pdf file path
sessions: dict[str, Path] = {}


def _render_page(pdf_path: Path, page_num: int) -> tuple[bytes, float, float]:
    """Render a PDF page to PNG bytes. Returns (png_bytes, width_pts, height_pts)."""
    doc = fitz.open(pdf_path)
    try:
        if page_num < 1 or page_num > len(doc):
            raise ValueError(f"Page {page_num} out of range (1-{len(doc)})")
        page = doc[page_num - 1]
        pix = page.get_pixmap(dpi=150)
        png_bytes = pix.tobytes("png")
        rect = page.rect
        return png_bytes, rect.width, rect.height
    finally:
        doc.close()


def _get_page_count(pdf_path: Path) -> int:
    doc = fitz.open(pdf_path)
    try:
        return len(doc)
    finally:
        doc.close()


@app.post("/upload")
async def upload_pdf(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()

    # Validate it's actually a PDF
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        doc.close()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    session_id = uuid.uuid4().hex
    pdf_path = UPLOAD_DIR / f"{session_id}.pdf"
    pdf_path.write_bytes(content)

    sessions[session_id] = pdf_path

    page_count = _get_page_count(pdf_path)
    png_bytes, width, height = _render_page(pdf_path, 1)

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "X-Session-Id": session_id,
            "X-Page-Count": str(page_count),
            "X-Page-Width": str(width),
            "X-Page-Height": str(height),
        },
    )


@app.get("/page/{page_num}")
async def get_page(page_num: int, session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    pdf_path = sessions[session_id]
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    try:
        png_bytes, width, height = _render_page(pdf_path, page_num)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Page {page_num} not found")

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "X-Page-Width": str(width),
            "X-Page-Height": str(height),
        },
    )
