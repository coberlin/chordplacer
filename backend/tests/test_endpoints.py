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
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:4] == b"\x89PNG"
    assert float(resp.headers["x-page-width"]) == pytest.approx(612.0)
    assert float(resp.headers["x-page-height"]) == pytest.approx(792.0)


@pytest.mark.asyncio
async def test_get_page_first(client, sample_pdf_bytes):
    upload_resp = await client.post(
        "/upload", files=_make_upload_file(sample_pdf_bytes)
    )
    session_id = upload_resp.headers["x-session-id"]

    resp = await client.get(f"/page/1?session_id={session_id}")
    assert resp.status_code == 200


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
