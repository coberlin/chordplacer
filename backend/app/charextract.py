"""Character-level coordinate extraction, word grouping, and line clustering."""

from pathlib import Path

import pdfplumber


def extract_characters(pdf_path: Path, page_num: int) -> list[dict]:
    """Extract all character data from a PDF page via pdfplumber.

    Returns both printable and whitespace characters so that callers
    can use whitespace positions for word boundary detection.

    Args:
        pdf_path: Path to the PDF file.
        page_num: 1-indexed page number.

    Returns:
        List of character dicts with char, x0, y0, x1, y1 in PDF-point coords,
        plus an "is_space" flag.
    """
    with pdfplumber.open(pdf_path) as pdf:
        if page_num < 1 or page_num > len(pdf.pages):
            raise ValueError(f"Page {page_num} out of range (1-{len(pdf.pages)})")
        page = pdf.pages[page_num - 1]
        chars = page.chars or []
        result = []
        for c in chars:
            text = c.get("text", "")
            if not text:
                continue
            result.append(
                {
                    "char": text,
                    "x0": round(c["x0"], 2),
                    "y0": round(c["top"], 2),
                    "x1": round(c["x1"], 2),
                    "y1": round(c["bottom"], 2),
                    "is_space": not text.strip(),
                }
            )
        return result


def group_into_words(raw_chars: list[dict]) -> list[dict]:
    """Group characters into words using whitespace as word boundaries.

    Whitespace characters (spaces) in the character stream mark word
    boundaries. Characters on different lines (different y0) also start
    new words.

    Args:
        raw_chars: List of character dicts from extract_characters
            (includes whitespace chars with is_space flag).

    Returns:
        List of word dicts, each with text, x0, y0, x1, y1, and chars list.
        The chars list in each word contains only non-space characters.
    """
    if not raw_chars:
        return []

    # Sort by vertical position first, then horizontal
    sorted_chars = sorted(raw_chars, key=lambda c: (c["y0"], c["x0"]))

    words = []
    current_chars: list[dict] = []

    for char in sorted_chars:
        if char["is_space"]:
            # Space marks a word boundary
            if current_chars:
                words.append(_make_word(current_chars))
                current_chars = []
            continue

        if current_chars:
            prev = current_chars[-1]
            same_line = abs(char["y0"] - prev["y0"]) < _line_tolerance(prev)
            if not same_line:
                # Line break also marks a word boundary
                words.append(_make_word(current_chars))
                current_chars = []

        current_chars.append(char)

    if current_chars:
        words.append(_make_word(current_chars))

    return words


def group_into_lines(words: list[dict], y_threshold: float = 3.0) -> list[dict]:
    """Group words into lines based on y-coordinate clustering.

    Words whose y0 values are within y_threshold of each other are
    considered to be on the same line.

    Args:
        words: List of word dicts from group_into_words.
        y_threshold: Maximum y-coordinate difference for same-line grouping.

    Returns:
        List of line dicts, each with y0, y1, and a list of words sorted by x0.
    """
    if not words:
        return []

    # Sort words by y0 then x0
    sorted_words = sorted(words, key=lambda w: (w["y0"], w["x0"]))

    lines = []
    current_line_words = [sorted_words[0]]
    current_y0 = sorted_words[0]["y0"]

    for word in sorted_words[1:]:
        if abs(word["y0"] - current_y0) <= y_threshold:
            current_line_words.append(word)
        else:
            lines.append(_make_line(current_line_words))
            current_line_words = [word]
            current_y0 = word["y0"]

    if current_line_words:
        lines.append(_make_line(current_line_words))

    return lines


def extract_page_chars(pdf_path: Path, page_num: int) -> list[dict]:
    """Extract characters from a PDF page grouped into lines and words.

    This is the main entry point combining extraction, word grouping, and
    line clustering.

    Args:
        pdf_path: Path to the PDF file.
        page_num: 1-indexed page number.

    Returns:
        List of line dicts with nested word and character data.
    """
    raw_chars = extract_characters(pdf_path, page_num)
    words = group_into_words(raw_chars)
    lines = group_into_lines(words)
    return lines


def _line_tolerance(char: dict) -> float:
    """Compute y-tolerance for same-line detection based on character height."""
    height = char["y1"] - char["y0"]
    # Use half the character height as tolerance, minimum 3 points
    return max(height * 0.5, 3.0)


def _make_word(chars: list[dict]) -> dict:
    """Create a word dict from a list of non-space character dicts."""
    # Strip the is_space flag from output chars
    clean_chars = [{k: v for k, v in c.items() if k != "is_space"} for c in chars]
    text = "".join(c["char"] for c in clean_chars)
    return {
        "text": text,
        "x0": clean_chars[0]["x0"],
        "y0": min(c["y0"] for c in clean_chars),
        "x1": clean_chars[-1]["x1"],
        "y1": max(c["y1"] for c in clean_chars),
        "chars": clean_chars,
    }


def _make_line(words: list[dict]) -> dict:
    """Create a line dict from a list of word dicts."""
    sorted_words = sorted(words, key=lambda w: w["x0"])
    return {
        "y0": min(w["y0"] for w in sorted_words),
        "y1": max(w["y1"] for w in sorted_words),
        "words": sorted_words,
    }
