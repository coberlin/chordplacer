import io

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app, sessions


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def clear_sessions():
    sessions.clear()
    yield
    sessions.clear()


def _make_upload_file(content: bytes, filename: str = "test.pdf"):
    return {"file": (filename, io.BytesIO(content), "application/pdf")}


# --- /upload tests ---


@pytest.mark.asyncio
async def test_upload_valid_pdf(client, sample_pdf_bytes):
    resp = await client.post("/upload", files=_make_upload_file(sample_pdf_bytes))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.headers["x-session-id"]
    assert resp.headers["x-page-count"] == "2"
    assert float(resp.headers["x-page-width"]) == pytest.approx(612.0)
    assert float(resp.headers["x-page-height"]) == pytest.approx(792.0)
    # PNG magic bytes
    assert resp.content[:4] == b"\x89PNG"


@pytest.mark.asyncio
async def test_upload_single_page_pdf(client, single_page_pdf_bytes):
    resp = await client.post("/upload", files=_make_upload_file(single_page_pdf_bytes))
    assert resp.status_code == 200
    assert resp.headers["x-page-count"] == "1"


@pytest.mark.asyncio
async def test_upload_non_pdf_extension(client):
    resp = await client.post(
        "/upload", files=_make_upload_file(b"not a pdf", "test.txt")
    )
    assert resp.status_code == 400
    assert "PDF" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_invalid_pdf_content(client):
    resp = await client.post(
        "/upload", files=_make_upload_file(b"not a real pdf", "test.pdf")
    )
    assert resp.status_code == 400
    assert "Invalid PDF" in resp.json()["detail"]


# --- /page/{n} tests ---


@pytest.mark.asyncio
async def test_get_page_valid(client, sample_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(sample_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/2?session_id={session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "image" in data
    assert data["width"] == pytest.approx(612.0)
    assert data["height"] == pytest.approx(792.0)
    assert "lines" in data
    # Verify image is valid base64 PNG
    import base64

    png_bytes = base64.b64decode(data["image"])
    assert png_bytes[:4] == b"\x89PNG"


@pytest.mark.asyncio
async def test_get_page_first(client, sample_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(sample_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/1?session_id={session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "image" in data
    assert "lines" in data


@pytest.mark.asyncio
async def test_get_page_out_of_range(client, sample_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(sample_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/3?session_id={session_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_page_zero(client, sample_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(sample_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/0?session_id={session_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_page_invalid_session(client):
    resp = await client.get("/page/1?session_id=nonexistent")
    assert resp.status_code == 404
    assert "Session not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_page_negative(client, sample_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(sample_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/-1?session_id={session_id}")
    assert resp.status_code == 404


# --- /page/{n} character map tests ---


@pytest.mark.asyncio
async def test_get_page_returns_character_map(client, lyric_sheet_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(lyric_sheet_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/1?session_id={session_id}")
    assert resp.status_code == 200
    data = resp.json()

    lines = data["lines"]
    assert len(lines) == 2  # Two lines of lyrics

    # Check first line has words
    first_line = lines[0]
    assert "words" in first_line
    assert "y0" in first_line
    assert "y1" in first_line
    assert len(first_line["words"]) > 0

    # Check word structure
    first_word = first_line["words"][0]
    assert first_word["text"] == "Amazing"
    assert "x0" in first_word
    assert "y0" in first_word
    assert "x1" in first_word
    assert "y1" in first_word
    assert "chars" in first_word
    assert len(first_word["chars"]) == 7  # A-m-a-z-i-n-g

    # Check character structure
    first_char = first_word["chars"][0]
    assert first_char["char"] == "A"
    assert "x0" in first_char
    assert "y0" in first_char
    assert "x1" in first_char
    assert "y1" in first_char


@pytest.mark.asyncio
async def test_get_page_empty_page(client, empty_page_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(empty_page_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/1?session_id={session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["lines"] == []


@pytest.mark.asyncio
async def test_get_page_non_ascii(client, non_ascii_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(non_ascii_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/1?session_id={session_id}")
    assert resp.status_code == 200
    data = resp.json()

    lines = data["lines"]
    assert len(lines) >= 1
    # Verify non-ASCII characters are preserved
    all_chars = ""
    for line in lines:
        for word in line["words"]:
            all_chars += word["text"]
    assert "é" in all_chars or "ö" in all_chars
