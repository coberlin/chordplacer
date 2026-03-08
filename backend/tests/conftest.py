import fitz
import pytest


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create a minimal valid PDF with 2 pages for testing."""
    doc = fitz.open()
    page1 = doc.new_page(width=612, height=792)
    page1.insert_text((72, 72), "Page 1 - Amazing Grace")
    page2 = doc.new_page(width=612, height=792)
    page2.insert_text((72, 72), "Page 2 - How sweet the sound")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def single_page_pdf_bytes() -> bytes:
    """Create a minimal valid PDF with 1 page."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Single page")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
