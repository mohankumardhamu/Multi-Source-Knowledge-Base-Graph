from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import fitz  # PyMuPDF


@dataclass
class Block:
    page_from: int
    page_to: int
    heading_path: list[str]
    block_type: str  # "text" | "code"
    token_count: int
    content: str


def _token_count(text: str) -> int:
    return len(text.split())


def _split_fenced_code(text: str) -> List[tuple[str, str]]:
    """Split text into segments: (type, content), type is 'text' or 'code'.
    Recognizes triple backtick fenced blocks.
    """
    lines = text.splitlines()
    segments: List[tuple[str, str]] = []
    buf: list[str] = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                # closing fence
                segments.append(("code", "\n".join(buf).strip()))
                buf = []
                in_code = False
            else:
                # starting fence
                if buf:
                    segments.append(("text", "\n".join(buf).strip()))
                    buf = []
                in_code = True
        else:
            buf.append(line)
    if buf:
        segments.append((("code" if in_code else "text"), "\n".join(buf).strip()))
    return [(t, s) for t, s in segments if s]


def extract_pdf_blocks(pdf_bytes: bytes) -> list[Block]:
    """Extract text and code blocks from a PDF and naïvely infer headings.

    - Headings: the first span with font size >= 18 on a page becomes the page heading.
    - Blocks: split page text by fenced code blocks (``` ... ```).
    """
    blocks: list[Block] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i, page in enumerate(doc, start=1):
        heading_path: list[str] = []
        try:
            d = page.get_text("dict")
            max_span = None
            max_size = 0.0
            for b in d.get("blocks", []):
                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        size = float(s.get("size", 0))
                        text = (s.get("text") or "").strip()
                        if text and size > max_size:
                            max_size = size
                            max_span = text
            if max_span and max_size >= 18:
                heading_path = [max_span]
        except Exception:
            heading_path = []

        page_text = page.get_text("text") or ""
        for seg_type, seg_text in _split_fenced_code(page_text):
            blocks.append(
                Block(
                    page_from=i,
                    page_to=i,
                    heading_path=heading_path,
                    block_type=("code" if seg_type == "code" else "text"),
                    token_count=_token_count(seg_text),
                    content=seg_text,
                )
            )
    return blocks

