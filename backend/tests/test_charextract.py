"""Tests for character extraction, word grouping, and line clustering."""

import tempfile
from pathlib import Path

import pytest

from app.charextract import (
    extract_characters,
    extract_page_chars,
    group_into_lines,
    group_into_words,
)


@pytest.fixture
def lyric_pdf_path(lyric_sheet_pdf_bytes) -> Path:
    """Write lyric sheet PDF to a temp file and return the path."""
    path = Path(tempfile.mktemp(suffix=".pdf"))
    path.write_bytes(lyric_sheet_pdf_bytes)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def non_ascii_pdf_path(non_ascii_pdf_bytes) -> Path:
    path = Path(tempfile.mktemp(suffix=".pdf"))
    path.write_bytes(non_ascii_pdf_bytes)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def empty_pdf_path(empty_page_pdf_bytes) -> Path:
    path = Path(tempfile.mktemp(suffix=".pdf"))
    path.write_bytes(empty_page_pdf_bytes)
    yield path
    path.unlink(missing_ok=True)


# --- extract_characters tests ---


class TestExtractCharacters:
    def test_extracts_characters_from_lyric_sheet(self, lyric_pdf_path):
        chars = extract_characters(lyric_pdf_path, 1)
        assert len(chars) > 0
        for c in chars:
            assert "char" in c
            assert "x0" in c
            assert "y0" in c
            assert "x1" in c
            assert "y1" in c
            assert "is_space" in c
            assert c["x1"] > c["x0"]
            assert c["y1"] > c["y0"]

    def test_includes_spaces_with_flag(self, lyric_pdf_path):
        chars = extract_characters(lyric_pdf_path, 1)
        spaces = [c for c in chars if c["is_space"]]
        non_spaces = [c for c in chars if not c["is_space"]]
        assert len(spaces) > 0, "Should include space characters"
        assert len(non_spaces) > 0, "Should include non-space characters"

    def test_empty_page_returns_empty(self, empty_pdf_path):
        chars = extract_characters(empty_pdf_path, 1)
        assert chars == []

    def test_page_out_of_range(self, lyric_pdf_path):
        with pytest.raises(ValueError, match="out of range"):
            extract_characters(lyric_pdf_path, 5)

    def test_page_zero(self, lyric_pdf_path):
        with pytest.raises(ValueError, match="out of range"):
            extract_characters(lyric_pdf_path, 0)

    def test_non_ascii_characters(self, non_ascii_pdf_path):
        chars = extract_characters(non_ascii_pdf_path, 1)
        char_texts = [c["char"] for c in chars if not c["is_space"]]
        assert any(c in char_texts for c in ["é", "ö"])

    def test_coordinates_are_rounded(self, lyric_pdf_path):
        chars = extract_characters(lyric_pdf_path, 1)
        for c in chars:
            assert c["x0"] == round(c["x0"], 2)
            assert c["y0"] == round(c["y0"], 2)
            assert c["x1"] == round(c["x1"], 2)
            assert c["y1"] == round(c["y1"], 2)


# --- group_into_words tests ---


class TestGroupIntoWords:
    def test_empty_input(self):
        assert group_into_words([]) == []

    def test_single_character(self):
        chars = [
            {"char": "A", "x0": 10, "y0": 50, "x1": 18, "y1": 62, "is_space": False}
        ]
        words = group_into_words(chars)
        assert len(words) == 1
        assert words[0]["text"] == "A"

    def test_groups_adjacent_chars_into_word(self):
        chars = [
            {"char": "H", "x0": 10, "y0": 50, "x1": 18, "y1": 62, "is_space": False},
            {"char": "i", "x0": 18, "y0": 50, "x1": 22, "y1": 62, "is_space": False},
        ]
        words = group_into_words(chars)
        assert len(words) == 1
        assert words[0]["text"] == "Hi"

    def test_splits_on_space(self):
        chars = [
            {"char": "H", "x0": 10, "y0": 50, "x1": 18, "y1": 62, "is_space": False},
            {"char": "i", "x0": 18, "y0": 50, "x1": 22, "y1": 62, "is_space": False},
            {"char": " ", "x0": 22, "y0": 50, "x1": 25, "y1": 62, "is_space": True},
            {"char": "T", "x0": 25, "y0": 50, "x1": 33, "y1": 62, "is_space": False},
        ]
        words = group_into_words(chars)
        assert len(words) == 2
        assert words[0]["text"] == "Hi"
        assert words[1]["text"] == "T"

    def test_splits_on_different_lines(self):
        chars = [
            {"char": "A", "x0": 10, "y0": 50, "x1": 18, "y1": 62, "is_space": False},
            {"char": "B", "x0": 10, "y0": 100, "x1": 18, "y1": 112, "is_space": False},
        ]
        words = group_into_words(chars)
        assert len(words) == 2
        assert words[0]["text"] == "A"
        assert words[1]["text"] == "B"

    def test_word_bounding_box(self):
        chars = [
            {"char": "H", "x0": 10, "y0": 50, "x1": 18, "y1": 62, "is_space": False},
            {"char": "i", "x0": 18, "y0": 50, "x1": 22, "y1": 62, "is_space": False},
        ]
        words = group_into_words(chars)
        assert words[0]["x0"] == 10
        assert words[0]["x1"] == 22
        assert words[0]["y0"] == 50
        assert words[0]["y1"] == 62

    def test_output_chars_have_no_is_space_flag(self):
        chars = [
            {"char": "A", "x0": 10, "y0": 50, "x1": 18, "y1": 62, "is_space": False},
        ]
        words = group_into_words(chars)
        for c in words[0]["chars"]:
            assert "is_space" not in c

    def test_multiple_spaces_between_words(self):
        chars = [
            {"char": "A", "x0": 10, "y0": 50, "x1": 18, "y1": 62, "is_space": False},
            {"char": " ", "x0": 18, "y0": 50, "x1": 21, "y1": 62, "is_space": True},
            {"char": " ", "x0": 21, "y0": 50, "x1": 24, "y1": 62, "is_space": True},
            {"char": "B", "x0": 24, "y0": 50, "x1": 32, "y1": 62, "is_space": False},
        ]
        words = group_into_words(chars)
        assert len(words) == 2
        assert words[0]["text"] == "A"
        assert words[1]["text"] == "B"

    def test_from_real_pdf(self, lyric_pdf_path):
        chars = extract_characters(lyric_pdf_path, 1)
        words = group_into_words(chars)
        word_texts = [w["text"] for w in words]
        assert "Amazing" in word_texts
        assert "Grace" in word_texts
        assert "how" in word_texts
        assert "sweet" in word_texts


# --- group_into_lines tests ---


class TestGroupIntoLines:
    def test_empty_input(self):
        assert group_into_lines([]) == []

    def test_single_word(self):
        words = [{"text": "Hello", "x0": 10, "y0": 50, "x1": 60, "y1": 62}]
        lines = group_into_lines(words)
        assert len(lines) == 1
        assert len(lines[0]["words"]) == 1

    def test_groups_same_y_into_one_line(self):
        words = [
            {"text": "Hello", "x0": 10, "y0": 50, "x1": 60, "y1": 62},
            {"text": "World", "x0": 70, "y0": 50.5, "x1": 120, "y1": 62.5},
        ]
        lines = group_into_lines(words)
        assert len(lines) == 1
        assert len(lines[0]["words"]) == 2

    def test_separates_different_y_into_lines(self):
        words = [
            {"text": "Line1", "x0": 10, "y0": 50, "x1": 60, "y1": 62},
            {"text": "Line2", "x0": 10, "y0": 100, "x1": 60, "y1": 112},
        ]
        lines = group_into_lines(words)
        assert len(lines) == 2

    def test_line_bounding_box(self):
        words = [
            {"text": "Hello", "x0": 10, "y0": 50, "x1": 60, "y1": 62},
            {"text": "World", "x0": 70, "y0": 50, "x1": 120, "y1": 63},
        ]
        lines = group_into_lines(words)
        assert lines[0]["y0"] == 50
        assert lines[0]["y1"] == 63

    def test_words_sorted_by_x(self):
        words = [
            {"text": "World", "x0": 70, "y0": 50, "x1": 120, "y1": 62},
            {"text": "Hello", "x0": 10, "y0": 50, "x1": 60, "y1": 62},
        ]
        lines = group_into_lines(words)
        assert lines[0]["words"][0]["text"] == "Hello"
        assert lines[0]["words"][1]["text"] == "World"

    def test_from_real_pdf(self, lyric_pdf_path):
        chars = extract_characters(lyric_pdf_path, 1)
        words = group_into_words(chars)
        lines = group_into_lines(words)
        assert len(lines) == 2


# --- extract_page_chars integration tests ---


class TestExtractPageChars:
    def test_full_pipeline(self, lyric_pdf_path):
        lines = extract_page_chars(lyric_pdf_path, 1)
        assert len(lines) == 2

        # First line: "Amazing Grace how sweet"
        first_line = lines[0]
        word_texts = [w["text"] for w in first_line["words"]]
        assert "Amazing" in word_texts
        assert "Grace" in word_texts

        # Second line: "the sound that saved"
        second_line = lines[1]
        word_texts = [w["text"] for w in second_line["words"]]
        assert "the" in word_texts
        assert "sound" in word_texts

    def test_empty_page(self, empty_pdf_path):
        lines = extract_page_chars(empty_pdf_path, 1)
        assert lines == []

    def test_characters_have_valid_bboxes(self, lyric_pdf_path):
        lines = extract_page_chars(lyric_pdf_path, 1)
        for line in lines:
            for word in line["words"]:
                for char in word["chars"]:
                    assert char["x1"] > char["x0"], f"Invalid char bbox: {char}"
                    assert char["y1"] > char["y0"], f"Invalid char bbox: {char}"

    def test_word_bbox_encompasses_chars(self, lyric_pdf_path):
        lines = extract_page_chars(lyric_pdf_path, 1)
        for line in lines:
            for word in line["words"]:
                for char in word["chars"]:
                    assert char["x0"] >= word["x0"]
                    assert char["x1"] <= word["x1"]
                    assert char["y0"] >= word["y0"]
                    assert char["y1"] <= word["y1"]

    def test_non_ascii_pipeline(self, non_ascii_pdf_path):
        lines = extract_page_chars(non_ascii_pdf_path, 1)
        assert len(lines) >= 1
        all_text = ""
        for line in lines:
            for word in line["words"]:
                all_text += word["text"] + " "
        assert "é" in all_text or "ö" in all_text

    def test_output_chars_clean(self, lyric_pdf_path):
        """Output character dicts should not contain internal flags."""
        lines = extract_page_chars(lyric_pdf_path, 1)
        for line in lines:
            for word in line["words"]:
                for char in word["chars"]:
                    assert "is_space" not in char
                    assert set(char.keys()) == {"char", "x0", "y0", "x1", "y1"}
