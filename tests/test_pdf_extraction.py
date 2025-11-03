from __future__ import annotations

import io

import fitz  # PyMuPDF

from kg_rag_common.text_extraction import extract_pdf_blocks


def make_sample_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Heading 1", fontsize=24)
    page.insert_text((72, 120), "```python\nprint('hi')\n```", fontsize=12)
    page.insert_text((72, 180), "Some additional text paragraph.", fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data


def test_extract_pdf_blocks_detects_code_and_text(tmp_path):
    pdf_bytes = make_sample_pdf_bytes()
    blocks = extract_pdf_blocks(pdf_bytes)

    types = {b.block_type for b in blocks}
    assert "code" in types
    assert "text" in types

    # heading path should include "Heading 1" for at least one block
    assert any("Heading 1" in (b.heading_path or []) for b in blocks)

    # code block contains print('hi')
    code_blocks = [b for b in blocks if b.block_type == "code"]
    assert any("print('hi')" in b.content for b in code_blocks)

