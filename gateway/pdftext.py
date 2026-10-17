"""One-page text PDFs. Shared with scripts/pdftext.py."""

from __future__ import annotations


def read_pdf_lines(data: bytes) -> list[str]:
    text = data.decode("latin-1", errors="replace")
    lines: list[str] = []
    index = 0
    while True:
        start = text.find("(", index)
        if start < 0:
            break
        chars: list[str] = []
        i = start + 1
        while i < len(text):
            char = text[i]
            if char == "\\" and i + 1 < len(text):
                chars.append(text[i + 1])
                i += 2
                continue
            if char == ")":
                break
            chars.append(char)
            i += 1
        lines.append("".join(chars))
        index = i + 1
    return [line for line in lines if line.strip()]
