"""Make a DOCX in memory."""

from __future__ import annotations

import io

from docx import Document


def build_docx(text: str) -> bytes:
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
